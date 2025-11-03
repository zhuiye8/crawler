# 后台管理系统详细实施指南

> 医药资讯 MVP - 后台管理系统详细开发指南（可直接执行）

## 📅 更新时间
2025-10-30

## 🎯 设计原则

1. **简单高效**：代码逻辑清晰，避免过度封装
2. **职责单一**：每个文件、函数只做一件事
3. **渐进式开发**：先核心功能，后扩展功能
4. **中文注释**：所有注释使用中文
5. **前后端分离**：API清晰定义，便于维护

---

## 第一阶段：核心功能开发（Day 1-10）

### Day 1-3：后端基础架构

#### 1.1 创建目录结构

```bash
cd C:\work\lianhuan\medical-news-mvp\backend

# 创建后台管理API目录
mkdir app\api\admin
type nul > app\api\admin\__init__.py
type nul > app\api\admin\articles.py
type nul > app\api\admin\crawler.py
type nul > app\api\admin\analytics.py

# 创建服务层
type nul > app\services\crawler_service.py

# 创建Schemas
type nul > app\schemas\admin.py
```

#### 1.2 定义数据模型（Pydantic Schemas）

**文件**：`backend/app/schemas/admin.py`

```python
"""后台管理API的Pydantic模型"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


# ========== 文章相关 ==========

class ArticleListQuery(BaseModel):
    """文章列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    category: Optional[str] = Field(None, description="分类筛选")
    content_source: Optional[str] = Field(None, description="内容来源: pharnexcloud/wechat")
    from_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    to_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")


class ArticleResponse(BaseModel):
    """文章响应"""
    id: int
    title: str
    summary: Optional[str]
    author: Optional[str]
    category: Optional[str]
    content_source: str
    published_at: datetime
    crawled_at: datetime
    has_wechat_content: bool  # 是否有微信内容

    class Config:
        from_attributes = True


class ArticleDetailResponse(ArticleResponse):
    """文章详情响应"""
    tags: Optional[List[str]]
    content_text: str
    content_url: str
    original_source_url: Optional[str]


class ArticleUpdateRequest(BaseModel):
    """文章更新请求"""
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


# ========== 爬虫相关 ==========

class CrawlerConfigRequest(BaseModel):
    """爬虫配置请求"""
    pages: int = Field(10, ge=1, le=100, description="爬取页数")
    max_articles: Optional[int] = Field(None, ge=1, le=1000, description="最大文章数")
    days_back: Optional[int] = Field(None, ge=1, le=365, description="最近N天")
    from_date: Optional[str] = Field(None, description="起始日期 YYYY-MM-DD")
    to_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    enable_wechat: bool = Field(True, description="是否启用微信爬取")


class CrawlerTaskResponse(BaseModel):
    """爬虫任务响应"""
    id: int
    config: dict
    status: str  # pending/running/completed/failed
    articles_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 统计分析相关 ==========

class AnalyticsOverview(BaseModel):
    """统计概览"""
    total_articles: int
    today_articles: int
    week_articles: int
    month_articles: int
    pharnex_count: int
    wechat_count: int
    wechat_ratio: float  # 微信转化率


class SourceDistribution(BaseModel):
    """来源分布"""
    name: str
    count: int
    percentage: float
```

**代码规范要点**：
- ✅ 使用 Pydantic Field 进行参数验证
- ✅ 中文注释说明每个字段
- ✅ 分类组织（文章、爬虫、统计）
- ✅ 简洁清晰，无冗余字段

#### 1.3 文章管理API实现

**文件**：`backend/app/api/admin/articles.py`

