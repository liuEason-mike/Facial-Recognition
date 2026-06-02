# `/ws/asr` 实时转写说话人分离问题分析

日期：2026-05-20

## 1. 问题概述

现象：

- 当前实时语音转文字只能得到统一文本流。
- 回包没有稳定的 `speaker`、片段起止时间、声纹聚类结果。
- 前端展示时只能把文本按收到时间追加，无法自动拆分为“说话人 A / 说话人 B / 多说话人”。
- 后端 `audio_records` 只保存 `suspect_id` 和 `text`，无法持久化说话人归属、分段时间轴和置信度。

结论：

“说话人分离”不是普通文本后处理。可靠方案必须基于音频信号做 speaker diarization，并把 diarization 的时间段与 ASR 转写片段对齐。仅在转写完成后拿一段纯文本去猜“谁说的”，只能做弱推断，不能满足“精准拆分归类”。

## 2. 当前链路事实

### 2.1 前端当前通过后端 `/ws/asr` 进入公有 ASR

`html-interrogate` 当前 ASR 主链路连接项目后端 `/ws/asr`：

- `html-interrogate/src/composables/useAsrSocket.ts`
- `docs/api/websocket-asr.md:5-8`

前端音频采集方式：

- 使用浏览器单麦克风音频流。
- `ScriptProcessorNode` 取单通道 PCM。
- 重采样为 16k。
- 转为 PCM S16LE Base64。
- 通过 WebSocket 发送给项目后端 `/ws/asr`，由后端代理 DashScope 公有实时 ASR。

关键代码：

- `html-interrogate/src/composables/useAsrSocket.ts`

这意味着当前后端 `/ws/asr` 代理和入库逻辑已回到 `html-interrogate` 主链路上。说话人分离仍按旁路设计：前端累计短窗口 WAV，提交给 `/api/asr/diarization/align`，再用 ASR 时间片做文本对齐。

### 2.2 前端只抽文本字段

当前前端解析 ASR 回包时，只递归提取以下文本字段：

- `text`
- `partial`
- `result`
- `transcript`
- `content`
- `sentence`

关键代码：

- `html-interrogate/src/utils/asr.ts:3-24`

`TranscriptSegment` 当前只有：

- `id`
- `time`
- `text`
- `raw`

关键代码：

- `html-interrogate/src/types/asr.ts:9-14`

缺少：

- `speaker_label`
- `speaker_index`
- `start_ms`
- `end_ms`
- `is_final`
- `confidence`
- `seq_start`
- `seq_end`

因此即使外部服务未来返回 speaker 信息，前端当前也不会归一化展示。

### 2.3 后端 `/ws/asr` 当前是 DashScope 代理实现

后端 `app/routes/ws/audio.py` 当前存在这些限制：

- 使用全局 `_active_ws`，多连接时后来的连接会覆盖前面的连接。
- `insert_to_neo4j` 定义了但没有在当前回包处理中调用。
- Neo4j 地址、用户名、密码硬编码在代码里。
- DashScope `result-generated` 回包会被归一化为 `[{start,end,text}]`，但 ASR 客户端仍是全局单例，多连接隔离仍需后续重构。

关键代码：

- `app/routes/ws/audio.py:15-20`
- `app/routes/ws/audio.py:38-48`
- `app/routes/ws/audio.py:51-68`
- `app/routes/ws/audio.py:76-93`

后端 ASR 客户端 `app/service/audio/qwen_asr.py` 当前也有约束：

- 默认 ASR 地址为 DashScope 公有 WebSocket，可通过 `ASR_DASHSCOPE_ENDPOINT` 覆盖。
- `_asr_client` 是全局单例。
- 发送给 DashScope 的二进制音频帧不携带 `suspect_id`、`session_id` 或 diarization 控制参数，这些业务字段仍由项目后端维护。

关键代码：

- `app/service/audio/qwen_asr.py:22`
- `app/service/audio/qwen_asr.py:48-55`
- `app/service/audio/qwen_asr.py:83-84`

### 2.4 数据库无法存说话人分离结果

当前 `audio_records` 模型只有：

- `id`
- `suspect_id`
- `text`
- `create_time`
- `update_time`

关键代码：

- `app/models/audio_records.py:5-11`
- `docs/SPEC/database.md:11-22`

