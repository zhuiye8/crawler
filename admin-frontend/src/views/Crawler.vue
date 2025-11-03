<template>
  <div class="crawler">
    <!-- 爬虫配置 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>爬虫配置</span>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="crawlerForm"
            :rules="rules"
            label-width="120px"
          >
            <el-form-item label="数据源" prop="source">
              <el-select
                v-model="crawlerForm.source"
                placeholder="选择数据源"
                :disabled="crawlerStore.status.is_running"
                style="width: 100%"
              >
                <el-option
                  v-for="source in availableSources"
                  :key="source.key"
                  :label="source.name"
                  :value="source.key"
                >
                  <span>{{ source.name }}</span>
                  <span v-if="source.supports_wechat" style="color: #67c23a; margin-left: 8px; font-size: 12px">
                    (支持微信原文)
                  </span>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="爬取页数" prop="pages">
              <el-input-number
                v-model="crawlerForm.pages"
                :min="1"
                :max="100"
                :disabled="crawlerStore.status.is_running"
              />
              <span class="form-tip">每页约 10 篇文章</span>
            </el-form-item>

            <el-form-item label="最大文章数">
              <el-input-number
                v-model="crawlerForm.max_articles"
                :min="1"
                :max="1000"
                :disabled="crawlerStore.status.is_running"
              />
              <span class="form-tip">可选，限制爬取数量</span>
            </el-form-item>

            <el-form-item label="时间范围">
              <el-radio-group
                v-model="timeRangeType"
                :disabled="crawlerStore.status.is_running"
                @change="handleTimeRangeChange"
              >
                <el-radio :label="1">最近N天</el-radio>
                <el-radio :label="2">日期范围</el-radio>
                <el-radio :label="0">不限</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item v-if="timeRangeType === 1" label="最近天数">
              <el-input-number
                v-model="crawlerForm.days_back"
                :min="1"
                :max="365"
                :disabled="crawlerStore.status.is_running"
              />
            </el-form-item>

            <el-form-item v-if="timeRangeType === 2" label="开始日期">
              <el-date-picker
                v-model="crawlerForm.from_date"
                type="date"
                placeholder="选择日期"
                :disabled="crawlerStore.status.is_running"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>

            <el-form-item v-if="timeRangeType === 2" label="结束日期">
              <el-date-picker
                v-model="crawlerForm.to_date"
                type="date"
                placeholder="选择日期"
                :disabled="crawlerStore.status.is_running"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="handleStartCrawl"
                :loading="crawlerStore.status.is_running"
                :icon="VideoPlay"
              >
                {{ crawlerStore.status.is_running ? '爬取中...' : '开始爬取' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>爬虫状态</span>
              <el-button
                size="small"
                :icon="Refresh"
                @click="crawlerStore.fetchStatus"
                :loading="crawlerStore.loading"
              >
                刷新
              </el-button>
            </div>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="运行状态">
              <el-tag v-if="crawlerStore.status.is_running" type="success" effect="dark">
                <el-icon class="el-icon--left"><Loading /></el-icon>
                运行中
              </el-tag>
              <el-tag v-else type="info">空闲</el-tag>
            </el-descriptions-item>

            <el-descriptions-item
              v-if="crawlerStore.status.current_task"
              label="当前任务ID"
            >
              {{ crawlerStore.status.current_task.id }}
            </el-descriptions-item>

            <el-descriptions-item
              v-if="crawlerStore.status.progress && crawlerStore.status.is_running"
              label="进度信息"
            >
              <div style="line-height: 1.8">
                <div><strong>状态:</strong> {{ crawlerStore.status.progress.status }}</div>
                <div v-if="crawlerStore.status.progress.articles_crawled !== undefined">
                  <strong>已爬取:</strong> {{ crawlerStore.status.progress.articles_crawled }} 篇文章
                </div>
                <div v-if="crawlerStore.status.progress.error" style="color: #f56c6c">
                  <strong>错误:</strong> {{ crawlerStore.status.progress.error }}
                </div>
              </div>
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="crawlerStore.status.is_running" class="progress-info">
            <el-alert
              type="info"
              :closable="false"
              style="margin-top: 20px"
            >
              <template #title>
                <el-icon class="is-loading"><Loading /></el-icon>
                爬取进行中，请耐心等待...
              </template>
              <div v-if="crawlerStore.status.progress">
                {{ crawlerStore.status.progress.status }}
                <span v-if="crawlerStore.status.progress.articles_crawled">
                  - 已爬取 {{ crawlerStore.status.progress.articles_crawled }} 篇
                </span>
              </div>
            </el-alert>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时日志 -->
    <el-card v-if="crawlerStore.status.is_running || logs.length > 0" class="logs-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>执行日志</span>
          <el-button size="small" :icon="Refresh" @click="loadLogs">刷新</el-button>
        </div>
      </template>
      <div class="logs-container">
        <div v-if="logs.length === 0" style="color: #909399; text-align: center; padding: 20px">
          暂无日志
        </div>
        <div v-else class="log-list">
          <div v-for="(log, index) in logs" :key="index" class="log-entry">
            <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 爬虫任务历史 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>任务历史</span>
        </div>
      </template>

      <el-table v-loading="historyLoading" :data="historyTasks">
        <el-table-column prop="id" label="任务ID" width="100" />

        <el-table-column label="配置" min-width="250">
          <template #default="{ row }">
            <div class="config-cell">
              <div v-if="row.config.source" style="margin-bottom: 4px">
                <el-tag size="small" type="info">
                  {{ getSourceName(row.config.source) }}
                </el-tag>
              </div>
              <div>
                页数: {{ row.config.pages }}
                <span v-if="row.config.max_articles">
                  , 最大: {{ row.config.max_articles }}
                </span>
                <span v-if="row.config.days_back">
                  , 最近{{ row.config.days_back }}天
                </span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'completed'" type="success">
              完成
            </el-tag>
            <el-tag v-else-if="row.status === 'running'" type="warning">
              运行中
            </el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger">
              失败
            </el-tag>
            <el-tag v-else type="info">待运行</el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="articles_count"
          label="文章数"
          width="100"
        />

        <el-table-column label="错误信息" min-width="200">
          <template #default="{ row }">
            <el-text v-if="row.error_message" type="danger" size="small" style="word-break: break-word">
              {{ row.error_message }}
            </el-text>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, Refresh, Loading } from '@element-plus/icons-vue'
import { useCrawlerStore } from '../stores/crawler'
import {
  createCrawlerTask,
  getCrawlerTasks,
  getAvailableSources,
  getCrawlerLogs,
  type CrawlerTask,
  type DataSource
} from '../api/admin'

const crawlerStore = useCrawlerStore()

// 可用数据源
const availableSources = ref<DataSource[]>([])

// 表单
const formRef = ref()
const crawlerForm = reactive({
  source: 'pharnexcloud',  // 默认数据源
  pages: 10,
  max_articles: undefined as number | undefined,
  days_back: undefined as number | undefined,
  from_date: undefined as string | undefined,
  to_date: undefined as string | undefined
})

// 时间范围类型
const timeRangeType = ref(0) // 0: 不限, 1: 最近N天, 2: 日期范围

// 表单验证规则
const rules = {
  pages: [
    { required: true, message: '请输入爬取页数', trigger: 'blur' }
  ]
}

// 任务历史
const historyLoading = ref(false)
const historyTasks = ref<CrawlerTask[]>([])

// 日志
const logs = ref<Array<{timestamp: string, message: string}>>([])

// 加载可用数据源
const loadAvailableSources = async () => {
  try {
    availableSources.value = await getAvailableSources()
    // 如果有可用数据源，设置默认值为第一个
    if (availableSources.value.length > 0 && !crawlerForm.source) {
      crawlerForm.source = availableSources.value[0].key
    }
  } catch (error) {
    console.error('加载数据源失败:', error)
    ElMessage.error('加载数据源失败')
  }
}

// 时间范围变化
const handleTimeRangeChange = () => {
  crawlerForm.days_back = undefined
  crawlerForm.from_date = undefined
  crawlerForm.to_date = undefined
}

// 开始爬取
const handleStartCrawl = async () => {
  try {
    await formRef.value.validate()

    // 构建配置
    const config: any = {
      source: crawlerForm.source,
      pages: crawlerForm.pages
    }

    if (crawlerForm.max_articles) {
      config.max_articles = crawlerForm.max_articles
    }

    if (timeRangeType.value === 1 && crawlerForm.days_back) {
      config.days_back = crawlerForm.days_back
    } else if (timeRangeType.value === 2) {
      if (crawlerForm.from_date) config.from_date = crawlerForm.from_date
      if (crawlerForm.to_date) config.to_date = crawlerForm.to_date
    }

    await createCrawlerTask(config)
    ElMessage.success('爬虫任务已创建并开始执行')

    // 开始轮询状态
    crawlerStore.startPolling()

    // 刷新任务历史
    loadHistory()
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('创建任务失败')
    }
  }
}

