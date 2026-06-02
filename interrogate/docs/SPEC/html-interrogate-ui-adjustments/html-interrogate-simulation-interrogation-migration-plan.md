# html-interrogate 讯问室页面迁移设计方案

版本：v0.1
日期：2026-05-18
适用范围：将旧项目 `simulation/interrogation` 讯问室页面迁移到 `/home/eason/workspace/interrogate/html-interrogate`

## 1. 目标

本方案用于指导把旧项目：

```text
/home/eason/workspace/审讯项目_新/ai-interrogation/ai-interrogation
```

中的路由页面：

```text
/simulation/interrogation/<case_id>
```

迁移到目标项目：

```text
/home/eason/workspace/interrogate/html-interrogate
```

迁移后的前端使用 `Vue 3 + TypeScript + Vite` 写法，视觉风格尽量按旧页面 1:1 还原，业务交互逻辑完整迁移，并与 `/home/eason/workspace/interrogate` 现有 Flask 后端、HTTP API 和 WebSocket 链路联调。

## 2. 结论

推荐采用“新建独立工程 `html-interrogate`，复用 `html-next` 技术栈和 WebSocket 封装”的方式迁移。

核心判断：

- 可以迁移旧页面的整体风格、布局、交互逻辑和业务流程。
- 不建议直接复制旧 Jinja 模板作为最终前端代码。
- 可以保持目标项目现有技术栈不变：`Vue 3`、`TypeScript`、`Vite`、`Element Plus`、`UnoCSS`、`pnpm`。
- 旧页面中的 Jinja 数据注入需要改成前端 API 请求。
- 旧页面中的 `/api/send-message`、`/api/voice/recognize` 需要在目标项目中重新定义或适配。
- 目标项目当前已有 `/ws/face` 和 `/ws/asr`，应优先复用它们，不再沿用旧页面的 WebM 上传识别方式作为主链路。

## 3. 已核对的现状

### 3.1 旧项目页面入口

旧项目路由位于：

```text
/home/eason/workspace/审讯项目_新/ai-interrogation/ai-interrogation/app.py
```

已核对关键位置：

| 功能 | 位置 | 说明 |
| --- | --- | --- |
| 讯问室页面路由 | `app.py:1017` | `@app.route('/simulation/interrogation/<int:case_id>')` |
| 模板渲染 | `app.py:1035` | `render_template('simulation/interrogation_room.html', ...)` |
| 发送讯问消息 | `app.py:1277` | `POST /api/send-message` |
| 语音识别 | `app.py:1471` | `POST /api/voice/recognize` |
| 页面模板 | `templates/simulation/interrogation_room.html` | 大量 HTML、CSS、Jinja 和内联 JavaScript |

旧页面本质是 Flask/Jinja 服务端渲染页面，不是纯静态页面。它依赖 `case`、`session`、`suspect_info`、`interrogation_points`、`evidence_chain` 等服务端模板变量。

### 3.2 目标项目现状

目标项目位于：

```text
/home/eason/workspace/interrogate
```

当前前端和后端情况：

| 模块 | 现状 |
| --- | --- |
| `html/` | 现有稳定前端，未明确要求时不应修改 |
| `html-next/` | 新审讯实时工作台，使用 `Vue 3 + TypeScript + Vite + Element Plus + UnoCSS`-未明确要求时不应修改 |
| `html-interrogate/` | 当前尚未存在，本次迁移建议新建 |
| 后端 HTTP | 已有 `GET /health` |
| 后端 WebSocket | 已有 `/ws/face` 和 `/ws/asr` |
| 案件/讯问会话 HTTP API | 目标项目当前没有完整对应接口，需要补齐或建立 adapter |

目标项目已有规范明确 `html-next` 使用 `pnpm`、`Vue 3`、`TypeScript`、`Vite`、`Element Plus`、`UnoCSS`。`html-interrogate` 应沿用这套栈，避免引入第二套前端技术体系。

