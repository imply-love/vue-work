import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { setTokenInvalidHandler } from './api'
import { useAuthStore } from './stores/auth'

// Layui Vue 组件库（全局注册，页面里直接使用 lay-card / lay-button 等组件）
import Layui from '@layui/layui-vue'
import '@layui/layui-vue/lib/index.css'

// 导入全局样式（layui 样式在前，自定义主题在后，保证主题变量覆盖生效）
import './styles/global.scss'
import './styles/layui-theme.scss'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(Layui)

// token 失效时同步清理 Pinia 登录态
setTokenInvalidHandler(() => useAuthStore().logout())

app.mount('#app')