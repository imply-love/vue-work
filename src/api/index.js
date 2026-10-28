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

// token 失效时的回调：由 main.js 注入，用于同步清理 Pinia 里的登录态，
// 避免 localStorage 已清空但内存里仍是「已登录」导致登录页又被弹回首页。
let tokenInvalidHandler = null
export const setTokenInvalidHandler = (handler) => {
  tokenInvalidHandler = handler
}

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const { response } = error
    if (response) {
      // 后端返回的业务错误码
      const { code, message } = response.data || {}
      if (code === 1007) {
        // token 无效或过期，清除本地存储与内存登录态并跳转登录
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        tokenInvalidHandler?.()
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
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
  // 我的关注列表
  getFollowing(params = {}) {
    return api.get('/user/following', { params })
  },
  // 我的粉丝列表
  getFollowers(params = {}) {
    return api.get('/user/followers', { params })
  },
  // 我获得的点赞（按帖子聚合）
  getReceivedLikes(params = {}) {
    return api.get('/user/received-likes', { params })
  },
  // 某个用户的公开资料卡
  getUserCard(userId) {
    return api.get(`/users/${userId}`)
  },
  // 提交账号申诉
  submitAppeal(data) {
    return api.post('/user/appeal', data)
  },
  // 我的申诉记录
  getAppeals(params = {}) {
    return api.get('/user/appeals', { params })
  },
  // 我的评论
  getMyReplies(params = {}) {
    return api.get('/user/replies', { params })
  },
}

// 好友相关 API
export const friendApi = {
  // 发起好友申请 { user_id, message }
  sendRequest(data) {
    return api.post('/friends/requests', data)
  },
  // 好友申请列表 direction=incoming|outgoing
  getRequests(params = {}) {
    return api.get('/friends/requests', { params })
  },
  // 处理好友申请 { action: 'accept' | 'reject' }
  handleRequest(id, data) {
    return api.put(`/friends/requests/${id}`, data)
  },
  // 待处理申请数量
  getPendingCount() {
    return api.get('/friends/pending-count')
  },
  // 好友列表
  getFriends(params = {}) {
    return api.get('/friends', { params })
  },
  // 解除好友
  removeFriend(userId) {
    return api.delete(`/friends/${userId}`)
  },
}

// 管理后台 API（仅管理员）
export const adminApi = {
  // 看板数据（统计 + 趋势 + 状态分布 + 待办清单）
  getDashboard() {
    return api.get('/admin/dashboard')
  },
  getPosts(params = {}) {
    return api.get('/admin/posts', { params })
  },
  reviewPost(id, data) {
    return api.put(`/admin/posts/${id}/review`, data)
  },
  // 评论审查
  getComments(params = {}) {
    return api.get('/admin/comments', { params })
  },
  reviewComment(id, data) {
    return api.put(`/admin/comments/${id}/review`, data)
  },
  // 资源分享审查
  getResources(params = {}) {
    return api.get('/admin/resources', { params })
  },
  reviewResource(id, data) {
    return api.put(`/admin/resources/${id}/review`, data)
  },
  // 求番审查
  getAnimeRequests(params = {}) {
    return api.get('/admin/anime-requests', { params })
  },
  reviewAnimeRequest(id, data) {
    return api.put(`/admin/anime-requests/${id}/review`, data)
  },
  // 番剧推荐审查
  getRecommendations(params = {}) {
    return api.get('/admin/anime-recommendations', { params })
  },
  reviewRecommendation(id, data) {
    return api.put(`/admin/anime-recommendations/${id}/review`, data)
  },
  // 身份申请审批
  getIdentityApplications(params = {}) {
    return api.get('/admin/identity-applications', { params })
  },
  handleIdentityApplication(id, data) {
    return api.put(`/admin/identity-applications/${id}`, data)
  },
  getUsers(params = {}) {
    return api.get('/admin/users', { params })
  },
  banUser(id, data) {
    return api.put(`/admin/users/${id}/ban`, data)
  },
  unbanUser(id) {
    return api.put(`/admin/users/${id}/unban`)
  },
  // 禁用 / 启用账号（禁用后无法登录，可再次启用）
  disableUser(id) {
    return api.put(`/admin/users/${id}/disable`)
  },
  enableUser(id) {
    return api.put(`/admin/users/${id}/enable`)
  },
  getAppeals(params = {}) {
    return api.get('/admin/appeals', { params })
  },
  handleAppeal(id, data) {
    return api.put(`/admin/appeals/${id}`, data)
  },
  getStats() {
    return api.get('/admin/stats')
  },
  // 公告管理
  getAnnouncements(params = {}) {
    return api.get('/admin/announcements', { params })
  },
  createAnnouncement(data) {
    return api.post('/admin/announcements', data)
  },
  updateAnnouncement(id, data) {
    return api.put(`/admin/announcements/${id}`, data)
  },
  setAnnouncementStatus(id, status) {
    return api.put(`/admin/announcements/${id}/status`, { status })
  },
  removeAnnouncement(id) {
    return api.delete(`/admin/announcements/${id}`)
  },
}

// 公告 API（前台公开展示）
export const announcementApi = {
  getList() {
    return api.get('/announcements')
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
  // 内容管理：我的帖子（status=all|published|draft，含审查状态）
  getMine(params = {}) {
    return api.get('/posts/mine', { params })
  },
  // 快速设置可见性 0-公开 1-私密 2-仅好友
  setVisibility(id, visibility) {
    return api.put(`/posts/${id}/visibility`, { visibility })
  },
  // 多级评论树
  getReplyTree(id) {
    return api.get(`/posts/${id}/replies/tree`)
  },
  // 删除评论
  removeReply(replyId) {
    return api.delete(`/replies/${replyId}`)
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

// 番剧库内容 API（管理员在后台录入，前台公开浏览）
export const animeApi = {
  getList(params = {}) {
    return api.get('/animes', { params })
  },
  create(data) {
    return api.post('/animes', data)
  },
  update(id, data) {
    return api.put(`/animes/${id}`, data)
  },
  remove(id) {
    return api.delete(`/animes/${id}`)
  },
}

// 番剧推荐 API（番名、链接、推荐理由必填）
export const animeRecommendationApi = {
  getList(params = {}) {
    return api.get('/anime-recommendations', { params })
  },
  create(data) {
    return api.post('/anime-recommendations', data)
  },
}

// 身份申请 API（番剧大佬 / 我就是资源）
export const identityApi = {
  getOverview() {
    return api.get('/identity/overview')
  },
  apply(data) {
    return api.post('/identity/applications', data)
  },
}

// 站内通知 API
export const notificationApi = {
  getList(params = {}) {
    return api.get('/notifications', { params })
  },
  getUnreadCount() {
    return api.get('/notifications/unread-count')
  },
  read(id) {
    return api.put(`/notifications/${id}/read`)
  },
  readAll() {
    return api.put('/notifications/read-all')
  },
}

// 资源分享相关 API（资源分享板块）
export const resourceApi = {
  // 获取资源列表（必须登录，未登录返回 1007）
  getList(params = {}) {
    return api.get('/resources', { params })
  },
  // 分享资源（需登录；visibility 0-所有同好 1-仅管理员与特殊身份 2-仅自己）
  create(data) {
    return api.post('/resources', data)
  },
  // 删除资源（发布者本人或管理员）
  remove(id) {
    return api.delete(`/resources/${id}`)
  },
}

export default api