/**
 * 爬虫管理 Store
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CrawlerStatus } from '../api/admin'
import { getCrawlerStatus } from '../api/admin'

export const useCrawlerStore = defineStore('crawler', () => {
  // 状态
  const status = ref<CrawlerStatus>({
    is_running: false,
    current_task: null,
    progress: null
  })

  const loading = ref(false)

  // 获取爬虫状态
  const fetchStatus = async () => {
    loading.value = true
    try {
      status.value = await getCrawlerStatus()
    } catch (error) {
      console.error('获取爬虫状态失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 开始轮询
  let pollingTimer: number | null = null
  const startPolling = (interval: number = 3000) => {
    if (pollingTimer) return

    fetchStatus() // 立即获取一次
    pollingTimer = window.setInterval(() => {
      fetchStatus()
    }, interval)
  }

  // 停止轮询
  const stopPolling = () => {
    if (pollingTimer) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  return {
    status,
    loading,
    fetchStatus,
    startPolling,
    stopPolling
  }
})
