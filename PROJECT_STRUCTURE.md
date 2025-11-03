# 医疗新闻MVP项目结构文档

## 项目概述

这是一个基于RAG（检索增强生成）技术的医疗新闻聚合与问答系统，支持自动爬取医疗资讯、AI分析和智能问答。

**技术栈**:
- **后端**: Python 3.11 + FastAPI + PostgreSQL + Redis + MinIO
- **管理前端**: Vue 3 + TypeScript + Vite + Element Plus
- **H5前端**: Vue 3 + TypeScript + Vite + Vant
- **AI**: DeepSeek API (兼容OpenAI SDK)
- **爬虫**: Patchright (Playwright fork)
- **任务调度**: APScheduler

---

## 目录结构

```
medical-news-mvp/
├── backend/                          # 后端服务
│   ├── app/                          # 核心应用
│   │   ├── api/                      # API路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # 认证API
│   │   │   ├── articles.py           # 公开文章API
│   │   │   ├── chat.py               # RAG聊天API
│   │   │   └── admin/                # 管理端API
│   │   │       ├── __init__.py
│   │   │       ├── articles.py       # 文章管理
│   │   │       ├── crawler.py        # 爬虫管理
│   │   │       └── analytics.py      # 数据分析
│   │   │
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py         # AI分析服务（DeepSeek）
│   │   │   ├── rag_service.py        # RAG问答服务
│   │   │   └── crawler_service.py    # 爬虫服务
│   │   │
│   │   ├── utils/                    # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── timezone.py           # 时区处理（中国时区）
│   │   │   ├── html_cleaner.py       # HTML清理
│   │   │   ├── text_splitter.py      # 文本分块
│   │   │   └── s3_client.py          # MinIO/S3客户端
│   │   │
│   │   ├── tasks/                    # 定时任务
│   │   │   └── cleanup.py            # 软删除文章清理任务
│   │   │
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI应用入口
│   │   ├── config.py                 # 配置管理
│   │   ├── database.py               # 数据库连接
│   │   ├── models.py                 # SQLAlchemy模型
│   │   └── schemas.py                # Pydantic数据模型
│   │
│   ├── crawler/                      # 爬虫模块
│   │   ├── __init__.py
│   │   ├── base_crawler.py           # 爬虫基类
│   │   ├── crawler_factory.py        # 爬虫工厂
│   │   ├── pharnex_crawler.py        # 药渡云爬虫
│   │   └── wechat_crawler.py         # 微信公众号爬虫
│   │
│   ├── scripts/                      # 脚本工具
│   │   ├── __init__.py
│   │   ├── init_db.py                # 初始化数据库
│   │   ├── crawl_and_ingest.py       # 爬取并入库脚本
│   │   ├── analyze_and_embed.py      # AI分析和向量化
│   │   ├── migrate_add_wechat_fields.py       # 数据库迁移：微信字段
│   │   └── migrate_add_crawler_tasks.py       # 数据库迁移：爬虫任务表
│   │
│   ├── cache/                        # 缓存目录
│   │   ├── wechat_articles/          # 微信文章缓存（93个文件）
│   │   └── wechat_browser_state.json # 浏览器状态缓存
│   │
│   ├── .env                          # 环境变量配置
│   ├── requirements.txt              # Python依赖
│   └── pyproject.toml                # Python项目配置
│
├── admin-frontend/                   # 管理端前端（Vue 3 + Element Plus）
│   ├── src/
│   │   ├── api/                      # API客户端
│   │   │   └── admin.ts              # 管理端API接口
│   │   ├── components/               # Vue组件
│   │   ├── views/                    # 页面组件
│   │   │   ├── Dashboard.vue         # 仪表盘
│   │   │   ├── Articles.vue          # 文章管理（含AI分析）
│   │   │   └── Crawler.vue           # 爬虫管理
│   │   ├── router/                   # Vue Router配置
│   │   ├── stores/                   # Pinia状态管理
│   │   ├── App.vue                   # 根组件
│   │   └── main.ts                   # 入口文件
│   │
│   ├── public/                       # 静态资源
│   ├── package.json                  # NPM依赖
│   ├── tsconfig.json                 # TypeScript配置
│   └── vite.config.ts                # Vite配置
│
├── frontend/                         # H5前端（Vue 3 + Vant）
│   ├── src/
│   │   ├── api/                      # API客户端
│   │   ├── views/                    # 页面组件
│   │   ├── App.vue                   # 根组件
│   │   └── main.ts                   # 入口文件
│   ├── package.json                  # NPM依赖
│   └── vite.config.ts                # Vite配置
│
├── docker-compose.yml                # Docker编排配置
├── API_DOCUMENTATION.md              # API文档
├── PROJECT_STRUCTURE.md              # 项目结构文档（本文件）
└── README.md                         # 项目README

```

