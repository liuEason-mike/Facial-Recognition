# 技术栈与版本规范

| 类型 | 当前依据 | 规范 |
| --- | --- | --- |
| Python | Docker 使用 `python3.12-bookworm-slim`，离线 wheel 为 `cp312` | Python `3.12.x` |
| 后端框架 | `flask==3.1.3`、`flask_sock==0.7.0` | Flask + Flask-Sock |
| ORM | `Flask-SQLAlchemy==3.1.1`、`SQLAlchemy==2.0.49` | SQLAlchemy 2.x |
| MySQL 驱动 | `PyMySQL==1.1.2` / `pymysql==1.1.2` | `mysql+pymysql://` |
| AI / CV | OpenCV、DeepFace、TensorFlow、MediaPipe、scikit-learn | 版本以 `requirement.txt` 为准 |
| Node.js | Docker 使用 `node:20`，`.node-version` 为 `lts-latest` | 开发使用 Node LTS，镜像当前固定 Node 20 |
| 包管理器 | `packageManager: pnpm@10.33.0` | 统一使用 pnpm |
| 前端框架 | Vue `^3.5.32`、Vite `^8.0.8` | Vue 3 + Vite |
| UI / 图表 | Element Plus、UnoCSS、ECharts | 保持现有技术栈 |
