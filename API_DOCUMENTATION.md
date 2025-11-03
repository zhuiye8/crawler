# 医疗新闻MVP API文档

## 基本信息

- **基础URL**: `http://localhost:8000`
- **前端URL**: `http://localhost:5173`
- **API版本**: v1
- **访问方式**: ✅ 完全开放，无需任何认证

> **重要提示**: 本API完全开放，不需要任何认证即可访问所有端点。外部用户可直接调用获取数据。

---

## 目录

1. [公开文章API](#公开文章api)
2. [聊天API](#聊天api)
3. [管理端-文章](#管理端-文章)
4. [管理端-爬虫](#管理端-爬虫)
5. [管理端-分析](#管理端-分析)
6. [通用响应格式](#通用响应格式)
7. [错误码说明](#错误码说明)

---

## 公开文章API

### 获取文章列表

获取已发布的文章列表，支持分页和过滤。

**端点**: `GET /v1/articles`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|-----|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20，最大100 |
| category | string | 否 | 按分类过滤 |
| from_date | string | 否 | 起始日期 (YYYY-MM-DD) |

**响应** (200 OK):
```json
{
  "data": [
    {
      "id": 1,
      "title": "完胜司美格鲁肽",
      "summary": "文章摘要内容...",
      "author": "药渡云",
      "source_name": "药渡云",
      "category": "前沿研究",
      "tags": ["减肥药", "GLP-1"],
      "published_at": "2025-11-03T10:00:00"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "page_size": 20
  }
}
```

**示例**:
```bash
# 获取第1页，每页20条
curl http://localhost:8000/v1/articles?page=1&page_size=20

# 按分类过滤
curl http://localhost:8000/v1/articles?category=前沿研究

# 按日期过滤
curl "http://localhost:8000/v1/articles?from_date=2025-10-01"
```

### 获取文章详情

获取单篇文章的完整内容和AI分析结果。

**端点**: `GET /v1/articles/{article_id}`

**路径参数**:
| 参数 | 类型 | 说明 |
|-----|------|-----|
| article_id | integer | 文章ID |

**响应** (200 OK):
```json
{
  "id": 1,
  "title": "完胜司美格鲁肽",
  "summary": "文章摘要...",
  "author": "药渡云",
  "source_name": "药渡云",
  "category": "前沿研究",
  "tags": ["减肥药"],
  "published_at": "2025-11-03T10:00:00",
  "content_url": "https://www.pharnexcloud.com/...",
  "content_text_excerpt": "文章内容前500字...",
  "ai_analysis": {
    "summary": "AI生成的摘要",
    "key_points": ["要点1", "要点2"],
    "entities": {
      "drugs": ["司美格鲁肽"],
      "companies": ["Novo Nordisk"]
    }
  }
}
```

**示例**:
```bash
curl http://localhost:8000/v1/articles/1
```

---

## 聊天API

### RAG问答

基于文章知识库进行智能问答。**完全开放，无需认证。**

**端点**: `POST /v1/chat`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "question": "GLP-1减肥药的最新研究进展是什么？",
  "conversation_id": "uuid-string"  // 可选，用于多轮对话
}
```

**响应** (200 OK):
```json
{
  "answer": "根据最新研究，GLP-1减肥药...",
  "sources": [
    {
      "article_id": 1,
      "title": "完胜司美格鲁肽",
      "excerpt": "相关内容片段..."
    }
  ],
  "conversation_id": "uuid-string"
}
```

**示例**:
```bash
# 直接调用，无需token
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "GLP-1减肥药有哪些？"}'

# 多轮对话示例
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "还有哪些副作用？",
    "conversation_id": "之前返回的conversation_id"
  }'
```

---

## 管理端-文章

管理端文章接口提供更强大的搜索、编辑和管理功能。

### 获取文章列表（管理端）

**端点**: `GET /v1/admin/articles/`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|-----|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| keyword | string | 否 | 关键词搜索（标题/摘要/作者） |
| category | string | 否 | 分类过滤 |
| content_source | string | 否 | 来源过滤 (wechat/pharnexcloud) |
| from_date | string | 否 | 起始日期 (YYYY-MM-DD) |
| to_date | string | 否 | 结束日期 (YYYY-MM-DD) |

**响应** (200 OK):
```json
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "items": [
    {
      "id": 1,
      "title": "完胜司美格鲁肽",
      "summary": "摘要...",
      "author": "药渡云",
      "category": "前沿研究",
      "tags": ["减肥药"],
      "published_at": "2025-11-03T10:00:00",
      "content_source": "wechat",
      "created_at": "2025-11-03T09:00:00"
    }
  ]
}
```

**示例**:
```bash
# 关键词搜索
curl "http://localhost:8000/v1/admin/articles/?keyword=减肥药"

# 按来源过滤
curl "http://localhost:8000/v1/admin/articles/?content_source=wechat"

# 组合搜索
curl "http://localhost:8000/v1/admin/articles/?keyword=GLP-1&from_date=2025-10-01&to_date=2025-11-03"
```

### 获取文章详情（管理端）

**端点**: `GET /v1/admin/articles/{article_id}`

**响应** (200 OK):
```json
{
  "id": 1,
  "title": "完胜司美格鲁肽",
  "summary": "摘要...",
  "author": "药渡云",
  "category": "前沿研究",
  "tags": ["减肥药"],
  "published_at": "2025-11-03T10:00:00",
  "content_url": "https://...",
  "content_text": "完整文本内容...",
  "content_source": "wechat",
  "original_source_url": "https://mp.weixin.qq.com/...",
  "wechat_content_html": "<div>...</div>",
  "created_at": "2025-11-03T09:00:00",
  "updated_at": "2025-11-03T09:30:00"
}
```

### 更新文章

**端点**: `PUT /v1/admin/articles/{article_id}`

**请求体**:
```json
{
  "title": "新标题",
  "summary": "新摘要",
  "category": "临床试验",
  "tags": ["新标签"]
}
```

**响应** (200 OK): 返回更新后的文章对象

### 删除文章（软删除）

**端点**: `DELETE /v1/admin/articles/{article_id}`

**响应** (200 OK):
```json
{
  "message": "Deleted successfully",
  "article_id": 1
}
```

### 批量删除文章

**端点**: `DELETE /v1/admin/articles/batch/delete`

**请求体**:
```json
{
  "article_ids": [1, 2, 3, 4, 5]
}
```

**响应** (200 OK):
```json
{
  "message": "Batch delete successful",
  "deleted_count": 5,
  "total_requested": 5
}
```

**示例**:
```bash
curl -X DELETE http://localhost:8000/v1/admin/articles/batch/delete \
  -H "Content-Type: application/json" \
  -d '{"article_ids": [1,2,3]}'
```

---

## 管理端-爬虫

爬虫管理接口用于启动爬取任务、查看任务状态和日志。

### 获取可用数据源

**端点**: `GET /v1/admin/crawler/sources`

**响应** (200 OK):
```json
[
  {
    "name": "pharnexcloud",
    "display_name": "药渡云",
    "description": "药渡云前沿研究栏目",
    "supports_wechat": true
  }
]
```

### 创建爬虫任务

**端点**: `POST /v1/admin/crawler/tasks`

**请求体**:
```json
{
  "source": "pharnexcloud",
  "pages": 10,
  "max_articles": 50,
  "days_back": 7,
  "from_date": "2025-10-01",
  "to_date": "2025-11-03"
}
```

**参数说明**:
- `source`: 数据源名称 (目前支持: pharnexcloud)
- `pages`: 爬取页数，默认10
- `max_articles`: 最大文章数，可选
- `days_back`: 爬取最近N天的文章，可选
- `from_date`: 起始日期，可选
- `to_date`: 结束日期，可选

**响应** (200 OK):
```json
{
  "message": "Task created and started",
  "task_id": 23,
  "config": {
    "pages": 10,
    "max_articles": 50
  }
}
```

**示例**:
```bash
# 爬取最近7天的文章
curl -X POST http://localhost:8000/v1/admin/crawler/tasks \
  -H "Content-Type: application/json" \
  -d '{"source": "pharnexcloud", "pages": 10, "days_back": 7}'

# 爬取指定日期范围
curl -X POST http://localhost:8000/v1/admin/crawler/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "source": "pharnexcloud",
    "pages": 5,
    "from_date": "2025-10-01",
    "to_date": "2025-11-01"
  }'
```

### 获取爬虫任务列表

**端点**: `GET /v1/admin/crawler/tasks`

**查询参数**:
| 参数 | 类型 | 说明 |
|-----|------|-----|
| page | integer | 页码 |
| page_size | integer | 每页数量 |
| status | string | 状态过滤 (pending/running/completed/failed) |

**响应** (200 OK):
```json
{
  "total": 23,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": 23,
      "config": {
        "pages": 10,
        "max_articles": 50
      },
      "status": "completed",
      "articles_count": 45,
      "started_at": "2025-11-03T10:00:00",
      "completed_at": "2025-11-03T10:05:00",
      "error_message": null,
      "created_at": "2025-11-03T09:59:00"
    }
  ]
}
```

### 获取任务详情

**端点**: `GET /v1/admin/crawler/tasks/{task_id}`

**响应** (200 OK): 返回单个任务对象

### 获取爬虫状态

**端点**: `GET /v1/admin/crawler/status`

**响应** (200 OK):
```json
{
  "is_running": true,
  "current_task": {
    "id": 23,
    "status": "running",
    "config": {"pages": 10}
  },
  "progress": {
    "current_page": 3,
    "total_pages": 10,
    "articles_found": 15
  }
}
```

### 获取爬虫日志

**端点**: `GET /v1/admin/crawler/logs`

**响应** (200 OK):
```json
[
  {
    "timestamp": "2025-11-03T10:00:00",
    "level": "INFO",
    "message": "任务 #23 开始执行..."
  },
  {
    "timestamp": "2025-11-03T10:00:10",
    "level": "INFO",
    "message": "正在爬取第 1 页..."
  }
]
```

**示例**:
```bash
# 实时监控爬虫日志
while true; do
  curl -s http://localhost:8000/v1/admin/crawler/logs | jq '.'
  sleep 2
