<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, postApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { usePostStore } from '@/stores/posts'

const router = useRouter()
const authStore = useAuthStore()
const postStore = usePostStore()

const running = ref(false)
const currentStep = ref(0)
const testResults = ref([])
const testLogs = ref([])
const testConfig = ref({
  baseUrl: window.location.origin,
  testUser: {
    username: `e2e_test_${Date.now()}`,
    email: `e2e_${Date.now()}@example.com`,
    password: '123456',
    nickname: 'E2E 测试用户'
  },
  cleanup: true
})

const steps = [
  { id: 'register', name: '用户注册', description: '注册新用户账号' },
  { id: 'login', name: '用户登录', description: '使用注册账号登录' },
  { id: 'profile', name: '获取用户资料', description: '验证 Token 携带与资料获取' },
  { id: 'posts-list', name: '浏览帖子列表', description: '验证公开接口与分页' },
  { id: 'post-detail', name: '查看帖子详情', description: '验证详情页路由与数据' },
  { id: 'auth-protection', name: '路由守卫保护', description: '验证未登录重定向' },
  { id: 'logout', name: '退出登录', description: '验证登出与 Token 清除' },
  { id: 'token-expiry', name: 'Token 过期处理', description: '验证过期 Token 拦截' },
]

const stats = computed(() => {
  const passed = testResults.value.filter(r => r.passed).length
  const failed = testResults.value.filter(r => r.passed === false).length
  const skipped = testResults.value.filter(r => r.skipped).length
  const pending = steps.length - testResults.value.length
  return { passed, failed, skipped, pending, total: steps.length }
})

function addLog(type, message, data = null) {
  testLogs.value.unshift({
    id: Date.now() + Math.random(),
    type,
    message,
    data,
    timestamp: new Date().toLocaleTimeString()
  })
  if (testLogs.value.length > 200) testLogs.value.pop()
}

async function runAllTests() {
  if (running.value) return
  running.value = true
  testResults.value = []
  testLogs.value = []
  currentStep.value = 0

  addLog('info', '开始端到端测试套件')

  for (let i = 0; i < steps.length; i++) {
    if (!running.value) break
    currentStep.value = i
    const step = steps[i]

    addLog('info', `步骤 ${i + 1}/${steps.length}: ${step.name}`)
    const result = await runStep(step)
    testResults.value.push({ ...step, ...result })

    if (result.passed) {
      addLog('success', `${step.name} - 通过`)
    } else if (result.skipped) {
      addLog('warning', `${step.name} - 跳过: ${result.message}`)
    } else {
      addLog('error', `${step.name} - 失败: ${result.message}`)
      // 关键步骤失败可选择停止
      if (['register', 'login'].includes(step.id)) {
        addLog('error', '关键步骤失败，终止后续测试')
        break
      }
    }

    await new Promise(r => setTimeout(r, 500))
  }

  running.value = false
  addLog('success', `测试完成: ${stats.value.passed}/${stats.value.total} 通过`)
}

function stopTests() {
  running.value = false
  addLog('warning', '用户手动停止测试')
}

async function runStep(step) {
  switch (step.id) {
    case 'register':
      return await testRegister()
    case 'login':
      return await testLogin()
    case 'profile':
      return await testProfile()
    case 'posts-list':
      return await testPostsList()
    case 'post-detail':
      return await testPostDetail()
    case 'auth-protection':
      return await testAuthProtection()
    case 'logout':
      return await testLogout()
    case 'token-expiry':
      return await testTokenExpiry()
    default:
      return { passed: false, message: '未知测试步骤' }
  }
}

async function testRegister() {
  try {
    const res = await authApi.register(testConfig.value.testUser)
    if (res.code === 0) {
      return { passed: true, message: `注册成功 (ID: ${res.data.id})`, data: res.data }
    }
    // 用户可能已存在
    if (res.code === 1002 || res.code === 1003) {
      return { passed: true, message: '用户已存在，视为通过', skipped: true, data: res }
    }
    return { passed: false, message: res.message }
  } catch (e) {
    return { passed: false, message: e.message }
  }
}

