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

        <!-- AI分析部分 -->
        <el-divider content-position="left">AI智能分析</el-divider>
        <div class="ai-analysis-section">
          <div v-if="!aiAnalysis && !aiLoading" class="no-ai-analysis">
            <el-empty description="暂无AI分析" />
            <el-button
              type="primary"
              :loading="aiLoading"
              @click="handleGenerateAI"
            >
              生成AI分析
            </el-button>
          </div>

          <el-skeleton v-if="aiLoading" :rows="5" animated />

          <div v-if="aiAnalysis && !aiLoading" class="ai-result">
            <div class="ai-analysis-content">
              <p>{{ aiAnalysis.analysis }}</p>
            </div>

            <el-button
              type="primary"
              :loading="aiLoading"
              @click="handleGenerateAI"
              style="margin-top: 16px"
            >
              重新生成
            </el-button>
          </div>
        </div>

        <!-- AI翻译部分 -->
        <el-divider content-position="left">AI智能翻译</el-divider>
        <div class="translation-section">
          <div v-if="!translation && !translationLoading" class="no-translation">
            <el-empty description="暂无翻译内容" />
            <el-button
              type="success"
              :loading="translationLoading"
              @click="handleGenerateTranslation"
            >
              生成翻译
            </el-button>
          </div>

          <el-skeleton v-if="translationLoading" :rows="5" animated />

          <div v-if="translation && !translationLoading" class="translation-result">
            <div v-if="translation.is_chinese" class="chinese-notice">
              <el-alert
                title="检测到中文文章"
                description="该文章为中文内容，无需翻译"
                type="info"
                show-icon
                :closable="false"
              />
            </div>

            <div v-else class="translation-content">
              <h4>HTML翻译内容：</h4>
              <div class="translated-html">
                <div v-if="translation.translated_content_html" class="translated-html-preview">
                  <el-row :gutter="16">
                    <el-col :span="12">
                      <el-button type="primary" size="small" @click="showTranslationPreview = true">
                        预览翻译结果
                      </el-button>
                      <small style="margin-left: 10px;">
                        已翻译（{{ translation.translated_content_html.length }} 字符）
                      </small>
                    </el-col>
                    <el-col :span="12">
                      <el-button
                        type="info"
                        size="small"
                        @click="copyTranslationToClipboard"
                        style="float: right;"
                      >
                        复制HTML内容
                      </el-button>
                    </el-col>
                  </el-row>
                </div>
                <div v-else>
                  <el-alert
                    title="翻译内容为空"
                    description="翻译结果为空，请重新生成翻译"
                    type="warning"
                    show-icon
                    :closable="false"
                  />
                </div>
              </div>
            </div>

            <el-button
              type="success"
              :loading="translationLoading"
              @click="handleGenerateTranslation"
              style="margin-top: 16px"
            >
              重新翻译
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 翻译预览对话框 -->
    <el-dialog
      v-model="showTranslationPreview"
      title="翻译预览"
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="translation-preview">
        <div v-if="translation?.translated_content_html" class="preview-content">
          <div class="preview-header">
            <el-button type="info" size="small" @click="copyTranslationToClipboard">
              复制HTML代码
            </el-button>
          </div>
          <div class="preview-html" v-html="translation.translated_content_html"></div>
        </div>
        <div v-else class="no-translation">
          <el-empty description="暂无翻译内容" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Delete } from '@element-plus/icons-vue'
