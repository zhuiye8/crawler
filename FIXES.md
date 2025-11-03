# 问题修复记录

## 修复/功能开发时间
- 第一轮: 2025-10-29 17:35 (初始bug修复)
- 第二轮: 2025-10-30 09:15 (数据库与Docker配置)
- 第三轮: 2025-10-30 10:30 (asyncpg多命令修复)
- 第四轮: 2025-10-30 11:00 (爬虫选择器修复)
- 第五轮: 2025-10-30 15:00 (微信公众号爬取功能开发) ⭐ 重大功能
- 第六轮: 2025-10-30 16:30 (Patchright迁移 - 绕过CDP检测) ⭐ 重要优化

## 修复的问题

### 1. SQLAlchemy保留字段名冲突 ✅

**问题**:
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

**原因**: `ArticleChunk`模型中使用了`metadata`作为字段名，这是SQLAlchemy的保留字

**修复**:
- `backend/app/models.py` 第71行: `metadata` → `chunk_metadata`
- `backend/scripts/analyze_and_embed.py` 第108行: `metadata=` → `chunk_metadata=`

### 2. Docker Compose版本字段过时 ✅

**问题**: `version: '3.8'` 在新版Docker Compose中已废弃

**修复**:
- `docker-compose.yml`: 移除第1行的 `version: '3.8'`

### 3. README环境配置 ✅

**问题**: README中使用venv虚拟环境，但用户使用conda环境lh

**修复**:
- `README.md` 第54-64行: 将venv创建和激活步骤改为 `conda activate lh`

### 4. pgvector扩展安装顺序 ✅

**问题**:
```
asyncpg.exceptions.UndefinedObjectError: type "vector" does not exist
```

**原因**: 在创建使用`VECTOR`类型的表之前，没有先安装`pgvector`扩展

**修复**:
- `backend/scripts/init_db.py`: 调整执行顺序
  1. 先执行 `CREATE EXTENSION IF NOT EXISTS vector;`
  2. 再执行 `Base.metadata.create_all()` 创建表
  3. 最后创建额外的索引和插入初始数据

### 5. asyncpg多命令prepared statement错误 ✅

**问题**:
```
asyncpg.exceptions.PostgresSyntaxError: cannot insert multiple commands into a prepared statement
```

**原因**: `SQL_INIT`字符串包含多条SQL语句(多个CREATE INDEX和INSERT)，asyncpg不允许在一个prepared statement中执行多条命令

**修复**:
- `backend/scripts/init_db.py` 第15-27行: 将`SQL_INIT`字符串改为`SQL_STATEMENTS`列表
- `backend/scripts/init_db.py` 第46-48行: 使用循环逐条执行每个SQL语句
  ```python
  for sql_statement in SQL_STATEMENTS:
      await conn.execute(text(sql_statement))
  ```

### 6. 爬虫CSS选择器错误导致抓不到文章 ✅

**问题**: 爬虫运行10页都是`Found 0 articles`，没有抓取到任何文章

**原因**: 爬虫使用的CSS选择器（`.article-item`, `.news-item`, `article`）是通用猜测，不匹配药渡云网站的实际HTML结构

**修复**:
- `backend/crawler/pharnex_crawler.py` 第52行: 改用正确的选择器 `li.report-item`
- `backend/crawler/pharnex_crawler.py` 第72-148行: 重写 `_parse_article_item` 方法，使用实际HTML结构:
  - 标题: `.report-detail .title a`
  - 链接: `a[href]`
  - 摘要: `.report-detail .desc`
  - 作者: 第一个 `.info .info-item`
  - 日期: 第二个 `.info .info-item`
  - 分类: `.img .tag`
  - 标签: 第三个 `.info .info-item span`

### 7. 微信公众号爬取功能开发 ⭐

**功能说明**: 集成微信公众号文章完整内容爬取

**⚠️  法律风险声明**:
- 此功能仅供个人学习研究使用
- 商业使用可能违反微信公众平台服务协议和《反不正当竞争法》
- 使用前需确保已获得内容所有者授权
- 开发者不承担任何法律责任

**实现内容**:

1. **数据库Schema更新** (`backend/app/models.py`)
   - 添加 `original_source_url` 字段：存储微信原文链接
   - 添加 `wechat_content_html` 字段：存储微信文章HTML内容
   - 添加 `wechat_content_text` 字段：存储微信文章纯文本
   - 添加 `content_source` 字段：标记内容来源 (pharnexcloud/wechat)

2. **微信爬虫模块** (`backend/crawler/wechat_crawler.py`)
   - 实现 `WechatArticleCrawler` 类
   - 支持微信公众号文章爬取
   - 包含反爬策略：延迟控制、随机UA、重试机制
   - 支持缓存机制避免重复爬取
   - 所有注释使用中文

3. **药渡云爬虫更新** (`backend/crawler/pharnex_crawler.py`)
   - 修改 `crawl_detail_page` 返回值：`(content_html, content_text, original_source_url)`
   - 添加 `_extract_wechat_url` 方法：从详情页提取微信原文链接
   - 支持多种链接提取策略

4. **数据摄取流程更新** (`backend/scripts/crawl_and_ingest.py`)
   - 集成微信爬虫到主流程
   - 添加配置开关：`ENABLE_WECHAT_CRAWL`
   - 降级策略：微信爬取失败时使用药渡云内容
   - 智能选择：如果微信内容更完整，优先使用微信版本