这无法表达一次多人对话中的片段边界，也无法保存同一段文本属于哪个说话人。

## 3. 技术边界

### 3.1 说话人分离与说话人识别不同

说话人分离（speaker diarization）回答的是：

```text
这段音频里，什么时候是谁在说话？
```

它通常只能输出：

- `speaker_a`
- `speaker_b`
- `speaker_c`

它不会天然知道：

- 谁是讯问员。
- 谁是嫌疑人。
- 谁是真实姓名。

如果要把 `speaker_a` 映射成“讯问员”、`speaker_b` 映射成“嫌疑人”，还需要：

- 人工确认映射。
- 角色先验，例如讯问员先开场。
- 声纹注册样本。
- 多麦克风或独立通道。

### 3.2 单麦克风实时分离存在天然上限

当前浏览器采集的是单声道麦克风流。单麦克风在以下场景中很难保证“精准”：

- 两人同时说话。
- 环境噪声较大。
- 麦克风距离两人很近或很远。
- 两个说话人音色相近。
- 说话片段过短，例如“嗯”“对”“不是”。

因此系统应把目标定义为：

- 自动聚类为 `speaker_a`、`speaker_b`、`speaker_c`。
- 给出置信度。
- 支持后续人工修正或角色映射。
- 对低置信度片段明确标记 `unknown` 或 `speaker_uncertain`。

不建议在协议层承诺 100% 精准。

### 3.3 只用文本做归类不可靠

如果只拿 ASR 文本做分类，例如根据“我问你”“我没有”等语义判断说话人，会遇到：

- 审讯双方可能使用相似短句。
- ASR partial 会反复修正，导致归类频繁变动。
- 没有声音特征，无法识别同一句话是谁说的。
- 不适用于三人及以上场景。

文本分类只能作为辅助策略，不能作为主方案。

## 4. 可选方案

### 4.1 方案 A：使用外部 ASR 原生说话人分离能力

如果当前外部 ASR 服务支持 diarization，推荐优先启用。

后端或前端只需要：

- 请求中增加 `speaker_diarization=true`、`speaker_count_hint=2` 等控制字段。
- 回包中消费 `speaker_label`、`start_ms`、`end_ms`、`is_final`。
- 入库和前端展示扩展字段。

优点：

- 对现有系统侵入较小。
- 本地无需部署大模型。
- 实时性通常最好。

风险：

- 当前接口文档只展示了 `partial` 文本，没有 speaker 字段。
- 需要确认外部服务是否支持、字段格式是否稳定、计费和延迟是否可接受。
- 如果前端继续直连外部服务，后端仍拿不到原始音频和完整分段，入库能力会弱。

### 4.2 方案 B：后端接管 ASR 流并引入本地/独立 diarization 服务

推荐作为可控性最强的工程方案。

链路改为：

```text
浏览器麦克风
  -> /ws/asr
  -> ASR 转写服务
  -> Diarization 服务
  -> 时间轴对齐
  -> 返回带 speaker 的 segment
  -> 写入 MySQL / 可选 Neo4j
```

核心模块：

- `AsrConnectionManager`：每个前端连接一份会话状态，替代全局 `_active_ws`。
- `AudioChunkBuffer`：按 `seq` 缓存最近几秒 PCM，记录采样率和时间轴。
- `DiarizationService`：VAD、声纹 embedding、聚类、说话人标签维护。
- `TranscriptAligner`：把 ASR 片段和 diarization 时间段对齐。
- `SpeakerSessionState`：维护当前会话内 `speaker_a/b/c` 的稳定映射。
- `AudioRecordsRepository`：保存带 speaker 的分段结果。

优点：

- 后端可以统一入库、审计、回放和前端协议。
- 可以控制 speaker 标签稳定性。
- 后续可接入声纹注册或人工校正。

风险：

- 引入模型依赖和 CPU/GPU 资源压力。
- 实时 diarization 通常需要 1-3 秒滑动窗口，会增加延迟。
- 需要明确模型部署方式、硬件要求和降级策略。

### 4.3 方案 C：双通道或多设备采集

如果业务允许使用双麦克风或多路设备，可以让每个说话人对应独立通道或设备。

优点：

