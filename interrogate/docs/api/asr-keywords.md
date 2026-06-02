# ASR 关键词提炼 API

## `POST /api/asr/keywords/extract`

用途：接收前端累计的 ASR 转写文本，抽取审讯场景关键词并按类别返回。

调用节奏：前端 ASR 实时转写去除空白字符后，每累计约 `100` 字触发一次请求；接口失败时前端继续保留实时转写，不中断音频采集。

### 请求

```json
{
  "session_id": "20260522001",
  "suspect_id": "1",
  "window_id": "asr-keywords-1",
  "text": "周某说凌晨三四点前往上海，随后签署仓储合同，并把预付款转出。",
  "context": ""
}
```

字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `text` | string | 是 | 本轮累计 ASR 转写文本 |
| `window_id` | string | 否 | 前端关键词窗口编号 |
| `suspect_id` | string | 否 | 嫌疑人编号 |
| `session_id` | string | 否 | 讯问会话编号 |
| `context` | string | 否 | 上下文摘要或上一轮关键词 |

### 成功响应

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "window_id": "asr-keywords-1",
    "suspect_id": "1",
    "session_id": "20260522001",
    "provider": "llm",
    "keywords": [
      {
        "text": "前往上海",
        "category": "地点",
        "confidence": 0.91,
        "source": "凌晨三四点前往上海",
        "count": 1
      }
    ]
  }
}
```

关键词分类固定为：

- `人物`
- `时间`
- `地点`
- `行为`
- `事件`

### 错误响应

空文本：

```json
{
  "code": 40001,
  "msg": "text_required",
  "data": null
}
```

文本过长：

```json
{
  "code": 40001,
  "msg": "text_too_long",
  "data": null
}
```

服务异常：

```json
{
  "code": 50000,
  "msg": "keyword_extract_failed",
  "data": null
}
```

### 配置

后端通过环境变量读取大模型接口配置，不在代码中写密钥：

| 变量 | 说明 |
| --- | --- |
| `DASHSCOPE_API_KEY` | DashScope 访问密钥，推荐用于默认接入 |
| `KEYWORD_LLM_ENDPOINT` | 大模型 HTTP 接口地址，默认 `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` |
| `KEYWORD_LLM_API_KEY` | 大模型访问密钥，优先级高于 `DASHSCOPE_API_KEY` |
| `KEYWORD_LLM_MODEL` | 模型名称，默认 `qwen3-max` |
| `KEYWORD_LLM_TIMEOUT` | 请求超时时间，默认 12 秒 |

兼容 `DASHSCOPE_LLM_ENDPOINT`、`DASHSCOPE_LLM_MODEL` 和 `BAIYING_LLM_ENDPOINT`、`BAIYING_LLM_API_KEY`、`BAIYING_LLM_MODEL`。
