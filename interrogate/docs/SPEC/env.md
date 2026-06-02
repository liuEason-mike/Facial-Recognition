# 环境变量规范

## 后端环境变量

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `APP_PROFILE` | 否 | 空 | 加载 `.env.<profile>` |
| `ENV_FILE` | 否 | 空 | 显式指定 env 文件，相对路径基于项目根目录 |
| `FLASK_ENV` | 否 | 空 | Flask 环境标识 |
| `SECRET_KEY` | 是 | `dev-secret` | Flask secret，生产必须覆盖 |
| `ENABLE_DATABASE` | 否 | `0` | `1` 时初始化 SQLAlchemy、自动建表并允许实时入库；`0` 时跳过数据库初始化和写入 |
| `DATABASE_URL` | 否 | 空 | 完整 MySQL 连接串；`ENABLE_DATABASE=1` 时必须以 `mysql+pymysql://` 开头 |
| `DB_HOST` | 启用数据库时是 | 空 | MySQL 主机 |
| `DB_PORT` | 否 | `3306` | MySQL 端口 |
| `DB_USER` | 启用数据库时是 | 空 | MySQL 用户 |
| `DB_PASSWORD` | 启用数据库时是 | 空 | MySQL 密码 |
| `DB_NAME` | 启用数据库时是 | 空 | MySQL 数据库名 |
| `DB_POOL_RECYCLE` | 否 | `28000` | SQLAlchemy 连接池回收秒数 |
| `DATA_ROOT` | 否 | `./storage` | 数据和日志根目录 |
| `SOCKET_CORS_ORIGINS` | 否 | `*` | WebSocket CORS 来源 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |
| `TESTING` | 否 | `0` | `1` 表示测试模式 |
| `DASHSCOPE_API_KEY` | 否 | `/ws/asr` 内置默认密钥 | DashScope 默认密钥，用于 `/ws/asr` 代理和 ASR 关键词提炼；配置后覆盖代码内置默认值，不得写入日志 |
| `ASR_DASHSCOPE_API_KEY` | 否 | 空 | `/ws/asr` DashScope 代理专用密钥；配置后优先于 `DASHSCOPE_API_KEY` 和代码内置默认值 |
| `ASR_DASHSCOPE_ENDPOINT` | 否 | `wss://dashscope.aliyuncs.com/api-ws/v1/inference` | `/ws/asr` DashScope WebSocket 地址 |
| `ASR_DASHSCOPE_MODEL` | 否 | `paraformer-realtime-v2` | `/ws/asr` DashScope 实时语音识别模型 |
| `ASR_SAMPLE_RATE` | 否 | `16000` | `/ws/asr` 转发给 DashScope 的音频采样率 |
| `ASR_AUDIO_FORMAT` | 否 | `pcm` | `/ws/asr` 转发给 DashScope 的音频格式 |
| `KEYWORD_LLM_ENDPOINT` | 否 | DashScope compatible chat completions 地址 | ASR 关键词提炼大模型 HTTP 接口地址 |
| `KEYWORD_LLM_API_KEY` | 否 | 空 | ASR 关键词提炼大模型密钥，优先级高于 `DASHSCOPE_API_KEY` |
| `KEYWORD_LLM_MODEL` | 否 | `qwen3-max` | ASR 关键词提炼模型名称 |
| `KEYWORD_LLM_TIMEOUT` | 否 | `12` | ASR 关键词提炼请求超时时间，单位秒 |
| `PYANNOTE_DIARIZATION_ENDPOINT` | 是 | 无 | 说话人分离外部 pyannote HTTP 地址，当前按 multipart `file=@*.wav` 调用 |
| `PYANNOTE_API_KEY` | 否 | 空 | pyannote 外部服务鉴权 token，如服务不需要鉴权可为空 |
| `PYANNOTE_TIMEOUT_SECONDS` | 否 | `15` | 单次 pyannote diarization 请求超时时间，单位秒 |
| `PYANNOTE_SPEAKER_COUNT_HINT` | 否 | `2` | 默认说话人数提示，仅作为外部服务 hint |
| `PYANNOTE_AUDIO_WINDOW_SECONDS` | 否 | `15` | 前端提交给 pyannote 的音频窗口长度，单位秒 |
| `FACE_SLOW_FRAME_LOG_MS` | 否 | `200` | `/ws/face` 单帧处理超过该毫秒数时记录分段耗时日志；只记录耗时和状态，不记录 Base64 图像 |
| `FACE_EMOTION_INFER_EVERY_N_FRAMES` | 否 | `5` | `/ws/face` 情绪模型推理间隔；已有缓存时每 N 帧重新推理一次，其余帧复用上次情绪分布 |