- 工程上最稳定，归类准确率最高。
- 可以避免复杂聚类。

风险：

- 对硬件和现场部署有要求。
- 浏览器采集多设备、多通道权限和兼容性更复杂。
- 不满足“单麦自动分离”的默认预期。

### 4.4 方案 D：文本后处理弱分类

仅作为临时兜底。

做法：

- 继续使用现有统一 ASR 文本。
- 用规则或 LLM 根据上下文把文本标成“疑似讯问员 / 疑似嫌疑人”。

优点：

- 改动小。
- 能快速提供演示效果。

风险：

- 不是真正说话人分离。
- 对短句、插话、多人场景准确率低。
- 不建议作为正式业务方案。

## 5. 推荐方案

推荐采用“两阶段”路线：

第一阶段：确认外部 ASR 能力并修正后端链路

- 确认外部 ASR 是否支持 speaker diarization。
- 若支持，优先使用方案 A。
- 将 `html-interrogate` ASR 链路从直连外部服务改回后端 `/ws/asr`，由后端统一转发、归一化、入库。
- 修复后端全局 `_active_ws` 和 `suspect_id="0"` 问题。
- 扩展前端类型和展示字段，先支持 `speaker_label`。

第二阶段：引入可控的后端 diarization 服务

- 如果外部 ASR 不支持 speaker 字段，或准确率/协议不可控，再落地方案 B。
- 后端维护音频 buffer 和 speaker session state。
- 对最终 ASR segment 做说话人对齐。
- 对 partial 只展示临时文本，不立即入库；对 final segment 入库。

这样可以先用较小成本打通协议和数据结构，再根据外部服务能力决定是否部署本地模型。

## 6. 建议 WebSocket 协议

### 6.1 客户端请求

保持现有字段兼容，新增可选字段：

```json
{
  "type": "audio",
  "audio": "<pcm_s16le_base64>",
  "seq": 12,
  "suspect_id": "1",
  "session_id": "session-20260520-001",
  "speaker_diarization": true,
  "speaker_count_hint": 2,
  "end": false
}
```

字段说明：

- `session_id`：绑定本次审讯会话，避免多人或多轮审讯混写。
- `speaker_diarization`：是否启用说话人分离。
- `speaker_count_hint`：说话人数提示，默认可为 `2`，但不强制。

### 6.2 服务端返回

建议新增标准 segment 回包：

```json
{
  "type": "segment_result",
  "suspect_id": "1",
  "session_id": "session-20260520-001",
  "seq_start": 10,
  "seq_end": 18,
  "data": {
    "text": "你今天几点到的现场？",
    "speaker_label": "speaker_a",
    "speaker_name": "说话人 A",
    "speaker_index": 0,
    "speaker_confidence": 0.86,
    "start_ms": 3200,
    "end_ms": 5200,
    "is_final": true
  }
}
```

低置信度或重叠说话建议返回：

```json
{
  "type": "segment_result",
  "data": {
    "text": "嗯，对。",
    "speaker_label": "unknown",
    "speaker_name": "说话人待确认",
    "speaker_confidence": 0.42,
    "is_final": true
  }
}
```

partial 回包可以保留，但建议加 `is_final=false`，前端只临时展示，不写入最终记录。

## 7. 建议数据库调整

当前 `audio_records` 无法满足多人对话分段。建议新增字段，或新增 `audio_segments` 表。

推荐新增独立表：

