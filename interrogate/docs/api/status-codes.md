# 状态码

HTTP 响应和 WebSocket 错误响应统一使用以下结构：

```json
{
  "code": 40001,
  "msg": "invalid_json",
  "data": null
}
```

说明：

- HTTP 成功响应使用 `code=0`。
- WebSocket 错误响应必须使用 `{code,msg,data}`。
- 现有 `/ws/face` 成功响应为裸 EmotionFrame，`/ws/asr` 成功响应为外部 ASR 透传结构；若后续统一成功响应结构，必须同步更新 `docs/api/` 和前端类型。

| code | 含义 |
| --- | --- |
| `0` | 成功 |
| `40001` | 参数非法 |
| `40002` | 图像解码失败 |
| `40100` | 未授权 |
| `40400` | 资源不存在 |
| `50000` | 内部错误 |
| `50001` | 数据库错误 |