## 4. 迁移边界

### 4.1 迁移内容

应迁移：

- 讯问室三栏工作台布局。
- 顶部案件和会话状态栏。
- 左侧视频、嫌疑人状态和实时分析区域。
- 中间讯问对话、阶段提示和发言指导。
- 右侧案件信息、证据链、审讯要点和控制面板。
- 消息发送、消息追加、阶段更新、情绪更新、提示更新等交互逻辑。
- 快捷查询嫌疑人、案件、证据、时间线、法律依据的前端逻辑。
- 录音、转写、停止录音、错误提示和权限状态。
- 页面加载、空状态、错误态、连接态、提交态。

### 4.2 不直接迁移的内容

不应直接迁移：

- Flask/Jinja 模板运行方式。
- 旧项目 `base.html`、`login_required`、Flask-Login 运行链路。
- 旧页面内联脚本的全局变量写法。
- 旧页面中直接写死的模板变量。
- 旧项目后端单体 `app.py` 的路由实现整体复制。
- 旧 `/api/voice/recognize` 的 WebM 文件上传方式作为主要语音识别链路。

### 4.3 需要适配的内容

需要适配：

- Jinja 变量改为 `GET /api/simulation/cases/:case_id` 等接口数据。
- 旧 `sendMessage()` 改为 Vue composable 和 API adapter。
- 旧 `MediaRecorder` WebM 上传改为目标项目已有 `/ws/asr` 音频流协议。
- 旧页面样式拆分为全局 token、路由样式和组件 scoped 样式。
- 旧页面 DOM 操作改为 Vue 响应式状态。
- 旧页面内联数据解析改为 TypeScript 类型和 adapter。

## 5. 推荐架构

### 5.1 目录结构

建议新建：

```text
interrogate/html-interrogate/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── uno.config.ts
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── router.ts
│   ├── api/
│   │   ├── http.ts
│   │   ├── simulation.ts
│   │   └── interrogation.ts
│   ├── components/
│   │   └── interrogation/
│   │       ├── RoomHeader.vue
│   │       ├── SuspectVideoPanel.vue
│   │       ├── FaceAnalysisPanel.vue
│   │       ├── CaseInfoPanel.vue
│   │       ├── ChatTranscript.vue
│   │       ├── MessageInput.vue
│   │       ├── StageIndicator.vue
│   │       ├── SpeechGuidancePanel.vue
│   │       ├── EvidencePanel.vue
│   │       ├── ControlPanel.vue
│   │       └── RecordingStatus.vue
│   ├── composables/
│   │   ├── useInterrogationRoom.ts
│   │   ├── useInterrogationChat.ts
│   │   ├── useCaseQuickQuery.ts
│   │   ├── useElapsedTimer.ts
│   │   ├── useFaceAnalysisSocket.ts
│   │   └── useAsrSocket.ts
│   ├── constants/
│   │   ├── emotion.ts
│   │   ├── stage.ts
│   │   └── routes.ts
│   ├── styles/
│   │   ├── tokens.css
│   │   ├── global.css
│   │   └── interrogation-room.css
│   ├── types/
│   │   ├── simulation.ts
│   │   ├── interrogation.ts
│   │   ├── face.ts
│   │   └── asr.ts
│   └── utils/
│       ├── date.ts
│       ├── format.ts
│       └── websocket.ts
└── tests/
```

说明：

- `views/` 可以只放一个路由页面 `SimulationInterrogationView.vue`，也可以直接由 `router.ts` 指向 `components` 外层页面。建议保留 `views/`，更符合 Vue 工程边界。
- `useFaceAnalysisSocket.ts` 和 `useAsrSocket.ts` 可以从 `html-next` 迁移并改名适配，不需要重新设计 WebSocket 基础能力。
- `styles/tokens.css` 用于固化旧页面颜色、间距、字号、状态色。
- `api/` 只处理请求和字段适配，页面组件不直接拼接接口路径。

