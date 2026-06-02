# Changelog

## 2026-05-27

- 来源：`docs/SPEC/html-interrogate-ui-adjustments/2026052704.md` 前端页面调整。
- 影响范围：`html-interrogate` 左侧栏高度分配、人声分离展示数量和关键词提炼滚动区域。
- 变更内容：左侧微表情分析显式填充剩余高度；人声分离固定展示按时间倒序的最新 6 条记录并隐藏溢出，不再显示内部滚动条；关键词提炼继续在模块内部滚动。
- 验证方式：`conda run --no-capture-output -n interrogation_env pnpm --dir html-interrogate exec node --test --experimental-strip-types src/utils/speakerTranscript.test.ts src/utils/layoutStructure.test.ts`；`conda run -n interrogation_env pnpm --dir html-interrogate test:unit`；`conda run -n interrogation_env pnpm --dir html-interrogate build`。
- 来源：`docs/SPEC/html-interrogate-ui-adjustments/2026052703.md` 前端页面调整。
- 影响范围：`html-interrogate` 左侧状态监测面板、右侧历史记录/实时转写/人声分离/关键词提炼布局和结构测试。
- 变更内容：拉高左侧“状态监测”面板；右侧改为固定栏目布局，固定历史记录、最新转写、人声分离和关键词提炼高度；移除带时间戳的转写列表；“说话人转写”改名为“人声分离”；关键词和人声分离列表过长时在各自区域内滚动。
- 验证方式：`conda run -n interrogation_env pnpm --dir html-interrogate test:unit`；`conda run -n interrogation_env pnpm --dir html-interrogate build`。
- 来源：服务器 Docker 容器缺少 `PYANNOTE_DIARIZATION_ENDPOINT` 导致 `/api/asr/diarization/align` 返回 `speaker_diarization_unavailable`。
- 影响范围：Docker 构建上下文与运行镜像内后端环境变量加载。
- 变更内容：允许根目录 `.env` 进入 Docker 构建上下文，并在运行镜像中复制为 `/app/.env`，供 Flask 启动时加载 pyannote endpoint 等配置。
- 验证方式：静态检查 `build/docker/Dockerfile` 包含 `COPY .env /app/.env`，`.dockerignore` 不再排除根目录 `.env`；完整镜像构建和容器内接口验证需在服务器执行。
- 来源：说话人分离接口 `/api/asr/diarization/align` 返回 `speaker_diarization_unavailable`。
- 影响范围：后端 pyannote 外部服务适配层、说话人分离单元测试。
- 变更内容：`PyannoteDiarizationClient` 默认使用无代理 `urllib` opener 直连 pyannote 服务，避免进程级 `HTTP_PROXY/HTTPS_PROXY` 影响内网 `PYANNOTE_DIARIZATION_ENDPOINT`。
- 验证方式：`conda run -n interrogation_env pytest test/test_speaker_diarization.py`；Flask 测试客户端调用 `/api/asr/diarization/align` 返回 `200 ok`。
- 补充修复：`PyannoteDiarizationClient` 请求前懒加载 `PYANNOTE_DIARIZATION_ENDPOINT`，并在进程环境缺失时无依赖读取项目根目录 `.env`，避免路由单例初始化早于 `.env` 加载时持续返回 `endpoint_required`。
- 来源：`docs/SPEC/html-interrogate-ui-adjustments/2026052701.md` 前端展示调整。
- 影响范围：`html-interrogate` 说话人转写展示、说话人片段过滤工具和前端单元测试。
- 变更内容：页面过滤空白说话人转写片段，不再显示说话片段起止时间，并统一展示为 `说话人A：转写文本内容`。
- 验证方式：`conda run -n interrogation_env pnpm --dir html-interrogate test:unit`；`conda run -n interrogation_env pnpm --dir html-interrogate build`。
