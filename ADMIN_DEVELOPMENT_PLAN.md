# 后台管理系统开发规划

> 医药资讯 MVP - 后台管理系统完整开发计划

## 📅 更新时间
2025-10-30

---

## 🎯 项目目标

开发一个功能完整的后台管理系统，用于：
1. 可视化管理爬取的文章数据
2. 配置和监控爬虫任务
3. 统计分析数据趋势

---

## ✅ 已完成的工作

### 1. 爬虫优化（2025-10-30）

✅ **PharnexCrawler 优化**
- 支持时间筛选（from_date, to_date）
- 支持数量控制（max_articles）
- 早停机制（连续3页无数据自动停止）

✅ **crawl_and_ingest.py 参数化**
- 支持命令行参数
- 支持 `--pages`, `--max-articles`, `--days-back` 等

✅ **数据库模型**
- 创建 `CrawlerTask` 模型
- 创建迁移脚本 `migrate_add_crawler_tasks.py`

**使用示例**：
```bash
# 只爬最近7天
python scripts/crawl_and_ingest.py --days-back 7

# 只爬50篇文章
python scripts/crawl_and_ingest.py --max-articles 50

# 组合使用
python scripts/crawl_and_ingest.py --days-back 30 --max-articles 100
```

---

## 🚀 后续开发计划

### 第一阶段：后台核心功能（2周）

#### Week 1：后端 API 开发

**1.1 文章管理 API**
```
POST   /v1/admin/articles          # 手动创建文章（可选）
GET    /v1/admin/articles          # 文章列表（分页、搜索、筛选）
GET    /v1/admin/articles/{id}     # 文章详情
PUT    /v1/admin/articles/{id}     # 编辑文章
DELETE /v1/admin/articles/{id}     # 删除文章（逻辑删除）
DELETE /v1/admin/articles/batch    # 批量删除
```

**1.2 爬虫管理 API**
```
POST   /v1/admin/crawler/tasks     # 创建爬虫任务
GET    /v1/admin/crawler/tasks     # 任务列表
GET    /v1/admin/crawler/tasks/{id} # 任务详情
GET    /v1/admin/crawler/status    # 当前任务状态
POST   /v1/admin/crawler/cancel/{id} # 取消任务
```

**1.3 统计分析 API**
```
GET    /v1/admin/analytics/overview    # 仪表盘总览
GET    /v1/admin/analytics/articles    # 文章统计
GET    /v1/admin/analytics/sources     # 来源分布
GET    /v1/admin/analytics/trends      # 时间趋势
```

**预计时间**：4-5天

#### Week 2：前端页面开发

**2.1 项目初始化**
- 技术栈：Vue 3 + Element Plus + TypeScript + Vite
- 目录：`admin-frontend/`
- 路由：Vue Router 4
- 状态管理：Pinia 2

**2.2 核心页面**
```
/admin/dashboard          # 仪表盘
/admin/articles           # 文章列表
/admin/articles/:id       # 文章详情
/admin/crawler/config     # 爬虫配置
/admin/crawler/monitor    # 任务监控
/admin/crawler/history    # 任务历史
```

**2.3 关键组件**
- ArticleTable（文章表格）
- CrawlerConfigForm（爬虫配置表单）
- TaskMonitor（任务监控面板）
- StatsCard（统计卡片）

**预计时间**：5-6天

---

### 第二阶段：增强功能（1周）

#### 3.1 实时监控（2-3天）
- WebSocket 集成
- 实时日志输出
- 进度条显示

#### 3.2 统计图表（2天）
- ECharts 集成
- 文章趋势图
- 来源分布饼图

#### 3.3 用户体验优化（1-2天）
- 加载状态优化
- 错误提示优化
- 移动端适配

---

### 第三阶段：高级功能（按需）

#### 4.1 定时任务（3天）
- Celery Beat 集成
- 定时爬取配置
- 任务调度管理

#### 4.2 权限管理（3-4天）
- 用户登录
- 角色权限
- 操作日志

#### 4.3 数据导入导出（2天）
- 文章导出（CSV/Excel）
- 数据备份

---

## 📂 项目结构规划