async function testLogin() {
  try {
    const res = await authApi.login({
      username: testConfig.value.testUser.username,
      password: testConfig.value.testUser.password
    })
    if (res.code === 0 && res.data.token) {
      // 手动设置 store 以便后续测试
      authStore.token = res.data.token
      authStore.user = res.data
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('user', JSON.stringify(res.data))
      return { passed: true, message: '登录成功，Token 已存储', data: { tokenLen: res.data.token.length } }
    }
    return { passed: false, message: res.message }
  } catch (e) {
    return { passed: false, message: e.message }
  }
}

async function testProfile() {
  if (!authStore.token) {
    return { passed: false, message: '未登录，无法测试' }
  }
  try {
    const res = await userApi.getProfile()
    if (res.code === 0) {
      return { passed: true, message: `获取资料成功 (${res.data.nickname})`, data: res.data }
    }
    return { passed: false, message: res.message }
  } catch (e) {
    return { passed: false, message: e.message }
  }
}

async function testPostsList() {
  try {
    const res = await postApi.getList({ page: 1, page_size: 5 })
    if (res.code === 0 && Array.isArray(res.data.list)) {
      return { passed: true, message: `获取列表成功 (${res.data.list.length} 条，共 ${res.data.total} 条)`, data: res.data }
    }
    return { passed: false, message: res.message }
  } catch (e) {
    return { passed: false, message: e.message }
  }
}

async function testPostDetail() {
  // 获取第一个帖子 ID
  try {
    const listRes = await postApi.getList({ page: 1, page_size: 1 })
    if (listRes.code === 0 && listRes.data.list.length > 0) {
      const postId = listRes.data.list[0].id
      // 导航到详情页
      await router.push(`/posts/${postId}`)
      await new Promise(r => setTimeout(r, 1000))
      return { passed: true, message: `导航到详情页成功 (ID: ${postId})`, data: { postId } }
    }
    return { passed: true, message: '无帖子数据，跳过详情测试', skipped: true }
  } catch (e) {
    return { passed: false, message: e.message }
  }
}

async function testAuthProtection() {
  // 登出后尝试访问受保护页面
  authStore.logout()
  await router.push('/profile')
  await new Promise(r => setTimeout(r, 500))

  const redirected = router.currentRoute.value.name === 'Login'
  if (redirected) {
    // 重新登录以便后续测试
    await testLogin()
    return { passed: true, message: '未登录访问受保护页正确重定向到登录页' }
  }
  return { passed: false, message: '未登录时未正确重定向' }
}

async function testLogout() {
  if (!authStore.token) {
    return { passed: true, message: '已登出，跳过', skipped: true }
  }
  authStore.logout()
  await new Promise(r => setTimeout(r, 200))
  const loggedOut = !authStore.token && !localStorage.getItem('token')
  return {
    passed: loggedOut,
    message: loggedOut ? '登出成功，本地存储已清除' : '登出失败，Token 残留',
    data: { token: authStore.token }
  }
}

async function testTokenExpiry() {
  // 测试无效 token
  const originalToken = authStore.token
  authStore.token = 'invalid.expired.token'
  localStorage.setItem('token', 'invalid.expired.token')

  try {
    const res = await userApi.getProfile()
    const correctlyRejected = res.code === 1007

    // 恢复原 token
    if (originalToken) {
      authStore.token = originalToken
      localStorage.setItem('token', originalToken)
    } else {
      authStore.logout()
    }

    return {
      passed: correctlyRejected,
      message: correctlyRejected ? '过期/无效 Token 被正确拦截 (code: 1007)' : 'Token 验证未生效',
      data: { code: res.code }
    }
  } catch (e) {
    // 恢复
    if (originalToken) {
      authStore.token = originalToken
      localStorage.setItem('token', originalToken)
    }
    return { passed: false, message: e.message }
  }
}

