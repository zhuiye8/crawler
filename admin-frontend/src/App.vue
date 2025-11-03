<template>
  <el-container class="app-container">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <h2>医药资讯后台</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/articles">
          <el-icon><Document /></el-icon>
          <span>文章管理</span>
        </el-menu-item>
        <el-menu-item index="/crawler">
          <el-icon><Connection /></el-icon>
          <span>爬虫管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-title">{{ pageTitle }}</div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 当前激活的菜单项
const activeMenu = computed(() => route.path)

// 页面标题
const pageTitle = computed(() => {
  return (route.meta.title as string) || '医药资讯后台管理'
})
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background: linear-gradient(180deg, #304156 0%, #263445 100%);
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.08);
  height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  color: #fff;
  font-weight: 600;
  letter-spacing: 1px;
}

.sidebar-menu {
  border: none;
  background: transparent !important;
}

.header {
  background: linear-gradient(90deg, #fff 0%, #f8f9fa 100%);
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px !important;
  z-index: 10;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.main-content {
  background-color: #f0f2f5;
  padding: 24px;
  height: calc(100vh - 64px);
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