```
medical-news-mvp/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── admin/              # 新增：后台管理 API
│   │   │       ├── __init__.py
│   │   │       ├── articles.py     # 文章管理
│   │   │       ├── crawler.py      # 爬虫管理
│   │   │       └── analytics.py    # 统计分析
│   │   ├── services/
│   │   │   └── crawler_service.py  # 新增：爬虫服务
│   │   └── models.py               # 已添加：CrawlerTask
│   └── scripts/
│       ├── crawl_and_ingest.py     # 已优化：支持参数
│       └── migrate_add_crawler_tasks.py  # 已创建：迁移脚本
│
├── admin-frontend/                  # 新增：后台前端项目
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue       # 仪表盘
│   │   │   ├── Articles/
│   │   │   │   ├── List.vue        # 文章列表
│   │   │   │   └── Detail.vue      # 文章详情
│   │   │   └── Crawler/
│   │   │       ├── Config.vue      # 爬虫配置
│   │   │       ├── Monitor.vue     # 实时监控
│   │   │       └── History.vue     # 任务历史
│   │   ├── components/
│   │   │   ├── ArticleTable.vue
│   │   │   ├── CrawlerForm.vue
│   │   │   └── StatsCard.vue
│   │   ├── api/
│   │   │   └── admin.ts            # API 客户端
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── stores/
│   │   │   └── crawler.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── vite.config.ts
│   ├── package.json
│   └── tsconfig.json
│
└── ADMIN_DEVELOPMENT_PLAN.md       # 本文档
```

---

## 🛠️ 技术栈

### 后端
- FastAPI 0.109（已有）
- SQLAlchemy 2.0（已有）
- PostgreSQL + pgvector（已有）
- WebSocket（用于实时推送）

### 前端
- Vue 3.4
- Element Plus 2.5（UI 组件库）
- TypeScript 5
- Vite 5（构建工具）
- Vue Router 4（路由）
- Pinia 2（状态管理）
- ECharts 5（图表）
- Axios（HTTP 客户端）

---

## ⏱️ 时间估算

| 阶段 | 内容 | 时间 |
|------|------|------|
| 第一阶段 | 后端 API + 前端核心页面 | 2周 |
| 第二阶段 | 实时监控 + 统计图表 | 1周 |
| 第三阶段 | 高级功能（按需） | 1-2周 |
| **总计** | | **3-5周** |

**注**：
- 单人开发：4-5周
- 双人协作：2-3周

---

## 💰 成本估算

- **人力成本**：1名全栈工程师 × 4周 = 4人周
- **云服务**：无额外成本（复用现有 Docker 环境）
- **第三方服务**：无（Element Plus 开源免费）

---

## 📝 开发规范

### 代码规范
1. ✅ 所有注释使用中文
2. ✅ 保持代码简洁高效
3. ✅ 遵循 RESTful API 设计
4. ✅ 前后端分离
5. ✅ TypeScript 严格模式

### Git 规范
- 分支命名：`feature/admin-articles`, `feature/admin-crawler`
- Commit 规范：`feat: 添加文章列表页面`, `fix: 修复爬虫超时问题`

---

## 🚦 下一步行动

### 立即可做（用户）
1. 测试爬虫优化功能
   ```bash
   python scripts/crawl_and_ingest.py --days-back 7 --max-articles 50
   ```

2. 运行数据库迁移
   ```bash
   python scripts/migrate_add_crawler_tasks.py
   ```

### 开始开发（开发者）
1. 创建 admin-frontend 项目
   ```bash
   cd medical-news-mvp
   npm create vite@latest admin-frontend -- --template vue-ts
   cd admin-frontend
   npm install element-plus vue-router pinia axios echarts
   ```

2. 创建后端 API 路由结构
   ```bash
   mkdir -p backend/app/api/admin
   touch backend/app/api/admin/__init__.py
   touch backend/app/api/admin/articles.py
   touch backend/app/api/admin/crawler.py
   touch backend/app/api/admin/analytics.py
   ```

3. 开始第一阶段开发

---

## ❓ FAQ

**Q: 为什么选择 Element Plus 而不是 Ant Design Vue？**
A: Element Plus 更轻量，Vue 3 原生支持好，中文文档完善，生态成熟。

**Q: 是否需要用户认证？**
A: 第一阶段不做认证，第三阶段按需添加。

**Q: 是否需要单独部署后台前端？**
A: 开发阶段可以 `npm run dev`，生产环境建议 `npm run build` 后用 Nginx 部署。

**Q: 实时监控如何实现？**
A: 使用 WebSocket 推送日志和进度，前端 Vue 组件订阅更新。

---

## 📚 参考资源

- Vue 3 文档：https://vuejs.org/
- Element Plus 文档：https://element-plus.org/
- FastAPI 文档：https://fastapi.tiangolo.com/
- ECharts 文档：https://echarts.apache.org/

---

**文档版本**：v1.0
**最后更新**：2025-10-30
**维护者**：Medical News MVP Team
