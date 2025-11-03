/**
 * 后台管理 API 客户端
 */

import axios from 'axios'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/v1/admin',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ==================== 文章管理 ====================

export interface Article {
  id: number
  title: string
  summary: string | null
  author: string | null
  category: string | null
  tags: string[]
  published_at: string
  crawled_at: string
  content_source: string
  content_url: string | null
  is_deleted: boolean
  created_at: string
  updated_at: string
}

export interface ArticleListQuery {
  page: number
  page_size: number
  keyword?: string
  category?: string
  content_source?: string
  from_date?: string
  to_date?: string
}

export interface ArticleListResponse {
  total: number
  page: number
  page_size: number
  total_pages: number
  items: Article[]
}

// 获取文章列表
export const getArticles = (params: ArticleListQuery): Promise<ArticleListResponse> => {
  return apiClient.get('/articles', { params })
}

// 获取文章详情
export const getArticleDetail = (id: number): Promise<Article> => {
  return apiClient.get(`/articles/${id}`)
}

// 删除文章
export const deleteArticle = (id: number): Promise<any> => {
  return apiClient.delete(`/articles/${id}`)
}

// 批量删除文章
export const batchDeleteArticles = (article_ids: number[]): Promise<any> => {
  return apiClient.delete('/articles/batch/delete', { data: { article_ids } })
}

// 生成AI分析（注意：这个API在公开的articles路由下）
export const generateAIAnalysis = (id: number, forceRegenerate: boolean = false): Promise<any> => {
  return axios.post(`http://localhost:8000/v1/articles/${id}/analyze?force_regenerate=${forceRegenerate}`)
}

// 生成AI翻译（使用admin路由）
export const generateTranslation = (id: number, forceRegenerate: boolean = false): Promise<any> => {
  return apiClient.post(`/articles/${id}/translate?force_regenerate=${forceRegenerate}`)
}

// ==================== 爬虫管理 ====================

export interface CrawlerConfig {
  source?: string  // 数据源标识符
  pages: number
  max_articles?: number
  days_back?: number
  from_date?: string
  to_date?: string
}

export interface DataSource {
  key: string
  name: string
  supports_wechat: boolean
}

export interface CrawlerTask {
  id: number
  config: Record<string, any>
  status: string
  articles_count: number
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  created_at: string
}

export interface CrawlerStatus {
  is_running: boolean
  current_task: CrawlerTask | null
  progress: Record<string, any> | null
}

// 创建爬虫任务
export const createCrawlerTask = (config: CrawlerConfig): Promise<any> => {
  return apiClient.post('/crawler/tasks', config)
}

// 获取爬虫任务列表
export const getCrawlerTasks = (params: { page: number; page_size: number }): Promise<any> => {
  return apiClient.get('/crawler/tasks', { params })
}

// 获取爬虫状态
export const getCrawlerStatus = (): Promise<CrawlerStatus> => {
  return apiClient.get('/crawler/status')
}

// 获取可用数据源列表
export const getAvailableSources = (): Promise<DataSource[]> => {
  return apiClient.get('/crawler/sources')
}

// 获取爬虫执行日志
export const getCrawlerLogs = (): Promise<Array<{timestamp: string, message: string}>> => {
  return apiClient.get('/crawler/logs')
}

// ==================== 统计分析 ====================

export interface OverviewStats {
  total_articles: number
  today_articles: number
  week_articles: number
  month_articles: number
  wechat_articles: number
  pharnex_articles: number
}

export interface TrendItem {
  date: string
  count: number
}

export interface SourceDistribution {
  source: string
  count: number
  percentage: number
}

// 获取概览统计
export const getOverviewStats = (): Promise<OverviewStats> => {
  return apiClient.get('/analytics/overview')
}

// 获取文章趋势
export const getArticleTrends = (days: number = 30): Promise<TrendItem[]> => {
  return apiClient.get('/analytics/trends', { params: { days } })
}

// 获取来源分布
export const getSourceDistribution = (): Promise<SourceDistribution[]> => {
  return apiClient.get('/analytics/sources')
}

export default apiClient
