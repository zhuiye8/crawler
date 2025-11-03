<template>
  <div class="articles">
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索标题、摘要、作者"
            clearable
            style="width: 240px"
          />
        </el-form-item>

        <el-form-item label="内容来源">
          <el-select
            v-model="searchForm.content_source"
            placeholder="全部来源"
            clearable
            style="width: 150px"
          >
            <el-option label="药渡云" value="pharnexcloud" />
            <el-option label="微信公众号" value="wechat" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch" :icon="Search">
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 文章列表 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>文章列表</span>
          <div>
            <el-button
              type="danger"
              :disabled="selectedIds.length === 0"
              @click="handleBatchDelete"
              :icon="Delete"
            >
              批量删除 ({{ selectedIds.length }})
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="articles"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="id" label="ID" width="80" />

        <el-table-column prop="title" label="标题" min-width="300">
          <template #default="{ row }">
            <div class="title-cell">
              {{ row.title }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="author" label="作者" width="150" />

        <el-table-column prop="content_source" label="来源" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.content_source === 'wechat'" type="success">
              微信
            </el-tag>
            <el-tag v-else type="info">药渡云</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="published_at" label="发布时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.published_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="handleView(row)"
            >
              查看
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadArticles"
          @current-change="loadArticles"
        />
      </div>
    </el-card>

    <!-- 文章详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentArticle?.title"
      width="70%"
    >
      <div v-if="currentArticle" class="article-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">
            {{ currentArticle.id }}
          </el-descriptions-item>
          <el-descriptions-item label="作者">
            {{ currentArticle.author || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="发布时间">
            {{ formatDate(currentArticle.published_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="来源">
            <el-tag v-if="currentArticle.content_source === 'wechat'" type="success">
              微信公众号
            </el-tag>
            <el-tag v-else type="info">药渡云</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="摘要" :span="2">
            {{ currentArticle.summary || '无' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Delete } from '@element-plus/icons-vue'
import {
  getArticles,
  deleteArticle,
  batchDeleteArticles,
  type Article
} from '../api/admin'

// 搜索表单
const searchForm = reactive({
  keyword: '',
  content_source: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 数据
const loading = ref(false)
const articles = ref<Article[]>([])
const selectedIds = ref<number[]>([])

// 对话框
const dialogVisible = ref(false)
const currentArticle = ref<Article | null>(null)

// 加载文章列表
const loadArticles = async () => {
  loading.value = true
  try {
    const response = await getArticles({
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchForm.keyword || undefined,
      content_source: searchForm.content_source || undefined
    })

    articles.value = response.items
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载文章列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadArticles()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.content_source = ''
  pagination.page = 1
  loadArticles()
}

// 选择变化
const handleSelectionChange = (selection: Article[]) => {
  selectedIds.value = selection.map(item => item.id)
}

// 查看详情
const handleView = (article: Article) => {
  currentArticle.value = article
  dialogVisible.value = true
}

// 删除文章
const handleDelete = async (article: Article) => {
  try {
    await ElMessageBox.confirm(
      `确定删除文章 "${article.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteArticle(article.id)
    ElMessage.success('删除成功')
    loadArticles()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedIds.value.length} 篇文章吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await batchDeleteArticles(selectedIds.value)
    ElMessage.success('批量删除成功')
    loadArticles()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadArticles()
})
</script>

<style scoped>
.articles {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.search-card {
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.table-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #303133;
}

.title-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.6;
  max-height: 3.2em;
}

.pagination {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
}

.article-detail {
  padding: 20px 0;
}

/* 表格样式优化 */
:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #fafafa !important;
  color: #606266;
  font-weight: 600;
}

:deep(.el-table td) {
  padding: 14px 0;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>
