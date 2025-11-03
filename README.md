# 医药资讯聚合 + AI对话 | MVP

> 基于RAG的医药资讯智能问答系统，爬取药渡云前沿研究资讯，提供中文智能问答

## 项目概述

**技术栈**
- **后端**: FastAPI + PostgreSQL + pgvector + OpenAI API
- **前端**: Vue 3 + Vant + TypeScript
- **爬虫**: Playwright
- **存储**: MinIO (S3兼容)

**核心功能**
- ✅ 爬取药渡云前沿研究资讯（100+篇文章）
- ✅ AI自动分析（摘要、实体提取）
- ✅ 向量检索 + 全文检索混合搜索
- ✅ GPT-4对话，带引用来源
- ✅ H5移动端对话页面

---

## 快速启动（5分钟）

### 前置要求
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+
- OpenAI API Key

### 1. 克隆项目
```bash
cd C:\work\lianhuan\medical-news-mvp
```

### 2. 启动基础设施
```bash
# 启动 PostgreSQL + Redis + MinIO
docker-compose up -d

# 验证服务
docker ps
# 应该看到 3 个容器运行中
```

### 3. 配置环境变量
```bash
cd backend
cp .env.example .env

# 编辑 .env 文件，填入你的 OpenAI API Key
# OPENAI_API_KEY=sk-your-key-here
```

### 4. 安装后端依赖
```bash
# 激活conda环境 lh
conda activate lh

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 5. 初始化数据库
```bash
python scripts/init_db.py
```

### 6. 爬取数据（10-15分钟）
```bash
# 爬取药渡云前沿研究（10页，约100篇文章）
python scripts/crawl_and_ingest.py

# 预期输出：
# ✅ Page 1: Found 10 articles
# ✅ Page 2: Found 10 articles
# ...
# ✅ Ingested: 文章标题 (ID: 1)
```

### 7. AI分析与向量化（15-20分钟）
```bash
# 生成AI分析 + 向量embedding
python scripts/analyze_and_embed.py

# 预期输出：
# 🤖 Processing: 文章标题
#   ✂️  Split into 5 chunks
#   📊 Embedding chunk 1/5
#   ✅ Completed
```

### 8. 启动后端API
```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload

# 访问 API 文档
# http://localhost:8000/docs
```

### 9. 启动前端H5
```bash
cd ../frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问应用
# http://localhost:5173
```

---

## 使用指南

### 1. 测试对话功能
1. 打开浏览器访问 `http://localhost:5173`
2. 在输入框中输入问题，例如：
   - "最近有哪些GLP-1药物的研发进展？"
   - "介绍一下CAR-T疗法的最新进展"
   - "肿瘤免疫治疗有哪些新突破？"
3. 系统会返回中文答案并附带引用来源
4. 点击引用可跳转到原文

### 2. 查看API文档
访问 `http://localhost:8000/docs` 查看完整的API文档

**核心API**:
- `POST /v1/auth/token` - 获取JWT token
- `GET /v1/articles` - 文章列表
- `GET /v1/articles/{id}` - 文章详情
- `POST /v1/chat` - 对话接口

### 3. 测试API（使用curl）
```bash
# 1. 获取token
curl -X POST http://localhost:8000/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'

# 2. 对话（替换<TOKEN>为上一步返回的token）
curl -X POST http://localhost:8000/v1/chat \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"question": "最近有哪些GLP-1药物的研发进展？"}'
```

---

## 项目结构

```
medical-news-mvp/
├── docker-compose.yml          # Docker服务配置
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI主应用
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── models.py          # SQLAlchemy模型
│   │   ├── schemas.py         # Pydantic模型
│   │   ├── api/               # API端点
│   │   │   ├── auth.py
│   │   │   ├── articles.py
│   │   │   └── chat.py
│   │   ├── services/          # 业务逻辑
│   │   │   └── rag_service.py # RAG核心服务
│   │   └── utils/             # 工具函数
│   │       ├── html_cleaner.py
│   │       ├── text_splitter.py
│   │       └── s3_client.py
│   ├── crawler/
│   │   └── pharnex_crawler.py # 药渡云爬虫
│   ├── scripts/
│   │   ├── init_db.py         # 数据库初始化
│   │   ├── crawl_and_ingest.py # 爬取并入库
│   │   └── analyze_and_embed.py # AI分析与向量化
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   └── Chat.vue       # 对话页面
│   │   ├── api/
│   │   │   └── client.ts      # API客户端
│   │   ├── App.vue
│   │   └── main.ts
│   ├── vite.config.ts
│   └── package.json
└── README.md
```