---

## 核心模块说明

### 1. API层 (`app/api/`)

**认证模块** (`auth.py`):
- JWT token生成和验证
- Bearer token认证中间件

**公开文章API** (`articles.py`):
- 文章列表（分页、过滤）
- 文章详情（含AI分析）
- AI分析生成（支持缓存和强制重新生成）

**聊天API** (`chat.py`):
- RAG问答接口
- 多轮对话支持

**管理端API** (`admin/`):
- `articles.py`: 文章CRUD、批量操作、高级搜索
- `crawler.py`: 爬虫任务管理、状态监控、日志查看
- `analytics.py`: 数据统计、趋势分析、来源分布

### 2. 业务逻辑层 (`app/services/`)

**AI分析服务** (`ai_service.py`):
- 使用DeepSeek API进行文章智能分析
- 150-250字专业医药行业分析
- 中文输出，易懂且专业
- 自动缓存机制，避免重复调用

**RAG服务** (`rag_service.py`):
- 向量检索（使用pgvector）
- GPT-4问答生成
- 对话历史管理

**爬虫服务** (`crawler_service.py`):
- 异步任务执行
- 进度跟踪
- 日志管理

### 3. 爬虫模块 (`crawler/`)

**基类架构**:
- `BaseCrawler`: 定义爬虫标准接口
- `CrawlerFactory`: 根据数据源创建爬虫实例

**具体实现**:
- `PharnexCrawler`: 药渡云前沿研究栏目
  - 列表页爬取
  - 详情页解析
  - 微信原文链接提取

- `WechatArticleCrawler`: 微信公众号文章
  - 浏览器自动化
  - 反爬策略（延迟、User-Agent轮换）
  - 缓存机制

### 4. 数据库模型 (`app/models.py`)

**核心表**:

**Article** (文章表):
```python
- id: Integer (主键)
- title: String
- summary: Text
- author: String
- source_id: Integer (外键)
- category: String
- tags: ARRAY(String)
- published_at: DateTime
- content_url: String
- content_text: Text
- content_source: String (wechat/pharnexcloud)
- original_source_url: String (微信原文链接)
- wechat_content_html: Text
- wechat_content_text: Text
- canonical_hash: String (SHA256，用于去重)
- is_deleted: Boolean (软删除标记)
- created_at: DateTime
- updated_at: DateTime
```

**Source** (数据源表):
```python
- id: Integer
- name: String (例如：药渡云)
- name_en: String
- base_url: String
```

**CrawlerTask** (爬虫任务表):
```python
- id: Integer
- config: JSONB (任务配置)
- status: String (pending/running/completed/failed)
- articles_count: Integer
- started_at: DateTime
- completed_at: DateTime
- error_message: Text
```

**ArticleAIOutput** (AI分析结果表):
```python
- id: Integer
- article_id: Integer (外键)
- version_no: Integer (文章版本号)
- summary: Text (存储AI分析文字，150-250字)
- key_points: ARRAY(String) (预留字段，当前未使用)
- entities: JSONB (预留字段，当前未使用)
- model_name: String (AI模型名称，如"deepseek-chat")
- created_at: DateTime
- updated_at: DateTime
```

