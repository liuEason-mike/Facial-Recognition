# WebSocket 音频 ASR

## `WS /ws/asr`

`interrogate` 后端 `/ws/asr` 当前作为 DashScope ASR WebSocket 代理：

```text
前端 -> ws://<host>:5000/ws/asr -> wss://dashscope.aliyuncs.com/api-ws/v1/inference
```

后端连接 DashScope 时优先使用 `ASR_DASHSCOPE_API_KEY`，其次使用
`DASHSCOPE_API_KEY`，最后使用代码内置默认密钥，作为
`Authorization: Bearer <api-key>` 认证头。前端仍只向后端发送 16k 单声道
PCM S16LE Base64 音频包。
`html-interrogate` 前端通过 `buildWebSocketUrl('/ws/asr')` 推导项目内 WebSocket
地址，不直接连接外部 ASR 地址，也不持有公有模型密钥。
如需切换测试环境，可通过 `ASR_DASHSCOPE_ENDPOINT` 覆盖默认 WebSocket 地址。

请求：

```json
{
  "type": "audio",
  "audio": "<pcm_s16le_base64>",
  "seq": 1,
  "suspect_id": "1"
}
```

结束包：

```json
{
  "type": "audio",
  "audio": "",
  "seq": 99,
  "end": true,
  "suspect_id": "1"
}
```

字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type` | string | 是 | 固定为 `audio` |
| `audio` | string | 是 | 16k 单声道 PCM S16LE Base64 |
| `seq` | number | 是 | 音频包序号 |
| `suspect_id` | string | 否 | 嫌疑人编号，当前代码存在 fallback 为 `"0"` 的情况 |
| `end` | boolean | 否 | 是否结束本轮音频流 |

后端向 DashScope 发送的控制指令：

- 连接建立后发送 `run-task`，模型默认 `paraformer-realtime-v2`。
- 收到 DashScope `task-started` 后，将前端 Base64 音频解码为二进制音频帧发送。
- 收到前端 `end=true` 结束包后，发送 `finish-task`。

后端响应数据：

```json
[
  { "start": 0.5, "end": 2.1, "text": "我们先看一下" }
]
```

响应字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `start` | number \| null | 句子开始时间，单位秒，由 DashScope `begin_time` 毫秒值换算 |
| `end` | number \| null | 句子结束时间，单位秒；中间结果可能为 `null` |
| `text` | string | 前端实时展示的 ASR 转写文本 |

## 关联说话人分离

说话人分离不改变 `/ws/asr` 主链路协议。前端会旁路累计约 15 秒音频窗口，将 WAV 文件和最近 ASR segments 提交到：

```text
POST /api/asr/diarization/align
```

接口契约见 `docs/api/asr-diarization.md`。该接口失败时只影响前端“说话人转写”区域，不影响 `/ws/asr` 实时转写回包。

错误响应仍使用 WebSocket 错误结构。DashScope 任务失败时返回
`asr_task_failed`，本地转发失败时返回 `asr_forward_failed`：

```json
{
  "code": 50000,
  "msg": "asr_forward_failed",
  "data": null
}
```
