# 日志规范

当前日志实现：

- 日志目录：`DATA_ROOT/logs`，默认 `./storage/logs`。
- 日志文件：`app.log`。
- 滚动策略：单文件 `1_000_000` bytes，保留 `3` 个备份。
- 日志格式：`%(asctime)s [%(levelname)s] %(name)s - %(message)s`。
- 日志级别：通过 `LOG_LEVEL` 控制，默认 `INFO`。

规范：

- 所有未捕获异常必须通过 `app.logger.exception()` 或模块 logger 输出堆栈。
- WebSocket 连接断开、图像解码失败、数据库写入失败、ASR 连接失败必须记录。
- 不得在日志中输出数据库密码、完整 `DATABASE_URL`、音频 Base64、图像 Base64。
- 生产环境应将 stdout/stderr 交给容器日志系统采集。
- 当前 `config.py` 中打印完整数据库连接的行为后续应改为脱敏输出。