### 5.2 路由设计

前端路由建议：

```text
/simulation/interrogation/:caseId
```

路由职责：

- 从 URL 读取 `caseId`。
- 加载案件详情。
- 创建或恢复讯问会话。
- 初始化页面状态。
- 在离开页面时释放摄像头、麦克风、WebSocket、定时器和事件监听。

### 5.3 技术栈选择

`html-interrogate` 推荐与 `html-next` 保持一致：

| 类型 | 选择 |
| --- | --- |
| 框架 | Vue 3 |
| 语言 | TypeScript |
| 构建 | Vite |
| 包管理 | pnpm |
| UI 组件 | Element Plus |
| 原子样式 | UnoCSS |
| 状态管理 | 页面内 composable 为主，必要时使用 Pinia |
| HTTP | Axios 或与 `html-next` 一致的封装 |
| WebSocket | 复用 `html-next` 地址推导和连接状态封装 |

不建议为本页面单独引入新的 UI 框架、动画库或状态库。

## 6. 旧页面到新组件的映射

| 旧页面区域或逻辑 | 新组件或模块 | 数据来源 | 迁移说明 |
| --- | --- | --- | --- |
| 顶部案件标题、状态、计时 | `RoomHeader.vue` | 案件详情、会话状态、本地计时器 | 保持旧页面信息密度，计时由 `useElapsedTimer` 管理 |
| 左侧视频区域 | `SuspectVideoPanel.vue` | 浏览器摄像头、`/ws/face` | 复用目标项目视频帧发送策略 |
| 面部/情绪/生理分析 | `FaceAnalysisPanel.vue` | `/ws/face` 响应 | 复用 `FaceAnalysisResult` 类型，展示情绪、AU、头姿、视线、心率 |
| 嫌疑人和案件摘要 | `CaseInfoPanel.vue` | `GET /api/simulation/cases/:case_id` | 替代旧 Jinja 注入 |
| 中间对话列表 | `ChatTranscript.vue` | 会话消息列表 | Vue 响应式渲染，支持滚动到底部 |
| 消息输入和发送 | `MessageInput.vue` | `POST /api/simulation/sessions/:session_id/messages` | 替代旧 `sendMessage()` |
| 阶段提示 | `StageIndicator.vue` | AI 回包 `stage_analysis` | 保留旧页面阶段推进展示 |
| 发言指导和违规提示 | `SpeechGuidancePanel.vue` | AI 回包 `speech_guidance` | 风险提示必须是辅助建议，不表达最终结论 |
| 证据链和审讯要点 | `EvidencePanel.vue` | 案件详情 | 替代旧 `case.evidence_chain` 和 `case.interrogation_points` |
| 控制按钮 | `ControlPanel.vue` | 会话状态、媒体状态 | 开始、暂停、停止、结束会话 |
| 录音状态 | `RecordingStatus.vue` | `/ws/asr`、麦克风权限 | 优先使用目标项目 ASR 流式协议 |
| 快捷查询逻辑 | `useCaseQuickQuery.ts` | 案件详情和本地索引 | 将旧模板中的查询函数改成纯前端 composable |

## 7. 数据和接口契约

### 7.1 前端需要的核心类型

建议前端建立以下 TypeScript 类型：

```ts
export interface SimulationCaseDetail {
  id: number
  title: string
  category?: string
  difficulty?: string
  description?: string
  suspect_info: SuspectInfo
  evidence_chain: EvidenceItem[]
  interrogation_points: InterrogationPoint[]
}

export interface InterrogationSession {
  id: number
  case_id: number
  status: 'created' | 'running' | 'paused' | 'ended'
  started_at?: string
  ended_at?: string
  messages: InterrogationMessage[]
}

export interface InterrogationMessage {
  id: string | number
  role: 'operator' | 'assistant' | 'suspect' | 'system'
  content: string
  created_at: string
  emotion?: string
  stage?: string
}
```