```sql
CREATE TABLE IF NOT EXISTS audio_segments (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  session_id VARCHAR(64),
  suspect_id VARCHAR(64),
  speaker_label VARCHAR(32),
  speaker_name VARCHAR(64),
  speaker_index INT,
  speaker_confidence DOUBLE,
  text TEXT,
  start_ms BIGINT,
  end_ms BIGINT,
  seq_start INT,
  seq_end INT,
  is_final BOOLEAN DEFAULT TRUE,
  raw_asr JSON,
  raw_diarization JSON,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_audio_segments_session_time (session_id, start_ms),
  INDEX idx_audio_segments_speaker (session_id, speaker_label),
  INDEX idx_audio_segments_suspect_id (suspect_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

保留 `audio_records` 作为兼容旧逻辑的全文或简化记录；新功能以 `audio_segments` 为准。

## 8. 后端改造点

### 8.1 路由层

`app/routes/ws/audio.py` 应只负责：

- 解析客户端消息。
- 获取当前 WebSocket 连接上下文。
- 调用 service。
- 发送 service 产出的标准回包。

不建议继续在路由层持有全局 `_active_ws` 或硬编码 Neo4j 配置。

### 8.2 ASR 客户端层

`app/service/audio/qwen_asr.py` 应调整为：

- endpoint 从环境变量读取。
- 每个前端会话独立管理外部 ASR 连接，或通过连接池绑定 session。
- 向外部 ASR 透传 `suspect_id`、`session_id` 和 diarization 控制参数。
- 能区分 partial 与 final。

### 8.3 Diarization 服务层

如果外部 ASR 不返回 speaker 字段，需要新增服务：

- 输入：PCM chunk、seq、采样率、session_id。
- 输出：带 `speaker_label` 的时间段列表。
- 状态：每个 session 独立维护 speaker embedding 和聚类结果。
- 延迟策略：按 1-3 秒滑动窗口更新，final segment 后稳定入库。

### 8.4 对齐层

需要把 ASR 文本片段和 diarization 时间段对齐：

- 如果 ASR 提供 `start_ms/end_ms`，直接按时间重叠最大者匹配。
- 如果 ASR 只返回纯文本，没有时间戳，则只能按接收时间和 seq 粗略映射，准确率会下降。
- 多个 speaker 覆盖同一文本时，应拆分片段或标记 `overlap` / `unknown`。

## 9. 前端改造点

前端类型需要扩展：

- `TranscriptSegment.speakerLabel`
- `TranscriptSegment.speakerName`
- `TranscriptSegment.speakerConfidence`
- `TranscriptSegment.startMs`
- `TranscriptSegment.endMs`
- `TranscriptSegment.isFinal`

展示建议：

- 每条转写前显示“说话人 A / B / C”。
- 不同 speaker 使用稳定颜色。
- `unknown` 或低置信度片段显示为“待确认”。
- partial 文本单独展示，不混入最终历史。
- 支持后续人工将 `speaker_a` 映射成“讯问员”、`speaker_b` 映射成“嫌疑人”。

## 10. 主要风险

1. 当前前端已回到后端 `/ws/asr` 主链路，但后端 ASR 客户端仍是全局单例，多连接隔离需要继续治理。
2. 当前外部 ASR 回包文档没有 speaker 字段，能力需要确认。
3. 单麦克风多人分离无法保证 100% 精准，尤其是重叠说话和短句。
4. 本地 diarization 会增加模型依赖、运行资源和延迟。
5. 当前后端 ASR 全局单例和 `_active_ws` 不支持多连接，会影响多人并发。
6. 当前数据库缺少会话维度，后续应补 `session_id`，否则多轮审讯数据难以隔离。

## 11. 建议验证指标

功能指标：

- 是否能稳定输出 `speaker_a`、`speaker_b` 多类标签。
- 同一说话人标签在会话内是否稳定。
- partial/final 是否正确区分。
- `speaker_label`、时间轴、文本是否成功入库。

质量指标：

- 转写延迟 P50 / P95。
- 说话人标签延迟 P50 / P95。
- 单人、双人、三人场景下的 speaker attribution accuracy。
- 重叠说话场景下的 `unknown` 标记比例。
- ASR WER 与引入 diarization 后的端到端错误率。

联调指标：

- 前端是否能按 speaker 分组展示。
- 停止审讯后是否发送结束包并释放连接。
- 多个浏览器连接是否互不串话。
- 数据库中同一 `session_id` 的片段是否按 `start_ms` 可恢复完整对话。

## 12. 需要确认的问题

进入实现前建议确认：

1. 当前外部 ASR 服务是否支持 speaker diarization，返回字段是什么。
2. 说话人数是否通常固定为 2，还是需要支持 3 人及以上。
3. 业务需要的是“说话人 A/B/C”，还是必须映射为“讯问员/嫌疑人/其他人”。
4. 是否进一步把后端 `/ws/asr` 从全局单例重构为每连接独立会话。
5. 生产环境是否允许部署额外音频模型，以及是否有 GPU。
6. 是否接受 1-3 秒的说话人分离延迟。