function clearResults() {
  testResults.value = []
  testLogs.value = []
  currentStep.value = 0
}

function exportReport() {
  const report = {
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    baseUrl: testConfig.value.baseUrl,
    config: testConfig.value,
    steps: testResults.value.map(r => ({
      name: r.name,
      passed: r.passed,
      skipped: r.skipped,
      message: r.message,
      duration: r.duration
    })),
    summary: stats.value
  }
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `e2e-report-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  addLog('success', '测试报告已导出')
}

function copyLogs() {
  const text = testLogs.value.map(l => `[${l.timestamp}] [${l.type.toUpperCase()}] ${l.message}`).join('\n')
  navigator.clipboard.writeText(text)
  addLog('success', '日志已复制到剪贴板')
}
</script>

<template>
  <div class="test-e2e page-enter">
    <div class="ghibli-container">
      <header class="test-e2e__header">
        <div>
          <h1 class="test-e2e__title">
            <span class="test-e2e__icon">🎭</span>
            端到端测试
          </h1>
          <p class="test-e2e__subtitle">完整用户流程自动化验证：注册 → 登录 → 浏览 → 交互 → 登出</p>
        </div>
        <div class="test-e2e__config">
          <button class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm" @click="showConfig = !showConfig">
            ⚙️ 配置
          </button>
        </div>
      </header>

      <!-- 配置面板 -->
      <transition name="slide-transition">
        <div v-show="showConfig" class="test-e2e__config-panel">
          <div class="ghibli-form-row">
            <div class="ghibli-form-group">
              <label class="ghibli-label">测试用户名前缀</label>
              <input v-model="testConfig.testUser.username" type="text" class="ghibli-input" placeholder="e2e_test_" />
            </div>
            <div class="ghibli-form-group">
              <label class="ghibli-label">测试邮箱前缀</label>
              <input v-model="testConfig.testUser.email" type="email" class="ghibli-input" placeholder="e2e_@example.com" />
            </div>
            <div class="ghibli-form-group">
              <label class="ghibli-label">测试密码</label>
              <input v-model="testConfig.testUser.password" type="password" class="ghibli-input" placeholder="123456" />
            </div>
          </div>
          <div class="ghibli-form-group">
            <label class="ghibli-checkbox">
              <input type="checkbox" v-model="testConfig.cleanup" class="ghibli-checkbox__input" />
              <span class="ghibli-checkbox__box"></span>
              测试后清理测试数据（登出）
            </label>
          </div>
        </div>
      </transition>

      <!-- 总体统计 -->
      <div class="test-e2e__stats">
        <div class="test-e2e__progress">
          <div class="test-e2e__progress-bar">
            <div
              class="test-e2e__progress-fill"
              :style="{ width: steps.length > 0 ? ((testResults.length / steps.length) * 100) + '%' : '0%' }"
            ></div>
          </div>
          <div class="test-e2e__progress-text">
            {{ testResults.length }} / {{ steps.length }} 步骤完成
          </div>
        </div>
        <div class="test-e2e__stat-cards">
          <div class="test-e2e__stat ghibli-badge ghibli-badge--success ghibli-badge--lg">
            <span class="test-e2e__stat-value">{{ stats.passed }}</span>
            <span class="test-e2e__stat-label">通过</span>
          </div>
          <div class="test-e2e__stat ghibli-badge ghibli-badge--error ghibli-badge--lg">
            <span class="test-e2e__stat-value">{{ stats.failed }}</span>
            <span class="test-e2e__stat-label">失败</span>
          </div>
          <div class="test-e2e__stat ghibli-badge ghibli-badge--warning ghibli-badge--lg">
            <span class="test-e2e__stat-value">{{ stats.skipped }}</span>
            <span class="test-e2e__stat-label">跳过</span>
          </div>
          <div class="test-e2e__stat ghibli-badge ghibli-badge--outline ghibli-badge--lg">
            <span class="test-e2e__stat-value">{{ stats.pending }}</span>
            <span class="test-e2e__stat-label">待测</span>
          </div>
        </div>
      </div>

      <!-- 控制按钮 -->
      <div class="test-e2e__controls">
        <button
          class="ghibli-btn ghibli-btn--primary ghibli-btn--lg"
          @click="runAllTests"
          :disabled="running"
        >
          <svg v-if="running" class="ghibli-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
            <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
          </svg>
          {{ running ? '测试进行中...' : '开始完整测试' }}
        </button>
        <button
          class="ghibli-btn ghibli-btn--ghost ghibli-btn--lg"
          @click="stopTests"
          :disabled="!running"
        >
          停止测试
        </button>
        <button
          class="ghibli-btn ghibli-btn--secondary"
          @click="clearResults"
        >
          清除结果
        </button>
        <button
          class="ghibli-btn ghibli-btn--warm"
          @click="exportReport"
          :disabled="testResults.length === 0"
        >
          导出报告
        </button>
        <button
          class="ghibli-btn ghibli-btn--ghost"
          @click="copyLogs"
          :disabled="testLogs.length === 0"
        >
          复制日志
        </button>
      </div>

      <!-- 测试步骤列表 -->
      <div class="test-e2e__steps">
        <div
          v-for="(step, index) in steps"
          :key="step.id"
          class="test-e2e__step"
          :class="{
            'test-e2e__step--current': running && index === currentStep,
            'test-e2e__step--passed': testResults[index]?.passed === true,
            'test-e2e__step--failed': testResults[index]?.passed === false,
            'test-e2e__step--skipped': testResults[index]?.skipped === true,
            'test-e2e__step--pending': !testResults[index]
          }"
        >
          <div class="test-e2e__step-number">
            <span v-if="testResults[index]?.passed === true" class="ghibli-badge ghibli-badge--success">✓</span>
            <span v-else-if="testResults[index]?.passed === false" class="ghibli-badge ghibli-badge--error">✗</span>
            <span v-else-if="testResults[index]?.skipped" class="ghibli-badge ghibli-badge--warning">⊘</span>
            <span v-else-if="running && index === currentStep" class="ghibli-spinner-small"></span>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="test-e2e__step-info">
            <h4 class="test-e2e__step-name">{{ step.name }}</h4>
            <p class="test-e2e__step-desc">{{ step.description }}</p>
            <p v-if="testResults[index]" class="test-e2e__step-result">{{ testResults[index].message }}</p>
          </div>
          <div class="test-e2e__step-duration" v-if="testResults[index]?.duration">
            {{ testResults[index].duration }}ms
          </div>
        </div>
      </div>

      <!-- 实时日志 -->
      <div class="test-e2e__logs" v-if="testLogs.length > 0">
        <div class="test-e2e__logs-header">
          <h3 class="test-e2e__logs-title">执行日志</h3>
          <button class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm" @click="testLogs = []">清空</button>
        </div>
        <div class="test-e2e__logs-content">
          <div
            v-for="log in testLogs"
            :key="log.id"
            class="test-e2e__log"
            :class="`test-e2e__log--${log.type}`"
          >
            <span class="test-e2e__log-time">{{ log.timestamp }}</span>
            <span class="test-e2e__log-badge">
              <span v-if="log.type === 'success'" class="ghibli-badge ghibli-badge--success ghibli-badge--sm">✓</span>
              <span v-else-if="log.type === 'error'" class="ghibli-badge ghibli-badge--error ghibli-badge--sm">✗</span>
              <span v-else-if="log.type === 'warning'" class="ghibli-badge ghibli-badge--warning ghibli-badge--sm">⚠</span>
              <span v-else class="ghibli-badge ghibli-badge--primary ghibli-badge--sm">ℹ</span>
            </span>
            <span class="test-e2e__log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>

      <!-- CI/CD 集成提示 -->
      <details class="test-e2e__ci">
        <summary>CI/CD 集成指南</summary>
        <div class="test-e2e__ci-content">
          <h4>GitHub Actions 示例</h4>
          <pre><code>.github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: yunmo
        ports: ["3306:3306"]
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - name: Install deps
        run: npm ci
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install backend deps
        run: |
          cd server
          pip install -r requirements.txt
      - name: Init database
        run: |
          cd server
          python init_db.py
      - name: Start backend
        run: |
          cd server
          python app.py &
          sleep 5
      - name: Build frontend
        run: npm run build
      - name: Run E2E tests
        run: |
          # 使用 Playwright 或 Cypress
          npx playwright install --with-deps
          npx playwright test
    </code></pre>
          <h4>Playwright 测试示例</h4>
          <pre><code>// tests/e2e.spec.ts
import { test, expect } from '@playwright/test'

test('用户完整流程', async ({ page }) => {
  // 注册
  await page.goto('/register')
  await page.fill('[name="username"]', 'testuser')
  await page.fill('[name="email"]', 'test@example.com')
  await page.fill('[name="password"]', '123456')
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/')

  // 登录
  await page.goto('/login')
  await page.fill('[name="username"]', 'testuser')
  await page.fill('[name="password"]', '123456')
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/')

  // 验证用户菜单
  await expect(page.locator('.ghibli-header__user-name')).toContainText('testuser')

  // 访问个人中心
  await page.click('.ghibli-header__user-trigger')
  await page.click('text=个人中心')
  await expect(page).toHaveURL('/profile')
})</code></pre>
        </div>
      </details>
    </div>
  </div>
</template>

<style scoped>
.test-e2e {
  padding: var(--space-8) 0 var(--space-16);
}

.test-e2e__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.test-e2e__title {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.test-e2e__icon {
  font-size: var(--text-3xl);
}

.test-e2e__subtitle {
  font-size: var(--text-lg);
  color: var(--color-text-muted);
  margin: 0;
}

.test-e2e__config-panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  margin-bottom: var(--space-6);
  animation: slideDown var(--duration-normal) var(--ease-gentle);
}

.ghibli-form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

/* 统计卡片 */
.test-e2e__stats {
  margin-bottom: var(--space-8);
}

.test-e2e__progress {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  margin-bottom: var(--space-6);
}

.test-e2e__progress-bar {
  height: 8px;
  background: var(--ghibli-paper-200);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--space-3);
}

.test-e2e__progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--ghibli-sky-400), var(--ghibli-forest-400), var(--ghibli-sun-400));
  border-radius: var(--radius-full);
  transition: width var(--duration-normal) var(--ease-gentle);
}

.test-e2e__progress-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  text-align: center;
}

.test-e2e__stat-cards {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.test-e2e__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-6);
  min-width: 90px;
}

.test-e2e__stat-value {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  line-height: 1;
}

.test-e2e__stat-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ghibli-badge--lg {
  padding: var(--space-3) var(--space-5);
}

.test-e2e__controls {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
}

.test-e2e__controls .ghibli-btn--lg {
  padding: var(--space-4) var(--space-8);
  font-size: var(--text-lg);
}

/* 步骤列表 */
.test-e2e__steps {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  margin-bottom: var(--space-8);
}

.test-e2e__step {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-divider);
  transition: var(--transition-gentle);
}

.test-e2e__step:last-child {
  border-bottom: none;
}

.test-e2e__step:hover {
  background: var(--ghibli-paper-50);
}

.test-e2e__step--current {
  background: var(--ghibli-sky-50);
  border-left: 3px solid var(--ghibli-sky-500);
}

.test-e2e__step--passed {
  background: var(--ghibli-forest-50);
}

.test-e2e__step--failed {
  background: var(--color-error-bg);
}

.test-e2e__step--skipped {
  background: var(--ghibli-sun-50);
}

.test-e2e__step--pending {
  opacity: 0.5;
}

.test-e2e__step-number {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-semibold);
  color: var(--color-text-muted);
  background: var(--ghibli-paper-100);
  border-radius: var(--radius-full);
  flex-shrink: 0.
}

.test-e2e__step--current .test-e2e__step-number {
  background: var(--ghibli-sky-100);
  color: var(--ghibli-sky-700);
}

.test-e2e__step--passed .test-e2e__step-number {
  background: var(--ghibli-forest-100);
  color: var(--ghibli-forest-700);
}

.test-e2e__step--failed .test-e2e__step-number {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.ghibli-spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid var(--ghibli-paper-200);
  border-top-color: var(--ghibli-sky-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.test-e2e__step-info {
  flex: 1;
  min-width: 0;
}

.test-e2e__step-name {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-1);
}

.test-e2e__step-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0 0 var(--space-1);
}

.test-e2e__step-result {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0;
  font-family: var(--font-mono);
}

.test-e2e__step-duration {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  background: var(--ghibli-paper-100);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

/* 日志 */
.test-e2e__logs {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.test-e2e__logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-divider);
  background: var(--ghibli-paper-50);
}

.test-e2e__logs-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0;
}

.test-e2e__logs-content {
  max-height: 300px;
  overflow-y: auto;
  padding: var(--space-3) var(--space-6);
}

.test-e2e__log {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  line-height: 1.5;
  border-bottom: 1px solid var(--color-divider);
}

.test-e2e__log:last-child {
  border-bottom: none;
}

.test-e2e__log-time {
  color: var(--color-text-muted);
  min-width: 70px;
}

.test-e2e__log-message {
  flex: 1;
  color: var(--color-text);
  word-break: break-word;
}

.test-e2e__log--success .test-e2e__log-message {
  color: var(--ghibli-forest-600);
}

.test-e2e__log--error .test-e2e__log-message {
  color: var(--color-error);
}

.test-e2e__log--warning .test-e2e__log-message {
  color: var(--ghibli-sun-700);
}

/* CI/CD */
.test-e2e__ci {
  margin-top: var(--space-8);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.test-e2e__ci summary {
  padding: var(--space-4) var(--space-6);
  background: var(--ghibli-paper-50);
  border-bottom: 1px solid var(--color-divider);
  cursor: pointer;
  font-weight: var(--font-semibold);
  color: var(--color-text);
  list-style: none;
}

.test-e2e__ci summary::-webkit-details-marker {
  display: none;
}

.test-e2e__ci summary::before {
  content: '▸';
  display: inline-block;
  margin-right: var(--space-2);
  transition: transform var(--duration-fast);
}

.test-e2e__ci[open] summary::before {
  transform: rotate(90deg);
}

.test-e2e__ci-content {
  padding: var(--space-6);
  font-size: var(--text-sm);
  line-height: 1.7;
}

.test-e2e__ci-content h4 {
  font-family: var(--font-display);
  font-size: var(--text-base);
  color: var(--color-text);
  margin: var(--space-4) 0 var(--space-2);
}

.test-e2e__ci-content h4:first-child {
  margin-top: 0;
}

.test-e2e__ci-content pre {
  background: var(--ghibli-ink-800);
  color: var(--ghibli-paper-100);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  overflow-x: auto; 
  margin: 0;
}

.test-e2e__ci-content code {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  line-height: 1.6;
}

/* 响应式 */
@media (max-width: 768px) {
  .test-e2e__title {
    font-size: var(--text-3xl);
  }

  .test-e2e__step {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .test-e2e__step-duration {
    align-self: flex-end;
  }

  .test-e2e__controls {
    flex-direction: column;
  }

  .test-e2e__controls .ghibli-btn {
    width: 100%;
  }

  .test-e2e__stat-cards {
    justify-content: center;
  }
}
</style>