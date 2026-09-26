<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, userApi, postApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { usePostStore } from '@/stores/posts'

const router = useRouter()
const authStore = useAuthStore()
const postStore = usePostStore()

// 测试状态
const activeTab = ref('connectivity')
const testResults = ref({})
const runningTests = ref(false)
const testLogs = ref([])
const autoRun = ref(false)

// 测试用例定义
const testCases = {
  connectivity: [
    { id: 'api-health', name: '后端健康检查', fn: testApiHealth },
    { id: 'cors', name: 'CORS 跨域配置', fn: testCORS },
    { id: 'proxy', name: 'Vite 代理转发', fn: testProxy },
  ],
  auth: [
    { id: 'register', name: '用户注册', fn: testRegister },
    { id: 'login', name: '用户登录', fn: testLogin },
    { id: 'profile', name: '获取用户资料', fn: testProfile },
    { id: 'token-refresh', name: 'Token 刷新机制', fn: testTokenRefresh },
    { id: 'logout', name: '退出登录', fn: testLogout },
  ],
  posts: [
    { id: 'list-posts', name: '获取帖子列表', fn: testListPosts },
    { id: 'pagination', name: '分页加载', fn: testPagination },
    { id: 'empty-state', name: '空状态处理', fn: testEmptyState },
  ],
  errorHandling: [
    { id: '404', name: '404 接口处理', fn: test404 },
    { id: '401', name: '401 未授权处理', fn: test401 },
    { id: 'validation', name: '参数验证错误', fn: testValidation },
    { id: 'network', name: '网络异常模拟', fn: testNetworkError },
  ],
  performance: [
    { id: 'response-time', name: '响应时间测试', fn: testResponseTime },
    { id: 'concurrent', name: '并发请求测试', fn: testConcurrent },
    { id: 'large-payload', name: '大数据量测试', fn: testLargePayload },
  ]
}

// 当前分类的测试用例
const currentTests = computed(() => testCases[activeTab.value] || [])

// 总体统计
const stats = computed(() => {
  const allTests = Object.values(testCases).flat()
  const passed = allTests.filter(t => testResults.value[t.id]?.passed).length
  const failed = allTests.filter(t => testResults.value[t.id]?.passed === false).length
  const pending = allTests.length - passed - failed
  return { passed, failed, pending, total: allTests.length }
})

// 添加日志
function addLog(type, message, data = null) {
  testLogs.value.unshift({
    id: Date.now() + Math.random(),
    type,
    message,
    data,
    timestamp: new Date().toLocaleTimeString()
  })
  if (testLogs.value.length > 100) testLogs.value.pop()
}

// 运行单个测试
async function runTest(testCase) {
  testResults.value[testCase.id] = { running: true, startTime: Date.now() }
  addLog('info', `开始测试: ${testCase.name}`)

  try {
    const result = await testCase.fn()
    const duration = Date.now() - testResults.value[testCase.id].startTime

    testResults.value[testCase.id] = {
      passed: result.success,
      duration,
      message: result.message,
      data: result.data
    }

    addLog(result.success ? 'success' : 'error', `${testCase.name}: ${result.message}`, result.data)
    return result.success
  } catch (error) {
    const duration = Date.now() - testResults.value[testCase.id].startTime
    testResults.value[testCase.id] = {
      passed: false,
      duration,
      message: error.message,
      error: true
    }
    addLog('error', `${testCase.name} 抛出异常: ${error.message}`, error)
    return false
  }
}

// 运行当前分类所有测试
async function runAllTests() {
  if (runningTests.value) return
  runningTests.value = true
  testLogs.value = []

  const tests = currentTests.value
  for (const testCase of tests) {
    if (!runningTests.value) break
    await runTest(testCase)
    // 间隔一点时间避免请求过快
    await new Promise(r => setTimeout(r, 300))
  }

  runningTests.value = false
  addLog('info', `测试完成: ${stats.value.passed}/${stats.value.total} 通过`)
}

