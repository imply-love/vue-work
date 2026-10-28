<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, PieChart, BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])
import { adminApi, animeApi, announcementApi, notificationApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const PAGE_SIZE = 10
// 不展示每页条数切换，避免分页器内部页大小与请求参数不一致
const PAGE_LAYOUT = ['prev', 'page', 'next', 'count']

// lay-page 的 change 事件回调参数为 { current, limit }
const resolvePage = (payload, fallback) => {
  if (typeof payload === 'number') return payload
  if (payload && typeof payload.current === 'number') return payload.current
  return fallback
}

const adminName = computed(
  () => authStore.user?.nickname || authStore.user?.username || '管理员'
)

const toast = (type, title, message) => {
  window.$ghibli?.showToast({ type, title, message })
}

const openLink = (link) => {
  if (!link) return
  window.open(link, '_blank', 'noopener,noreferrer')
}

// ===== 未读通知提醒 =====
const notifCount = ref(0)

const loadNotifCount = async () => {
  try {
    const res = await notificationApi.getUnreadCount()
    notifCount.value = res.code === 0 ? res.data.count : 0
  } catch {
    notifCount.value = 0
  }
}

const goNotifications = () => router.push('/notifications')

// ===== 区块切换 =====
const SECTION_TABS = [
  { key: 'dashboard', label: '看板' },
  { key: 'posts', label: '内容审查' },
  { key: 'animes', label: '番剧库管理' },
  { key: 'identity', label: '身份申请' },
  { key: 'users', label: '用户管理' },
  { key: 'appeals', label: '申诉处理' },
  { key: 'announcements', label: '公告管理' },
]

const section = ref('dashboard')

const switchSection = (key, source) => {
  section.value = key
  if (key === 'dashboard') {
    loadDashboard()
  } else if (key === 'posts') {
    if (source) reviewSource.value = source
    loadModeration(reviewSource.value, 1)
  } else if (key === 'animes') {
    loadAnimes(1)
  } else if (key === 'identity') {
    loadIdentityApps(1)
  } else if (key === 'users') {
    loadAdminUsers(1)
  } else if (key === 'appeals') {
    loadAdminAppeals(1)
  } else if (key === 'announcements') {
    loadAnnouncements(1)
  }
}

// ===== 看板：ECharts 全局预览 + 待办事项 =====
const dashboard = ref(null)
const dashboardLoading = ref(false)
const dashboardError = ref('')

const trendChartRef = ref(null)
const postPieChartRef = ref(null)
const categoryBarChartRef = ref(null)
let trendChart = null
let postPieChart = null
let categoryBarChart = null

const GHIBLI_COLORS = ['#6ea8d8', '#f2a7b3', '#f6c168', '#9bbf8f', '#b8a6d9', '#8fd0c8', '#e2a76f', '#a5c8e8']
const REVIEW_STATUS_LABELS = { 0: '正常', 1: '推荐', 2: '打回', 3: '封禁', 4: '待审核' }

const loadDashboard = async () => {
  dashboardLoading.value = true
  dashboardError.value = ''
  try {
    const res = await adminApi.getDashboard()
    if (res.code === 0) {
      dashboard.value = res.data || null
      await nextTick()
      renderCharts()
    } else {
      dashboardError.value = res.message || '看板加载失败'
    }
  } catch (err) {
    dashboardError.value = err.message || '看板加载失败，请稍后重试'
  } finally {
    dashboardLoading.value = false
  }
}

const renderCharts = () => {
  if (!dashboard.value) return

  // 近 14 天趋势折线
  if (trendChartRef.value) {
    trendChart = trendChart || echarts.init(trendChartRef.value)
    const trends = dashboard.value.trends || {}
    trendChart.setOption({
      color: GHIBLI_COLORS,
      tooltip: { trigger: 'axis' },
      legend: { data: ['新增用户', '新增帖子', '新增评论'], bottom: 0 },
      grid: { left: 40, right: 20, top: 30, bottom: 40 },
      xAxis: { type: 'category', boundaryGap: false, data: trends.days || [] },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        {
          name: '新增用户', type: 'line', smooth: true,
          data: trends.users || [], areaStyle: { opacity: 0.08 },
        },
        { name: '新增帖子', type: 'line', smooth: true, data: trends.posts || [] },
        { name: '新增评论', type: 'line', smooth: true, data: trends.replies || [] },
      ],
    })
  }

  // 帖子审查状态分布（环形图）
  if (postPieChartRef.value) {
    postPieChart = postPieChart || echarts.init(postPieChartRef.value)
    const statusMap = dashboard.value.post_status || {}
    const pieData = Object.entries(statusMap)
      .map(([key, value]) => ({
        name: REVIEW_STATUS_LABELS[key] || `状态${key}`,
        value,
      }))
      .filter((item) => item.value > 0)
    postPieChart.setOption({
      color: GHIBLI_COLORS,
      tooltip: { trigger: 'item', formatter: '{b}: {c} 篇（{d}%）' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['38%', '65%'],
          center: ['50%', '44%'],
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { formatter: '{b}: {c}' },
          data: pieData,
        },
      ],
    })
  }

  // 帖子分类排行（横向柱状）
  if (categoryBarChartRef.value) {
    categoryBarChart = categoryBarChart || echarts.init(categoryBarChartRef.value)
    const top = [...(dashboard.value.category_top || [])]
    const names = top.map((item) => item.name)
    const counts = top.map((item) => item.count)
    categoryBarChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 70, right: 30, top: 20, bottom: 30 },
      xAxis: { type: 'value', minInterval: 1 },
      yAxis: { type: 'category', data: names.reverse() },
      series: [
        {
          type: 'bar',
          data: counts.reverse(),
          itemStyle: { color: '#9bbf8f', borderRadius: [0, 6, 6, 0] },
          barMaxWidth: 22,
        },
      ],
    })
  }
}

const handleChartResize = () => {
  trendChart?.resize()
  postPieChart?.resize()
  categoryBarChart?.resize()
}

const disposeCharts = () => {
  trendChart?.dispose()
  trendChart = null
  postPieChart?.dispose()
  postPieChart = null
  categoryBarChart?.dispose()
  categoryBarChart = null
}

// 切出看板时销毁图表实例；切回时若数据已就绪则重绘
watch(section, (key) => {
  if (key !== 'dashboard') {
    disposeCharts()
  } else if (dashboard.value) {
    nextTick(renderCharts)
  }
})

// 图表容器由 lay-card 插槽渲染，可能晚于父组件 nextTick；
// 容器 ref 就绪后再绘制，避免 echarts.init 拿到空容器
watch([trendChartRef, postPieChartRef, categoryBarChartRef], () => {
  if (trendChartRef.value && postPieChartRef.value && categoryBarChartRef.value && dashboard.value) {
    renderCharts()
  }
})

// ===== 概览统计 =====
const stats = ref({
  users_total: 0,
  posts_total: 0,
  pending_posts: 0,
  pending_comments: 0,
  banned_users: 0,
  pending_appeals: 0,
  unreviewed_resources: 0,
  unreviewed_requests: 0,
  pending_identity: 0,
})
const statsLoading = ref(false)
const statsError = ref('')

const STAT_CARDS = [
  { key: 'users_total', label: '用户总数', target: 'users' },
  { key: 'posts_total', label: '已发布帖子', target: 'posts', source: 'posts' },
  { key: 'pending_posts', label: '待审核帖子', target: 'posts', source: 'posts' },
  { key: 'pending_comments', label: '待审核评论', target: 'posts', source: 'comments' },
  { key: 'unreviewed_resources', label: '待审资源', target: 'posts', source: 'resources' },
  { key: 'unreviewed_requests', label: '待审求番', target: 'posts', source: 'requests' },
  { key: 'pending_identity', label: '待审身份申请', target: 'identity' },
  { key: 'banned_users', label: '封禁用户', target: 'users' },
  { key: 'pending_appeals', label: '待处理申诉', target: 'appeals' },
]

