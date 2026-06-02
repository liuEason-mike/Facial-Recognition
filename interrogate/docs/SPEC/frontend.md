# 前端构建规范

本项目当前存在两套前端：

| 前端 | 路径 | 用途 | 约束 |
| --- | --- | --- | --- |
| 旧前端 | `interrogate/html/` | 现有稳定前端 | 未明确要求时不得修改 |
| 新前端 | `interrogate/html-interrogate/` | 审讯实时工作台新版前端 | 独立开发、独立验证 |

## 1. 旧前端开发

开发：

```bash
cd interrogate/html
pnpm install
pnpm run dev
```

构建：

```bash
cd interrogate/html
pnpm run build
```

质量检查：

```bash
cd interrogate/html
pnpm run typecheck
pnpm run lint
pnpm run release:check
```

规范：

- 包管理器必须使用 pnpm。
- 构建产物输出到 `html/dist/`。
- 前后端一体镜像必须将 `html/dist/` 复制到后端 `/app/static`。
- 开发代理中的 `/ws` 指向后端 WebSocket。
- 生产环境 WebSocket 地址由页面当前协议、域名、端口推导，HTTPS 页面必须使用 WSS。
- 视频帧发送频率由 `MAGIC_NUMBER.frameRate` 控制。
- 音频采样率固定为 `16000`，声道固定为单声道，编码为 PCM S16LE。
- WebSocket 协议变更必须同步更新 `html/src/types/` 中的 TypeScript 类型。

## 2. 新前端开发

`html-interrogate` 是新审讯实时工作台前端，默认通过 Vite 开发服务器运行，并通过代理连接后端 `/api` 和 `/ws`。

环境准备：

```bash
conda activate interrogation_env
cd /home/eason/workspace/interrogate/html-interrogate
pnpm install
```

开发：

```bash
conda activate interrogation_env
cd /home/eason/workspace/interrogate/html-interrogate
pnpm dev --host 0.0.0.0
```

默认访问地址：

```text
http://localhost:5173/
http://<lan-ip>:5173/
```

质量检查：

```bash
conda activate interrogation_env
cd /home/eason/workspace/interrogate/html-interrogate
pnpm typecheck
pnpm build
```

新前端约束：

- 新前端必须位于 `interrogate/html-interrogate/`，不得混入 `interrogate/html/`。
- `html-interrogate` 使用 pnpm、Vue 3、TypeScript、Vite、Element Plus、UnoCSS。
- `html-interrogate` 的 `/api` 和 `/ws` 开发代理默认指向后端 `127.0.0.1:5000`。
- 如果后端不在本机 5000 端口，应通过 `VITE_DEV_API_TARGET` 和 `VITE_DEV_WS_TARGET` 调整代理目标。
- 新前端构建产物输出到 `html-interrogate/dist/`。
- 修改 `html-interrogate` 后必须运行 `pnpm typecheck` 和 `pnpm build`。
- 修改完成后必须确认 `git status` 中没有 `html/` 文件变更。

## 3. 后端启动与联调

后端入口：

```bash
conda activate interrogation_env
cd /home/eason/workspace/interrogate
python run.py
```

后端默认监听：

```text
http://127.0.0.1:5000
ws://127.0.0.1:5000/ws/face
ws://127.0.0.1:5000/ws/asr
```

联调检查：

```bash
curl -i http://localhost:5000/health
curl -I http://localhost:5173/
```

WebSocket 检查使用后端 `5000` 端口直连，可通过无效 JSON 触发后端错误响应：

```bash
node -e "const ws=new WebSocket('ws://localhost:5000/ws/face'); ws.onopen=()=>ws.send('not-json'); ws.onmessage=e=>{console.log(String(e.data)); ws.close(); process.exit(0)}"
node -e "const ws=new WebSocket('ws://localhost:5000/ws/asr'); ws.onopen=()=>ws.send('not-json'); ws.onmessage=e=>{console.log(String(e.data)); ws.close(); process.exit(0)}"
```

预期响应：

```json
{"code":40001,"msg":"invalid_json","data":null}
```

联调约束：

- `run.py` 启动的是 Flask + WebSocket 同端口服务，端口为 `5000`。
- 开发阶段访问新前端应使用 Vite 地址 `http://localhost:5173/`。
- `run.py` 优先托管 `FRONTEND_DIST_DIR`，默认可托管 `interrogate/html-interrogate/dist/`。
- Docker 一体化镜像通过 `FRONTEND_DIST_DIR=/app/html-interrogate/dist` 让后端直接托管新前端。
- 浏览器真实联调需要允许摄像头和麦克风权限，再点击“开始审讯”。
- 仅收到 WebSocket `invalid_json` 响应只能证明握手和代理链路可用，不能证明视频/音频业务流完整可用。

## 4. Git 与交付约束

- Codex 可以修改代码和文档，但不执行 `git add`、`git commit` 或 `git push`，除非用户明确要求。
- 修改完成后不能做任何关于 git 的操作。
- 每次交付说明必须列出已运行的验证命令和结果。
- 无法验证时必须说明原因，不得声称验证通过。
