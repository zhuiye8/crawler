# H5页面测试与交付指南

## 📱 项目概述

这是一个医药资讯智能问答的H5移动端页面，基于 Vue 3 + Vite + Vant 开发，可以嵌入到其他项目中使用。

**功能特点：**
- ✅ 移动端适配（响应式设计）
- ✅ 智能问答对话界面
- ✅ 支持多轮对话（自动保持会话ID）
- ✅ 显示文章来源链接
- ✅ 无需认证，开箱即用
- ✅ 美观的紫色渐变主题

---

## 🧪 本地测试指南

### 前置要求

1. **Node.js** - 版本 16.x 或以上
2. **后端API服务** - 必须运行在 `http://localhost:8000`

### 测试步骤

#### 1. 安装依赖

```bash
cd medical-news-mvp/frontend
npm install
```

#### 2. 启动开发服务器

```bash
npm run dev
```

服务将运行在 `http://localhost:5173`

#### 3. 浏览器测试

在浏览器中打开以下地址：
- **桌面浏览器**: http://localhost:5173
- **移动端模拟器**:
  1. 打开 Chrome DevTools (F12)
  2. 点击设备模拟按钮（Ctrl+Shift+M）
  3. 选择移动设备（如 iPhone 12 Pro）

#### 4. 手机真机测试

**方法一：局域网访问（推荐）**

1. 确保手机和电脑在同一Wi-Fi网络
2. 查看电脑IP地址：
   ```bash
   # Windows
   ipconfig
   # 找到 IPv4 地址，例如 192.168.1.100
   ```
3. 在手机浏览器访问：`http://你的电脑IP:5173`
   - 例如：`http://192.168.1.100:5173`

**方法二：使用二维码**
1. 访问 https://cli.im/ 等二维码生成网站
2. 输入 `http://你的电脑IP:5173`
3. 用手机扫描生成的二维码

---

## 📦 生产环境构建

### 构建静态文件

```bash
cd medical-news-mvp/frontend
npm run build
```

构建完成后，会在 `frontend/dist` 目录生成以下文件：

```
dist/
├── index.html          # 入口HTML文件
├── assets/
│   ├── index-xxx.js    # 编译后的JS文件
│   └── index-xxx.css   # 编译后的CSS文件
└── ...
```

---

## 🚀 交付方式

根据对方的集成需求，提供以下几种交付方案：

### 方案一：完整静态文件包（最简单）

**适用场景：** 对方有独立的Web服务器，可以直接部署静态文件

**交付内容：**
```
医药资讯H5页面.zip
├── dist/                    # 构建后的完整目录
│   ├── index.html
│   ├── assets/
│   └── ...
├── 部署说明.txt              # 简要说明
└── API接口文档.md            # 后端API文档
```

**部署说明（提供给对方）：**
```
1. 解压文件到Web服务器目录
2. 配置Nginx/Apache，将/v1路径代理到后端API
3. 访问 index.html 即可使用

Nginx配置示例：
location /v1 {
    proxy_pass http://你的后端地址:8000;
    proxy_set_header Host $host;
}
```

### 方案二：Iframe嵌入（最灵活）

**适用场景：** 对方想在现有页面中嵌入聊天功能

**交付内容：**
1. 完整的H5页面部署包（同方案一）
2. 嵌入代码示例文件

**创建嵌入示例文件：**

```html
<!-- 嵌入示例.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>医药资讯问答 - 嵌入示例</title>
  <style>
    /* iframe容器样式 */
    .chat-iframe-container {
      width: 100%;
      max-width: 500px;
      height: 600px;
      border: none;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      margin: 20px auto;
      display: block;
    }

    /* 移动端全屏样式 */
    @media (max-width: 768px) {
      .chat-iframe-container {
        width: 100%;
        height: 100vh;
        max-width: 100%;
        margin: 0;
        border-radius: 0;
      }
    }
  </style>
</head>
<body>
  <!-- 嵌入聊天iframe -->
  <iframe
    src="http://你的域名/h5-chat/index.html"
    class="chat-iframe-container"
    frameborder="0"
    allow="clipboard-write"
  ></iframe>
</body>
</html>
```

### 方案三：源码交付（需要二次开发）

**适用场景：** 对方需要自定义样式或功能

**交付内容：**
```
医药资讯H5源码.zip
├── frontend/                # 完整前端源码
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
├── 开发文档.md               # 开发和修改指南
└── API接口文档.md            # 后端API文档
```

**开发文档内容要点：**
- 技术栈说明（Vue 3 + TypeScript + Vite + Vant）
- 目录结构说明
- 如何修改主题色
- 如何修改接口地址
- 如何添加新功能

---

## 🔧 配置说明

### 修改API地址

如果后端API不在同一域名下，需要修改 `vite.config.ts`：

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/v1': {
        target: 'http://你的后端API地址',  // 修改这里
        changeOrigin: true
      }
    }
  }
})
```

**生产环境配置（Nginx）：**

```nginx
# 部署在 https://你的域名.com/h5-chat/
location /h5-chat/ {
    alias /var/www/h5-chat/dist/;
    try_files $uri $uri/ /h5-chat/index.html;
}

