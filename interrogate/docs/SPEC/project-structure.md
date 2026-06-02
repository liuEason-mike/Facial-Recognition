# 目录结构

```text
interrogate/
├── run.py                         # Flask + WebSocket + 静态前端启动入口
├── requirement.txt                # Python 依赖
├── .env                           # 本地环境变量，禁止提交真实密钥
├── .env_pro                       # 生产环境变量样式文件，禁止提交真实密钥
├── face_landmarker.task           # MediaPipe 模型资源
├── deepface/weight/               # DeepFace 权重
├── wheel/                         # 离线 Python wheel
├── app/
│   ├── __init__.py                # 应用工厂、日志、健康检查、建表
│   ├── config.py                  # 配置与数据库连接
│   ├── extensions.py              # SQLAlchemy 实例
│   ├── constants/codes.py         # 业务状态码
│   ├── utils/                     # 响应、图像工具
│   ├── models/                    # SQLAlchemy ORM 模型
│   ├── repository/                # 数据访问层
│   ├── routes/
│   │   ├── api/                   # HTTP API，当前 baseline.py 为空
│   │   └── ws/                    # WebSocket 路由
│   └── service/
│       ├── audio/                 # ASR 客户端
│       └── video/                 # 图像分析、特征、异常检测
├── html/
│   ├── package.json               # 前端依赖与脚本
│   ├── vite.config.ts             # Vite 构建与代理配置
│   ├── .env                       # 前端环境变量
│   └── src/
│       ├── pages/                 # 页面路由
│       ├── components/            # 页面组件
│       ├── constants/             # 常量
│       ├── types/                 # TypeScript 类型
│       ├── utils/                 # WebSocket、媒体工具
│       └── styles/                # 全局样式
├── html-interrogate/
│   ├── package.json               # 新审讯实时工作台前端依赖与脚本
│   ├── vite.config.ts             # Vite 构建与 /api、/ws 开发代理配置
│   ├── uno.config.ts              # UnoCSS 配置
│   └── src/
│       ├── components/interrogation/ # 审讯室组件
│       ├── composables/            # 媒体、WebSocket、会话状态组合式函数
│       ├── types/                  # WebSocket 与页面状态类型
│       ├── utils/                  # WebSocket、媒体、ASR、风险工具函数
│       └── views/                  # 路由级页面
├── build/docker/
│   ├── Dockerfile                 # 前后端一体镜像
│   └── Dockerfile_backend         # 后端镜像，当前存在污染内容，需修复后使用
├── storage/
│   ├── app.db                     # SQLite fallback 产物，生产禁止使用
│   └── logs/                      # 应用日志
└── docs/
    ├── api/                       # 接口文档
    └── SPEC/                      # 产品需求与工程规范文档
        ├── overview.md            # 工程规范总览索引
        ├── PRD.md                 # 产品需求文档
        └── *.md                   # 工程规范子文档
```