### 5. 定时任务 (`app/tasks/cleanup.py`)

**清理任务**:
- 每天凌晨3:00自动执行
- 删除超过30天的软删除文章（可配置）
- 同时删除关联的S3文件
- 使用APScheduler调度

---

## 数据流程

### 1. 文章爬取流程

```
1. 用户通过前端创建爬虫任务
   ↓
2. POST /v1/admin/crawler/tasks
   ↓
3. crawler_service 创建任务记录
   ↓
4. 异步执行爬取：
   - PharnexCrawler 爬取列表页和详情页
   - 提取微信原文链接
   - WechatArticleCrawler 爬取微信内容
   ↓
5. 内容去重检查：
   - 计算 canonical_hash (SHA256)
   - 查询未删除文章
   - 查询已删除文章
   ↓
6. 数据存储：
   - 上传原始HTML到MinIO (raw bucket)
   - 上传清理后文本到MinIO (clean bucket)
   - 保存文章记录到PostgreSQL
   ↓
7. 任务完成，更新状态
```

### 2. RAG问答流程

```
1. 用户提交问题
   ↓
2. POST /v1/chat (需JWT认证)
   ↓
3. rag_service 处理：
   - 生成问题的向量表示
   - 在pgvector中检索相关文章
   - 构建上下文
   ↓
4. 调用GPT-4生成回答
   ↓
5. 返回答案和来源引用
```

### 3. 软删除与物理删除流程

```
1. 用户删除文章
   ↓
2. DELETE /v1/admin/articles/{id}
   ↓
3. 设置 is_deleted = True
   ↓
4. 文章不再出现在列表中
   ↓
5. 如果再次爬取相同文章：
   - 检测到已删除记录
   - 更新内容并恢复 (is_deleted = False)
   ↓
6. 30天后（凌晨3:00）：
   - cleanup_task 自动执行
   - 物理删除数据库记录
   - 删除S3文件
```

---

## 配置说明

### 环境变量 (`.env`)

**必需配置**:
```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/medical_news

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO/S3
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_RAW=medical-news-raw
S3_BUCKET_CLEAN=medical-news-clean

# DeepSeek AI (兼容OpenAI SDK)
AI_API_KEY=sk-...
AI_API_BASE=https://api.deepseek.com
AI_MODEL_CHAT=deepseek-chat
EMBEDDING_ENABLED=false

# JWT
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 清理配置
CLEANUP_DELETED_AFTER_DAYS=30  # 软删除文章保留天数
```

### Docker Compose 服务

```yaml
services:
  postgres:
    ports: 5432:5432
    volumes:
      - postgres_data:/var/lib/postgresql/data
    extensions: pgvector  # 向量检索

  redis:
    ports: 6379:6379

  minio:
    ports:
      - 9000:9000  # API
      - 9001:9001  # Console
    volumes:
      - minio_data:/data
```

---

## 部署说明

### 本地开发环境

**1. 启动基础服务**:
```bash
docker-compose up -d postgres redis minio
```

**2. 安装Python依赖**:
```bash
cd backend
pip install -r requirements.txt
```

**3. 初始化数据库**:
```bash
python scripts/init_db.py
```

**4. 启动后端**:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**5. 启动管理前端**:
```bash
cd admin-frontend
npm install
npm run dev
```

**6. 启动H5前端**:
```bash
cd frontend
npm install
npm run dev
```

**访问地址**:
- 管理前端: http://localhost:5173
- H5前端: http://localhost:5174 (自动分配端口)
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- MinIO控制台: http://localhost:9001

### 生产环境部署