```python
"""文章管理API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List

from app.database import get_db
from app.models import Article
from app.schemas.admin import (
    ArticleListQuery,
    ArticleResponse,
    ArticleDetailResponse,
    ArticleUpdateRequest
)

router = APIRouter()


@router.get("/", response_model=dict)
async def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None),
    category: str = Query(None),
    content_source: str = Query(None),
    from_date: str = Query(None),
    to_date: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文章列表

    支持分页、搜索、筛选
    """
    # 构建基础查询
    query = select(Article).where(Article.is_deleted == False)

    # 关键词搜索（标题或摘要）
    if keyword:
        query = query.where(
            or_(
                Article.title.ilike(f"%{keyword}%"),
                Article.summary.ilike(f"%{keyword}%")
            )
        )

    # 分类筛选
    if category:
        query = query.where(Article.category == category)

    # 来源筛选
    if content_source:
        query = query.where(Article.content_source == content_source)

    # 时间范围筛选
    if from_date:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        query = query.where(Article.published_at >= from_dt)

    if to_date:
        to_dt = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.where(Article.published_at <= to_dt)

    # 按发布时间倒序
    query = query.order_by(Article.published_at.desc())

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # 执行查询
    result = await db.execute(query)
    articles = result.scalars().all()

    # 转换响应
    items = [
        {
            "id": a.id,
            "title": a.title,
            "summary": a.summary,
            "author": a.author,
            "category": a.category,
            "content_source": a.content_source,
            "published_at": a.published_at,
            "crawled_at": a.crawled_at,
            "has_wechat_content": bool(a.wechat_content_text)
        }
        for a in articles
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """获取文章详情"""
    result = await db.execute(
        select(Article).where(Article.id == article_id, Article.is_deleted == False)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    return article


@router.put("/{article_id}")
async def update_article(
    article_id: int,
    data: ArticleUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新文章"""
    result = await db.execute(
        select(Article).where(Article.id == article_id, Article.is_deleted == False)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 更新字段
    if data.title is not None:
        article.title = data.title
    if data.summary is not None:
        article.summary = data.summary
    if data.tags is not None:
        article.tags = data.tags

    await db.commit()
    await db.refresh(article)

    return {"message": "更新成功", "id": article.id}


@router.delete("/{article_id}")
async def delete_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """删除文章（逻辑删除）"""
    result = await db.execute(
        select(Article).where(Article.id == article_id, Article.is_deleted == False)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.is_deleted = True
    await db.commit()

    return {"message": "删除成功"}


@router.post("/batch-delete")
async def batch_delete_articles(
    article_ids: List[int],
    db: AsyncSession = Depends(get_db)
):
    """批量删除文章"""
    result = await db.execute(
        select(Article).where(
            Article.id.in_(article_ids),
            Article.is_deleted == False
        )
    )
    articles = result.scalars().all()

    for article in articles:
        article.is_deleted = True

    await db.commit()

    return {"message": f"成功删除 {len(articles)} 篇文章"}
```

**代码规范要点**：
- ✅ 路由职责单一（一个路由处理一个功能）
- ✅ 使用 Query 参数清晰定义参数类型
- ✅ 逻辑删除而非物理删除
- ✅ 详细的中文注释
- ✅ 统一的错误处理

#### 1.4 爬虫管理API实现

**文件**：`backend/app/services/crawler_service.py`

```python
"""爬虫服务"""

import asyncio
import subprocess
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CrawlerTask
from app.schemas.admin import CrawlerConfigRequest


class CrawlerService:
    """爬虫服务"""

    async def create_task(
        self,
        config: CrawlerConfigRequest,
        db: AsyncSession
    ) -> CrawlerTask:
        """创建爬虫任务"""
        task = CrawlerTask(
            config=config.model_dump(),
            status="pending"
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    async def run_crawler(
        self,
        task_id: int,
        config: CrawlerConfigRequest,
        db: AsyncSession
    ):
        """执行爬虫任务（后台运行）"""
        # 更新任务状态
        result = await db.execute(
            select(CrawlerTask).where(CrawlerTask.id == task_id)
        )
        task = result.scalar_one()
        task.status = "running"
        task.started_at = datetime.now()
        await db.commit()

        try:
            # 构建命令
            cmd = ["python", "scripts/crawl_and_ingest.py"]
            cmd.extend(["--pages", str(config.pages)])

            if config.max_articles:
                cmd.extend(["--max-articles", str(config.max_articles)])
            if config.days_back:
                cmd.extend(["--days-back", str(config.days_back)])
            if config.from_date:
                cmd.extend(["--from-date", config.from_date])
            if config.to_date:
                cmd.extend(["--to-date", config.to_date])

            # 执行命令
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd="C:/work/lianhuan/medical-news-mvp/backend"
            )

            # 解析结果
            if process.returncode == 0:
                # 成功
                task.status = "completed"
                # 从输出解析文章数量（简化版，实际可以更精确）
                task.articles_count = 0  # TODO: 从输出解析
            else:
                # 失败
                task.status = "failed"
                task.error_message = process.stderr

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)

        finally:
            task.completed_at = datetime.now()
            await db.commit()
```