import {
  getArticles,
  deleteArticle,
  batchDeleteArticles,
  generateAIAnalysis,
  generateTranslation,
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

// AI分析相关
const aiAnalysis = ref<any>(null)
const aiLoading = ref(false)

// 翻译相关
const translation = ref<any>(null)
const translationLoading = ref(false)
const showTranslationPreview = ref(false)

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
const handleView = async (article: Article) => {
  currentArticle.value = article
  dialogVisible.value = true

  // 自动加载AI分析（如果已有则直接返回，不会重新生成）
  if (article.id) {
    aiLoading.value = true
    try {
      const response = await generateAIAnalysis(article.id, false)
      // response.data 是后端返回的完整对象: { success, message, data: { analysis } }
      // 我们需要提取 response.data.data
      if (response.data && response.data.data) {
        aiAnalysis.value = response.data.data
      }
    } catch (error: any) {
      console.error('加载AI分析失败:', error)
      // 如果是404或其他错误，说明还没有AI分析，不显示错误
      aiAnalysis.value = null
    } finally {
      aiLoading.value = false
    }
  }
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

// 生成AI分析
const handleGenerateAI = async () => {
  if (!currentArticle.value) return

  // 如果已有分析，则是重新生成，需要传递force_regenerate=true
  const isRegenerate = !!aiAnalysis.value

  aiLoading.value = true
  try {
    const response = await generateAIAnalysis(currentArticle.value.id, isRegenerate)
    // response.data 是后端返回的完整对象: { success, message, data: { analysis } }
    // 我们需要提取 response.data.data
    aiAnalysis.value = response.data.data
    ElMessage.success(isRegenerate ? 'AI分析重新生成成功' : 'AI分析生成成功')
  } catch (error: any) {
    console.error('AI分析失败:', error)
    ElMessage.error(error.response?.data?.detail || 'AI分析失败，请检查DeepSeek API配置')
  } finally {
    aiLoading.value = false
  }
}

// 生成翻译
const handleGenerateTranslation = async () => {
  if (!currentArticle.value) return

  // 如果已有翻译，则是重新翻译，需要传递force_regenerate=true
  const isRegenerate = !!translation.value

  translationLoading.value = true
  try {
    const response = await generateTranslation(currentArticle.value.id, isRegenerate)
    // response 是后端返回的完整对象: { success, message, data: { ... } }
    translation.value = response.data
    ElMessage.success(isRegenerate ? '翻译重新生成成功' : '翻译生成成功')
  } catch (error: any) {
    console.error('翻译失败:', error)
    ElMessage.error(error.response?.data?.detail || '翻译失败，请检查DeepSeek API配置')
  } finally {
    translationLoading.value = false
  }
}

// 复制翻译内容到剪贴板
const copyTranslationToClipboard = async () => {
  if (!translation.value?.translated_content_html) {
    ElMessage.warning('没有翻译内容可复制')
    return
  }

  try {
    await navigator.clipboard.writeText(translation.value.translated_content_html)
    ElMessage.success('翻译内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 监听对话框关闭，清空AI分析和翻译数据
watch(dialogVisible, (newVal) => {
  if (!newVal) {
    aiAnalysis.value = null
    translation.value = null
  }
})

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

/* AI分析部分样式 */
.ai-analysis-section {
  margin-top: 24px;
}

.no-ai-analysis {
  text-align: center;
  padding: 20px 0;
}

.ai-result {
  padding: 16px 0;
}

.ai-analysis-content {
  background-color: #f5f7fa;
  border-left: 4px solid #409eff;
  padding: 20px;
  border-radius: 4px;
}

.ai-analysis-content p {
  margin: 0;
  line-height: 1.8;
  font-size: 15px;
  color: #303133;
  white-space: pre-wrap;
}

/* AI翻译部分样式 */
.translation-section {
  margin-top: 24px;
}

.no-translation {
  text-align: center;
  padding: 20px 0;
}

.translation-result {
  padding: 16px 0;
}

.chinese-notice {
  margin-bottom: 16px;
}

.translation-content {
  background-color: #f0f9ff;
  border-left: 4px solid #67c23a;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 16px;
}

.translation-content h4 {
  margin: 0 0 12px 0;
  color: #409eff;
  font-size: 16px;
}

.translated-text p {
  margin: 0;
  line-height: 1.8;
  font-size: 15px;
  color: #303133;
  white-space: pre-wrap;
}

.translated-html-preview {
  margin-top: 12px;
  padding: 8px 12px;
  background-color: #e1f3d8;
  border-radius: 4px;
  color: #67c23a;
}

.key-points-list li {
  margin-bottom: 8px;
  color: #606266;
}

.entities {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.entity-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.entity-list {
  color: #606266;
  flex: 1;
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
