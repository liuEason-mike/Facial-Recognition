# 运维部署规范

## 部署目标

生产部署目标是以 Docker 镜像运行 `interrogate` 一体化服务，外部依赖 MySQL 8.x，按需依赖外部 ASR WebSocket 服务和 Neo4j 服务。

推荐部署拓扑：

```text
Browser
  |
  | HTTP / WebSocket
  v
Nginx or Ingress
  |
  v
interrogate container :5000
  |
  +--> MySQL 8.x
  +--> External ASR WebSocket
  +--> Neo4j, optional/current code path
```

## 服务器基础要求

最低配置建议：

| 资源 | 最低要求 | 推荐要求 |
| --- | --- | --- |
| CPU | 4 核 | 8 核或以上 |
| 内存 | 8 GB | 16 GB 或以上 |
| 磁盘 | 50 GB | 100 GB 或以上，SSD |
| 操作系统 | Linux x86_64 | Ubuntu 22.04 / Debian 12 / CentOS Stream 兼容环境 |
| Docker | 24.x | 最新稳定版 |
| Docker Compose | v2 | 最新稳定版 |

说明：

- 当前模型推理依赖 TensorFlow、OpenCV、MediaPipe，CPU 部署可运行但实时性能受机器性能影响。
- 如后续引入 GPU/NPU 推理，必须单独补充硬件驱动、运行时和镜像规范。

## 部署目录规范

推荐生产目录：

```text
/opt/interrogate/
├── .env                         # 生产环境变量，由运维创建
├── docker-compose.yml           # 生产编排文件
├── storage/
│   ├── logs/                    # 应用日志挂载目录
│   └── models/                  # 可选：异常检测模型持久化目录
├── mysql-backup/                # MySQL 备份目录
└── releases/                    # 可选：镜像版本或部署记录
```

挂载规范：

- `DATA_ROOT` 必须挂载到宿主机持久化目录。
- 日志目录必须可写。
- 异常检测模型目录如仍位于代码目录内，后续应迁移到 `DATA_ROOT/models`。
- 数据库数据目录由 MySQL 服务单独管理，不与应用容器混放。

生产环境变量模板见 [环境变量规范](./env.md#生产环境变量模板)。

## docker-compose 部署示例

应用服务示例：

```yaml
services:
  interrogate:
    image: interrogate:latest
    container_name: interrogate
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "5000:5000"
    volumes:
      - ./storage:/app/storage
    command: ["python", "run.py"]
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 60s
```

MySQL 可使用独立服务或外部托管数据库。若使用本仓库现有 MySQL compose，必须修改默认 root 密码并限制访问来源。

## Nginx 反向代理规范

Nginx 必须支持 WebSocket upgrade：

```nginx
server {
    listen 80;
    server_name your-domain.example;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

HTTPS 部署时，前端页面会使用 `wss://` 连接 WebSocket，因此代理必须正确处理 TLS 和 Upgrade。

## 发布流程

标准发布流程：

1. 拉取或确认目标代码版本。
2. 执行前端质量检查：`pnpm run release:check`。
3. 执行后端可用性检查：至少运行 `python -m py_compile run.py app/**/*.py` 或等效检查。
4. 构建镜像：`docker build -f build/docker/Dockerfile -t interrogate:<version> .`。
5. 推送镜像到镜像仓库。
6. 在目标服务器更新 `docker-compose.yml` 中的镜像 tag。
7. 执行 `docker compose pull` 和 `docker compose up -d`。
8. 检查 `GET /health`。
9. 检查 `/ws/face` 和 `/ws/asr` 连接。
10. 观察日志至少 5 分钟，确认无启动异常、数据库异常和模型加载异常。

## 回滚流程

回滚要求：

- 每次发布必须记录镜像 tag、发布时间、提交版本和发布人。
- 回滚优先使用上一稳定镜像 tag，不在服务器上临时修改代码。
- 数据库 schema 变更必须有向前兼容策略；若存在破坏性迁移，必须单独制定回滚脚本。

回滚命令示例：

```bash
cd /opt/interrogate
docker compose down
sed -i 's/interrogate:new-version/interrogate:previous-version/' docker-compose.yml
docker compose up -d
curl -f http://127.0.0.1:5000/health
```