**文件**：`backend/app/api/admin/crawler.py`

```python
"""爬虫管理API"""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CrawlerTask
from app.schemas.admin import CrawlerConfigRequest, CrawlerTaskResponse
from app.services.crawler_service import CrawlerService

router = APIRouter()


@router.post("/tasks", response_model=CrawlerTaskResponse)
async def create_crawler_task(
    config: CrawlerConfigRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """创建并启动爬虫任务"""
    service = CrawlerService()

    # 创建任务
    task = await service.create_task(config, db)

    # 后台执行
    background_tasks.add_task(
        service.run_crawler,
        task_id=task.id,
        config=config,
        db=db
    )

    return task


@router.get("/tasks", response_model=list[CrawlerTaskResponse])
async def get_crawler_tasks(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取爬虫任务列表"""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(CrawlerTask)
        .order_by(CrawlerTask.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    tasks = result.scalars().all()
    return tasks


@router.get("/tasks/{task_id}", response_model=CrawlerTaskResponse)
async def get_crawler_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务详情"""
    result = await db.execute(
        select(CrawlerTask).where(CrawlerTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task
```

**代码规范要点**：
- ✅ 服务层分离（crawler_service.py）
- ✅ 使用 BackgroundTasks 异步执行
- ✅ subprocess 调用现有脚本（复用逻辑）
- ✅ 简洁的API设计

#### 1.5 统计分析API实现

**文件**：`backend/app/api/admin/analytics.py`

```python
"""统计分析API"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Article
from app.schemas.admin import AnalyticsOverview

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """获取统计概览"""

    # 总文章数
    total_result = await db.execute(
        select(func.count(Article.id)).where(Article.is_deleted == False)
    )
    total_articles = total_result.scalar()

    # 今日新增
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.crawled_at >= today_start
        )
    )
    today_articles = today_result.scalar()

    # 本周新增
    week_start = today_start - timedelta(days=today_start.weekday())
    week_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.crawled_at >= week_start
        )
    )
    week_articles = week_result.scalar()

    # 本月新增
    month_start = today_start.replace(day=1)
    month_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.crawled_at >= month_start
        )
    )
    month_articles = month_result.scalar()

    # 药渡云数量
    pharnex_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.content_source == "pharnexcloud"
        )
    )
    pharnex_count = pharnex_result.scalar()

    # 微信数量
    wechat_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.content_source == "wechat"
        )
    )
    wechat_count = wechat_result.scalar()

    # 微信转化率
    wechat_ratio = (wechat_count / total_articles * 100) if total_articles > 0 else 0

    return AnalyticsOverview(
        total_articles=total_articles,
        today_articles=today_articles,
        week_articles=week_articles,
        month_articles=month_articles,
        pharnex_count=pharnex_count,
        wechat_count=wechat_count,
        wechat_ratio=round(wechat_ratio, 2)
    )
```

**代码规范要点**：
- ✅ 使用SQLAlchemy聚合函数
- ✅ 时间计算准确（今日0点、本周、本月）
- ✅ 返回结构化数据
- ✅ 计算转化率

#### 1.6 注册路由

**文件**：`backend/app/main.py`（修改）

```python
# 在现有路由下方添加

from app.api.admin import articles, crawler, analytics

# 后台管理路由
app.include_router(
    articles.router,
    prefix="/v1/admin/articles",
    tags=["Admin - Articles"]
)
app.include_router(
    crawler.router,
    prefix="/v1/admin/crawler",
    tags=["Admin - Crawler"]
)
app.include_router(
    analytics.router,
    prefix="/v1/admin/analytics",
    tags=["Admin - Analytics"]
)
```

---

### Day 4-7：前端项目搭建

#### 2.1 创建项目

```bash
cd C:\work\lianhuan\medical-news-mvp

# 创建Vue 3项目
npm create vite@latest admin-frontend -- --template vue-ts

cd admin-frontend

# 安装依赖
npm install element-plus
npm install @element-plus/icons-vue
npm install vue-router
npm install pinia
npm install axios
npm install dayjs
```

#### 2.2 配置Element Plus