// 加载任务历史
const loadHistory = async () => {
  historyLoading.value = true
  try {
    const response = await getCrawlerTasks({ page: 1, page_size: 10 })
    historyTasks.value = response.items
  } catch (error) {
    console.error('加载任务历史失败:', error)
  } finally {
    historyLoading.value = false
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

// 获取数据源名称
const getSourceName = (sourceKey: string) => {
  const source = availableSources.value.find(s => s.key === sourceKey)
  return source ? source.name : sourceKey
}

// 加载日志
const loadLogs = async () => {
  try {
    logs.value = await getCrawlerLogs()
  } catch (error) {
    console.error('加载日志失败:', error)
  }
}

// 格式化日志时间
const formatLogTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 定时加载日志
let logsTimer: number | null = null
const startLogsPolling = () => {
  if (logsTimer) return
  loadLogs()
  logsTimer = window.setInterval(() => {
    if (crawlerStore.status.is_running) {
      loadLogs()
    }
  }, 1000) // 每秒更新一次日志
}

const stopLogsPolling = () => {
  if (logsTimer) {
    clearInterval(logsTimer)
    logsTimer = null
  }
}

onMounted(() => {
  loadAvailableSources()
  crawlerStore.fetchStatus()
  crawlerStore.startPolling()
  loadHistory()
  startLogsPolling()
})

onUnmounted(() => {
  stopLogsPolling()
})

onUnmounted(() => {
  crawlerStore.stopPolling()
})
</script>

<style scoped>
.crawler {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.progress-info {
  margin-top: 20px;
}

.history-card {
  margin-top: 20px;
}

.config-cell {
  font-size: 13px;
  color: #606266;
}

.logs-container {
  max-height: 400px;
  overflow-y: auto;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
}

.log-list {
  font-family: 'Courier New', Consolas, monospace;
  font-size: 13px;
}

.log-entry {
  padding: 4px 0;
  border-bottom: 1px solid #e4e7ed;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  color: #909399;
  margin-right: 12px;
}

.log-message {
  color: #303133;
}
</style>