const loadStats = async () => {
  statsLoading.value = true
  statsError.value = ''
  try {
    const res = await adminApi.getStats()
    if (res.code === 0) {
      stats.value = res.data || {}
    } else {
      statsError.value = res.message || '概览加载失败'
    }
  } catch (err) {
    statsError.value = err.message || '概览加载失败'
  } finally {
    statsLoading.value = false
  }
}

// ===== 内容审查：多来源 =====
const REVIEW_SOURCES = [
  { key: 'posts', label: '帖子' },
  { key: 'comments', label: '评论审核' },
  { key: 'resources', label: '资源分享' },
  { key: 'requests', label: '番剧库求番' },
  { key: 'recommendations', label: '番剧推荐' },
]

const reviewSource = ref('posts')

const createModerationState = () => ({
  items: [],
  total: 0,
  page: 1,
  keyword: '',
  // 评审状态：0=未评审（默认） 1=已评审
  reviewed: '0',
  // 评审结果：''=全部 1=推荐 2=打回 3=封禁
  reviewStatus: '',
  loading: false,
  error: '',
})

const moderation = reactive({
  posts: createModerationState(),
  comments: createModerationState(),
  resources: createModerationState(),
  requests: createModerationState(),
  recommendations: createModerationState(),
})

const MODERATION_API = {
  posts: {
    list: (params) => adminApi.getPosts({ ...params, status: 'all' }),
    review: (id, data) => adminApi.reviewPost(id, data),
    unit: '篇',
    empty: '暂无符合条件的帖子',
    keywordPlaceholder: '搜索帖子标题或作者昵称',
  },
  comments: {
    list: (params) => adminApi.getComments(params),
    review: (id, data) => adminApi.reviewComment(id, data),
    unit: '条',
    empty: '暂无符合条件的评论',
    keywordPlaceholder: '搜索评论内容、作者昵称或用户名',
  },
  resources: {
    list: (params) => adminApi.getResources(params),
    review: (id, data) => adminApi.reviewResource(id, data),
    unit: '条',
    empty: '暂无符合条件的资源',
    keywordPlaceholder: '搜索资源标题、分享者昵称或用户名',
  },
  requests: {
    list: (params) => adminApi.getAnimeRequests(params),
    review: (id, data) => adminApi.reviewAnimeRequest(id, data),
    unit: '条',
    empty: '暂无符合条件的求番',
    keywordPlaceholder: '搜索番名或发起人',
  },
  recommendations: {
    list: (params) => adminApi.getRecommendations(params),
    review: (id, data) => adminApi.reviewRecommendation(id, data),
    unit: '条',
    empty: '暂无符合条件的番剧推荐',
    keywordPlaceholder: '搜索番名或推荐人',
  },
}

const activeModeration = computed(() => moderation[reviewSource.value])
const activeMeta = computed(() => MODERATION_API[reviewSource.value])

const REVIEW_META = {
  0: { label: '正常', className: '' },
  1: { label: '推荐', className: 'status-tag--recommend' },
  2: { label: '打回', className: 'status-tag--reject' },
  3: { label: '封禁', className: 'status-tag--ban' },
  4: { label: '待审核', className: 'status-tag--pending' },
}

// 审查结果筛选：帖子/评论的「正常」是已处理状态；资源/求番/推荐的 0 表示未评审，不提供该选项
const REVIEW_RESULT_TABS = computed(() => {
  const tabs = [
    { value: '', label: '全部结果' },
    { value: '1', label: '推荐' },
    { value: '2', label: '打回' },
    { value: '3', label: '封禁' },
  ]
  if (reviewSource.value === 'posts' || reviewSource.value === 'comments') {
    tabs.splice(1, 0, { value: '0', label: '正常' })
  }
  return tabs
})

const reviewLabel = (status) => REVIEW_META[status]?.label || '未评审'
const reviewTagClass = (status) => REVIEW_META[status]?.className || ''

const VISIBILITY_LABELS = {
  0: '所有同好',
  1: '仅管理员与特殊身份',
  2: '仅自己',
}

const visibilityLabel = (value) => VISIBILITY_LABELS[value] || VISIBILITY_LABELS[0]

const actionLabel = (action) => {
  if (reviewSource.value === 'requests') {
    if (action === 'recommend') return '收录'
    if (action === 'restore') return '恢复待收录'
  }
  return { approve: '通过', recommend: '推荐', reject: '打回', ban: '封禁', restore: '恢复' }[action]
}

const loadModeration = async (key = reviewSource.value, page) => {
  const state = moderation[key]
  const targetPage = page || state.page
  state.loading = true
  state.error = ''
  try {
    const params = {
      page: targetPage,
      page_size: PAGE_SIZE,
      reviewed: state.reviewed,
      q: state.keyword.trim(),
    }
    // 仅「已评审」时启用评审结果筛选；未评审时不发送该条件
    if (state.reviewed === '1' && state.reviewStatus !== '') {
      params.review_status = Number(state.reviewStatus)
    }

    const res = await MODERATION_API[key].list(params)
    if (res.code === 0) {
      state.items = res.data.list || []
      state.total = res.data.total || 0
      state.page = res.data.page || targetPage
    } else {
      state.error = res.message || '加载失败'
    }
  } catch (err) {
    state.error = err.message || '加载失败，请稍后重试'
  } finally {
    state.loading = false
  }
}

const switchReviewSource = (key) => {
  if (reviewSource.value === key) return
  reviewSource.value = key
  const state = moderation[key]
  if (state.items.length === 0 && !state.loading) {
    loadModeration(key, 1)
  }
}

const searchModeration = () => loadModeration(reviewSource.value, 1)

// 评审状态切换：切到「未评审」时清空并隐藏评审结果筛选
const switchReviewed = (value) => {
  const state = activeModeration.value
  if (state.reviewed === value) return
  state.reviewed = value
  state.reviewStatus = ''
  loadModeration(reviewSource.value, 1)
}

const switchReviewResult = (value) => {
  const state = activeModeration.value
  if (state.reviewStatus === value) return
  state.reviewStatus = value
  loadModeration(reviewSource.value, 1)
}

const onModerationPageChange = (payload) => {
  loadModeration(reviewSource.value, resolvePage(payload, activeModeration.value.page))
}

