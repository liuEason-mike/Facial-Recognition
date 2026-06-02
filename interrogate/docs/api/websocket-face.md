# WebSocket 面部分析

## `WS /ws/face`

统一服务端口为 `5000`：

```text
ws://<host>:5000/ws/face
```

请求：

```json
{
  "id": "1",
  "image": "<jpeg_base64_without_data_url_prefix>",
  "test_status": 0,
  "client_seq": 12
}
```

字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string / number | 是 | 嫌疑人编号，后端写入 `suspect_id` |
| `image` | string | 是 | JPEG Base64，不包含 `data:image/jpeg;base64,` 前缀 |
| `test_status` | number | 否 | `0` 实时检测并采集/异步训练基线，`1` 基线检测结束并使用 ready 基线执行异常评分，`2` 本次审讯结束并释放该嫌疑人的内存模型缓存 |
| `client_seq` | number | 否 | 前端发送帧序号；后端原样回显，便于定位慢回包和丢弃过期帧 |

成功响应现状为分析结果对象，不包裹 `{code,msg,data}`。WebSocket 错误响应统一使用 `{code,msg,data}`。后续如要统一成功响应结构，必须同步更新前端 TypeScript 类型和页面解析逻辑。

`baseline_status=released` 只表示异常检测模型缓存已释放；后端仍会正常返回人脸检测、情绪、头姿、视线、心率、AU 和区域坐标等实时展示字段。

关键响应字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string / number | 前端传入的嫌疑人编号 |
| `suspect_id` | string | 入库用嫌疑人编号 |
| `client_seq` | number | 前端传入的帧序号，未传时不返回 |
| `frame` | number | 当前帧编号 |
| `time_sec` | number | 毫秒时间戳 |
| `processing_ms` | number | 后端处理该帧总耗时，单位毫秒 |
| `performance` | object | 后端分段耗时，包含 `decode_ms`、`face_analyze_ms`、`face_landmark_ms`、`emotion_ms`、`db_ms`、`baseline_ms`、`anomaly_ms`、`total_ms` |
| `dominant_emotion` | number | 主导情绪，`1` 愤怒、`2` 厌恶、`3` 恐惧、`4` 快乐、`5` 悲伤、`6` 惊讶、`7` 中性 |
| `emotion_scores` | object | 七类情绪分数 |
| `heart_rate` | number | 心率 |
| `gaze_direction` | number | 视线方向 |
| `head_pose` | object | `pitch`、`yaw`、`roll` |
| `attention` | number | 注意力标签，当前基于 pitch/yaw 简化判断 |
| `au_intensities` | object | AU 强度 |
| `region` | object | 人脸、眼睛、眉毛、嘴部等区域坐标 |
| `left_eye_gaze` | object | 左眼凝视角 |
| `right_eye_gaze` | object | 右眼凝视角 |
| `baseline_status` | string | 基线状态：`collecting`、`training`、`ready`、`not_ready`、`failed`、`released` |
| `anomaly_status` | string | 异常评分状态：`collecting`、`ready`、`skipped`、`released` |
| `anomaly_data` | object | `test_status=1` 且 `baseline_status=ready` 时可能返回异常评分；当前测速阶段不写入 `emotion_anomaly` 表 |

兜底响应：

- 若图像解码成功但面部分析模型未返回有效结果，或面部分析过程抛出异常，服务端仍返回 EmotionFrame 形态对象，不返回空对象。
- 此时 `emotion_scores` 固定为：

```json
{
  "angry": 0,
  "disgust": 0,
  "fear": 0,
  "happy": 0,
  "sad": 0,
  "surprise": 0,
  "neutral": 0
}
```

- 兜底帧不写入 `emotion_real_time`，不参与基线采集、训练或异常评分；`test_status=2` 仍会释放该嫌疑人的基线缓存。
- 情绪模型推理默认通过 `FACE_EMOTION_INFER_EVERY_N_FRAMES=5` 降频运行，其余帧复用最近一次情绪分布；`performance.emotion_ms` 可用于观察该段耗时。

错误响应：

```json
{
  "code": 40001,
  "msg": "invalid_json",
  "data": null
}
```
