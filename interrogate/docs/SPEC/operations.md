# 运维操作规范

## 备份策略

MySQL 备份：

- 生产环境至少每日全量备份一次。
- 备份保留周期不少于 7 天。
- 重要演示或审讯前后应进行手动备份。

示例：

```bash
mysqldump -h <mysql-host> -P 3306 -u <mysql-user> -p --single-transaction --routines --triggers interrogation > /opt/interrogate/mysql-backup/interrogation-$(date +%F).sql
```

应用数据备份：

- 备份 `DATA_ROOT` 下的日志和模型文件。
- 日志归档前应注意隐私和合规要求。

## 监控与告警

最低监控项：

- 容器存活状态。
- `GET /health` 状态。
- CPU、内存、磁盘使用率。
- MySQL 连接可用性。
- `storage/logs/app.log` 中的 `ERROR` 和异常堆栈。
- WebSocket 连接失败率。
- ASR 外部服务连接失败次数。

建议告警阈值：

- 健康检查连续 3 次失败。
- 容器重启次数 10 分钟内超过 3 次。
- 磁盘使用率超过 80%。
- 应用日志 5 分钟内出现 10 条以上 `ERROR`。

## 常见故障排查

数据库连接失败：

- 检查 `DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`。
- 检查 MySQL 是否允许应用服务器访问。
- 检查 `DATABASE_URL` 是否以 `mysql+pymysql://` 开头。

WebSocket 连接失败：

- 检查 Nginx 是否配置 `Upgrade` 和 `Connection`。
- HTTPS 页面必须使用 WSS。
- 检查浏览器控制台和后端日志。

图像推理失败：

- 检查模型文件是否存在。
- 检查 OpenCV 系统依赖和无界面环境变量。
- 检查输入 Base64 是否去掉 data URL 前缀。

ASR 无返回：

- 检查外部 ASR WebSocket 地址是否可达。
- 检查音频是否为 16k 单声道 PCM S16LE Base64。
- 检查后端 ASR 接收线程是否异常退出。