const reviewItem = async (item, action) => {
  let reason = ''
  if (action === 'ban' || action === 'reject') {
    const label = action === 'ban' ? '封禁' : '打回'
    const input = await window.$ghibli?.showPrompt({
      title: `请输入${label}理由`,
      placeholder: `${label}必须填写理由，最多 200 字`,
    })
    if (input === null || input === undefined) return
    reason = input
    if (!reason) {
      toast('warning', '缺少理由', `${label}必须填写理由`)
      return
    }
  }

  try {
    const res = await MODERATION_API[reviewSource.value].review(item.id, { action, reason })
    if (res.code === 0) {
      toast('success', '操作成功', res.message || '评审结果已更新')
      await loadModeration(reviewSource.value, activeModeration.value.page)
      loadStats()
    } else {
      toast('error', '操作失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '操作失败', err.message || '请稍后重试')
  }
}

// ===== 番剧库管理 =====
const animes = reactive({
  items: [],
  total: 0,
  page: 1,
  keyword: '',
  loading: false,
  error: '',
})

const animeFormOpen = ref(false)
const editingAnimeId = ref(null)
const animeSubmitting = ref(false)
const animeFormError = ref('')
const animeForm = reactive({
  title: '',
  category: '',
  cover: '',
  description: '',
  link: '',
})

const resetAnimeForm = () => {
  animeForm.title = ''
  animeForm.category = ''
  animeForm.cover = ''
  animeForm.description = ''
  animeForm.link = ''
}

const openAnimeForm = (item = null) => {
  animeFormError.value = ''
  editingAnimeId.value = item ? item.id : null
  if (item) {
    animeForm.title = item.title || ''
    animeForm.category = item.category || ''
    animeForm.cover = item.cover || ''
    animeForm.description = item.description || ''
    animeForm.link = item.link || ''
  } else {
    resetAnimeForm()
  }
  animeFormOpen.value = true
}

const closeAnimeForm = () => {
  animeFormOpen.value = false
  animeFormError.value = ''
  editingAnimeId.value = null
}

const loadAnimes = async (page = animes.page) => {
  animes.loading = true
  animes.error = ''
  try {
    const res = await animeApi.getList({
      page,
      page_size: PAGE_SIZE,
      q: animes.keyword.trim(),
    })
    if (res.code === 0) {
      animes.items = res.data.list || []
      animes.total = res.data.total || 0
      animes.page = res.data.page || page
    } else {
      animes.error = res.message || '加载失败'
    }
  } catch (err) {
    animes.error = err.message || '加载失败，请稍后重试'
  } finally {
    animes.loading = false
  }
}

const searchAnimes = () => loadAnimes(1)

const onAnimesPageChange = (payload) => {
  loadAnimes(resolvePage(payload, animes.page))
}

const submitAnime = async () => {
  if (animeSubmitting.value) return
  animeFormError.value = ''
  const title = animeForm.title.trim()
  const link = animeForm.link.trim()
  if (!title) {
    animeFormError.value = '请填写番剧名称'
    return
  }
  if (link && !/^https?:\/\/\S+$/i.test(link)) {
    animeFormError.value = '番剧链接需为 http:// 或 https:// 开头的有效地址'
    return
  }

  const payload = {
    title,
    category: animeForm.category.trim(),
    cover: animeForm.cover.trim(),
    description: animeForm.description.trim(),
    link,
  }

  animeSubmitting.value = true
  const isEdit = Boolean(editingAnimeId.value)
  try {
    const res = isEdit
      ? await animeApi.update(editingAnimeId.value, payload)
      : await animeApi.create(payload)
    if (res.code === 0) {
      toast('success', '保存成功', res.message || '番剧库已更新')
      closeAnimeForm()
      await loadAnimes(isEdit ? animes.page : 1)
    } else {
      animeFormError.value = res.message || '保存失败，请稍后重试'
    }
  } catch (err) {
    animeFormError.value = err.message || '保存失败，请稍后重试'
  } finally {
    animeSubmitting.value = false
  }
}

const deleteAnime = async (item) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '删除番剧',
    message: `确定从番剧库删除「${item.title}」吗？该操作不可撤销。`,
  })
  if (!confirmed) return

  try {
    const res = await animeApi.remove(item.id)
    if (res.code === 0) {
      toast('success', '已删除', res.message || '番剧已从番剧库移除')
      await loadAnimes(animes.page)
    } else {
      toast('error', '删除失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '删除失败', err.message || '请稍后重试')
  }
}

// ===== 身份申请 =====
const identityApps = reactive({
  items: [],
  total: 0,
  page: 1,
  keyword: '',
  status: '',
  loading: false,
  error: '',
})

const IDENTITY_LABELS = {
  anime_master: '番剧大佬',
  resource_master: '我就是资源',
}

const identityLabel = (type) => IDENTITY_LABELS[type] || '特殊身份'

const identityStatusMeta = (status) => {
  if (status === 1) return { label: '已通过', className: '' }
  if (status === 2) return { label: '已驳回', className: 'status-tag--reject' }
  return { label: '待审批', className: 'status-tag--recommend' }
}

const loadIdentityApps = async (page = identityApps.page) => {
  identityApps.loading = true
  identityApps.error = ''
  try {
    const params = {
      page,
      page_size: PAGE_SIZE,
      q: identityApps.keyword.trim(),
    }
    if (identityApps.status !== '') params.status = Number(identityApps.status)

    const res = await adminApi.getIdentityApplications(params)
    if (res.code === 0) {
      identityApps.items = res.data.list || []
      identityApps.total = res.data.total || 0
      identityApps.page = res.data.page || page
    } else {
      identityApps.error = res.message || '加载失败'
    }
  } catch (err) {
    identityApps.error = err.message || '加载失败，请稍后重试'
  } finally {
    identityApps.loading = false
  }
}

const searchIdentityApps = () => loadIdentityApps(1)

const onIdentityPageChange = (payload) => {
  loadIdentityApps(resolvePage(payload, identityApps.page))
}

const handleIdentityApp = async (app, action) => {
  const input = await window.$ghibli?.showPrompt({
    title: action === 'accept' ? `通过「${identityLabel(app.identity_type)}」申请` : '驳回身份申请',
    placeholder: '可填写审批备注（选填）',
  })
  if (input === null || input === undefined) return

  try {
    const res = await adminApi.handleIdentityApplication(app.id, { action, note: input })
    if (res.code === 0) {
      toast('success', '处理成功', res.message || '申请已处理')
      await loadIdentityApps(identityApps.page)
      loadStats()
      loadNotifCount()
    } else {
      toast('error', '处理失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '处理失败', err.message || '请稍后重试')
  }
}

// ===== 用户管理 =====
const adminUsers = ref([])
const usersLoading = ref(false)
const usersError = ref('')
const usersPage = ref(1)
const usersTotal = ref(0)
const userKeyword = ref('')
const userStatus = ref('')

const userStatusMeta = (status) => {
  if (status === 2) return { label: '已封禁', className: 'status-tag--ban' }
  if (status === 0) return { label: '已禁用', className: 'status-tag--pending' }
  return { label: '正常', className: '' }
}

const loadAdminUsers = async (page = usersPage.value) => {
  usersLoading.value = true
  usersError.value = ''
  try {
    const params = {
      page,
      page_size: PAGE_SIZE,
      q: userKeyword.value.trim(),
    }
    if (userStatus.value !== '') params.status = Number(userStatus.value)

    const res = await adminApi.getUsers(params)
    if (res.code === 0) {
      adminUsers.value = res.data.list || []
      usersTotal.value = res.data.total || 0
      usersPage.value = res.data.page || page
    } else {
      usersError.value = res.message || '加载失败'
    }
  } catch (err) {
    usersError.value = err.message || '加载失败，请稍后重试'
  } finally {
    usersLoading.value = false
  }
}

const searchUsers = () => loadAdminUsers(1)

const onUsersPageChange = (payload) => {
  loadAdminUsers(resolvePage(payload, usersPage.value))
}

const banUser = async (user) => {
  const input = await window.$ghibli?.showPrompt({
    title: '请输入封禁理由（必填）',
    placeholder: '请说明封禁原因，用户可在申诉页看到该理由',
  })
  if (input === null || input === undefined) return
  const reason = input
  if (!reason) {
    toast('warning', '缺少理由', '封禁账号必须填写理由')
    return
  }

  try {
    const res = await adminApi.banUser(user.id, { reason })
    if (res.code === 0) {
      toast('success', '已封禁', res.message || '该账号已被封禁')
      await loadAdminUsers(usersPage.value)
      loadStats()
    } else {
      toast('error', '封禁失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '封禁失败', err.message || '请稍后重试')
  }
}

const unbanUser = async (user) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '解除封禁',
    message: `确定解除「${user.nickname || user.username}」的封禁吗？`,
  })
  if (!confirmed) return

  try {
    const res = await adminApi.unbanUser(user.id)
    if (res.code === 0) {
      toast('success', '已解封', res.message || '该账号已恢复正常')
      await loadAdminUsers(usersPage.value)
      loadStats()
    } else {
      toast('error', '解封失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '解封失败', err.message || '请稍后重试')
  }
}

const disableUser = async (user) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '禁用账号',
    message: `确定禁用「${user.nickname || user.username}」吗？禁用后该账号将无法登录。`,
  })
  if (!confirmed) return

  try {
    const res = await adminApi.disableUser(user.id)
    if (res.code === 0) {
      toast('success', '已禁用', res.message || '该账号已禁用')
      await loadAdminUsers(usersPage.value)
      loadStats()
    } else {
      toast('error', '禁用失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '禁用失败', err.message || '请稍后重试')
  }
}

const enableUser = async (user) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '启用账号',
    message: `确定启用「${user.nickname || user.username}」吗？启用后该账号可正常登录。`,
  })
  if (!confirmed) return

  try {
    const res = await adminApi.enableUser(user.id)
    if (res.code === 0) {
      toast('success', '已启用', res.message || '该账号已恢复登录')
      await loadAdminUsers(usersPage.value)
      loadStats()
    } else {
      toast('error', '启用失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '启用失败', err.message || '请稍后重试')
  }
}

// ===== 申诉处理 =====
const appeals = ref([])
const appealsLoading = ref(false)
const appealsError = ref('')
const appealsPage = ref(1)
const appealsTotal = ref(0)
const appealStatus = ref('')
const appealKeyword = ref('')

const appealStatusMeta = (status) => {
  if (status === 1) return { label: '已通过', className: '' }
  if (status === 2) return { label: '已驳回', className: 'status-tag--reject' }
  return { label: '待处理', className: 'status-tag--recommend' }
}

const loadAdminAppeals = async (page = appealsPage.value) => {
  appealsLoading.value = true
  appealsError.value = ''
  try {
    const params = { page, page_size: PAGE_SIZE, q: appealKeyword.value.trim() }
    if (appealStatus.value !== '') params.status = Number(appealStatus.value)

    const res = await adminApi.getAppeals(params)
    if (res.code === 0) {
      appeals.value = res.data.list || []
      appealsTotal.value = res.data.total || 0
      appealsPage.value = res.data.page || page
    } else {
      appealsError.value = res.message || '加载失败'
    }
  } catch (err) {
    appealsError.value = err.message || '加载失败，请稍后重试'
  } finally {
    appealsLoading.value = false
  }
}

const onAppealsPageChange = (payload) => {
  loadAdminAppeals(resolvePage(payload, appealsPage.value))
}

const searchAppeals = () => loadAdminAppeals(1)

const handleAppeal = async (appeal, action) => {
  // 处理备注选填，点取消则放弃本次操作
  const input = await window.$ghibli?.showPrompt({
    title: action === 'accept' ? '通过申诉' : '驳回申诉',
    placeholder: '可填写处理备注（选填）',
  })
  if (input === null || input === undefined) return

  try {
    const res = await adminApi.handleAppeal(appeal.id, { action, note: input })
    if (res.code === 0) {
      toast('success', '处理成功', res.message || '申诉已处理')
      await loadAdminAppeals(appealsPage.value)
      loadStats()
    } else {
      toast('error', '处理失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '处理失败', err.message || '请稍后重试')
  }
}

// ===== 公告管理 =====
const announcements = reactive({
  items: [],
  total: 0,
  page: 1,
  keyword: '',
  status: '',
  loading: false,
  error: '',
})

const announceFormOpen = ref(false)
const editingAnnouncementId = ref(null)
const announceSubmitting = ref(false)
const announceFormError = ref('')
const announceForm = reactive({ title: '', content: '', status: '1' })

const resetAnnounceForm = () => {
  announceForm.title = ''
  announceForm.content = ''
  announceForm.status = '1'
}

const openAnnounceForm = (item = null) => {
  announceFormError.value = ''
  editingAnnouncementId.value = item ? item.id : null
  if (item) {
    announceForm.title = item.title || ''
    announceForm.content = item.content || ''
    announceForm.status = String(item.status)
  } else {
    resetAnnounceForm()
  }
  announceFormOpen.value = true
}

const closeAnnounceForm = () => {
  announceFormOpen.value = false
  announceFormError.value = ''
  editingAnnouncementId.value = null
}

const loadAnnouncements = async (page = announcements.page) => {
  announcements.loading = true
  announcements.error = ''
  try {
    const params = {
      page,
      page_size: PAGE_SIZE,
      q: announcements.keyword.trim(),
    }
    if (announcements.status !== '') params.status = Number(announcements.status)

    const res = await adminApi.getAnnouncements(params)
    if (res.code === 0) {
      announcements.items = res.data.list || []
      announcements.total = res.data.total || 0
      announcements.page = res.data.page || page
    } else {
      announcements.error = res.message || '加载失败'
    }
  } catch (err) {
    announcements.error = err.message || '加载失败，请稍后重试'
  } finally {
    announcements.loading = false
  }
}

const searchAnnouncements = () => loadAnnouncements(1)

const onAnnouncementsPageChange = (payload) => {
  loadAnnouncements(resolvePage(payload, announcements.page))
}

const submitAnnouncement = async () => {
  if (announceSubmitting.value) return
  announceFormError.value = ''
  const title = announceForm.title.trim()
  const content = announceForm.content.trim()
  if (!title) {
    announceFormError.value = '请填写公告标题'
    return
  }
  if (!content) {
    announceFormError.value = '请填写公告内容'
    return
  }

  const isEdit = Boolean(editingAnnouncementId.value)
  const payload = isEdit
    ? { title, content }
    : { title, content, status: announceForm.status === '1' ? 1 : 0 }

  announceSubmitting.value = true
  try {
    const res = isEdit
      ? await adminApi.updateAnnouncement(editingAnnouncementId.value, payload)
      : await adminApi.createAnnouncement(payload)
    if (res.code === 0) {
      toast('success', '保存成功', res.message || '公告已保存')
      closeAnnounceForm()
      await loadAnnouncements(isEdit ? announcements.page : 1)
    } else {
      announceFormError.value = res.message || '保存失败，请稍后重试'
    }
  } catch (err) {
    announceFormError.value = err.message || '保存失败，请稍后重试'
  } finally {
    announceSubmitting.value = false
  }
}

const toggleAnnouncementStatus = async (item) => {
  const target = item.status === 1 ? 0 : 1
  try {
    const res = await adminApi.setAnnouncementStatus(item.id, target)
    if (res.code === 0) {
      toast('success', '操作成功', res.message || '公告状态已更新')
      await loadAnnouncements(announcements.page)
    } else {
      toast('error', '操作失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '操作失败', err.message || '请稍后重试')
  }
}

const deleteAnnouncement = async (item) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '删除公告',
    message: `确定删除公告「${item.title}」吗？删除后无法恢复。`,
  })
  if (!confirmed) return

  try {
    const res = await adminApi.removeAnnouncement(item.id)
    if (res.code === 0) {
      toast('success', '已删除', res.message || '公告已删除')
      await loadAnnouncements(announcements.page)
    } else {
      toast('error', '删除失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '删除失败', err.message || '请稍后重试')
  }
}

onMounted(() => {
  loadDashboard()
  loadNotifCount()
  window.addEventListener('resize', handleChartResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleChartResize)
  disposeCharts()
})
</script>

<template>
  <div class="page-wrap">
    <!-- 顶部 -->
    <section class="page-hero">
      <div class="hero-row">
        <div>
          <h1 class="page-title">管理后台</h1>
          <p class="page-sub">内容审查、番剧库、身份申请、用户封禁与申诉处理</p>
        </div>
        <div class="admin-hero-actions">
          <lay-button size="sm" @click="goNotifications">
            消息通知{{ notifCount > 0 ? `（${notifCount}）` : '' }}
          </lay-button>
          <div class="admin-who">
            <span class="avatar-circle">{{ adminName.charAt(0) }}</span>
            <span class="admin-who__text">
              <span class="muted admin-who__role">当前管理员</span>
              <strong class="admin-who__name">{{ adminName }}</strong>
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- 区块切换 -->
    <div class="page-toolbar section-toolbar">
      <div class="tab-row">
        <lay-button
          v-for="item in SECTION_TABS"
          :key="item.key"
          :type="section === item.key ? 'primary' : undefined"
          @click="switchSection(item.key)"
        >
          {{ item.label }}
        </lay-button>
      </div>
    </div>

    <lay-card>
      <!-- ===== 看板 ===== -->
      <template v-if="section === 'dashboard'">
        <div v-if="dashboardLoading" class="loading-box">正在加载看板…</div>

        <div v-else-if="dashboardError" class="empty-box">
          <p class="danger-text">{{ dashboardError }}</p>
          <lay-button type="primary" @click="loadDashboard">重试</lay-button>
        </div>

        <template v-else-if="dashboard">
          <!-- 全局预览统计 -->
          <div class="stat-grid admin-stats">
            <div
              v-for="card in STAT_CARDS"
              :key="card.key"
              class="stat-card"
              @click="switchSection(card.target, card.source)"
            >
              <div class="stat-card__value">{{ dashboard.stats?.[card.key] ?? 0 }}</div>
              <div class="stat-card__label">{{ card.label }}</div>
            </div>
          </div>

          <!-- 待办事项 -->
          <div class="todo-grid">
            <div
              v-for="todo in dashboard.todos"
              :key="todo.type"
              class="todo-card"
              @click="switchSection(todo.target, todo.source)"
            >
              <div class="todo-card__count" :class="{ 'todo-card__count--hot': todo.count > 0 }">
                {{ todo.count }}
              </div>
              <div class="todo-card__label">{{ todo.label }}</div>
              <div class="todo-card__action">去处理 →</div>
            </div>
          </div>

          <!-- ECharts 全局预览 -->
          <div class="chart-grid">
            <lay-card class="chart-card chart-card--wide">
              <h3 class="chart-title">近 14 天内容趋势</h3>
              <div ref="trendChartRef" class="chart-box chart-box--lg"></div>
            </lay-card>
            <lay-card class="chart-card">
              <h3 class="chart-title">帖子审查状态分布</h3>
              <div ref="postPieChartRef" class="chart-box"></div>
            </lay-card>
            <lay-card class="chart-card">
              <h3 class="chart-title">帖子分类排行</h3>
              <div ref="categoryBarChartRef" class="chart-box"></div>
            </lay-card>
          </div>
        </template>
      </template>

      <!-- ===== 内容审查 ===== -->
      <template v-else-if="section === 'posts'">
        <div class="tab-row source-tabs">
          <lay-button
            v-for="item in REVIEW_SOURCES"
            :key="item.key"
            :type="reviewSource === item.key ? 'primary' : undefined"
            @click="switchReviewSource(item.key)"
          >
            {{ item.label }}
          </lay-button>
        </div>

        <div class="review-filter-groups">
          <div class="tab-group">
            <span class="tab-group__label">审查状态</span>
            <div class="tab-row">
              <lay-button
                size="sm"
                :type="activeModeration.reviewed === '0' ? 'primary' : undefined"
                @click="switchReviewed('0')"
              >
                待审核
              </lay-button>
              <lay-button
                size="sm"
                :type="activeModeration.reviewed === '1' ? 'primary' : undefined"
                @click="switchReviewed('1')"
              >
                已处理
              </lay-button>
            </div>
          </div>

          <!-- 待审核时不显示审查结果筛选 -->
          <div v-if="activeModeration.reviewed === '1'" class="tab-group">
            <span class="tab-group__label">评审结果</span>
            <div class="tab-row">
              <lay-button
                v-for="item in REVIEW_RESULT_TABS"
                :key="item.value"
                size="sm"
                :type="activeModeration.reviewStatus === item.value ? 'primary' : undefined"
                @click="switchReviewResult(item.value)"
              >
                {{ item.label }}
              </lay-button>
            </div>
          </div>
        </div>

        <div class="admin-filters">
          <lay-input
            v-model="activeModeration.keyword"
            style="width: 240px"
            :placeholder="activeMeta.keywordPlaceholder"
            @keyup.enter="searchModeration"
          />
          <lay-button type="primary" @click="searchModeration">搜索</lay-button>
          <span class="page-toolbar__spacer"></span>
          <span class="muted filter-count">
            共 {{ activeModeration.total }} {{ activeMeta.unit }}
          </span>
        </div>

        <div v-if="activeModeration.loading" class="loading-box">正在加载内容…</div>

        <div v-else-if="activeModeration.error" class="empty-box">
          <p class="danger-text">{{ activeModeration.error }}</p>
          <lay-button type="primary" @click="loadModeration(reviewSource, activeModeration.page)">
            重试
          </lay-button>
        </div>

        <div v-else-if="!activeModeration.items.length" class="empty-box">
          <lay-empty :description="activeMeta.empty" />
        </div>

        <template v-else>
          <div v-for="item in activeModeration.items" :key="item.id" class="list-row">
            <div class="list-row__main">
              <!-- 帖子 -->
              <template v-if="reviewSource === 'posts'">
                <h3 class="list-row__title">{{ item.title || '（无标题）' }}</h3>
                <div class="meta">
                  <span>作者：{{ item.author_nickname || item.author_username || '未知' }}</span>
                  <span v-if="item.category">{{ item.category }}</span>
                  <span v-if="item.publish_time">发布于 {{ item.publish_time }}</span>
                  <span v-else>创建于 {{ item.create_time }}</span>
                  <span>{{ item.like_count || 0 }} 赞 · {{ item.reply_count || 0 }} 评论</span>
                </div>
              </template>

              <!-- 评论审核 -->
              <template v-else-if="reviewSource === 'comments'">
                <h3 class="list-row__title">评论 #{{ item.id }}</h3>
                <p class="item-desc">
                  <span v-if="item.post_title">在「{{ item.post_title }}」下：</span>{{ item.content }}
                </p>
                <div class="meta">
                  <span>作者：{{ item.author_nickname || item.author_username || '未知' }}</span>
                  <span>{{ item.create_time }}</span>
                </div>
              </template>

              <!-- 资源分享 -->
              <template v-else-if="reviewSource === 'resources'">
                <h3 class="list-row__title">{{ item.title }}</h3>
                <p v-if="item.description" class="item-desc">{{ item.description }}</p>
                <div class="meta">
                  <span>分享者：{{ item.author_nickname || item.author_username || '未知' }}</span>
                  <span>{{ item.create_time }}</span>
                  <span :class="['status-tag', item.visibility === 0 ? '' : 'status-tag--recommend']">
                    {{ visibilityLabel(item.visibility) }}
                  </span>
                  <a v-if="item.link" class="inline-link" @click="openLink(item.link)">查看链接</a>
                </div>
              </template>

              <!-- 番剧库求番 -->
              <template v-else-if="reviewSource === 'requests'">
                <h3 class="list-row__title">求番：{{ item.anime_name }}</h3>
                <p v-if="item.reason" class="item-desc">求番理由：{{ item.reason }}</p>
                <div class="meta">
                  <span>发起人：{{ item.author_nickname || item.author_username || '未知' }}</span>
                  <span>{{ item.create_time }}</span>
                  <span :class="['status-tag', item.status === 1 ? 'status-tag--recommend' : '']">
                    {{ item.status === 1 ? '已收录' : '待收录' }}
                  </span>
                </div>
              </template>

              <!-- 番剧推荐 -->
              <template v-else>
                <h3 class="list-row__title">推荐：{{ item.anime_name }}</h3>
                <p v-if="item.reason" class="item-desc">推荐理由：{{ item.reason }}</p>
                <div class="meta">
                  <span>推荐人：{{ item.author_nickname || item.author_username || '未知' }}</span>
                  <span>{{ item.create_time }}</span>
                  <a v-if="item.link" class="inline-link" @click="openLink(item.link)">查看链接</a>
                </div>
              </template>

              <div class="tag-row review-row">
                <span class="review-label">审查结果：</span>
                <span :class="['status-tag', reviewTagClass(item.review_status)]">
                  {{ reviewLabel(item.review_status) }}
                </span>
                <span v-if="item.review_note" class="review-note">理由：{{ item.review_note }}</span>
              </div>
            </div>

            <div class="row-actions">
              <lay-button
                v-if="reviewSource === 'posts' || reviewSource === 'comments'"
                size="xs"
                type="primary"
                @click="reviewItem(item, 'approve')"
              >
                {{ actionLabel('approve') }}
              </lay-button>
              <lay-button size="xs" @click="reviewItem(item, 'recommend')">
                {{ actionLabel('recommend') }}
              </lay-button>
              <lay-button size="xs" type="warm" @click="reviewItem(item, 'reject')">
                {{ actionLabel('reject') }}
              </lay-button>
              <lay-button size="xs" type="danger" @click="reviewItem(item, 'ban')">
                {{ actionLabel('ban') }}
              </lay-button>
              <lay-button size="xs" type="normal" @click="reviewItem(item, 'restore')">
                {{ actionLabel('restore') }}
              </lay-button>
            </div>
          </div>

          <div v-if="activeModeration.total > 0" class="pagination-wrap">
            <lay-page
              v-model="activeModeration.page"
              :total="activeModeration.total"
              :limit="PAGE_SIZE"
              :layout="PAGE_LAYOUT"
              @change="onModerationPageChange"
            />
          </div>
        </template>
      </template>

      <!-- ===== 番剧库管理 ===== -->
      <template v-else-if="section === 'animes'">
        <div class="admin-filters">
          <lay-input
            v-model="animes.keyword"
            style="width: 240px"
            placeholder="搜索番剧名称或分类"
            @keyup.enter="searchAnimes"
          />
          <lay-button type="primary" @click="searchAnimes">搜索</lay-button>
          <lay-button type="warm" @click="openAnimeForm()">新增番剧</lay-button>
          <span class="page-toolbar__spacer"></span>
          <span class="muted filter-count">共 {{ animes.total }} 部</span>
        </div>

        <div v-if="animeFormOpen" class="sub-form">
          <div class="sub-form__head">
            <h2 class="sub-form__title">{{ editingAnimeId ? '编辑番剧' : '新增番剧' }}</h2>
            <lay-button size="sm" @click="closeAnimeForm">收起</lay-button>
          </div>

          <lay-form label-position="top" @submit="submitAnime">
            <div v-if="animeFormError" class="form-error" role="alert">{{ animeFormError }}</div>

            <div class="form-grid">
              <lay-form-item label="番剧名称" required>
                <lay-input v-model="animeForm.title" placeholder="例如：千与千寻" maxlength="200" allow-clear />
              </lay-form-item>
              <lay-form-item label="分类">
                <lay-input v-model="animeForm.category" placeholder="例如：剧场版 / 奇幻" maxlength="30" allow-clear />
              </lay-form-item>
            </div>

            <lay-form-item label="封面地址（选填）">
              <lay-input v-model="animeForm.cover" placeholder="https:// 开头的图片地址" maxlength="255" allow-clear />
            </lay-form-item>

            <lay-form-item label="番剧链接（选填）">
              <lay-input v-model="animeForm.link" placeholder="https:// 开头的番剧地址" maxlength="500" allow-clear />
            </lay-form-item>

            <lay-form-item label="简介（选填）">
              <lay-textarea
                v-model="animeForm.description"
                :rows="4"
                :maxlength="5000"
                show-count
                placeholder="一句话介绍这部番，方便同好判断要不要追"
              />
            </lay-form-item>

            <div class="form-actions">
              <lay-button type="primary" native-type="submit" :loading="animeSubmitting">
                {{ animeSubmitting ? '保存中...' : '保存' }}
              </lay-button>
              <lay-button native-type="button" @click="closeAnimeForm">取消</lay-button>
            </div>
          </lay-form>
        </div>

        <div v-if="animes.loading" class="loading-box">正在加载番剧库…</div>

        <div v-else-if="animes.error" class="empty-box">
          <p class="danger-text">{{ animes.error }}</p>
          <lay-button type="primary" @click="loadAnimes(animes.page)">重试</lay-button>
        </div>

        <div v-else-if="!animes.items.length" class="empty-box">
          <lay-empty description="番剧库还没有内容，点「新增番剧」添加第一部" />
        </div>

        <template v-else>
          <div v-for="item in animes.items" :key="item.id" class="list-row">
            <img v-if="item.cover" :src="item.cover" class="anime-cover" alt="" />
            <div class="list-row__main">
              <h3 class="list-row__title">{{ item.title }}</h3>
              <div class="meta">
                <span v-if="item.category">{{ item.category }}</span>
                <span>{{ item.create_time }}</span>
                <a v-if="item.link" class="inline-link" @click="openLink(item.link)">查看链接</a>
              </div>
              <p v-if="item.description" class="item-desc">{{ item.description }}</p>
            </div>
            <div class="row-actions">
              <lay-button size="xs" @click="openAnimeForm(item)">编辑</lay-button>
              <lay-button size="xs" type="danger" @click="deleteAnime(item)">删除</lay-button>
            </div>
          </div>

          <div v-if="animes.total > 0" class="pagination-wrap">
            <lay-page
              v-model="animes.page"
              :total="animes.total"
              :limit="PAGE_SIZE"
              :layout="PAGE_LAYOUT"
              @change="onAnimesPageChange"
            />
          </div>
        </template>
      </template>

      <!-- ===== 身份申请 ===== -->
      <template v-else-if="section === 'identity'">
        <div class="admin-filters">
          <lay-input
            v-model="identityApps.keyword"
            style="width: 240px"
            placeholder="搜索用户名或昵称"
            @keyup.enter="searchIdentityApps"
          />
          <lay-select
            v-model="identityApps.status"
            :allow-clear="false"
            style="width: 150px"
            @change="searchIdentityApps"
          >
            <lay-select-option label="全部申请" value="" />
            <lay-select-option label="待审批" value="0" />
            <lay-select-option label="已通过" value="1" />
            <lay-select-option label="已驳回" value="2" />
          </lay-select>
          <lay-button type="primary" @click="searchIdentityApps">搜索</lay-button>
          <span class="page-toolbar__spacer"></span>
          <span class="muted filter-count">共 {{ identityApps.total }} 条</span>
        </div>

        <div v-if="identityApps.loading" class="loading-box">正在加载身份申请…</div>

        <div v-else-if="identityApps.error" class="empty-box">
          <p class="danger-text">{{ identityApps.error }}</p>
          <lay-button type="primary" @click="loadIdentityApps(identityApps.page)">重试</lay-button>
        </div>

        <div v-else-if="!identityApps.items.length" class="empty-box">
          <lay-empty description="暂无符合条件的身份申请" />
        </div>

        <template v-else>
          <div v-for="app in identityApps.items" :key="app.id" class="list-row">
            <span class="avatar-circle">{{ (app.nickname || app.username || '?').charAt(0) }}</span>
            <div class="list-row__main">
              <h3 class="list-row__title">
                {{ app.nickname || app.username }}
                <span class="status-tag status-tag--recommend">{{ identityLabel(app.identity_type) }}</span>
              </h3>
              <div class="meta">
                <span>@{{ app.username }}</span>
                <span>提交于 {{ app.create_time || '——' }}</span>
                <span :class="['status-tag', identityStatusMeta(app.status).className]">
                  {{ identityStatusMeta(app.status).label }}
                </span>
                <span v-if="app.handle_time">处理于 {{ app.handle_time }}</span>
              </div>
              <div class="meta">
                <span>有效番剧推荐：{{ app.anime_valid || 0 }} 部</span>
                <span>有效资源分享：{{ app.resource_valid || 0 }} 项</span>
                <span v-if="app.identity">已有身份：{{ app.identity }}</span>
              </div>
              <p class="appeal-text">申请说明：{{ app.reason || '未填写' }}</p>
              <p v-if="app.admin_note" class="appeal-text">审批备注：{{ app.admin_note }}</p>
            </div>

            <div v-if="app.status === 0" class="row-actions">
              <lay-button size="xs" type="primary" @click="handleIdentityApp(app, 'accept')">
                通过
              </lay-button>
              <lay-button size="xs" type="danger" @click="handleIdentityApp(app, 'reject')">
                驳回
              </lay-button>
            </div>
          </div>

          <div v-if="identityApps.total > 0" class="pagination-wrap">
            <lay-page
              v-model="identityApps.page"
              :total="identityApps.total"
              :limit="PAGE_SIZE"
              :layout="PAGE_LAYOUT"
              @change="onIdentityPageChange"
            />
          </div>
        </template>
      </template>

      <!-- ===== 用户管理 ===== -->
      <template v-else-if="section === 'users'">
        <div class="admin-filters">
          <lay-input
            v-model="userKeyword"
            style="width: 240px"
            placeholder="搜索用户名、昵称或邮箱"
            @keyup.enter="searchUsers"
          />
          <lay-select
            v-model="userStatus"
            :allow-clear="false"
            style="width: 150px"
            @change="searchUsers"
          >
            <lay-select-option label="全部状态" value="" />
            <lay-select-option label="正常" value="1" />
            <lay-select-option label="封禁" value="2" />
            <lay-select-option label="禁用" value="0" />
          </lay-select>
          <lay-button type="primary" @click="searchUsers">搜索</lay-button>
          <span class="page-toolbar__spacer"></span>
          <span class="muted filter-count">共 {{ usersTotal }} 人</span>
        </div>

        <div v-if="usersLoading" class="loading-box">正在加载用户…</div>

        <div v-else-if="usersError" class="empty-box">
          <p class="danger-text">{{ usersError }}</p>
          <lay-button type="primary" @click="loadAdminUsers(usersPage)">重试</lay-button>
        </div>

        <div v-else-if="!adminUsers.length" class="empty-box">
          <lay-empty description="暂无符合条件的用户" />
        </div>

        <template v-else>
          <div v-for="user in adminUsers" :key="user.id" class="list-row">
            <span class="avatar-circle">{{ (user.nickname || user.username || '?').charAt(0) }}</span>
            <div class="list-row__main">
              <h3 class="list-row__title">
                {{ user.nickname || user.username }}
                <span v-if="user.role === 1" class="status-tag">管理员</span>
              </h3>
              <div class="meta">
                <span>@{{ user.username }}</span>
                <span>{{ user.email || '未绑定邮箱' }}</span>
                <span>{{ user.posts_count || 0 }} 篇帖子</span>
                <span>{{ user.followers_count || 0 }} 粉丝</span>
                <span>注册于 {{ user.create_time || '——' }}</span>
              </div>
              <div class="tag-row review-row">
                <span :class="['status-tag', userStatusMeta(user.status).className]">
                  {{ userStatusMeta(user.status).label }}
                </span>
                <span v-if="user.status === 2 && user.ban_reason" class="review-note">
                  封禁理由：{{ user.ban_reason }}
                  <template v-if="user.ban_time">（{{ user.ban_time }}）</template>
                </span>
              </div>
            </div>

            <div class="row-actions">
              <template v-if="user.status === 2">
                <lay-button size="xs" type="primary" @click="unbanUser(user)">
                  解封
                </lay-button>
              </template>
              <template v-else-if="user.role !== 1">
                <lay-button
                  v-if="user.status === 0"
                  size="xs"
                  type="primary"
                  @click="enableUser(user)"
                >
                  启用
                </lay-button>
                <template v-else>
                  <lay-button size="xs" type="warm" @click="disableUser(user)">
                    禁用
                  </lay-button>
                  <lay-button size="xs" type="danger" @click="banUser(user)">
                    封禁
                  </lay-button>
                </template>
              </template>
              <span v-else class="muted">管理员账号</span>
            </div>
          </div>

          <div v-if="usersTotal > 0" class="pagination-wrap">
            <lay-page
              v-model="usersPage"
              :total="usersTotal"
              :limit="PAGE_SIZE"
              :layout="PAGE_LAYOUT"
              @change="onUsersPageChange"
            />
          </div>
        </template>
      </template>

      <!-- ===== 申诉处理 ===== -->
      <template v-else-if="section === 'appeals'">
        <div class="admin-filters">
          <lay-input
            v-model="appealKeyword"
            style="width: 240px"
            placeholder="搜索用户、昵称或申诉理由"
            @keyup.enter="searchAppeals"
          />
          <lay-select
            v-model="appealStatus"
            :allow-clear="false"
            style="width: 170px"
            @change="loadAdminAppeals(1)"
          >
            <lay-select-option label="全部申诉" value="" />
            <lay-select-option label="待处理" value="0" />
            <lay-select-option label="已通过" value="1" />
            <lay-select-option label="已驳回" value="2" />
          </lay-select>
          <lay-button type="primary" @click="searchAppeals">搜索</lay-button>
          <span class="page-toolbar__spacer"></span>
          <span class="muted filter-count">共 {{ appealsTotal }} 条</span>
        </div>

        <div v-if="appealsLoading" class="loading-box">正在加载申诉…</div>

        <div v-else-if="appealsError" class="empty-box">
          <p class="danger-text">{{ appealsError }}</p>
          <lay-button type="primary" @click="loadAdminAppeals(appealsPage)">重试</lay-button>
        </div>

        <div v-else-if="!appeals.length" class="empty-box">
          <lay-empty description="暂无符合条件的申诉" />
        </div>

        <template v-else>
          <div v-for="appeal in appeals" :key="appeal.id" class="list-row">
            <span class="avatar-circle">{{ (appeal.nickname || appeal.username || '?').charAt(0) }}</span>
            <div class="list-row__main">
              <h3 class="list-row__title">{{ appeal.nickname || appeal.username }} 的申诉</h3>
              <div class="meta">
                <span>提交于 {{ appeal.create_time || '——' }}</span>
                <span
                  :class="['status-tag', appealStatusMeta(appeal.status).className]"
                >
                  {{ appealStatusMeta(appeal.status).label }}
                </span>
                <span v-if="appeal.handle_time">处理于 {{ appeal.handle_time }}</span>
              </div>
              <p class="appeal-text">申诉理由：{{ appeal.reason || '未填写' }}</p>
              <p class="appeal-text muted">原封禁理由：{{ appeal.ban_reason || '未填写' }}</p>
              <p v-if="appeal.admin_note" class="appeal-text">处理备注：{{ appeal.admin_note }}</p>
            </div>

            <div v-if="appeal.status === 0" class="row-actions">
              <lay-button size="xs" type="primary" @click="handleAppeal(appeal, 'accept')">
                申诉通过
              </lay-button>
              <lay-button size="xs" type="danger" @click="handleAppeal(appeal, 'reject')">
                驳回
              </lay-button>
            </div>
          </div>

          <div v-if="appealsTotal > 0" class="pagination-wrap">
            <lay-page
              v-model="appealsPage"
              :total="appealsTotal"
              :limit="PAGE_SIZE"
              :layout="PAGE_LAYOUT"
              @change="onAppealsPageChange"
            />
          </div>
        </template>
      </template>

      <!-- ===== 公告管理 ===== -->
      <template v-else>
        <div class="admin-filters">
          <lay-input
            v-model="announcements.keyword"
            style="width: 240px"
            placeholder="搜索公告标题"
            @keyup.enter="searchAnnouncements"
          />
          <lay-select
            v-model="announcements.status"
            :allow-clear="false"
            style="width: 150px"
            @change="searchAnnouncements"
          >
            <lay-select-option label="全部状态" value="" />
            <lay-select-option label="发布中" value="1" />
            <lay-select-option label="已下架" value="0" />
          </lay-select>
          <lay-button type="primary" @click="searchAnnouncements">搜索</lay-button>
          <lay-button type="warm" @click="openAnnounceForm()">新建公告</lay-button>
          <span class="page-toolbar__spacer"></span>
          <span class="muted filter-count">共 {{ announcements.total }} 条</span>
        </div>

        <div v-if="announceFormOpen" class="sub-form">
          <div class="sub-form__head">
            <h2 class="sub-form__title">{{ editingAnnouncementId ? '编辑公告' : '新建公告' }}</h2>
            <lay-button size="sm" @click="closeAnnounceForm">收起</lay-button>
          </div>

          <lay-form label-position="top" @submit="submitAnnouncement">
            <div v-if="announceFormError" class="form-error" role="alert">{{ announceFormError }}</div>

            <lay-form-item label="公告标题" required>
              <lay-input
                v-model="announceForm.title"
                placeholder="例如：新版本讨论区上线公告"
                maxlength="100"
                allow-clear
              />
            </lay-form-item>

            <lay-form-item label="公告内容" required>
              <lay-textarea
                v-model="announceForm.content"
                :rows="5"
                :maxlength="2000"
                show-count
                placeholder="公告正文，会展示在首页公告栏"
              />
            </lay-form-item>

            <lay-form-item v-if="!editingAnnouncementId" label="发布方式">
              <lay-select v-model="announceForm.status" :allow-clear="false" style="width: 200px">
                <lay-select-option label="立即发布" value="1" />
                <lay-select-option label="仅保存（不发布）" value="0" />
              </lay-select>
            </lay-form-item>

            <div class="form-actions">
              <lay-button type="primary" native-type="submit" :loading="announceSubmitting">
                {{ announceSubmitting ? '保存中...' : '保存' }}
              </lay-button>
              <lay-button native-type="button" @click="closeAnnounceForm">取消</lay-button>
            </div>
          </lay-form>
        </div>

        <div v-if="announcements.loading" class="loading-box">正在加载公告…</div>

        <div v-else-if="announcements.error" class="empty-box">
          <p class="danger-text">{{ announcements.error }}</p>
          <lay-button type="primary" @click="loadAnnouncements(announcements.page)">重试</lay-button>
        </div>

        <div v-else-if="!announcements.items.length" class="empty-box">
          <lay-empty description="还没有公告，点「新建公告」发布第一条" />
        </div>

        <template v-else>
          <div v-for="item in announcements.items" :key="item.id" class="list-row">
            <div class="list-row__main">
              <h3 class="list-row__title">
                {{ item.title }}
                <span
                  :class="['status-tag', item.status === 1 ? 'status-tag--recommend' : 'status-tag--pending']"
                >
                  {{ item.status === 1 ? '发布中' : '已下架' }}
                </span>
              </h3>
              <p class="item-desc">{{ item.content }}</p>
              <div class="meta">
                <span>发布人：{{ item.admin_nickname || '管理员' }}</span>
                <span v-if="item.publish_time">发布于 {{ item.publish_time }}</span>
                <span>创建于 {{ item.create_time }}</span>
              </div>
            </div>

            <div class="row-actions">
              <lay-button
                v-if="item.status === 1"
                size="xs"
                type="warm"
                @click="toggleAnnouncementStatus(item)"
              >
                下架
              </lay-button>
              <lay-button v-else size="xs" type="primary" @click="toggleAnnouncementStatus(item)">
                发布
              </lay-button>
              <lay-button size="xs" @click="openAnnounceForm(item)">编辑</lay-button>
              <lay-button size="xs" type="danger" @click="deleteAnnouncement(item)">删除</lay-button>
            </div>
          </div>

          <div v-if="announcements.total > 0" class="pagination-wrap">
            <lay-page
              v-model="announcements.page"
              :total="announcements.total"
              :limit="PAGE_SIZE"
              :layout="PAGE_LAYOUT"
              @change="onAnnouncementsPageChange"
            />
          </div>
        </template>
      </template>
    </lay-card>
  </div>
</template>

<style scoped>
.hero-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.admin-hero-actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.admin-who {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.admin-who__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.admin-who__role {
  font-size: var(--text-xs);
}

.admin-who__name {
  font-size: var(--text-base);
  color: var(--ghibli-sky-800);
}

.admin-stats {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: var(--space-4);
}

.stats-error {
  margin: 0 0 var(--space-4);
  font-size: var(--text-sm);
}

/* ===== 看板：待办事项 ===== */
.todo-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.todo-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-3);
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-lg);
  background: var(--ghibli-paper-50, #fdfcf7);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-gentle);
}

.todo-card:hover {
  border-color: var(--ghibli-sky-300);
  background: var(--ghibli-sky-50, #f7fbff);
  transform: translateY(-2px);
  box-shadow: var(--shadow-xs);
}

.todo-card__count {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-light);
  line-height: 1.1;
}

.todo-card__count--hot {
  color: var(--ghibli-sakura-600);
}

.todo-card__label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.todo-card__action {
  font-size: var(--text-xs);
  color: var(--ghibli-sky-600);
  opacity: 0.8;
}

/* ===== 看板：ECharts ===== */
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.chart-card--wide {
  grid-column: 1 / -1;
}

.chart-title {
  margin: 0 0 var(--space-3);
  font-size: var(--text-base);
  color: var(--ghibli-sky-800);
}

.chart-box {
  width: 100%;
  height: 260px;
}

.chart-box--lg {
  height: 300px;
}

.inline-link {
  color: var(--ghibli-sky-600);
  cursor: pointer;
  text-decoration: underline;
}

.section-toolbar {
  margin-top: var(--space-6);
}

.tab-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.source-tabs {
  margin-bottom: var(--space-4);
}

.review-filter-groups {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
  margin-bottom: var(--space-4);
}

.tab-group {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.tab-group__label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
}

.admin-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.filter-count {
  font-size: var(--text-sm);
}

.loading-box {
  padding: var(--space-16) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.review-row {
  align-items: center;
  margin-top: var(--space-2);
}

.review-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.review-note {
  font-size: var(--text-xs);
  line-height: var(--leading-relaxed);
  color: var(--ghibli-warm-800);
  word-break: break-word;
}

.item-desc {
  margin: var(--space-2) 0 0;
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text);
  word-break: break-word;
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: var(--space-2);
  flex-shrink: 0;
}

.appeal-text {
  margin: var(--space-2) 0 0;
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text);
  word-break: break-word;
}

.sub-form {
  margin-bottom: var(--space-5);
  padding: var(--space-5);
  border: 1px solid var(--ghibli-sky-100);
  border-radius: var(--radius-lg);
  background: var(--ghibli-sky-50, #f7fbff);
}

.sub-form__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.sub-form__title {
  margin: 0;
  font-size: var(--text-lg);
  color: var(--ghibli-sky-800);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.form-error {
  margin-bottom: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  background: var(--ghibli-warm-100, #fff4e6);
  color: var(--ghibli-warm-800);
  font-size: var(--text-sm);
}

.form-actions {
  display: flex;
  gap: var(--space-2);
}

.anime-cover {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  object-fit: cover;
  background: var(--ghibli-sky-100);
}

@media (max-width: 1100px) {
  .admin-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .todo-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .admin-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .todo-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .chart-card--wide {
    grid-column: auto;
  }

  .list-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .row-actions {
    justify-content: flex-start;
  }

  .admin-filters {
    align-items: stretch;
  }

  .form-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