**文件**：`admin-frontend/src/main.ts`

```typescript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, { locale: zhCn })
app.use(createPinia())
app.use(router)
app.mount('#app')
```

#### 2.3 配置路由

**文件**：`admin-frontend/src/router/index.ts`

```typescript
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/articles',
    name: 'Articles',
    component: () => import('../views/Articles/List.vue')
  },
  {
    path: '/articles/:id',
    name: 'ArticleDetail',
    component: () => import('../views/Articles/Detail.vue')
  },
  {
    path: '/crawler/config',
    name: 'CrawlerConfig',
    component: () => import('../views/Crawler/Config.vue')
  },
  {
    path: '/crawler/history',
    name: 'CrawlerHistory',
    component: () => import('../views/Crawler/History.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

#### 2.4 配置API客户端

**文件**：`admin-frontend/src/api/admin.ts`

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/v1/admin',
  timeout: 30000
})

// 文章API
export const articleApi = {
  getList: (params: any) => api.get('/articles', { params }),
  getDetail: (id: number) => api.get(`/articles/${id}`),
  update: (id: number, data: any) => api.put(`/articles/${id}`, data),
  delete: (id: number) => api.delete(`/articles/${id}`),
  batchDelete: (ids: number[]) => api.post('/articles/batch-delete', ids)
}

// 爬虫API
export const crawlerApi = {
  createTask: (config: any) => api.post('/crawler/tasks', config),
  getTasks: (params: any) => api.get('/crawler/tasks', { params }),
  getTask: (id: number) => api.get(`/crawler/tasks/${id}`)
}

// 统计API
export const analyticsApi = {
  getOverview: () => api.get('/analytics/overview')
}
```

#### 2.5 核心页面实现

**文件**：`admin-frontend/src/views/Dashboard.vue`

```vue
<template>
  <div class="dashboard">
    <h1>数据概览</h1>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_articles }}</div>
            <div class="stat-label">总文章数</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ stats.today_articles }}</div>
            <div class="stat-label">今日新增</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ stats.week_articles }}</div>
            <div class="stat-label">本周新增</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ stats.wechat_ratio }}%</div>
            <div class="stat-label">微信转化率</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { analyticsApi } from '@/api/admin'

const stats = ref({
  total_articles: 0,
  today_articles: 0,
  week_articles: 0,
  month_articles: 0,
  wechat_ratio: 0
})

const loadStats = async () => {
  const res = await analyticsApi.getOverview()
  stats.value = res.data
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  margin-top: 8px;
  color: #909399;
}
</style>
```

**文件**：`admin-frontend/src/views/Articles/List.vue`

```vue
<template>
  <div class="articles-list">
    <h1>文章管理</h1>

    <!-- 搜索筛选 -->
    <el-form :inline="true" :model="searchForm">
      <el-form-item label="关键词">
        <el-input v-model="searchForm.keyword" placeholder="搜索标题或摘要" clearable />
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="searchForm.category" placeholder="选择分类" clearable>
          <el-option label="前沿研究" value="前沿研究" />
        </el-select>
      </el-form-item>
      <el-form-item label="来源">
        <el-select v-model="searchForm.content_source" placeholder="选择来源" clearable>
          <el-option label="药渡云" value="pharnexcloud" />
          <el-option label="微信" value="wechat" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 文章表格 -->
    <el-table :data="articles" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="标题" min-width="300" />
      <el-table-column prop="author" label="作者" width="150" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="content_source" label="来源" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.content_source === 'wechat'" type="success">微信</el-tag>
          <el-tag v-else>药渡云</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="published_at" label="发布时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.published_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handleView(row.id)">查看</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.page_size"
      :total="pagination.total"
      @current-change="loadArticles"
      layout="total, prev, pager, next"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { articleApi } from '@/api/admin'
import dayjs from 'dayjs'

const router = useRouter()

const articles = ref([])
const loading = ref(false)

const searchForm = reactive({
  keyword: '',
  category: '',
  content_source: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const loadArticles = async () => {
  loading.value = true
  try {
    const res = await articleApi.getList({
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    })
    articles.value = res.data.items
    pagination.total = res.data.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadArticles()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.category = ''
  searchForm.content_source = ''
  handleSearch()
}

const handleView = (id: number) => {
  router.push(`/articles/${id}`)
}

const handleDelete = async (id: number) => {
  await ElMessageBox.confirm('确定删除这篇文章吗？', '提示', {
    type: 'warning'
  })

  await articleApi.delete(id)
  ElMessage.success('删除成功')
  loadArticles()
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  loadArticles()
})
</script>
```

