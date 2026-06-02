# Docker 镜像规范

当前镜像文件：

| 文件 | 用途 | 状态 |
| --- | --- | --- |
| `build/docker/Dockerfile` | 前后端一体镜像 | 主镜像规范 |
| `build/docker/Dockerfile_backend` | 后端镜像 | 当前存在污染字符串，修复前不得用于生产 |

前后端一体镜像规范：

- 第一阶段默认使用 `swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-bookworm-slim` 构建前端，可通过 `NODE_IMAGE` build arg 覆盖。
- 前端入口为 `html-interrogate/`，构建命令为 `pnpm install --frozen-lockfile` 和 `pnpm run build`。
- 前端依赖层必须只依赖 `html-interrogate/package.json` 与 `html-interrogate/pnpm-lock.yaml`，业务源码复制应位于依赖安装之后。
- 第二阶段默认使用 `swr.cn-north-4.myhuaweicloud.com/ddn-k8s/ghcr.io/astral-sh/uv:python3.12-bookworm-slim`，可通过 `PYTHON_IMAGE` build arg 覆盖。
- 必须安装 OpenCV / TensorFlow / MediaPipe 所需系统库。
- 后端运行阶段应先安装系统库、`pip`、`libclang` 和 `requirement.txt` 依赖，再复制 `app/`、`deepface/`、`run.py` 与模型文件，避免普通源码提交打穿依赖缓存。
- 必须将 `html-interrogate/dist/` 复制到 `/app/html-interrogate/dist/`。
- 必须设置 `FRONTEND_DIST_DIR=/app/html-interrogate/dist`，由 `run.py` 在同一端口托管前端 SPA。
- 必须设置无界面环境变量：

```dockerfile
ENV QT_QPA_PLATFORM=offscreen \
    OPENCV_OPENCL_RUNTIME="" \
    CV2_NO_GUI=1
```

- 必须暴露端口 `5000`。
- 镜像应明确启动命令：

```dockerfile
CMD ["python", "run.py"]
```

构建命令：

```bash
cd interrogate
docker build -f build/docker/Dockerfile -t interrogate:latest .
```

运行命令：

```bash
docker run --rm -p 5000:5000 --env-file .env interrogate:latest
```

单端口访问：

| 地址 | 说明 |
| --- | --- |
| `http://127.0.0.1:5000/` | `html-interrogate` 前端页面 |
| `http://127.0.0.1:5000/api/...` | 后端 HTTP API |
| `ws://127.0.0.1:5000/ws/face` | 面部分析 WebSocket |
| `ws://127.0.0.1:5000/ws/asr` | ASR WebSocket |
