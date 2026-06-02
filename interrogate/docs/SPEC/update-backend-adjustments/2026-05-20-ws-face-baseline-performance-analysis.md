# `/ws/face` 基准对比开启后的性能问题分析

日期：2026-05-20

更新：2026-05-21

现已调整为：`test_status=0` 采集样本并异步训练/更新基线模型，`test_status=1` 表示基准测试结束并在模型 ready 后做异常评分，`test_status=2` 表示本次审讯彻底结束并释放该嫌疑人的内存模型缓存。当前测速阶段已临时关闭 `emotion_anomaly` 同步写入，用于隔离数据库提交对实时速率的影响。无论基线模型状态是 `ready` 还是 `released`，`/ws/face` 都必须继续返回完整实时检测展示数据，模型状态只影响 `anomaly_data`。

## 1. 问题概述

现象：

- 关闭基准模型对比逻辑，只执行业务模型推理时，`/ws/face` 响应速度较快，返回字段完整。
- 开启基准模型对比后，接口整体变慢，最终推送到前端的数据跟不上前端发帧速率。

结论：

旧实现的问题不是单个字段缺失导致，而是 `/ws/face` 同一条 WebSocket 消息处理链路中混入了同步训练、同步模型文件读写、同步数据库写入和无背压的固定频率发帧。基准对比开启后，单帧处理耗时超过前端 5 FPS 的发送间隔，消息开始排队，前端收到的是延迟结果，表现为“返回跟不上前端速率”。

## 2. 当前链路事实

服务端入口位于 `app/routes/ws/register.py`：

- `ws.receive()` 收到一帧。
- 调用 `process_video(payload)`。
- `process_video` 内部同步调用 `process_frame_ws_payload(...)`。
- 处理完成后才 `ws.send(...)`。

关键代码：

- `app/routes/ws/register.py:13-22`
- `app/routes/ws/video.py:25-32`
- `app/service/video/realtime_features.py:145-282`

这意味着同一个连接内，当前实现是严格串行的：某一帧没有处理完，服务端不会处理下一帧，也不会提前发送状态回包。

前端 `html-interrogate` 当前固定 5 FPS 发送视频帧：

- `html-interrogate/src/constants/session.ts:2`
- `html-interrogate/src/composables/useFaceAnalysisSocket.ts:74-78`

前端基准状态流：

- 采集中：每帧 `test_status=0`
- 点击基准结束后：持续发送 `test_status=1`，后端停止采集并在基线 ready 后做异常评分
- 停止本次审讯：发送一次 `test_status=2`，后端释放该嫌疑人的基线状态和内存模型缓存

关键代码：

- `html-interrogate/src/utils/faceTestStatus.ts:28-41`

所以当前前端主链路在基准结束后会持续发送 `test_status=1`，不再把 `test_status=2` 当作异常监测帧。`test_status=2` 只作为审讯结束释放信号，但后端仍先执行基础实时检测并返回展示字段。

## 3. 根因拆解

### 3.1 旧实现中 `test_status=1` 在请求主链路同步训练模型

`app/service/video/realtime_features.py:178-230` 中，`test_status == 1` 会同步执行：

1. 从数据库读取该嫌疑人的历史实时帧，最多 5000 条。
2. 将 ORM 对象逐条转换成孤立森林需要的字典结构。
3. 训练孤立森林模型。

`app/service/video/isolation_forest/iso_forest_detector.py:184-202` 中，训练会对 5 个域分别训练模型：

- `emotion`
- `heart_rate`
- `head_pose`
- `eye_gaze`
- `au_intensity`

每个域内部使用：

- `IsolationForest(n_estimators=300, ...)`
- `clf.fit(X)`
- `pickle.dump(clf, f)`

关键代码：

- `app/service/video/isolation_forest/iso_forest_detector.py:159-160`
- `app/service/video/isolation_forest/iso_forest_detector.py:193-200`

这部分属于 CPU 密集 + 磁盘 IO 操作，不适合放在逐帧 WebSocket 请求主路径里。

### 3.2 旧实现中异常评分帧每帧都从磁盘反序列化模型

旧实现中，异常评分帧每帧都会调用 `_iso_detector.score_record(...)`。

`score_record` 内部每次都会执行 5 次 `load_model`：

- `app/service/video/isolation_forest/iso_forest_detector.py:204-212`
- `app/service/video/isolation_forest/iso_forest_detector.py:240-244`

也就是说，异常监测进入稳定期后，前端 5 FPS 下单连接约等于每秒 25 次 pickle 文件读取与反序列化。随着连接数、磁盘状态或模型文件变大，单帧耗时会明显上升。

### 3.3 开启异常评分后每帧增加一次异常表写入

基础检测每帧都会写 `emotion_real_time`：

- `app/service/video/realtime_features.py:168-174`
- `app/repository/emotion_real_time.py:29-36`

旧实现开启异常评分后，还会写 `emotion_anomaly`：

- `app/service/video/realtime_features.py:250-253`
- `app/service/video/realtime_features.py:276-278`
- `app/repository/emotion_anomaly.py:20-25`

因此异常监测阶段每帧至少两次同步事务提交。前端 5 FPS 时，单连接每秒约 10 次 commit。数据库延迟稍高时，会直接放大 WebSocket 回包延迟。当前测速阶段已先关闭异常表写入，保留基础实时帧入库，用于观察速率变化。

### 3.4 缺少服务端背压和状态回包