字段命名建议以目标项目新 API 为准。旧项目存在模板字段和数据库字段不完全一致的风险，例如页面可能引用 `case_number`、`case_type`、`incident_date`、`location` 一类字段，但旧 `Case` 模型未必完整提供。迁移时应在后端 adapter 或前端 adapter 中统一字段，不让页面直接依赖不稳定字段。

### 7.2 推荐 HTTP API

不新增加任何 `simulation` API，本次只迁移前端的样式和风格：

推荐统一响应结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

如果短期为了降低迁移成本保留旧接口 `/api/send-message`，也应在 `html-interrogate/src/api/interrogation.ts` 内部适配，不让页面组件直接依赖旧接口。

### 7.3 发送讯问消息响应

建议 `POST /api/simulation/sessions/:session_id/messages` 返回：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "assistant_message": {
      "id": "m-1002",
      "role": "assistant",
      "content": "请继续说明案发当天的行程。",
      "created_at": "2026-05-18T10:30:00+08:00"
    },
    "emotion": "neutral",
    "stage_analysis": {
      "current_stage": "fact_checking",
      "label": "事实核验",
      "confidence": 0.73
    },
    "speech_guidance": {
      "suggestions": [
        "保持问题简短，避免一次询问多个事实。"
      ],
      "violations": []
    }
  }
}
```

### 7.4 WebSocket 复用策略

目标项目已有 WebSocket：

| 路径 | 用途 | 是否复用 |
| --- | --- | --- |
| `/ws/face` | 视频帧面部分析 | 复用 |
| `/ws/asr` | 音频 ASR 流式识别 | 复用 |

`/ws/face` 请求继续使用：

```json
{
  "id": "1",
  "image": "<jpeg_base64_without_data_url_prefix>",
  "test_status": 0
}
```

`/ws/asr` 请求继续使用：

```json
{
  "type": "audio",
  "audio": "<pcm_s16le_base64>",
  "seq": 1,
  "suspect_id": "1"
}
```

结束包继续使用：

```json
{
  "type": "audio",
  "audio": "",
  "seq": 99,
  "end": true,
  "suspect_id": "1"
}
```

迁移时需要补充一个会话绑定策略：页面知道 `case_id`、`session_id` 和 `suspect_id`，WebSocket 当前主要识别 `suspect_id`。如果后端需要把实时分析写入特定讯问会话，应扩展协议或建立后端映射，避免所有 ASR 记录落到默认嫌疑人 `"0"`。

## 8. 视觉 1:1 迁移策略

### 8.1 样式迁移原则

旧页面的视觉可以尽量 1:1 迁移，但建议拆分成可维护结构：

| 旧页面写法 | 新项目写法 |
| --- | --- |
| 大量内联 CSS | `tokens.css`、`global.css`、组件 scoped CSS |
| 全局 class 堆叠 | 语义类名 + UnoCSS 辅助类 |
| Jinja 控制显示 | Vue 条件渲染 |
| 原生 DOM 更新 | Vue 响应式状态 |
| 直接操作滚动和输入框 | `ref` + composable 管理 |

### 8.2 第一屏布局

推荐保留旧页面的讯问室工作台结构：

```text
RoomHeader
└── InterrogationWorkspace
    ├── LeftColumn
    │   ├── SuspectVideoPanel
    │   └── FaceAnalysisPanel
    ├── CenterColumn
    │   ├── ChatTranscript
    │   ├── StageIndicator
    │   └── MessageInput
    └── RightColumn
        ├── CaseInfoPanel
        ├── EvidencePanel
        └── ControlPanel