5. **数据库迁移脚本** (`backend/scripts/migrate_add_wechat_fields.py`)
   - 添加新字段的SQL迁移
   - 支持回滚操作

6. **测试脚本** (`backend/scripts/test_wechat_single.py`)
   - 完整流程测试：药渡云 + 微信
   - 独立微信爬取测试
   - 内容对比分析

**使用方法**:

```bash
# 1. 运行数据库迁移
cd backend
python scripts/migrate_add_wechat_fields.py

# 2. 测试单篇文章（推荐先测试）
python scripts/test_wechat_single.py

# 3. 运行完整爬取（启用微信爬取）
python scripts/crawl_and_ingest.py
```

**配置选项** (`crawl_and_ingest.py`):

```python
ENABLE_WECHAT_CRAWL = True   # 启用/禁用微信爬取
WECHAT_CRAWL_DELAY = 10      # 微信爬取间隔（秒）
```

**技术特性**:
- ✅ 反爬策略：随机UA、延迟控制、重试机制
- ✅ 缓存机制：避免重复爬取同一文章
- ✅ 降级策略：爬取失败时使用备用内容
- ✅ 智能选择：自动选择更完整的内容版本
- ✅ 完整性检查：验证爬取内容的完整性

**注意事项**:
1. ⚠️  **法律风险**：请确保合法合规使用
2. ⚠️  **频率限制**：建议延迟10秒以上避免被封
3. ⚠️  **降级处理**：爬取失败会自动降级到药渡云内容
4. ⚠️  **缓存清理**：缓存文件保存在 `backend/cache/wechat_articles/`

### 8. Patchright迁移 - 绕过CDP检测 ⭐

**优化说明**: 从Playwright迁移到Patchright，绕过Chrome DevTools Protocol反爬检测

**问题背景**:
- Playwright使用CDP（Chrome DevTools Protocol）控制浏览器
- 现代反爬系统可以检测CDP的存在（微信公众号、药渡云等）
- 被检测后可能触发验证码、限流或IP封禁

**调研结论**:
- ❌ Chrome DevTools MCP 同样使用CDP，无反爬优势
- ✅ Patchright 是Playwright的修补版本，专门解决CDP检测
- ✅ API 100%兼容，代码几乎零改动

**修改内容**:

1. **爬虫模块**
   - `backend/crawler/wechat_crawler.py` 第21行：导入语句改为 `from patchright.async_api`
   - `backend/crawler/pharnex_crawler.py` 第5行：导入语句改为 `from patchright.async_api`

2. **测试脚本**
   - `backend/scripts/test_single_article.py` 第37行：导入语句改为 `from patchright.async_api`
   - `backend/scripts/debug_crawler.py` 第4行：导入语句改为 `from patchright.async_api`

3. **依赖声明**
   - `backend/requirements.txt` 第26行：`playwright==1.41.0` → `patchright==1.45.1`

**安装步骤**:

```bash
# 1. 卸载旧依赖（可选）
pip uninstall playwright -y

# 2. 安装 Patchright
pip install patchright==1.45.1

# 3. 安装浏览器驱动
patchright install chromium
```

**验证测试**:

```bash
# 测试导入
python -c "from patchright.async_api import async_playwright; print('✅ Success')"

# 测试爬虫
cd backend
python scripts/test_wechat_single.py
```

**技术优势**:
- ✅ 绕过CDP检测机制
- ✅ 修复浏览器指纹泄露
- ✅ API完全兼容Playwright
- ✅ 社区活跃维护

**预期收益**:
- 降低被检测和封禁风险
- 提高爬取成功率
- 减少验证码触发
- 无需改变代码逻辑

**回滚方案**:
如果遇到问题可以快速回滚：
```bash
pip uninstall patchright -y
pip install playwright==1.41.0
# 恢复所有导入语句为 from playwright.async_api
```

**相关文档**:
- 详细迁移指南：`backend/PATCHRIGHT_MIGRATION.md`
- Patchright官方：https://github.com/Kaliiiiiiiiii-Vinyzu/patchright

---

## 修复后的启动步骤

```bash
# 1. 激活conda环境
conda activate lh

# 2. 安装依赖
cd C:\work\lianhuan\medical-news-mvp\backend
pip install -r requirements.txt
playwright install chromium

# 3. 启动Docker服务
cd ..
docker-compose up -d

# 4. 配置环境变量
cd backend
cp .env.example .env
# 编辑 .env 文件，填入 OPENAI_API_KEY

# 5. 初始化数据库
python scripts/init_db.py

# 6. 爬取数据
python scripts/crawl_and_ingest.py

# 7. AI分析与向量化
python scripts/analyze_and_embed.py

# 8. 启动API服务
uvicorn app.main:app --reload
```

---

## 验证

运行以下命令验证修复：

```bash
# 验证数据库初始化
python scripts/init_db.py

# 应该看到：
# 🚀 Initializing database...
# 🔧 Installing pgvector extension...
# 📋 Creating tables...
# 🔧 Creating additional indexes...
# ✅ Database initialization completed!
```

---

## 注意事项

1. **确保conda环境lh已创建**: 如果没有，先运行 `conda create -n lh python=3.10`
2. **确保Docker服务运行**: `docker ps` 应该看到3个容器
3. **确保OpenAI API Key有效**: 测试前检查余额和网络连接

---

所有问题已修复，可以继续开发！✅
