# html-interrogate 基准检测与异常波形展示设计草案

## 1. 背景

前端页面需要接入 `/ws/face` 的基准检测结束状态，并展示后端孤立森林模型返回的 `anomaly_data`。本草案仅用于需求讨论，不包含实现代码。

已读取接口文档：

- `docs/api/base_emotion.md` 的“异常数据展示”部分。
- `docs/api/websocket-face.md` 的 `/ws/face` 请求与响应字段说明。

## 2. 接口事实

`/ws/face` 客户端请求当前结构：

```json
{
  "id": 1,
  "image": "<BASE64编码的摄像头帧>",
  "test_status": 0
}
```

`test_status` 在文档和后端代码中的含义：

| 值 | 含义 | 后端行为 |
| --- | --- | --- |
| `0` | 开始检测 / 实时基础检测 | 返回基础面部分析结果，不返回或不保证返回 `anomaly_data`，后端开始根据id开始生成孤立模型，后端的逻辑代码已有。 |
| `1` | 基准检测结束 | 基于历史实时帧训练孤立森林模型，并对当前帧返回 `anomaly_data` |
| `2` | 检测完成 / 异常评分 | 使用已训练模型对当前帧返回 `anomaly_data` |

`anomaly_data` 字段结构：

```json
{
  "emotion": { "score": -0.0737, "is_anomaly": true },
  "heart_rate": { "score": 0, "is_anomaly": false },
  "head_pose": { "score": -0.04, "is_anomaly": true },
  "eye_gaze": { "score": 0, "is_anomaly": false },
  "au_intensity": { "score": -0.055, "is_anomaly": true }
}
```

字段语义：

- `score`：异常分数，数值越低越异常。
- `is_anomaly`：是否异常，`true` 表示异常，`false` 表示正常。
- 前端不自行判断阈值，异常结论以 `is_anomaly` 为准。

## 3. 需要确认的契约点

用户最新需求提到：

- 默认 `/ws/face` 传值是 `0`。
- 点击“基准检测结束”按钮后传值是 `1`。
- 彻底结束是 `2`。



| 方案 | 前端状态流 | 优点 | 风险 |
| --- | --- | --- | --- |
| 推荐方案 A | 默认 `0`，点击基准检测结束后持续发送 `1`，后端停止采集并在 ready 后输出 `anomaly_data`。发送 `2` 是本次审讯结束并释放模型缓存 | 避免每帧重复训练模型，符合文档和后端代码 | 需要继续验证关闭异常表写入后的实时速率 |


建议采用方案 A。按钮点击的核心语义是“结束基准采集并触发一次训练”，而不是让每一帧都重复训练。

## 4. 前端交互设计

### 4.1 按钮位置

在演示视频左上角现有操作按钮组中新增按钮：

- 按钮文案：`基准检测结束`
- 位置：与 `开始`、`暂停/继续`、`结束`、`重置` 同一组，保持当前紧凑按钮风格。
- 禁用条件：
  - 讯问未运行时禁用。
  - 已点击且等待首个 `anomaly_data` 返回时禁用。
  - 基准已结束并进入异常监测后禁用，避免重复训练。

### 4.2 状态流

推荐状态：

| 前端状态 | 按钮状态 | 发送值 |
| --- | --- | --- |
| 未开始 | 禁用 | 无发送 |
| 基准采集中 | 可点击 | 每帧 `test_status=0` |
| 基准结束处理中 | 禁用，显示处理中 | 发送 `test_status=1`，后端停止采集并等待模型 ready |
| 异常监测中 | 禁用，显示已完成 | 持续发送 `test_status=1` 并接收异常评分 |
| 讯问结束 / 重置 | 重置按钮状态 | 发送一次 `test_status=2` 释放模型缓存，内部状态归零 |

## 5. `anomaly_data` 波形展示方案

### 5.1 推荐展示方式

新增一个“异常波形”面板，展示五个异常域的连续波形：

| 字段 | 中文展示名 | 颜色建议 |
| --- | --- | --- |
| `emotion` | 情绪 | 蓝色 |
| `heart_rate` | 心率 | 绿色 |
| `head_pose` | 头部姿态 | 黄色 |
| `eye_gaze` | 眼动 | 青色 |
| `au_intensity` | AU 强度 | 红色 |