done
```

---

## 管理端-分析

数据分析和统计接口。

### 获取概览统计

**端点**: `GET /v1/admin/analytics/overview`

**响应** (200 OK):
```json
{
  "total_articles": 150,
  "today_articles": 5,
  "week_articles": 35,
  "month_articles": 120,
  "wechat_articles": 80,
  "pharnex_articles": 70
}
```

### 获取文章趋势

**端点**: `GET /v1/admin/analytics/trends`

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|-----|
| days | integer | 30 | 分析天数 (1-365) |

**响应** (200 OK):
```json
[
  {
    "date": "2025-10-01",
    "count": 5
  },
  {
    "date": "2025-10-02",
    "count": 8
  }
]
```

**示例**:
```bash
# 获取最近30天趋势
curl http://localhost:8000/v1/admin/analytics/trends?days=30

# 获取最近7天趋势
curl http://localhost:8000/v1/admin/analytics/trends?days=7
```

### 获取来源分布

**端点**: `GET /v1/admin/analytics/sources`

**响应** (200 OK):
```json
[
  {
    "source": "WeChat",
    "count": 80,
    "percentage": 53.33
  },
  {
    "source": "PharnexCloud",
    "count": 70,
    "percentage": 46.67
  }
]
```

### 获取分类分布

**端点**: `GET /v1/admin/analytics/categories`

**响应** (200 OK):
```json
[
  {
    "category": "前沿研究",
    "count": 85
  },
  {
    "category": "临床试验",
    "count": 45
  },
  {
    "category": "药物审批",
    "count": 20
  }
]
```

---

## 通用响应格式

### 成功响应

所有成功的API请求返回HTTP状态码 `2xx` 和JSON格式数据。

### 分页响应

包含分页的响应格式：
```json
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "items": [...]
}
```

---

## 错误码说明

### HTTP状态码

| 状态码 | 说明 |
|--------|-----|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（需要登录） |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "错误详细信息"
}
```