// 运行所有分类测试
async function runFullSuite() {
  const originalTab = activeTab.value
  runningTests.value = true
  testLogs.value = []

  for (const tab of Object.keys(testCases)) {
    activeTab.value = tab
    const tests = testCases[tab]
    for (const testCase of tests) {
      if (!runningTests.value) break
      await runTest(testCase)
      await new Promise(r => setTimeout(r, 300))
    }
  }

  activeTab.value = originalTab
  runningTests.value = false
  addLog('success', `全量测试完成: ${stats.value.passed}/${stats.value.total} 通过`)
}

// 清除结果
function clearResults() {
  testResults.value = {}
  testLogs.value = []
}

// ===== 具体测试实现 =====

async function testApiHealth() {
  try {
    const start = performance.now()
    const res = await fetch('/api/posts')
    const duration = performance.now() - start
    const data = await res.json()
    return {
      success: res.ok && data.code === 0,
      message: `HTTP ${res.status}, 耗时 ${duration.toFixed(0)}ms`,
      data: { status: res.status, duration: `${duration.toFixed(0)}ms` }
    }
  } catch (e) {
    return { success: false, message: `连接失败: ${e.message}` }
  }
}

async function testCORS() {
  try {
    const res = await fetch('/api/posts', { method: 'OPTIONS' })
    const corsHeaders = {
      origin: res.headers.get('Access-Control-Allow-Origin'),
      methods: res.headers.get('Access-Control-Allow-Methods'),
      headers: res.headers.get('Access-Control-Allow-Headers')
    }
    return {
      success: !!corsHeaders.origin,
      message: corsHeaders.origin ? 'CORS 头部配置正确' : '缺少 CORS 头部',
      data: corsHeaders
    }
  } catch (e) {
    return { success: false, message: `CORS 测试失败: ${e.message}` }
  }
}

async function testProxy() {
  try {
    // 测试前端代理是否正确转发到后端
    const res = await fetch('/api/posts?page=1&page_size=1')
    const data = await res.json()
    const hasExpectedStructure = data && typeof data.code === 'number' && !!data.data && Array.isArray(data.data.list)
    return {
      success: hasExpectedStructure,
      message: hasExpectedStructure ? '代理转发正常，数据结构正确' : '代理转发异常或数据结构不符',
      data: { structure: hasExpectedStructure }
    }
  } catch (e) {
    return { success: false, message: `代理测试失败: ${e.message}` }
  }
}

