# 启动方式

本地默认联调入口为后端 `run.py` + 新前端 `html-interrogate/`。旧前端 `html/` 为现有稳定前端，未明确要求时不作为默认开发入口。

## 本地后端

```bash
cd /home/eason/workspace/interrogate
python run.py
```

后端默认监听：

```text
http://127.0.0.1:5000
ws://127.0.0.1:5000/ws/face
ws://127.0.0.1:5000/ws/asr
```

首次准备 Python 环境时，可按项目实际环境安装依赖：

```bash
cd /home/eason/workspace/interrogate
python -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
```

## 本地新前端

`html-interrogate/` 是新审讯实时工作台默认开发入口。

```bash
cd /home/eason/workspace/interrogate/html-interrogate
pnpm install
pnpm dev --host 0.0.0.0
```

默认访问地址：

```text
http://localhost:5173/
```

`html-interrogate` 开发环境通过 Vite 代理连接后端 `/api` 和 `/ws`，默认代理目标为 `http://127.0.0.1:5000` / `ws://127.0.0.1:5000`。如后端不在本机 `5000` 端口，应通过 `VITE_DEV_API_TARGET` 和 `VITE_DEV_WS_TARGET` 调整代理目标。

## 旧前端

旧前端位于 `html/`，用于维护现有稳定页面。未明确要求时，不修改、不迁移、不作为新功能默认入口。

## 本地 MySQL

```bash
cd /home/eason/workspace/interrogate/docker/mysql
docker compose up -d
```

## Docker 一体化

```bash
cd /home/eason/workspace/interrogate
docker build -f build/docker/Dockerfile -t interrogate:latest .
docker run --rm -p 5000:5000 --env-file .env interrogate:latest
```

当前 `build/docker/Dockerfile` 会在 Node 构建阶段打包 `html-interrogate/dist/`，并在 Python 运行阶段通过 `FRONTEND_DIST_DIR=/app/html-interrogate/dist` 交给 `run.py` 托管。前端、HTTP API 和 WebSocket 均通过容器 `5000` 端口访问。

## 统一服务地址

| 地址 | 说明 |
| --- | --- |
| `http://127.0.0.1:5000/health` | 健康检查 |
| `http://localhost:5173/` | 本地新前端开发页面 |
| `http://127.0.0.1:5000/` | Docker 一体化前端页面 |
| `ws://127.0.0.1:5000/ws/face` | 面部分析 WebSocket |
| `ws://127.0.0.1:5000/ws/asr` | 音频 ASR WebSocket |