面板位置建议：

- 放在左侧栏“生理与姿态数据”下方、“设备状态”上方。
- 不占用视频区域，不影响现有 AU52 表格和视频大小。
- 异常波形”面板下方，增加一个小型告警状态条(当五个类型返回is_anomaly为异常的时候)。

### 5.2 波形表现

使用单个 SVG 折线图，不新增图表库：

- 横轴：最近一段时间的帧序列，例如最近 120 个 anomaly 点。
- 纵轴：异常风险强度，越高越异常。
- 每个域一条连续折线。
- `is_anomaly=true` 的点用亮色圆点、短脉冲或竖向告警线标记。
- 图表下方显示五个小状态标签：当前分数、正常/异常。

### 5.3 分数转换

由于后端说明是“`score` 越低越异常”，前端不直接把原始 `score` 当成越高越危险的值。

建议转换为展示用风险值：

```text
risk = score < 0 ? clamp(abs(score) / 0.1, 0, 1) : 0
```

展示规则：

- 波形画 `risk`，便于用户直观看到“越高越异常”。
- tooltip 或状态标签显示原始 `score`，保留后端真实数值。
- 是否异常只认后端 `is_anomaly`，前端不自行推断。
- 如果后端后续给出固定 score 范围或阈值，前端再把 `0.1` 改成接口配置或常量。

### 5.4 异常如何突出

当任一域 `is_anomaly=true`：

- 对应折线最后一段加亮。
- 对应状态标签显示 `异常`，使用危险色。
- 面板标题右侧显示 `异常 N 项`。
- 不弹窗打断讯问流程，异常波形”面板下方，增加一个小型告警状态条(当五个类型返回is_anomaly为异常的时候)

当全部正常：

- 标题显示 `正常`。
- 折线保持低亮度连续波动。

当未收到 `anomaly_data`：

- 面板显示 `等待基准检测结束`。
- 不生成假数据。
- 波形区域保留空态网格，避免页面跳动。

## 6. 前端实现边界

计划修改范围：

- `src/types/face.ts`：把 `anomaly_data` 从 `Record<string, unknown>` 收紧为明确类型。
- `src/composables/useFaceAnalysisSocket.ts`：增加 `test_status` 状态控制、一次性发送 `1` 的能力，以及结束/重置回到 `0`。
- `src/composables/useInterrogationRoom.ts`：暴露基准状态和按钮事件。
- `src/components/interrogation/ControlPanel.vue`：新增“基准检测结束”按钮。
- `src/components/interrogation/AnomalyWaveformPanel.vue`：新增异常波形组件。
- `src/views/SimulationInterrogationView.vue`：接入按钮事件和异常波形面板。
- `src/utils/faceAnalysis.ts` 或新增 `src/utils/anomalyData.ts`：负责 `anomaly_data` 字段归一化和风险值计算。

不在本次前端改动中做：

- 不修改后端孤立森林模型逻辑。
- 不新增 HTTP 接口。
- 不引入新的图表库。
- 不改变现有 AU52 表格大小和视频显示大小。

## 7. 验收标准

- 讯问运行后，默认发送帧中的 `test_status` 为 `0`。
- 点击“基准检测结束”后，前端能按确认后的状态流发送 `1`。
- 基准结束后，后端返回的 `anomaly_data` 能进入前端状态。
- 异常波形面板能连续展示五个域的最新数据。
- `is_anomaly=true` 的域有明显但不打断流程的视觉高亮。
- 未收到 `anomaly_data` 时显示稳定空态，不报错、不闪烁。
- 结束或重置后，前端内部 `test_status` 回到 `0`。

## 8. 建议测试

- 单元测试：`test_status` 默认值、点击基准结束后的发送值、结束重置逻辑。
- 单元测试：`anomaly_data` 归一化，缺字段、`score=null`、`is_anomaly=false` 的展示结果。
- 组件测试或源码结构测试：页面存在“基准检测结束”按钮和 `AnomalyWaveformPanel`。
- 手工联调：启动讯问，采集一段基线，点击按钮，确认后端返回 `anomaly_data` 后波形开始更新。