**文件**：`admin-frontend/src/views/Crawler/Config.vue`

```vue
<template>
  <div class="crawler-config">
    <h1>爬虫配置</h1>

    <el-form :model="config" label-width="120px" style="max-width: 600px">
      <el-form-item label="页数限制">
        <el-input-number v-model="config.pages" :min="1" :max="100" />
      </el-form-item>

      <el-form-item label="文章数限制">
        <el-input-number v-model="config.max_articles" :min="1" :max="1000" placeholder="可选" />
      </el-form-item>

      <el-form-item label="时间范围">
        <el-radio-group v-model="timeType">
          <el-radio label="recent">最近N天</el-radio>
          <el-radio label="range">日期范围</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="最近天数" v-if="timeType === 'recent'">
        <el-input-number v-model="config.days_back" :min="1" :max="365" />
      </el-form-item>

      <el-form-item label="日期范围" v-if="timeType === 'range'">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="微信爬取">
        <el-switch v-model="config.enable_wechat" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="startCrawler" :loading="loading">
          开始爬取
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { crawlerApi } from '@/api/admin'
import dayjs from 'dayjs'

const router = useRouter()

const timeType = ref('recent')
const dateRange = ref([])
const loading = ref(false)

const config = ref({
  pages: 10,
  max_articles: null,
  days_back: 7,
  from_date: null,
  to_date: null,
  enable_wechat: true
})

watch(timeType, (val) => {
  if (val === 'recent') {
    config.value.from_date = null
    config.value.to_date = null
  } else {
    config.value.days_back = null
  }
})

watch(dateRange, (val) => {
  if (val && val.length === 2) {
    config.value.from_date = dayjs(val[0]).format('YYYY-MM-DD')
    config.value.to_date = dayjs(val[1]).format('YYYY-MM-DD')
  }
})

const startCrawler = async () => {
  loading.value = true
  try {
    const res = await crawlerApi.createTask(config.value)
    ElMessage.success(`任务已创建，ID: ${res.data.id}`)
    router.push('/crawler/history')
  } finally {
    loading.value = false
  }
}
</script>
```

---

### Day 8-10：集成测试与优化

#### 3.1 测试清单

```bash
# 后端测试
cd C:\work\lianhuan\medical-news-mvp\backend

# 1. 运行数据库迁移
python scripts/migrate_add_crawler_tasks.py

# 2. 启动后端
uvicorn app.main:app --reload

# 3. 测试API
# 访问 http://localhost:8000/docs
# 测试各个API端点

# 前端测试
cd C:\work\lianhuan\medical-news-mvp\admin-frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev

# 3. 访问 http://localhost:5173
# 测试各个页面功能
```

#### 3.2 Vite配置（解决跨域）

**文件**：`admin-frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    proxy: {
      '/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

---

## 📊 开发进度跟踪表

| 阶段 | 任务 | 预计时间 | 状态 |
|------|------|---------|------|
| Day 1-3 | 后端API开发 | 3天 | ⏳ 待开始 |
| Day 4-7 | 前端页面开发 | 4天 | ⏳ 待开始 |
| Day 8-10 | 集成测试优化 | 3天 | ⏳ 待开始 |

---

## ✅ 代码规范检查清单

每次提交前检查：

- [ ] 所有注释使用中文
- [ ] 函数职责单一
- [ ] 无冗余代码
- [ ] 变量命名清晰
- [ ] 错误处理完善
- [ ] 类型声明准确（TypeScript）
- [ ] API响应格式统一

---

## 📝 总结

本文档提供了后台管理系统的详细实施指南，包括：

1. ✅ 完整的代码示例（可直接复制使用）
2. ✅ 详细的步骤说明
3. ✅ 代码规范要点
4. ✅ 测试清单

**预计完成时间**：10个工作日

**下一步行动**：按照 Day 1-3 开始后端API开发

---

**文档版本**：v2.0（详细实施版）
**最后更新**：2025-10-30
**维护者**：Medical News MVP Team