当前协议没有明确：

- 服务端正在训练基准模型。
- 基准模型训练完成。
- 当前帧是否跳过异常评分。
- 服务端处理耗时。
- 当前回包对应前端哪一帧。
- 是否因为服务端压力丢弃了旧帧。

前端也没有按“收到上一帧响应后再发下一帧”的节奏发送，而是固定 5 FPS 定时发送。只要服务端单帧耗时超过 200ms，队列就会增长。

### 3.5 查询基线样本存在会话边界风险

`list_by_suspect_id(sid, limit=5000)` 当前只按 `suspect_id` 查询，没有审讯会话边界。查询排序是 `time_sec.asc()` 后 `limit(5000)`，实际拿到的是该嫌疑人最早的 5000 条，而不是“最近 N 条”或“本次基线采集窗口”。

风险：

- 基线训练可能混入历史会话数据。
- 数据越积越多后，训练样本和当前审讯状态不一致。
- 无法准确控制训练数据规模。

## 4. 为什么关闭对比逻辑时表现正常

关闭基准对比后，主链路主要是：

1. Base64 解码。
2. 面部业务模型推理。
3. 写入 `emotion_real_time`。
4. 返回基础分析结果。

开启后额外增加：

1. 旧实现中 `test_status=1` 同步查询最多 5000 条历史数据。
2. 同步训练 5 个 300-tree IsolationForest。
3. 同步保存 5 个模型文件。
4. 每个异常评分帧同步加载 5 个模型文件。
5. 每个异常评分帧同步写入 `emotion_anomaly`。

这些工作叠加后，服务端处理速率低于前端发帧速率，延迟自然会持续累积。

## 5. 建议整改方向

### 5.1 后端短期止血

1. 将基线训练入口前移到 `test_status=0`，持续采集样本并后台训练/更新模型；`test_status=1` 只停止基线采集和训练，不等待训练完成。
2. 为每个 `suspect_id` 或未来的 `session_id` 维护基线状态：`collecting`、`training`、`ready`、`failed`。
3. `training` 期间收到 `test_status=1` 时，只返回基础分析结果并携带 `baseline_status=training`，暂不做异常评分。
4. 训练完成后把模型放入内存缓存，评分时优先使用缓存对象，不再每帧 `pickle.load`。
5. `emotion_anomaly` 写入改为异步队列，或先按固定频率采样写入，例如每秒 1 条或每 N 帧 1 条；当前测速阶段先完全关闭该表同步写入。
6. 对服务端逐帧处理增加耗时日志，例如 `decode_ms`、`business_infer_ms`、`db_ms`、`baseline_train_ms`、`anomaly_score_ms`、`total_ms`。

### 5.2 协议与前端配合

建议在不破坏现有字段的前提下新增可选字段：

```json
{
  "baseline_status": "collecting | training | ready | failed",
  "anomaly_status": "skipped | scoring | ready | failed",
  "client_seq": 12,
  "server_seq": 12,
  "processing_ms": 87,
  "dropped_frames": 0
}
```

前端策略建议：

1. 点击“基准检测结束”后，进入等待状态，不要立即把业务语义理解为模型已可用。
2. 只有收到 `baseline_status=ready` 后，再进入异常波形持续展示。
3. 视频帧发送增加背压：最多允许 1 个或少量 in-flight 帧；服务端未回包时跳过新帧。
4. 回包中如果带 `client_seq`，前端只展示最新序号，丢弃过期回包。

### 5.3 数据侧调整

1. 为基线训练引入 `session_id` 或明确的 `baseline_start_at` / `baseline_end_at`。
2. 查询本次基线窗口的数据，而不是只按 `suspect_id` 查询历史数据。
3. 如果暂时没有会话字段，至少改为查询最近 N 条：先按 `time_sec.desc()` 限制数量，再在内存按时间升序训练。
4. 明确异常表写入频率，避免逐帧无条件事务提交压垮实时链路。

## 6. 推荐落地顺序

第一阶段：可观测性与止血

- 增加分段耗时日志。
- `test_status=0` 调度后台训练；`test_status=1` 停止基线采集和训练，模型 ready 后做异常评分。
- 训练期间 `test_status=1` 跳过异常评分，返回基础结果和 `baseline_status=training`。

第二阶段：缓存与背压

- 模型训练完成后保存在内存缓存。
- `score_record` 支持直接使用缓存模型，避免每帧读 pkl。
- 前端按回包节奏限流，或服务端主动丢弃旧帧。

第三阶段：协议和数据治理

- 引入 `session_id` 或基线采集窗口。
- 更新 `docs/api/websocket-face.md`。
- 更新前端 TypeScript 类型和展示逻辑。
- 明确异常数据写库采样策略。

## 7. 需要验证的指标

整改前后建议记录：

- 前端发送 FPS。
- 服务端实际处理 FPS。
- 单帧总耗时 P50 / P95。
- `test_status=0` 后台基线训练耗时。
- `test_status=1` 评分耗时。
- 每秒 DB commit 次数。
- WebSocket 回包延迟。
- 是否出现过期帧覆盖最新 UI。

验收目标建议：

- 基础分析帧在开启基准对比后仍能稳定返回。
- 训练阶段前端明确显示“基准处理中”，不误判为异常数据缺失。
- 异常监测稳定期单帧服务端处理耗时低于前端发送间隔，或前端具备跳帧背压。
- `anomaly_data` 只在模型 ready 后持续返回。
