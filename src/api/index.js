import axios from 'axios'

// 接口基础路径：
// - 开发环境走 Vite 代理（vite.config.js 的 server.proxy），生产环境由部署平台转发，两者都用相对路径。
// - 若后端部署在独立域名且不走平台转发，构建时设置 VITE_API_BASE_URL=https://your-api.example.com/api 即可覆盖。
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

// 创建 axios 实例
const api = axios.create({
  baseURL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动携带 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const { response } = error
    if (response) {
      // 后端返回的业务错误码
      const { code, message } = response.data || {}
      if (code === 1007) {
        // token 无效或过期，清除本地存储并跳转登录
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      return Promise.reject({ code, message: message || '请求失败' })
    }
    return Promise.reject({ code: -1, message: '网络错误，请检查连接' })
  }
)

// 认证相关 API
export const authApi = {
  // 注册
  register(data) {
    return api.post('/register', data)
  },
  // 登录
  login(data) {
    return api.post('/login', data)
  },
}

// 用户相关 API
export const userApi = {
  // 获取当前用户资料
  getProfile() {
    return api.get('/user/profile')
  },
}

// 帖子相关 API
export const postApi = {
  // 获取帖子列表
  getList(params = {}) {
    return api.get('/posts', { params })
  },
}

export default api