### 常见错误示例

**400 Bad Request**:
```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

**404 Not Found**:
```json
{
  "detail": "Article not found"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Chat error: OpenAI API key not configured"
}
```

---

## 自动API文档

FastAPI自动生成的交互式API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

这些界面提供：
- 所有API端点的详细说明
- 请求/响应示例
- 在线测试功能
- 数据模型Schema

---

## 注意事项

1. **完全开放**: ✅ 所有API完全开放，无需任何认证即可访问
2. **时区**: 所有时间字段使用中国时区（Asia/Shanghai, UTC+8）
3. **软删除**: 删除操作为软删除，文章仍保留在数据库中（`is_deleted=true`）
4. **物理删除**: 已删除的文章会在30天后自动物理删除（每天凌晨3:00执行）
5. **爬虫限制**: 同一时间只能运行一个爬虫任务
6. **微信内容**: 系统会自动尝试爬取微信公众号原文（如果有链接）

### 安全建议

虽然API完全开放，但在生产环境中建议：
- 使用反向代理（Nginx）添加基础的IP白名单
- 监控OpenAI API使用量，避免超额费用
- 定期检查数据库访问日志
- 考虑添加简单的API key或rate limiting（如有需要）

---

## 更新日志

### v1.0.0 (2025-11-03)
- ✅ 完整的文章管理API
- ✅ 爬虫任务管理
- ✅ RAG智能问答
- ✅ 数据分析统计
- ✅ 微信公众号内容爬取
- ✅ 定时清理任务
- ✅ 软删除机制