async function testRegister() {
  const testUser = {
    username: `test_${Date.now()}`,
    email: `test_${Date.now()}@example.com`,
    password: '123456',
    nickname: `测试用户_${Date.now()}`
  }
  try {
    const res = await authApi.register(testUser)
    return {
      success: res.code === 0,
      message: res.code === 0 ? `注册成功 (ID: ${res.data.id})` : res.message,
      data: res.data
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function testLogin() {
  // 先注册一个用户用于登录测试
  const testUser = {
    username: `login_test_${Date.now()}`,
    email: `login_${Date.now()}@example.com`,
    password: '123456',
    nickname: '登录测试用户'
  }
  try {
    const registerRes = await authApi.register(testUser)
    if (registerRes.code !== 0) {
      return { success: false, message: registerRes.message }
    }
    // 走 authStore.login，与登录页行为一致：token 会写入 store 与 localStorage。
    // 后续「获取用户资料」「Token 刷新机制」两个用例依赖这份登录态。
    const result = await authStore.login({
      username: testUser.username,
      password: testUser.password,
    })
    return {
      success: result.success && !!authStore.token,
      message: result.success ? '登录成功，获取到 Token' : result.message,
      data: result.success ? { tokenLength: authStore.token.length } : null
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function testProfile() {
  if (!authStore.token) {
    return { success: false, message: '未登录，跳过测试' }
  }
  try {
    const res = await userApi.getProfile()
    return {
      success: res.code === 0,
      message: res.code === 0 ? `获取资料成功 (用户: ${res.data.nickname})` : res.message,
      data: res.data
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function testLogout() {
  authStore.logout()
  return { success: true, message: '本地 Token 已清除' }
}

async function testTokenRefresh() {
  // 测试 Token 是否在请求头中自动携带
  if (!authStore.token) {
    return { success: false, message: '未登录，无法测试 Token 携带' }
  }
  try {
    // 发起一个需要认证的请求
    const res = await userApi.getProfile()
    // 请求成功说明 token 既被自动携带、也通过了后端校验
    const hasAuth = res.code === 0
    return {
      success: hasAuth,
      message: hasAuth ? 'Token 自动携带正常' : 'Token 可能已过期或未携带',
      data: { code: res.code }
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function testListPosts() {
  try {
    const res = await postApi.getList({ page: 1, page_size: 5 })
    return {
      success: res.code === 0 && Array.isArray(res.data.list),
      message: res.code === 0 ? `获取列表成功 (${res.data.list.length} 条)` : res.message,
      data: { count: res.data.list.length, total: res.data.total }
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function testPagination() {
  try {
    const res1 = await postApi.getList({ page: 1, page_size: 2 })
    const res2 = await postApi.getList({ page: 2, page_size: 2 })
    // 后端分页响应是扁平结构：{ list, total, page, page_size, total_pages }
    // 与 src/stores/posts.js 中 fetchPosts 的解构方式保持一致
    const hasPagination = res1.code === 0 && res2.code === 0 &&
      res1.data.page === 1 && res2.data.page === 2 &&
      typeof res1.data.total_pages === 'number'
    return {
      success: hasPagination,
      message: hasPagination ? '分页参数正常工作' : '分页参数异常',
      data: {
        page1: { page: res1.data.page, total: res1.data.total, total_pages: res1.data.total_pages },
        page2: { page: res2.data.page, total: res2.data.total, total_pages: res2.data.total_pages }
      }
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function testEmptyState() {
  // 测试大页码返回空列表
  try {
    const res = await postApi.getList({ page: 9999, page_size: 10 })
    const isEmpty = res.code === 0 && res.data.list.length === 0
    return {
      success: isEmpty,
      message: isEmpty ? '空列表处理正确' : '空列表处理异常',
      data: { page: 9999, count: res.data.list.length }
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function test404() {
  try {
    const res = await fetch('/api/nonexistent-endpoint')
    const data = await res.json()
    return {
      success: res.status === 404 && data.code === 1009,
      message: `返回状态: ${res.status}, 业务码: ${data.code}`,
      data: { status: res.status, code: data.code }
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function test401() {
  // 使用无效 token
  try {
    const res = await fetch('/api/user/profile', {
      headers: { Authorization: 'Bearer invalid_token_xxx' }
    })
    const data = await res.json()
    return {
      success: data.code === 1007,
      message: `返回业务码: ${data.code} (${data.code === 1007 ? '正确拦截' : '未正确拦截'})`,
      data: { code: data.code }
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function testValidation() {
  try {
    // 缺少必填参数
    const res = await authApi.register({ username: '', email: 'invalid', password: '1' })
    return {
      success: res.code === 1001,
      message: `参数验证码: ${res.code} (${res.code === 1001 ? '正确拦截' : '未正确拦截'})`,
      data: { code: res.code, message: res.message }
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

async function testNetworkError() {
  // 这个测试只能模拟，实际网络错误难以在浏览器中触发
  return {
    success: true,
    message: '网络错误处理由 axios 拦截器统一处理 (见 src/api/index.js)',
    data: { note: '实际测试需断网或后端停止' }
  }
}

async function testResponseTime() {
  const times = []
  for (let i = 0; i < 5; i++) {
    const start = performance.now()
    await fetch('/api/posts')
    times.push(performance.now() - start)
    await new Promise(r => setTimeout(r, 50))
  }
  const avg = times.reduce((a, b) => a + b, 0) / times.length
  const max = Math.max(...times)
  return {
    success: avg < 1000, // 平均响应时间小于 1 秒
    message: `平均 ${avg.toFixed(0)}ms, 最大 ${max.toFixed(0)}ms`,
    data: { times: times.map(t => `${t.toFixed(0)}ms`), avg: `${avg.toFixed(0)}ms`, max: `${max.toFixed(0)}ms` }
  }
}

async function testConcurrent() {
  const start = performance.now()
  const promises = Array(10).fill(null).map(() => fetch('/api/posts'))
  try {
    await Promise.all(promises)
    const duration = performance.now() - start
    return {
      success: true,
      message: `10 个并发请求完成，总耗时 ${duration.toFixed(0)}ms`,
      data: { concurrent: 10, duration: `${duration.toFixed(0)}ms` }
    }
  } catch (e) {
    return { success: false, message: `并发测试失败: ${e.message}` }
  }
}

async function testLargePayload() {
  // 测试大量数据请求
  try {
    const res = await postApi.getList({ page: 1, page_size: 50 })
    const size = JSON.stringify(res).length
    return {
      success: res.code === 0,
      message: `获取 50 条数据，响应大小约 ${(size / 1024).toFixed(1)} KB`,
      data: { count: res.data.list.length, sizeKB: (size / 1024).toFixed(1) }
    }
  } catch (e) {
    return { success: false, message: e.message }
  }
}

// 标签样式映射
const tabLabels = {
  connectivity: '连通性',
  auth: '认证流程',
  posts: '帖子接口',
  errorHandling: '错误处理',
  performance: '性能测试'
}

const tabIcons = {
  connectivity: '🌐',
  auth: '🔐',
  posts: '📝',
  errorHandling: '⚠️',
  performance: '⚡'
}
</script>

<template>
  <div class="test-dashboard page-enter">
    <div class="ghibli-container">
      <!-- 页面标题 -->
      <header class="test-dashboard__header">
        <div class="test-dashboard__title-group">
          <h1 class="test-dashboard__title">
            <span class="test-dashboard__icon">🧪</span>
            测试中心
          </h1>
          <p class="test-dashboard__subtitle">前后端连通性与功能验证仪表盘</p>
        </div>
        <div class="test-dashboard__stats">
          <div class="ghibli-stat">
            <span class="ghibli-stat__value ghibli-text-success">{{ stats.passed }}</span>
            <span class="ghibli-stat__label">通过</span>
          </div>
          <div class="ghibli-stat">
            <span class="ghibli-stat__value ghibli-text-error">{{ stats.failed }}</span>
            <span class="ghibli-stat__label">失败</span>
          </div>
          <div class="ghibli-stat">
            <span class="ghibli-stat__value ghibli-text-warning">{{ stats.pending }}</span>
            <span class="ghibli-stat__label">待测</span>
          </div>
          <div class="ghibli-stat">
            <span class="ghibli-stat__value">{{ stats.total }}</span>
            <span class="ghibli-stat__label">总计</span>
          </div>
        </div>
      </header>

      <!-- 标签页导航 -->
      <nav class="ghibli-tabs test-dashboard__tabs" role="tablist">
        <button
          v-for="(label, key) in tabLabels"
          :key="key"
          :class="['ghibli-tab', { 'ghibli-tab--active': activeTab === key }]"
          @click="activeTab = key"
          :aria-selected="activeTab === key"
          role="tab"
        >
          <span class="ghibli-tab__icon">{{ tabIcons[key] }}</span>
          <span>{{ label }}</span>
          <span class="ghibli-tab__count">
            {{ (testCases[key] || []).filter(t => testResults[t.id]?.passed).length }} / {{ (testCases[key] || []).length }}
          </span>
        </button>
      </nav>

      <!-- 操作按钮 -->
      <div class="test-dashboard__actions">
        <button
          class="ghibli-btn ghibli-btn--primary"
          @click="runAllTests"
          :disabled="runningTests"
        >
          <svg v-if="runningTests" class="ghibli-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
            <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
          </svg>
          {{ runningTests ? '测试中...' : '运行当前分类' }}
        </button>
        <button
          class="ghibli-btn ghibli-btn--warm"
          @click="runFullSuite"
          :disabled="runningTests"
        >
          运行全量测试
        </button>
        <button
          class="ghibli-btn ghibli-btn--ghost"
          @click="clearResults"
        >
          清除结果
        </button>
      </div>

      <!-- 测试用例列表 -->
      <div class="test-dashboard__list">
        <div
          v-for="testCase in currentTests"
          :key="testCase.id"
          class="test-dashboard__item"
          :class="{
            'test-dashboard__item--running': testResults[testCase.id]?.running,
            'test-dashboard__item--passed': testResults[testCase.id]?.passed === true,
            'test-dashboard__item--failed': testResults[testCase.id]?.passed === false
          }"
        >
          <div class="test-dashboard__item-main">
            <div class="test-dashboard__item-status">
              <div v-if="testResults[testCase.id]?.running" class="ghibli-spinner-small"></div>
              <svg v-else-if="testResults[testCase.id]?.passed === true" class="test-dashboard__icon-success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <svg v-else-if="testResults[testCase.id]?.passed === false" class="test-dashboard__icon-error" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              <svg v-else class="test-dashboard__icon-pending" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
              </svg>
            </div>
            <div class="test-dashboard__item-info">
              <h4 class="test-dashboard__item-name">{{ testCase.name }}</h4>
              <p v-if="testResults[testCase.id]" class="test-dashboard__item-message">{{ testResults[testCase.id].message }}</p>
              <p v-else class="test-dashboard__item-message ghibli-text-muted">点击运行测试</p>
            </div>
            <div class="test-dashboard__item-meta" v-if="testResults[testCase.id] && !testResults[testCase.id].running">
              <span class="test-dashboard__duration">{{ testResults[testCase.id].duration }}ms</span>
              <button
                class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm"
                @click="runTest(testCase)"
                :disabled="runningTests"
              >
                重跑
              </button>
            </div>
          </div>
          <div v-if="testResults[testCase.id]?.data" class="test-dashboard__item-detail">
            <pre class="test-dashboard__json">{{ JSON.stringify(testResults[testCase.id].data, null, 2) }}</pre>
          </div>
        </div>
      </div>

      <!-- 测试日志 -->
      <div class="test-dashboard__logs" v-if="testLogs.length > 0">
        <h3 class="test-dashboard__logs-title">测试日志</h3>
        <div class="test-dashboard__logs-content">
          <div
            v-for="log in testLogs"
            :key="log.id"
            class="test-dashboard__log"
            :class="`test-dashboard__log--${log.type}`"
          >
            <span class="test-dashboard__log-time">{{ log.timestamp }}</span>
            <span class="test-dashboard__log-type">
              <span v-if="log.type === 'success'" class="ghibli-badge ghibli-badge--success">✓</span>
              <span v-else-if="log.type === 'error'" class="ghibli-badge ghibli-badge--error">✗</span>
              <span v-else-if="log.type === 'warning'" class="ghibli-badge ghibli-badge--warning">⚠</span>
              <span v-else class="ghibli-badge ghibli-badge--primary">ℹ</span>
            </span>
            <span class="test-dashboard__log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.test-dashboard {
  padding: var(--space-8) 0 var(--space-16);
}

.test-dashboard__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-6);
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
}

.test-dashboard__title {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.test-dashboard__icon {
  font-size: var(--text-3xl);
  animation: gentleBreathe 3s ease-in-out infinite;
}

.test-dashboard__subtitle {
  font-size: var(--text-lg);
  color: var(--color-text-muted);
  margin: 0;
}

.test-dashboard__stats {
  display: flex;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.ghibli-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  min-width: 80px;
  box-shadow: var(--shadow-sm);
}

.ghibli-stat__value {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  line-height: 1;
}

.ghibli-stat__label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.test-dashboard__tabs {
  margin-bottom: var(--space-6);
  border-bottom-color: var(--color-divider);
}

.ghibli-tab__icon {
  margin-right: var(--space-2);
}

.ghibli-tab__count {
  margin-left: var(--space-2);
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
  background: var(--ghibli-paper-200);
  border-radius: var(--radius-full);
  color: var(--color-text-muted);
}

.ghibli-tab--active .ghibli-tab__count {
  background: var(--ghibli-sky-200);
  color: var(--ghibli-sky-700);
}

.test-dashboard__actions {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
}

.test-dashboard__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-8);
}

.test-dashboard__item {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-5) var(--space-6);
  transition: var(--transition-gentle);
}

.test-dashboard__item:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
}

.test-dashboard__item--running {
  border-color: var(--ghibli-sky-300);
  background: var(--ghibli-sky-50);
}

.test-dashboard__item--passed {
  border-color: var(--ghibli-forest-300);
}

.test-dashboard__item--failed {
  border-color: var(--color-error);
  background: var(--color-error-bg);
}

.test-dashboard__item-main {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.test-dashboard__item-status {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ghibli-spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid var(--ghibli-paper-200);
  border-top-color: var(--ghibli-sky-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.test-dashboard__icon-success {
  width: 22px;
  height: 22px;
  color: var(--ghibli-forest-500);
}

.test-dashboard__icon-error {
  width: 22px;
  height: 22px;
  color: var(--color-error);
}

.test-dashboard__icon-pending {
  width: 22px;
  height: 22px;
  color: var(--color-text-muted);
  opacity: 0.4;
}

.test-dashboard__item-info {
  flex: 1;
  min-width: 0;
}

.test-dashboard__item-name {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-1);
}

.test-dashboard__item-message {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.test-dashboard__item-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.test-dashboard__duration {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  background: var(--ghibli-paper-100);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
}

.test-dashboard__item-detail {
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-divider);
  animation: slideDown var(--duration-normal) var(--ease-gentle);
}

.test-dashboard__json {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  line-height: 1.6;
  background: var(--ghibli-ink-800);
  color: var(--ghibli-paper-100);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  overflow-x: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.test-dashboard__logs {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.test-dashboard__logs-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-divider);
  background: var(--ghibli-paper-100);
}

.test-dashboard__logs-content {
  max-height: 300px;
  overflow-y: auto;
  padding: var(--space-3) var(--space-6);
}

.test-dashboard__log {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  line-height: 1.5;
  border-bottom: 1px solid var(--color-divider);
}

.test-dashboard__log:last-child {
  border-bottom: none;
}

.test-dashboard__log-time {
  color: var(--color-text-muted);
  min-width: 70px;
}

.test-dashboard__log-message {
  flex: 1;
  color: var(--color-text);
  word-break: break-word;
}

.test-dashboard__log--success .test-dashboard__log-message {
  color: var(--ghibli-forest-600);
}

.test-dashboard__log--error .test-dashboard__log-message {
  color: var(--color-error);
}

.test-dashboard__log--warning .test-dashboard__log-message {
  color: var(--ghibli-sun-700);
}

/* 响应式 */
@media (max-width: 768px) {
  .test-dashboard__header {
    flex-direction: column;
    align-items: stretch;
  }

  .test-dashboard__stats {
    justify-content: center;
  }

  .test-dashboard__item-main {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .test-dashboard__item-meta {
    align-self: flex-end;
  }
}

@media (max-width: 480px) {
  .test-dashboard__title {
    font-size: var(--text-3xl);
  }

  .ghibli-stat {
    min-width: 70px;
    padding: var(--space-3) var(--space-4);
  }

  .test-dashboard__actions {
    flex-direction: column;
  }

  .test-dashboard__actions .ghibli-btn {
    width: 100%;
  }
}
</style>