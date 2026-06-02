ARG NODE_IMAGE=swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-bookworm-slim
ARG PYTHON_IMAGE=swr.cn-north-4.myhuaweicloud.com/ddn-k8s/ghcr.io/astral-sh/uv:python3.12-bookworm-slim
ARG PNPM_VERSION=10.33.0

FROM ${NODE_IMAGE} AS frontend-deps

WORKDIR /frontend

ARG PNPM_VERSION

# pnpm 版本通常远比业务代码稳定，放在依赖清单之前便于长期复用缓存。
RUN npm install -g pnpm@${PNPM_VERSION} --registry=https://registry.npmmirror.com

# html-interrogate 使用 pnpm + Vite 构建；只在 package/lock 文件变化时重装依赖。
COPY html-interrogate/package.json html-interrogate/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --registry=https://registry.npmmirror.com

FROM frontend-deps AS frontend-builder

# 前端源码最后复制；普通后端提交不会打穿前端依赖缓存。
COPY html-interrogate/ ./
RUN pnpm run build

FROM ${PYTHON_IMAGE} AS runtime

WORKDIR /app

# OpenCV / TensorFlow / MediaPipe 在无界面容器内需要这些运行时库。
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    libgl1 \
    libgl1-mesa-glx \
    libegl1-mesa \
    libgles2-mesa \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FRONTEND_DIST_DIR=/app/html-interrogate/dist \
    QT_QPA_PLATFORM=offscreen \
    OPENCV_OPENCL_RUNTIME="" \
    CV2_NO_GUI=1

# Python 工具链和 libclang 比业务代码稳定，放在 requirements 之前。
RUN pip install --upgrade pip \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn

RUN pip install --no-cache-dir libclang==18.1.1 \
    -i http://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    --default-timeout=1000 \
    --retries 10

COPY requirement.txt /app/
# 只有 requirement.txt 变化时才重装 Python 依赖。
RUN pip install --no-cache-dir -r requirement.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn

# 运行镜像只复制后端必需文件，避免前端源码或测试文档变更打穿后端运行层缓存。
COPY app/ /app/app/
COPY deepface/ /app/deepface/
COPY face_landmarker.task run.py requirement.txt /app/
# 当前部署要求把构建宿主机根目录 .env 放入容器，供 Flask 启动时加载 pyannote 等运行配置。
COPY .env /app/.env
COPY --from=frontend-builder /frontend/dist /app/html-interrogate/dist

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)"

CMD ["python", "run.py"]
