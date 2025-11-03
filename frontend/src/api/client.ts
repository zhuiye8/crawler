import axios from 'axios'

// Create axios instance
const apiClient = axios.create({
  baseURL: '/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    return Promise.reject(error.response?.data || error)
  }
)

// Chat API - 无需认证，直接调用
export const chatAPI = async (question: string, conversationId?: string) => {
  return await apiClient.post('/chat', {
    question,
    conversation_id: conversationId
  })
}

// Articles API - 无需认证，直接调用
export const getArticles = async (page = 1, pageSize = 20) => {
  return await apiClient.get('/articles', {
    params: { page, page_size: pageSize }
  })
}

export const getArticleDetail = async (articleId: number) => {
  return await apiClient.get(`/articles/${articleId}`)
}
