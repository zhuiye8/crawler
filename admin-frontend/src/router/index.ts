/**
 * Vue Router 配置
 */

import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { title: '仪表盘' }
    },
    {
      path: '/articles',
      name: 'Articles',
      component: () => import('../views/Articles.vue'),
      meta: { title: '文章管理' }
    },
    {
      path: '/crawler',
      name: 'Crawler',
      component: () => import('../views/Crawler.vue'),
      meta: { title: '爬虫管理' }
    }
  ]
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} - 医药资讯后台管理`
  next()
})

export default router