```

视觉目标：

- 信息密度接近旧页面。
- 三栏比例接近旧页面。
- 保持审讯/指挥中心风格，但不要使用大面积单一色系。
- 卡片圆角不超过 `8px`。
- 关键按钮有明确 loading、disabled、危险确认和连接状态。
- 窄屏下改为纵向堆叠，不出现文字重叠或按钮溢出。

### 8.3 颜色和状态

建议把旧页面颜色抽象成 token：

| token | 用途 |
| --- | --- |
| `--room-bg` | 页面背景 |
| `--room-panel-bg` | 面板背景 |
| `--room-border` | 分隔线 |
| `--room-text` | 主文本 |
| `--room-muted` | 次文本 |
| `--room-primary` | 主操作、选中 |
| `--room-warning` | 警告、注意 |
| `--room-danger` | 高风险、停止 |
| `--room-success` | 在线、成功 |

迁移时先从旧 CSS 中抽取颜色，再合并同义 token，避免把旧页面所有颜色原样散落到组件中。

## 9. 业务逻辑迁移策略

### 9.1 页面初始化

旧页面由 Flask 在渲染时注入 `case`、`session` 和 `suspect_info`。

新页面流程建议：

1. 进入 `/simulation/interrogation/:caseId`。
2. `useInterrogationRoom` 读取 `caseId`。
3. 调用 `GET /api/simulation/cases/:case_id` 获取案件详情。
4. 调用 `POST /api/simulation/sessions` 创建会话，或通过查询参数恢复已有会话。
5. 初始化计时器、消息列表、媒体状态、WebSocket 状态。

### 9.2 消息发送

旧页面逻辑：

```text
sendMessage() -> fetch('/api/send-message') -> append response -> update emotion/stage/guidance
```

新页面逻辑：

```text
MessageInput.vue
-> useInterrogationChat.sendMessage()
-> api/interrogation.ts
-> POST /api/simulation/sessions/:session_id/messages
-> ChatTranscript 追加消息
-> StageIndicator 更新阶段
-> SpeechGuidancePanel 更新提示
```

页面组件只关心“发送中、成功、失败、回包数据”，不直接处理 `fetch`、错误结构或字段兼容。


### 9.4 视频分析

旧页面左侧视频和分析面板应迁移到目标项目已有视频分析链路：

```text
浏览器摄像头
-> canvas 抽帧
-> /ws/face
-> FaceAnalysisResult
-> FaceAnalysisPanel
```

需要保留：

- 摄像头权限提示。
- 连接中、已连接、断开、错误状态。
- 停止审讯时释放媒体流。
- 页面卸载时关闭 WebSocket。
- 发送频率控制。

### 9.5 ASR 语音识别

旧页面使用 `MediaRecorder` 录制 WebM，并上传到 `/api/voice/recognize`。

目标项目已有 `/ws/asr`，并要求 16k 单声道 PCM S16LE Base64 音频包。迁移时建议：

- 不把旧 WebM 上传作为主路径迁入。
- 复用 `html-next` 的音频采集、重采样、PCM 编码和 ASR WebSocket 逻辑。
- 在 UI 上保留旧页面的录音按钮、录音状态、识别结果和错误提示。
- 如果需要兼容旧按钮行为，由 `useAsrSocket` 和 `RecordingStatus` 提供一致状态。

## 10. 后端配套改造建议

完整迁移需要目标项目补齐案件和会话接口。建议新增或整理以下后端分层：

```text
interrogate/app/routes/http/simulation.py
interrogate/app/service/simulation/case_service.py
interrogate/app/service/simulation/session_service.py
interrogate/app/models/simulation.py
interrogate/docs/api/simulation-interrogation.md
```

后端实现建议：

- 路由层只处理参数、响应结构和错误码。
- 服务层处理案件详情聚合、会话创建、消息发送、AI 回包和历史记录。
- 模型层使用目标项目当前 SQLAlchemy 初始化方式，不整体复制旧项目 `database.py`。
- 接口响应不暴露堆栈、数据库连接串、完整音视频 Base64 或隐私原文。
- 新增接口后同步更新 `docs/api/` 和前端 `types/`。

## 11. 分阶段迁移计划

### 阶段 0：迁移准备

目标：

- 明确 `html-interrogate` 是独立前端工程。
- 在项目文档中登记它与 `html-next`、`html/` 的关系。
- 后端先不新增任何接口。

产出：

- `html-interrogate` 工程骨架设计。
- API 契约文档。
- 字段映射表。

### 阶段 1：静态视觉重构

目标：

- 新建 Vue 页面和组件。
- 使用 mock 数据还原旧页面首屏。
- 抽取旧页面颜色、间距、字体、边框和状态样式。

验收：

- `/simulation/interrogation/1` 可访问。
- 首屏布局接近旧页面。
- 桌面三栏和窄屏纵向布局不重叠。
- 无真实接口时页面有清晰 mock 状态说明。

### 阶段 2：前端状态和消息逻辑迁移

目标：

- 建立 `useInterrogationRoom`、`useInterrogationChat`、`useCaseQuickQuery`。
- 将旧页面全局函数迁移为 composable。
- 将 DOM 操作改为响应式渲染。

验收：

- 发送消息有 loading 和失败提示。
- 消息追加、滚动到底部、阶段提示和发言指导可用。
- 快捷查询结果来源清晰。

### 阶段 3：WebSocket 真实链路接入

目标：

- 接入 `/ws/face`。
- 接入 `/ws/asr`。
- 复用目标项目现有 WebSocket 类型和工具。

验收：

- 摄像头授权后可看到视频。
- `/ws/face` 返回后分析面板更新。
- 麦克风授权后 `/ws/asr` 能收到转写回包。
- 停止审讯后媒体设备和 WebSocket 均释放。

### 阶段 4：后端 HTTP API 接入

目标：

- 接入案件详情 API。
- 接入会话创建 API。
- 接入发送讯问消息 API。
- 接入结束会话 API。

验收：

- 页面不再依赖 Jinja 注入。
- 刷新页面可恢复案件和会话基本信息。
- AI 回包能驱动消息、情绪、阶段和指导面板。

### 阶段 5：去除 mock 和兼容收尾

目标：

- 移除生产路径中的 mock 数据。
- 统一错误码和空状态。
- 更新 `docs/api/`、`docs/SPEC/frontend.md` 和部署说明。

验收：

- `pnpm typecheck` 通过。
- `pnpm build` 通过。
- 页面关键流程人工验证通过。
- 没有硬编码生产域名、密钥、Token、数据库地址或内部服务路径。

## 12. 验证方案

前端本地验证：

```bash
cd /home/eason/workspace/interrogate/html-interrogate
pnpm install
pnpm typecheck
pnpm build
pnpm dev --host 0.0.0.0
```

后端本地验证：

```bash
cd /home/eason/workspace/interrogate
python run.py
curl -i http://localhost:5000/health
```

WebSocket 链路验证：

```bash
node -e "const ws=new WebSocket('ws://localhost:5000/ws/face'); ws.onopen=()=>ws.send('not-json'); ws.onmessage=e=>{console.log(String(e.data)); ws.close(); process.exit(0)}"
node -e "const ws=new WebSocket('ws://localhost:5000/ws/asr'); ws.onopen=()=>ws.send('not-json'); ws.onmessage=e=>{console.log(String(e.data)); ws.close(); process.exit(0)}"
```

浏览器人工验收：

- 打开 `/simulation/interrogation/1`。
- 页面首屏布局与旧页面接近。
- 案件、嫌疑人、证据链、审讯要点显示正确。
- 摄像头权限、麦克风权限、连接状态、错误状态清晰可见。
- 发送消息后对话、阶段、发言指导同步更新。
- 停止审讯后摄像头、麦克风、WebSocket 和计时器释放。
- 控制台无未处理异常。
- 窄屏下没有文字重叠、按钮溢出和面板错位。

## 13. 风险和处理建议

| 风险 | 影响 | 处理建议 |
| --- | --- | --- |
| 旧页面是 Jinja，不是纯静态页面 | 不能直接复制成 Vue 工程 | 按组件和 composable 重构 |
| 旧模板字段与旧数据库模型可能不完全一致 | 迁移后字段缺失或显示空白 | 后端或前端 adapter 统一字段 |
| 目标项目当前缺少案件/会话 HTTP API | 页面无法完整联调 | 先定义 `/api/simulation/...` 契约，再实现后端 |
| 旧 `/api/voice/recognize` 与目标 `/ws/asr` 协议不同 | 录音逻辑不能直接复制 | 使用目标项目 `/ws/asr` 作为主链路 |
| `/ws/asr` 当前存在 `suspect_id` fallback 为 `"0"` 的情况 | ASR 记录可能无法绑定真实嫌疑人或会话 | 前端必须传 `suspect_id`，后端必要时扩展 `session_id` |
| `html-interrogate` 是新增前端入口 | 构建、部署和文档需要补充 | 更新 `docs/SPEC/frontend.md`、部署说明和 Docker 策略 |
| 视觉 1:1 与技术栈规范存在冲突 | 组件可维护性下降 | 保留视觉结果，重写实现结构 |
| 旧权限和登录链路未迁入 | 生产访问控制不完整 | 旧权限和登录链路不迁入 |

## 14. 推荐实施顺序

推荐顺序如下：

1. 新建 `html-interrogate` 工程骨架，技术栈对齐 `html-next`。
2. 用 mock 数据完成静态页面 1:1 重构。
3. 拆分组件和 composable，迁移旧页面交互逻辑。
4. 接入 `/ws/face` 和 `/ws/asr`。
5. 设计并实现 `/api/simulation/...` 后端接口。
6. 替换 mock 数据，完成案件、会话、消息真实联调。
7. 更新 API 文档、前端构建规范和部署策略。
8. 运行类型检查、构建检查和浏览器人工验收。

## 15. 最小可行版本

如果希望先快速跑通迁移页面，最小版本可以只包含：

- `html-interrogate` 工程骨架。
- `/simulation/interrogation/:caseId` 路由。
- 旧页面三栏布局和主要视觉样式。
- mock 案件数据。
- 本地消息发送模拟。
- `/ws/face` 实时分析。
- `/ws/asr` 语音转写。
- 停止审讯释放资源。

这个版本不包含完整案件管理、登录权限、历史复盘和正式 AI 审讯消息接口，但可以先验证页面结构、实时视频、实时音频和迁移风格是否成立。

## 16. 正式版本完成标准

正式版本应满足：

- 页面风格与旧 `simulation/interrogation` 基本一致。
- 前端实现为 Vue/TypeScript，不依赖 Jinja。
- 案件详情、会话创建、消息发送、结束会话先不与目标项目连通后端接口。
- 视频分析走 `/ws/face`。
- 语音识别走 `/ws/asr`。
- 所有接口字段在 `docs/api/` 和 `src/types/` 中有对应定义。
- 页面具备加载、空状态、错误、断开、重连、提交中和结束态。
- `pnpm typecheck` 和 `pnpm build` 通过。
- 后端 `GET /health`、`/ws/face`、`/ws/asr` 基础链路可验证。
- 没有修改 `interrogate/html/` 稳定旧前端。

## 17. 迁移决策建议

最终建议：

- 使用独立目录 `interrogate/html-interrogate/`。
- 技术栈完全对齐 `interrogate/html-next/`。
- 视觉结果尽量 1:1 还原旧页面。
- 代码结构按 Vue 组件和 composable 重写。
- 后端新建 `/api/simulation/...` 契约，不把旧项目单体路由整体搬入。
- 实时视频和语音优先复用目标项目已有 `/ws/face`、`/ws/asr`。
- 先做静态视觉和前端状态，再做后端真实联调。