# API代理
location /v1/ {
    proxy_pass http://后端API地址:8000/v1/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 修改主题颜色

编辑 `src/views/Chat.vue` 中的样式：

```css
.chat-header {
  /* 修改这里的渐变色 */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message.user {
  /* 修改用户消息气泡颜色 */
  background-color: #667eea;
}
```

---

## 📱 移动端适配测试清单

在交付前，请确保在以下设备/分辨率测试：

- [ ] iPhone 12/13/14 Pro (390x844)
- [ ] iPhone SE (375x667)
- [ ] Android 大屏 (412x915)
- [ ] iPad (768x1024)
- [ ] 横屏模式

**测试要点：**
- [ ] 输入框不被键盘遮挡
- [ ] 消息列表自动滚动到底部
- [ ] 长消息正常换行
- [ ] 来源链接可点击跳转
- [ ] 加载状态正常显示

---

## 🎯 交付检查清单

### 文件准备

- [ ] 构建生产版本（npm run build）
- [ ] 测试dist目录的静态文件是否正常运行
- [ ] 压缩打包（去除node_modules等开发文件）
- [ ] 准备API接口文档
- [ ] 准备部署说明文档

### 文档准备

- [ ] **部署说明.md** - 如何部署静态文件
- [ ] **API接口文档.md** - 后端API调用说明
- [ ] **嵌入示例.html** - iframe嵌入代码示例
- [ ] **配置说明.md** - 如何修改API地址和主题

### 测试验证

- [ ] 本地测试通过
- [ ] 移动端真机测试通过
- [ ] 网络异常处理正常（断网、超时）
- [ ] API错误提示友好

---

## 📄 提供给对方的快速开始文档

创建一个 `快速开始.txt` 文件：

```
===========================================
    医药资讯H5问答页面 - 快速部署指南
===========================================

【第一步】解压文件到Web服务器
将 dist 目录中的所有文件上传到您的Web服务器

【第二步】配置API代理
在Nginx/Apache中配置 /v1 路径代理到后端API
后端API地址：http://您提供的地址:8000

Nginx配置示例：
location /v1 {
    proxy_pass http://后端API地址:8000;
    proxy_set_header Host $host;
}

【第三步】访问测试
浏览器打开: http://您的域名/index.html

【如需嵌入到现有页面】
使用iframe标签：
<iframe src="http://您的域名/index.html"
        width="100%"
        height="600px"
        frameborder="0">
</iframe>

【技术支持】
遇到问题请联系：[您的联系方式]

【API文档】
详见附件：API_DOCUMENTATION.md
```

---

## 🎨 自定义开发指南（给对方开发者）

如果对方需要自定义样式或功能：

### 1. 修改欢迎语

编辑 `src/views/Chat.vue` 第118-122行：

```typescript
onMounted(() => {
  messages.value.push({
    role: 'assistant',
    content: '修改为你想要的欢迎语！'
  })
})
```

### 2. 添加自定义按钮

在 `src/views/Chat.vue` 的模板中添加：

```vue
<template>
  <div class="chat-container">
    <div class="chat-header">
      <h1>医药资讯问答</h1>
      <!-- 添加自定义按钮 -->
      <button @click="handleCustomAction">自定义操作</button>
    </div>
    <!-- ... -->
  </div>
</template>
```

### 3. 集成到React项目

可以通过iframe或Web Component方式集成：

```jsx
// React组件示例
function MedicalChat() {
  return (
    <iframe
      src="http://h5-chat-url/index.html"
      style={{
        width: '100%',
        height: '600px',
        border: 'none',
        borderRadius: '12px'
      }}
    />
  );
}
```

---

## ⚠️ 注意事项

1. **跨域问题**
   - 如果H5页面和后端API不在同一域名，需要配置CORS
   - 后端已配置允许跨域，但生产环境建议使用Nginx代理

2. **HTTPS要求**
   - 如果主站使用HTTPS，H5页面和API也必须使用HTTPS
   - 混合内容（HTTPS页面加载HTTP资源）会被浏览器阻止

3. **移动端键盘**
   - iOS Safari可能会出现键盘遮挡输入框的问题
   - 已在代码中处理，如有问题请及时反馈

4. **性能优化**
   - 生产环境建议启用CDN
   - 构建时已自动压缩和优化资源

---

## 📞 交付后支持

建议提供以下支持：

1. **部署指导** - 协助对方完成首次部署（远程/文档）
2. **集成测试** - 验证在对方环境中运行正常
3. **问题排查** - 提供1-2周的技术支持期
4. **更新维护** - 约定后续功能更新和bug修复的方式

---

## 📋 交付清单模板

**医药资讯H5页面交付清单**

□ 生产环境构建文件 (dist.zip)
□ 源代码包 (frontend.zip) - 可选
□ API接口文档 (API_DOCUMENTATION.md)
□ 部署说明文档 (本文档)
□ 快速开始指南 (快速开始.txt)
□ iframe嵌入示例 (嵌入示例.html)
□ Nginx配置示例 (nginx.conf)

交付日期：__________
交付方式：□ 邮件  □ 网盘  □ Git仓库  □ 其他
技术支持：__________

---

**祝部署顺利！** 🎉
