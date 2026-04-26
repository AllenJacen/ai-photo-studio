# AI 艺术照生成平台

AI 驱动的婚纱照与艺术照生成平台，支持上传个人照片，选择场景，调用多种 AI 大模型生成高质量艺术照。

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui |
| 后端 | Python FastAPI + SQLAlchemy + Alembic |
| 队列 | Celery + Redis |
| AI 模型 | Flux.1 Dev/Pro、SDXL、DALL-E 3（Strategy Pattern 统一接口） |
| 存储 | S3/OSS（本地用 MinIO） |
| 数据库 | PostgreSQL |

## 快速启动（Docker Compose）

```bash
# 1. 克隆并进入项目
cd ai-photo-studio

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Keys（不填则使用 Mock 模式可体验 UI）

# 3. 一键启动所有服务
docker compose up --build

# 4. 访问
#   前端:     http://localhost:3000
#   后端 API: http://localhost:8000/docs
#   任务监控: http://localhost:5555  (Flower)
#   对象存储: http://localhost:9001  (MinIO Console，admin/minioadmin)
```

## 本地开发

### 后端
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 启动 PostgreSQL 和 Redis（可用 Docker）
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16-alpine
docker run -d -p 6379:6379 redis:7-alpine

# 初始化数据库 + 种子数据
python app/db/seed.py

# 启动 API 服务
uvicorn main:app --reload --port 8000

# 启动 Celery Worker（新终端）
celery -A app.workers.celery_app worker -Q generation -c 2 --loglevel=info
```

### 前端
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

## 功能列表

- ✅ 用户注册/登录（邮箱 + 密码）
- ✅ 图片上传（OSS 直传，人脸检测）
- ✅ 场景库（13 个初始场景，支持扩展）
- ✅ AI 模型切换（Flux Dev/Pro、SDXL、DALL-E 3）
- ✅ 异步生成任务（Celery + Redis 队列）
- ✅ WebSocket 实时进度推送
- ✅ 生成结果展示与下载
- ✅ 历史记录管理
- ✅ 积分系统（注册送 5 次免费额度）
- ✅ 会员体系（免费/标准/专业）

## AI 模型集成（Mock 模式）

不填写 API Key 时，系统自动使用 Mock 模式（返回 picsum 随机图片），可完整体验所有 UI 功能。

填写真实 API Key 后即可切换真实 AI 生成：
- `REPLICATE_API_TOKEN`：用于 Flux.1 Dev/Pro 和 SDXL
- `OPENAI_API_KEY`：用于 DALL-E 3

## 项目结构

```
ai-photo-studio/
├── frontend/               # React 前端
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── services/       # API 调用
│   │   ├── stores/         # Zustand 状态
│   │   └── types/          # TypeScript 类型
│   └── Dockerfile
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/         # API 路由
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/        # Pydantic Schema
│   │   ├── services/
│   │   │   └── ai_gateway/ # AI 模型调度层
│   │   ├── workers/        # Celery Worker
│   │   └── db/seed.py      # 种子数据
│   └── Dockerfile
├── docker-compose.yml      # 一键启动
└── .env.example            # 环境变量模板
```