生产规范：

- 需要业务数据持久化时必须设置 `ENABLE_DATABASE=1` 并提供 MySQL 配置，禁止依赖 SQLite fallback。
- 临时演示或服务器未准备数据库时可设置 `ENABLE_DATABASE=0`，此时 `/ws/face` 和 `/ws/asr` 保持实时回包但不写入关系型数据库。
- 生产环境禁止使用 `SECRET_KEY=dev-secret`。
- 日志中不得输出完整 `DATABASE_URL`、密码、Base64 图像或 Base64 音频。
- `/ws/asr` 当前按 Docker 单容器部署要求内置 DashScope 默认密钥；日志和文档不得输出完整密钥。
- ASR 服务地址、Neo4j 地址、Neo4j 用户名和密码后续应从环境变量读取，禁止硬编码。

## 前端环境变量

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `VITE_APP_TITLE` | 否 | 页面标题，当前为“智慧审讯 · AI辅助审讯系统” |
| `VITE_API_BASE_URL` | 否 | HTTP API base URL，默认 `/api` |
| `VITE_WS_BASE_URL` | 否 | WebSocket base URL，未配置时按当前页面协议和 host 推导；`html-interrogate` 的 `/ws/face` 与 `/ws/asr` 都基于它生成 |
| `VITE_DEV_API_TARGET` | 否 | Vite 开发代理 HTTP 后端地址，默认 `http://127.0.0.1:5000` |
| `VITE_DEV_WS_TARGET` | 否 | Vite 开发代理 WebSocket 后端地址，默认 `ws://127.0.0.1:5000` |

## 生产环境变量模板

生产 `.env` 示例：

```dotenv
FLASK_ENV=production
SECRET_KEY=<replace-with-strong-random-secret>

ENABLE_DATABASE=1
DB_HOST=<mysql-host>
DB_PORT=3306
DB_USER=<mysql-user>
DB_PASSWORD=<mysql-password>
DB_NAME=interrogation

DATA_ROOT=/app/storage
SOCKET_CORS_ORIGINS=<https://your-domain.example>
LOG_LEVEL=INFO
DB_POOL_RECYCLE=28000

ASR_DASHSCOPE_ENDPOINT=wss://dashscope.aliyuncs.com/api-ws/v1/inference
ASR_DASHSCOPE_MODEL=paraformer-realtime-v2
ASR_SAMPLE_RATE=16000
ASR_AUDIO_FORMAT=pcm
KEYWORD_LLM_MODEL=qwen3-max
KEYWORD_LLM_TIMEOUT=12
PYANNOTE_DIARIZATION_ENDPOINT=<pyannote-diarization-url>
PYANNOTE_TIMEOUT_SECONDS=15
PYANNOTE_SPEAKER_COUNT_HINT=2
PYANNOTE_AUDIO_WINDOW_SECONDS=15
FACE_SLOW_FRAME_LOG_MS=200
FACE_EMOTION_INFER_EVERY_N_FRAMES=5
```

不得在生产 `.env` 中使用开发密码、`dev-secret`、本地测试 IP 或无意义占位值。
