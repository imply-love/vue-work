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
  // 注册前发送邮箱验证码
  sendEmailCode(data) {
    return api.post('/email/code', data)
  },
}

// 用户相关 API
export const userApi = {
  // 获取当前用户资料
  getProfile() {
    return api.get('/user/profile')
  },
  // 更新当前用户资料（昵称、邮箱；换邮箱时需带 code）
  updateProfile(data) {
    return api.put('/user/profile', data)
  },
  // 换绑邮箱时发送验证码
  sendBindEmailCode(data) {
    return api.post('/user/email/code', data)
  },
  // 绑定 / 换绑 / 解绑手机号（phone 传空串表示解绑）
  updatePhone(data) {
    return api.put('/user/phone', data)
  },
  // 修改密码（需验证原密码）
  changePassword(data) {
    return api.put('/user/password', data)
  },
  // 登录记录（分页，最近登录在前）
  getLoginLogs(params = {}) {
    return api.get('/user/login-logs', { params })
  },
  // 注销账号（需输入当前密码确认）
  deleteAccount(data) {
    return api.delete('/user/account', { data })
  },
  // 关注 / 取消关注指定用户（幂等切换）
  follow(userId) {
    return api.post(`/users/${userId}/follow`)
  },
}

// 收藏相关 API（个人中心「我的收藏」）
export const favoriteApi = {
  // 我的收藏列表（分页，仅展示已发布的帖子）
  getList(params = {}) {
    return api.get('/favorites', { params })
  },
  // 收藏帖子
  add(postId) {
    return api.post('/favorites', { post_id: postId })
  },
  // 取消收藏
  remove(postId) {
    return api.delete(`/favorites/${postId}`)
  },
}

// 帖子相关 API
export const postApi = {
  // 获取帖子列表（支持 sort 排序、q 搜索、category 分类）
  getList(params = {}) {
    return api.get('/posts', { params })
  },
  // 获取帖子详情
  getDetail(id) {
    return api.get(`/posts/${id}`)
  },
  // 发布新帖 / 保存草稿（需登录：管理员与普通用户均可）
  create(data) {
    return api.post('/posts', data)
  },
  // 我的草稿列表（需登录）
  getDrafts(params = {}) {
    return api.get('/posts/drafts', { params })
  },
  // 更新自己的帖子/草稿（需登录，仅作者）
  update(id, data) {
    return api.put(`/posts/${id}`, data)
  },
  // 删除自己的帖子/草稿（需登录，仅作者）
  remove(id) {
    return api.delete(`/posts/${id}`)
  },
  // 点赞 / 取消点赞切换（需登录）
  like(id) {
    return api.post(`/posts/${id}/like`)
  },
  // 评论列表（公开）
  getReplies(id, params = {}) {
    return api.get(`/posts/${id}/replies`, { params })
  },
  // 发表评论（需登录）
  addReply(id, data) {
    return api.post(`/posts/${id}/replies`, data)
  },
}

// 求番相关 API（番剧库板块）
export const animeRequestApi = {
  // 获取求番列表
  getList(params = {}) {
    return api.get('/anime-requests', { params })
  },
  // 发起求番（需登录：管理员与普通用户均可）
  create(data) {
    return api.post('/anime-requests', data)
  },
}

// 资源分享相关 API（资源分享板块）
export const resourceApi = {
  // 获取资源列表
  getList(params = {}) {
    return api.get('/resources', { params })
  },
  // 分享资源（需登录：管理员与普通用户均可）
  create(data) {
    return api.post('/resources', data)
  },
}

export default api