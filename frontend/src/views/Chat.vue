<template>
  <div class="chat-container">
    <!-- Header -->
    <div class="chat-header">
      <h1>医药资讯问答</h1>
    </div>

    <!-- Messages -->
    <div class="chat-messages" ref="messagesRef">
      <div v-for="(msg, index) in messages" :key="index" class="message-wrapper">
        <div :class="['message', msg.role]">
          <div class="message-content">{{ msg.content }}</div>
          <div v-if="msg.sources && msg.sources.length > 0" class="sources">
            <div class="sources-title">参考来源：</div>
            <div
              v-for="(source, idx) in msg.sources"
              :key="idx"
              class="source-item"
              @click="openSource(source)"
            >
              [{{ idx + 1 }}] {{ source.title }} ({{ formatDate(source.published_at) }})
            </div>
          </div>
        </div>
      </div>

      <div v-if="loading" class="message-wrapper">
        <div class="message assistant">
          <van-loading type="spinner">思考中...</van-loading>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input">
      <van-field
        v-model="inputText"
        placeholder="请输入您的问题..."
        @keyup.enter="sendMessage"
      />
      <van-button type="primary" :disabled="loading || !inputText.trim()" @click="sendMessage">
        发送
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { Field as VanField, Button as VanButton, Loading as VanLoading, Toast } from 'vant'
import { chatAPI } from '../api/client'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
}

const messages = ref<Message[]>([])
const inputText = ref('')
const loading = ref(false)
const messagesRef = ref<HTMLElement>()
const conversationId = ref<string>()

const sendMessage = async () => {
  if (!inputText.value.trim() || loading.value) return

  const question = inputText.value.trim()
  inputText.value = ''

  // Add user message
  messages.value.push({
    role: 'user',
    content: question
  })

  scrollToBottom()
  loading.value = true

  try {
    const response = await chatAPI(question, conversationId.value)

    conversationId.value = response.conversation_id

    // Add assistant message
    messages.value.push({
      role: 'assistant',
      content: response.answer,
      sources: response.sources
    })

    scrollToBottom()
  } catch (error: any) {
    console.error('Chat error:', error)
    Toast.fail(error.message || '发送失败，请重试')
  } finally {
    loading.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const formatDate = (dateStr: string) => {
  return dateStr.split('T')[0]
}

const openSource = (source: any) => {
  window.open(source.url, '_blank')
}

onMounted(() => {
  // Add welcome message
  messages.value.push({
    role: 'assistant',
    content: '您好！我是医药资讯智能助手，可以帮您查找和解读最新的医药行业资讯。请问有什么可以帮您的？'
  })
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.chat-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chat-header h1 {
  font-size: 18px;
  font-weight: 600;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.message-wrapper {
  margin-bottom: 16px;
}

.message {
  display: inline-block;
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
}

.message.user {
  background-color: #667eea;
  color: white;
  float: right;
  clear: both;
}

.message.assistant {
  background-color: white;
  color: #333;
  float: left;
  clear: both;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.message-content {
  line-height: 1.6;
  white-space: pre-wrap;
}

.sources {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.sources-title {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.source-item {
  font-size: 13px;
  color: #667eea;
  margin: 4px 0;
  cursor: pointer;
  text-decoration: underline;
}

.source-item:hover {
  color: #764ba2;
}

.chat-input {
  display: flex;
  padding: 12px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  gap: 8px;
}

.chat-input :deep(.van-field) {
  flex: 1;
}

.chat-input :deep(.van-button) {
  flex-shrink: 0;
}
</style>