**建议配置**:
1. 使用Gunicorn + Uvicorn workers运行后端
2. 使用Nginx作为反向代理
3. 启用HTTPS
4. 配置PostgreSQL连接池
5. 设置Redis持久化
6. 配置MinIO集群模式
7. 定期备份数据库

---

## 核心特性

### 1. 智能去重机制

**内容哈希**:
- 使用SHA256计算文章内容的哈希值
- 存储在 `canonical_hash` 字段
- 用于检测重复文章

**去重策略**:
1. 先查询未删除文章中是否存在
2. 如果存在，跳过爬取
3. 再查询已删除文章中是否存在
4. 如果存在，更新内容并恢复文章
5. 否则，插入新文章

### 2. 微信内容优先

**智能选择**:
- 如果检测到微信原文链接，自动爬取
- 比较微信内容和药渡云内容长度
- 选择内容更完整的版本作为主内容
- 同时保留两个版本供参考

### 3. 时区统一

**中国时区** (Asia/Shanghai, UTC+8):
- 所有时间字段使用naive datetime
- 值表示中国时间
- 兼容PostgreSQL `TIMESTAMP WITHOUT TIME ZONE`
- 统一使用 `app.utils.timezone` 模块

### 4. 缓存机制

**微信文章缓存**:
- 使用URL的MD5作为缓存文件名
- 缓存位置: `backend/cache/wechat_articles/`
- 避免重复爬取相同文章
- 加速开发和测试

**浏览器状态缓存**:
- 保存验证后的Cookie
- 复用浏览器会话
- 减少验证码风险

### 5. AI智能分析

**DeepSeek API集成**:
- 使用DeepSeek模型进行文章智能分析
- 兼容OpenAI SDK，易于集成
- 成本更低，响应更快

**分析特性**:
- 自动生成150-250字专业分析
- 医药行业专业术语理解
- 简体中文输出，专业且易懂
- 智能缓存机制，避免重复分析

**前端集成**:
- 管理后台一键生成AI分析
- 支持查看已有分析
- 支持强制重新生成
- 实时显示分析进度

### 6. 定时清理

**APScheduler调度**:
- 每天凌晨3:00执行
- 清理超过30天的软删除文章
- 删除数据库记录和S3文件
- 自动日志记录

---

## 开发规范

### 代码风格

- Python: PEP 8
- TypeScript: ESLint + Prettier
- 使用类型提示
- 编写文档字符串

### Git提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
refactor: 重构
test: 测试
chore: 构建/工具变更
```

### API设计原则

1. RESTful风格
2. 统一的响应格式
3. 详细的错误信息
4. 分页参数标准化
5. 使用HTTP状态码

---

## 故障排查

### 常见问题

**1. 后端启动失败**
- 检查PostgreSQL是否运行
- 检查环境变量配置
- 查看 `docker-compose logs`

**2. 爬虫失败**
- 检查网络连接
- 查看爬虫日志: GET /v1/admin/crawler/logs
- 检查目标网站HTML结构是否变化

**3. 微信爬取被阻止**
- 降低爬取频率
- 清除浏览器缓存
- 更换User-Agent

**4. 向量检索慢**
- 为embedding字段创建索引
- 增加PostgreSQL内存配置
- 考虑使用专业向量数据库

---

## 待优化项

1. **性能优化**:
   - 添加Redis缓存层
   - 实现文章全文搜索（Elasticsearch）
   - 优化数据库查询

2. **功能增强**:
   - 支持更多数据源
   - 文章自动分类
   - 用户权限管理
   - 导出功能

3. **监控**:
   - 添加Prometheus指标
   - 集成日志聚合（ELK）
   - 错误追踪（Sentry）

4. **测试**:
   - 单元测试覆盖
   - 集成测试
   - E2E测试

---

## 许可证

本项目为内部MVP项目，未对外开源。

---

## 联系方式

如有问题，请联系项目维护团队。

**最后更新**: 2025-11-03 (v1.1.0 - 新增AI智能分析功能)
