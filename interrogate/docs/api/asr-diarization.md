# ASR 说话人分离

## `POST /api/asr/diarization/align`

将前端采集的一段 WAV 音频窗口转发到外部 pyannote 服务，并把 pyannote 返回的说话人时间段与 ASR 文本片段按时间重叠对齐。

该接口是实时 ASR 的旁路增强能力。接口失败时，前端只展示“说话人分离暂不可用”，不得影响实时转写、音频波形和关键词提炼。

### 请求

请求类型：`multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | file | 是 | WAV 音频窗口，前端当前按 16k 单声道 PCM S16LE 封装 |
| `segments` | string | 否 | JSON 字符串，ASR segments 数组，例如 `[{"start":15.2,"end":16.0,"text":"收到"}]` |
| `offset_sec` | number | 否 | 当前音频窗口相对本轮会话的开始秒数，默认 `0` |
| `session_id` | string | 否 | 审讯会话 ID |
| `suspect_id` | string | 否 | 嫌疑人 ID |

示例：

```bash
curl -X POST "http://localhost:5000/api/asr/diarization/align" \
  -F "file=@window.wav;type=audio/wav" \
  -F 'segments=[{"start":15.2,"end":16.0,"text":"收到"}]' \
  -F "offset_sec=15" \
  -F "session_id=session-1" \
  -F "suspect_id=1"
```

### 成功响应

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "provider": "pyannote",
    "segments": [
      {
        "speaker": "A",
        "start": "00:00:15",
        "end": "00:00:16",
        "start_sec": 15.0,
        "end_sec": 16.0,
        "source": "pyannote",
        "session_id": "session-1",
        "suspect_id": "1",
        "text": "收到"
      }
    ]
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `speaker` | string | 会话内稳定说话人标签，例如 `A`、`B`、`C` |
| `start` / `end` | string | 展示用时间，格式 `HH:mm:ss` |
| `start_sec` / `end_sec` | number | 会话内秒级时间，用于排序和后续对齐 |
| `text` | string | 与该 speaker 时间段最大重叠的 ASR 文本；无匹配时为空字符串 |
| `source` | string | 当前固定为 `pyannote` |

### 错误响应

缺少文件：

```json
{
  "code": 40001,
  "msg": "file_required",
  "data": null
}
```

外部 pyannote 服务不可用：

```json
{
  "code": 50000,
  "msg": "speaker_diarization_unavailable",
  "data": {
    "segments": []
  }
}
```

### 外部服务配置

后端通过环境变量调用外部 pyannote 服务：

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `PYANNOTE_DIARIZATION_ENDPOINT` | 是 | 无 | pyannote HTTP 地址。当前外部服务按 `POST /diarize` multipart `file=@*.wav` 返回 |
| `PYANNOTE_API_KEY` | 否 | 空 | 外部服务鉴权 token，如无需鉴权可为空 |
| `PYANNOTE_TIMEOUT_SECONDS` | 否 | `15` | 单次请求超时时间，单位秒 |
| `PYANNOTE_SPEAKER_COUNT_HINT` | 否 | `2` | 默认说话人数提示，仅作为 hint |
| `PYANNOTE_AUDIO_WINDOW_SECONDS` | 否 | `15` | 前端和部署约定的音频窗口长度，单位秒 |

外部服务返回示例：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.942,
      "end": 3.305,
      "duration": 2.362
    }
  ]
}
```

后端会把外部 `SPEAKER_00`、`SPEAKER_01` 等标签映射为前端稳定标签 `A`、`B`、`C`。