---

## 常见问题

### Q1: docker-compose启动失败
**A**: 检查Docker是否正在运行，端口5432/6379/9000是否被占用
```bash
# 检查端口占用
netstat -ano | findstr "5432"
netstat -ano | findstr "6379"
netstat -ano | findstr "9000"
```

### Q2: 爬虫失败或超时
**A**:
1. 检查网络连接
2. 药渡云网站可能有反爬机制，可以：
   - 调整`pharnex_crawler.py`中的`headless=False`查看浏览器行为
   - 增加`await asyncio.sleep()`延时
   - 手动调整HTML选择器

### Q3: OpenAI API调用失败
**A**:
1. 检查`.env`中的`OPENAI_API_KEY`是否正确
2. 检查网络是否能访问OpenAI API
3. 检查API余额是否充足

### Q4: pgvector扩展安装失败
**A**:
```bash
# 进入PostgreSQL容器
docker exec -it medical-news-postgres bash

# 手动安装扩展
psql -U postgres -d medical_news -c "CREATE EXTENSION vector;"
```

### Q5: 前端无法连接后端
**A**:
1. 确保后端API在`http://localhost:8000`运行
2. 检查`frontend/vite.config.ts`中的proxy配置
3. 查看浏览器Console是否有CORS错误

---

## 开发指南

### 添加新的数据源
1. 在`backend/crawler/`创建新的爬虫文件
2. 在`sources`表中添加新的数据源记录
3. 修改`crawl_and_ingest.py`支持新爬虫
4. 运行爬虫并入库

### 调整AI分析维度
修改`backend/scripts/analyze_and_embed.py`中的Prompt模板：
```python
prompt = f"""
你是一名熟悉医药行业的资深分析师。

【输出JSON】
{{
  "summary": "...",
  "key_points": [...],
  "entities": {{...}},
  "新字段": "..."
}}

【文章】
{article.content_text}
"""
```

### 调整向量检索策略
修改`backend/app/services/rag_service.py`中的`hybrid_search`函数：
- 调整`top_k`参数（默认10）
- 调整RRF的`k`参数（默认60）
- 添加重排模型（Cross-Encoder）

---

## 性能优化建议

1. **缓存热门问题**
```python
# 使用Redis缓存
@lru_cache(maxsize=100)
async def chat_with_rag(question, ...):
    ...
```

2. **批量生成Embedding**
```python
# 一次调用生成多个embedding
embeddings = await client.embeddings.create(
    model="text-embedding-3-small",
    input=[chunk1, chunk2, chunk3]
)
```

3. **添加数据库索引**
```sql
CREATE INDEX idx_articles_category ON articles(category);
CREATE INDEX idx_chat_messages_session_created
  ON chat_messages(session_id, created_at DESC);
```

---

## 后续扩展计划

### Phase 2（W4-W5）
- [ ] 扩展药渡云其他栏目（招标采购、公司动态等）
- [ ] 添加药智网数据源
- [ ] 定时爬取任务（Celery Beat）
- [ ] 完整AI分析（新闻分类、情感分析）

### Phase 3（W6+）
- [ ] Content Studio管理后台
- [ ] 搜索页（/search）
- [ ] 用户反馈与评分
- [ ] 监控告警（Prometheus + Grafana）

---

## 技术支持

如遇到问题，请检查：
1. 📋 本README的"常见问题"章节
2. 📝 `/MVP开发计划_3周快速迭代.md` - 详细开发计划
3. 📊 `/开发实施计划_5周迭代.md` - 完整技术方案
4. 📄 `/医药资讯聚合_ai_对话_PRD_v1.4_final.md` - 产品需求文档

---

## License

MIT License

---

## 致谢

- OpenAI - GPT-4 & Embedding API
- pgvector - PostgreSQL向量检索扩展
- FastAPI - 高性能Web框架
- Vue 3 & Vant - 前端UI框架
- Playwright - 浏览器自动化

---

**MVP Status**: ✅ 核心功能已完成，可开始测试与迭代优化！
