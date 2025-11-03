import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

// Vant styles
import 'vant/lib/index.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')
