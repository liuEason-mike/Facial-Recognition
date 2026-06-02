# 基础展示信息

## 目录
* [审讯管理]()
    * [表情数据实时展现](#实时展示)
    * [异常数据](#异常数据展示)
    * [音频数据展示](#音频数据展示)


## <a name="审讯管理">审讯管理</a>

### <a name="实时展示">实时展示</a>
- 接口名称: 基础展示信息（EmotionFrame）
- 适用场景: 前端展示单帧检测的核心指标（情绪、注视、头部姿态、人脸框、AU 强度等）
- 数据格式: JSON Object
- 请求方式: WebSocket（服务端按帧推送 EmotionFrame JSON）

接口地址

- ws://<host>:5000/ws/face

客户端请求消息（Client -> Server）

```json
{
  "id": 1, // 嫌疑人编号
  "image": "<BASE64编码的摄像头帧>", // 摄像头帧 BASE64 编码
  "test_status": 0 // 检测状态 0/1/2   0=采集并异步训练基线 1=基准结束并异常评分 2=审讯结束并释放模型缓存
}
```

websocket的响应数据

#### 字段

| 字段 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| suspect_id | number | 嫌疑人编号 | 5 |
| frame | number | 当前帧序号 | 5 |
| dominant_emotion | number | 主导情绪标签 /1=愤怒 2=厌恶 3=恐惧 4=快乐 5=悲伤 6=惊讶 7=中性 | 1 |
| emotion_scores | object | 各情绪得分（0–100） | { angry: 6.11, … } |
| emotion_scores.angry | number | 愤怒得分 | 6.11 |
| emotion_scores.disgust | number | 厌恶得分 | 0.000000254 |
| emotion_scores.fear | number | 恐惧得分 | 0.544 |
| emotion_scores.happy | number | 快乐得分 | 0.00000101 |
| emotion_scores.sad | number | 悲伤得分 | 54.607 |
| emotion_scores.surprise | number | 惊讶得分 | 0.000331 |
| emotion_scores.neutral | number | 中性得分 | 38.735 |
| region | object | 统一面部坐标集合（全部像素坐标） | 见下方 |
| region.face | object | 人脸检测框 | { x: 26, y: 230, w: 634, h: 634 } |
| region.face.x | number | 人脸框左上角 x | 26 |
| region.face.y | number | 人脸框左上角 y | 230 |
| region.face.w | number | 人脸框宽度 | 634 |
| region.face.h | number | 人脸框高度 | 634 |
| region.left_eyebrow | object | 左眉毛坐标 | { x1: 80, y1: 260, x2: 120, y2: 255 } |
| region.left_eyebrow.x1 | number | 左眉毛左端点 x | 80 |
| region.left_eyebrow.y1 | number | 左眉毛左端点 y | 260 |
| region.left_eyebrow.x2 | number | 左眉毛右端点 x | 120 |
| region.left_eyebrow.y2 | number | 左眉毛右端点 y | 255 |
| region.right_eyebrow | object | 右眉毛坐标 | { x1: 180, y1: 258, x2: 220, y2: 262 } |
| region.right_eyebrow.x1 | number | 右眉毛左端点 x | 180 |
| region.right_eyebrow.y1 | number | 右眉毛左端点 y | 258 |
| region.right_eyebrow.x2 | number | 右眉毛右端点 x | 220 |
| region.right_eyebrow.y2 | number | 右眉毛右端点 y | 262 |
| region.left_eye | object | 左眼坐标 | { x: 95, y: 290, w: 45, h: 28 } |
| region.left_eye.x | number | 左眼框左上角 x | 95 |
| region.left_eye.y | number | 左眼框左上角 y | 290 |
| region.left_eye.w | number | 左眼框宽度 | 45 |
| region.left_eye.h | number | 左眼框高度 | 28 |
| region.right_eye | object | 右眼坐标 | { x: 195, y: 292, w: 43, h: 27 } |
| region.right_eye.x | number | 右眼框左上角 x | 195 |
| region.right_eye.y | number | 右眼框左上角 y | 292 |
| region.right_eye.w | number | 右眼框宽度 | 43 |
| region.right_eye.h | number | 右眼框高度 | 27 |
| region.mouth | object | 嘴巴坐标 | { x1: 110, y1: 380, x2: 200, y2: 385 } |
| region.mouth.x1 | number | 嘴巴左端点 x | 110 |
| region.mouth.y1 | number | 嘴巴左端点 y | 380 |
| region.mouth.x2 | number | 嘴巴右端点 x | 200 |
| region.mouth.y2 | number | 嘴巴右端点 y | 385 |
| region.nose | object | 鼻子坐标 | { x1: 399, y1: 380, x2: 473, y2: 486 } |
| region.nose.x1 | number | 鼻子左端点 x | 399 |
| region.nose.y1 | number | 鼻子顶端点 y | 380 |
| region.nose.x2 | number | 鼻子右端点 x | 473 |
| region.nose.y2 | number | 鼻子底端点 y | 486 |
| region.chin | object | 下巴坐标 | { x1: 348, y1: 534, x2: 572, y2: 618 } |
| region.chin.x1 | number | 下巴左上角 x | 348 |
| region.chin.y1 | number | 下巴左上角 y | 534 |
| region.chin.x2 | number | 下巴右下角 x | 572 |
| region.chin.y2 | number | 下巴右下角 y | 618 |
| region.teeth | object | 牙齿坐标 | { x1: 389, y1: 529, x2: 491, y2: 534 } |
| region.teeth.x1 | number | 牙齿区域左上角 x | 389 |
| region.teeth.y1 | number | 牙齿区域左上角 y | 529 |
| region.teeth.x2 | number | 牙齿区域右下角 x | 491 |
| region.teeth.y2 | number | 牙齿区域右下角 y | 534 |
| region.left_pupil | object | 左瞳孔坐标 | { x1: 361, y1: 373, x2: 387, y2: 397 } |
| region.left_pupil.x1 | number | 左瞳孔区域左上角 x | 361 |
| region.left_pupil.y1 | number | 左瞳孔区域左上角 y | 373 |
| region.left_pupil.x2 | number | 左瞳孔区域右下角 x | 387 |
| region.left_pupil.y2 | number | 左瞳孔区域右下角 y | 397 |
| region.right_pupil | object | 右瞳孔坐标 | { x1: 505, y1: 380, x2: 531, y2: 403 } |
| region.right_pupil.x1 | number | 右瞳孔区域左上角 x | 505 |
| region.right_pupil.y1 | number | 右瞳孔区域左上角 y | 380 |
| region.right_pupil.x2 | number | 右瞳孔区域右下角 x | 531 |
| region.right_pupil.y2 | number | 右瞳孔区域右下角 y | 403 |
| time_sec | number | Unix 时间戳（毫秒） | 1766465735000 |
| heart_rate | number | 心率（bpm），无值可为 0 | 0 |
| gaze_direction | int | 视线方向代码，0=center，1=left，2=right，3=up，4=down | 0 |
| head_pose | object | 头部姿态角（度） | { pitch: -7.2, yaw: -0.2, roll: -2.5 } |
| head_pose.pitch | number | 俯仰角（°） | -7.2 |
| head_pose.yaw | number | 偏航角（°） | -0.2 |
| head_pose.roll | number | 翻滚角（°） | -2.5 |
| attention | int | 注意力/专注度标签 /1=专注 2=轻度分心 3=严重分心 | 1 |
#### <a name="blendshapes-list">附录：52 类 Blendshapes 列表</a>

这些数据遵循 ARKit 标准，包括以下 52 个维度的表情强度（0.0000 ~ 1.0000）：

- **眉毛**: `browDownLeft`, `browDownRight`, `browInnerUp`, `browOuterUpLeft`, `browOuterUpRight`
- **眼睛**: `eyeBlinkLeft`, `eyeBlinkRight`, `eyeSquintLeft`, `eyeSquintRight`, `eyeWideLeft`, `eyeWideRight`
- **凝视**: `eyeLookDownLeft`, `eyeLookDownRight`, `eyeLookInLeft`, `eyeLookInRight`, `eyeLookOutLeft`, `eyeLookOutRight`, `eyeLookUpLeft`, `eyeLookUpRight`
- **下颌**: `jawForward`, `jawLeft`, `jawOpen`, `jawRight`
- **嘴部**: `mouthClose`, `mouthDimpleLeft`, `mouthDimpleRight`, `mouthFrownLeft`, `mouthFrownRight`, `mouthFunnel`, `mouthLeft`, `mouthLowerDownLeft`, `mouthLowerDownRight`, `mouthPressLeft`, `mouthPressRight`, `mouthPucker`, `mouthRight`, `mouthRollLower`, `mouthRollUpper`, `mouthShrugLower`, `mouthShrugUpper`, `mouthSmileLeft`, `mouthSmileRight`, `mouthStretchLeft`, `mouthStretchRight`, `mouthUpperUpLeft`, `mouthUpperUpRight`
- **鼻子/脸颊**: `cheekPuff`, `cheekSquintLeft`, `cheekSquintRight`, `noseSneerLeft`, `noseSneerRight`
- **其他**: `_neutral`
| left_eye_gaze | object | 左眼凝视角（°） | { horizontal: -2.1, vertical: -2.0 } |
| left_eye_gaze.horizontal | number | 左眼水平角（°） | -2.1 |
| left_eye_gaze.vertical | number | 左眼垂直角（°） | -2.0 |
| right_eye_gaze | object | 右眼凝视角（°） | { horizontal: 0.0, vertical: -0.9 } |
| right_eye_gaze.horizontal | number | 右眼水平角（°） | 0.0 |
| right_eye_gaze.vertical | number | 右眼垂直角（°） | -0.9 |

*示例响应(此举例是test_status=0)*

```json
{
  "suspect_id":1,
  "frame": 5,
  "dominant_emotion": 1,
  "emotion_scores": {
    "angry": 6.113341823220253,
    "disgust": 0.00000025447035589820644,
    "fear": 0.5441904533654451,
    "happy": 0.0000010103542003037091,
    "sad": 54.60745096206665,
    "surprise": 0.00033105914098996436,
    "neutral": 38.73467743396759
  },
  "region": {
    "face": {
      "x": 26,
      "y": 230,
      "w": 634,
      "h": 634
    },
    "left_eyebrow": {
      "x1": 80,
      "y1": 260,
      "x2": 120,
      "y2": 255
    },
    "right_eyebrow": {
      "x1": 180,
      "y1": 258,
      "x2": 220,
      "y2": 262
    },
    "left_eye": {
      "x": 95,
      "y": 290,
      "w": 45,
      "h": 28
    },
    "right_eye": {
      "x": 195,
      "y": 292,
      "w": 43,
      "h": 27
    },
    "mouth": {
      "x1": 110,
      "y1": 380,
      "x2": 200,
      "y2": 385
    },
    "nose": {
      "x1": 399,
      "y1": 380,
      "x2": 473,
      "y2": 486
    },
    "chin": {
      "x1": 348,
      "y1": 534,
      "x2": 572,
      "y2": 618
    },
    "teeth": {
      "x1": 389,
      "y1": 529,
      "x2": 491,
      "y2": 534
    },
    "left_pupil": {
      "x1": 361,
      "y1": 373,
      "x2": 387,
      "y2": 397
    },
    "right_pupil": {
      "x1": 505,
      "y1": 380,
      "x2": 531,
      "y2": 403
    }
  },
  "time_sec": 1766465735000,
  "heart_rate": 0,
  "gaze_direction": 0,
  "head_pose": {
    "pitch": -7.2,
    "yaw": -0.2,
    "roll": -2.5
  },
  "attention": 1,
  "au_52": {
    "_neutral": 0.0000,
    "browDownLeft": 0.0004,
    "browDownRight": 0.0002,
    "browInnerUp": 0.6376,
    "browOuterUpLeft": 0.5285,
    "browOuterUpRight": 0.6282,
    "cheekPuff": 0.0000,
    "cheekSquintLeft": 0.0000,
    "cheekSquintRight": 0.0000,
    "eyeBlinkLeft": 0.0776,
    "eyeBlinkRight": 0.0097,
    "eyeLookDownLeft": 0.3234,
    "eyeLookDownRight": 0.3154,
    "eyeLookInLeft": 0.0092,
    "eyeLookInRight": 0.2357,
    "eyeLookOutLeft": 0.2244,
    "eyeLookOutRight": 0.0237,
    "eyeLookUpLeft": 0.0208,
    "eyeLookUpRight": 0.0244,
    "eyeSquintLeft": 0.3180,
    "eyeSquintRight": 0.0818,
    "eyeWideLeft": 0.0096,
    "eyeWideRight": 0.0574,
    "jawForward": 0.0002,
    "jawLeft": 0.0003,
    "jawOpen": 0.0024,
    "jawRight": 0.0001,
    "mouthClose": 0.0004,
    "mouthDimpleLeft": 0.0099,
    "mouthDimpleRight": 0.0002,
    "mouthFrownLeft": 0.0224,
    "mouthFrownRight": 0.0324,
    "mouthFunnel": 0.0011,
    "mouthLeft": 0.0030,
    "mouthLowerDownLeft": 0.0004,
    "mouthLowerDownRight": 0.0014,
    "mouthPressLeft": 0.1052,
    "mouthPressRight": 0.0051,
    "mouthPucker": 0.0217,
    "mouthRight": 0.0003,
    "mouthRollLower": 0.0075,
    "mouthRollUpper": 0.0010,
    "mouthShrugLower": 0.0237,
    "mouthShrugUpper": 0.0931,
    "mouthSmileLeft": 0.0068,
    "mouthSmileRight": 0.0020,
    "mouthStretchLeft": 0.0255,
    "mouthStretchRight": 0.0208,
    "mouthUpperUpLeft": 0.0017,
    "mouthUpperUpRight": 0.0010,
    "noseSneerLeft": 0.0000,
    "noseSneerRight": 0.0000
  },
  "left_eye_gaze": {
    "horizontal": -2.1,
    "vertical": -2.0
  },
  "right_eye_gaze": {
    "horizontal": 0.0,
    "vertical": -0.9
  }
}
```

### <a name="异常数据">异常数据展示</a>

- 接口名称: 异常数据展示（AnalysisResult）
- 适用场景: 基于已训练的基线模型，对单帧记录进行多域异常评分（情绪/心率/头部姿态/眼动/AU），用于前端异常高亮与告警展示
- 数据格式: JSON Object
- 请求方式: WebSocket

接口地址
- ws://<host>:5000/ws/face

客户端请求消息（Client -> Server）
```BASH
{
  "id": 1, // 嫌疑人编号
  "image": "<BASE64编码的摄像头帧>", // 摄像头帧 BASE64 编码
  "test_status": 1 // 检测状态 0/1/2   0=采集并异步训练基线 1=基准结束并异常评分 2=审讯结束并释放模型缓存
}
```
websocket的响应数据

#### 字段

| 字段 | 类型 | 说明 | 示例 |
| --- | --- | --- | --- |
| emotion | object | 情绪域异常评分 | {"score":-0.07,"is_anomaly":true} |
| emotion.score | number | 异常分数（越低越异常） | -0.0737 |
| emotion.is_anomaly | boolean | 是否异常((true异常false正常)) | true |
| heart_rate | object | 心率域异常评分 | {"score":0.0,"is_anomaly":false} |
| heart_rate.score | number | 异常分数（越低越异常） | -6.66e-16 |
| heart_rate.is_anomaly | boolean | 是否异常((true异常false正常)) | false |
| head_pose | object | 头部姿态域异常评分 | {"score":-0.04,"is_anomaly":true} |
| head_pose.score | number | 异常分数（越低越异常） | -0.0399 |
| head_pose.is_anomaly | boolean | 是否异常((true异常false正常)) | true |
| eye_gaze | object | 眼动域异常评分 | {"score":0.0,"is_anomaly":false} |
| eye_gaze.score | number | 异常分数（越低越异常） | -6.66e-16 |
| eye_gaze.is_anomaly | boolean | 是否异常((true异常false正常)) | false |
| au_intensity | object | AU 强度域异常评分 | {"score":-0.055,"is_anomaly":true} |
| au_intensity.score | number | 异常分数（越低越异常） | -0.0554 |
| au_intensity.is_anomaly | boolean | 是否异常((true异常false正常)) | true |

示例响应（当test_status=1且基线模型ready的时候：多加的字段；当前测速阶段不写入 emotion_anomaly 表）

```json
anomaly_data:{
    "emotion": { "score": -0.0737, "is_anomaly": true },
    "heart_rate": { "score": 0, "is_anomaly": false },
    "head_pose": { "score": -0.04, "is_anomaly": true },
    "eye_gaze": { "score": 0, "is_anomaly": false },
    "au_intensity": { "score": -0.055, "is_anomaly": true }
}
    
```
示例响应(当test_status=1且基线模型ready的时候：完整的字段示例)
```json
{
  "suspect_id":1,
  "frame": 5,
  "dominant_emotion": 1,
  "emotion_scores": {
    "angry": 6.113341823220253,
    "disgust": 0.00000025447035589820644,
    "fear": 0.5441904533654451,
    "happy": 0.0000010103542003037091,
    "sad": 54.60745096206665,
    "surprise": 0.00033105914098996436,
    "neutral": 38.73467743396759
  },
  "region": {
    "face": {
      "x": 26,
      "y": 230,
      "w": 634,
      "h": 634
    },
    "left_eyebrow": {
      "x1": 80,
      "y1": 260,
      "x2": 120,
      "y2": 255
    },
    "right_eyebrow": {
      "x1": 180,
      "y1": 258,
      "x2": 220,
      "y2": 262
    },
    "left_eye": {
      "x": 95,
      "y": 290,
      "w": 45,
      "h": 28
    },
    "right_eye": {
      "x": 195,
      "y": 292,
      "w": 43,
      "h": 27
    },
    "mouth": {
      "x1": 110,
      "y1": 380,
      "x2": 200,
      "y2": 385
    }
  },
  "time_sec": 1766465735000,
  "heart_rate": 0,
  "gaze_direction": 0,
  "head_pose": {
    "pitch": -7.2,
    "yaw": -0.2,
    "roll": -2.5
  },
  "attention": 1,
  "au_intensities": {
    "inner_brow_raiser": 0.0000,
    "outer_brow_raiser": 0.6370,
    "brow_furrower": 1.0000,
    "upper_eyelid_raiser": 0.3470,
    "cheek_raiser": 0.0000,
    "nose_wrinkler": 0.9800,
    "upper_lip_raiser": 0.0000,
    "lip_corner_puller": 1.0000,
    "lip_corner_depressor": 0.0000,
    "jaw_raiser": 0.0000,
    "lip_stretcher": 0.0000,
    "lip_compressor": 0.0000,
    "lip_parter": 0.0000,
    "jaw_dropper": 0.8990,
    "eye_closure": 0.0000
  },
  "au_52": {
    "_neutral": 0.0000,
    "browDownLeft": 0.0004,
    "browDownRight": 0.0002,
    "browInnerUp": 0.6376,
    "browOuterUpLeft": 0.5285,
    "browOuterUpRight": 0.6282,
    "eyeBlinkLeft": 0.0776,
    "eyeBlinkRight": 0.0097,
    "jawOpen": 0.0024,
    "mouthSmileLeft": 0.0068,
    "mouthSmileRight": 0.0020
  },
  "left_eye_gaze": {
    "horizontal": -2.1,
    "vertical": -2.0
  },
  "right_eye_gaze": {
    "horizontal": 0.0,
    "vertical": -0.9
  },
  "anomaly_data": {
    "emotion": { "score": -0.0737, "is_anomaly": true },
    "heart_rate": { "score": 0, "is_anomaly": false },
    "head_pose": { "score": -0.04, "is_anomaly": true },
    "eye_gaze": { "score": 0, "is_anomaly": false },
    "au_intensity": { "score": -0.055, "is_anomaly": true }
  }
}
```
### <a name="音频数据展示">音频数据展示</a>

- 接口名称: 音频数据展示(ASR)
- 编码规范：音频为原始 PCM S16LE，单声道，采样率 16000 Hz，发送前对原始字节做 base64 编码（不要携带 WAV/MP3 容器头）
接口地址
- ws://<host>:5000/ws/asr

客户端请求消息（Client -> Server）

```json
{"type":"audio","audio":"<base64-encoded-pcm>","suspect_id":"1","seq":1}
```
若结束此次音频识别，需要在 60 秒内发送 `end=true` 结束包，否则会超时。
```json
{"type":"audio","audio":"","suspect_id":"1","seq":99,"end":true}
```

后端响应数据
```json
{
    "type": "partial",
    "data": {
        "partial": "嗯。"
    }
}
```
