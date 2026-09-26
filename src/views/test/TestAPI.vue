<script setup>
import { ref, onMounted, computed } from 'vue'
import { authApi, userApi, postApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { usePostStore } from '@/stores/posts'

const authStore = useAuthStore()
const postStore = usePostStore()

const activeEndpoint = ref('posts-list')
const requestConfig = ref({
  method: 'GET',
  url: '/api/posts',
  headers: {},
  params: { page: 1, page_size: 10 },
  body: null
})
const response = ref(null)
const responseTime = ref(0)
const requestHistory = ref([])
const loading = ref(false)
const saveAsTest = ref(false)

const endpoints = [
  { id: 'posts-list', name: 'GET /api/posts', category: '帖子', desc: '获取帖子分页列表' },
  { id: 'posts-detail', name: 'GET /api/posts/:id', category: '帖子', desc: '获取帖子详情（需后端支持）' },
  { id: 'user-profile', name: 'GET /api/user/profile', category: '用户', desc: '获取当前用户资料（需登录）', auth: true },
  { id: 'register', name: 'POST /api/register', category: '认证', desc: '用户注册' },
  { id: 'login', name: 'POST /api/login', category: '认证', desc: '用户登录' },
  { id: 'custom', name: '自定义请求', category: '其他', desc: '手动构造任意请求' },
]

const categories = computed(() => [...new Set(endpoints.map(e => e.category))])

function loadEndpointConfig(endpoint) {
  activeEndpoint.value = endpoint.id
  const configs = {
    'posts-list': { method: 'GET', url: '/api/posts', params: { page: 1, page_size: 10 }, body: null },
    'posts-detail': { method: 'GET', url: '/api/posts/1', params: {}, body: null },
    'user-profile': { method: 'GET', url: '/api/user/profile', params: {}, body: null },
    'register': { method: 'POST', url: '/api/register', params: {}, body: { username: 'testuser', email: 'test@example.com', password: '123456', nickname: '测试用户' } },
    'login': { method: 'POST', url: '/api/login', params: {}, body: { username: 'testuser', password: '123456' } },
    'custom': { method: 'GET', url: '/api/', params: {}, body: null }
  }
  requestConfig.value = { ...configs[endpoint.id], headers: {} }
  if (endpoint.auth) {
    requestConfig.value.headers.Authorization = `Bearer ${authStore.token || ''}`
  }
  response.value = null
  responseTime.value = 0
}

async function sendRequest() {
  loading.value = true
  response.value = null
  const start = performance.now()

  try {
    const config = requestConfig.value
    const url = new URL(config.url, window.location.origin)
    Object.entries(config.params || {}).forEach(([k, v]) => url.searchParams.set(k, v))

    const options = {
      method: config.method,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers
      }
    }

    if (config.body && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
      options.body = JSON.stringify(config.body)
    }

    const res = await fetch(url.toString(), options)
    const data = await res.json().catch(() => ({ _raw: await res.text() }))
    const duration = performance.now() - start

    response.value = { status: res.status, ok: res.ok, headers: Object.fromEntries(res.headers), data }
    responseTime.value = duration

    // 添加到历史
    requestHistory.value.unshift({
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      method: config.method,
      url: config.url,
      status: res.status,
      duration: `${duration.toFixed(0)}ms`,
      success: res.ok
    })
    if (requestHistory.value.length > 20) requestHistory.value.pop()

    // 如果是登录成功，自动保存 token
    if (config.url.includes('/login') && data.code === 0 && data.data.token) {
      authStore.token = data.data.token
      authStore.user = data.data
      localStorage.setItem('token', data.data.token)
      localStorage.setItem('user', JSON.stringify(data.data))
      addLog('success', '登录成功，Token 已自动保存')
    }

    addLog(res.ok ? 'success' : 'error', `${config.method} ${config.url} - ${res.status} (${duration.toFixed(0)}ms)`)

  } catch (error) {
    const duration = performance.now() - start
    response.value = { error: error.message, status: 0 }
    responseTime.value = duration
    addLog('error', `请求失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

function addLog(type, message) {
  // 可以集成到全局 toast
  console.log(`[${type}] ${message}`)
}

function formatJSON(obj) {
  return JSON.stringify(obj, null, 2)
}

function copyResponse() {
  if (response.value) {
    navigator.clipboard.writeText(formatJSON(response.value))
    addLog('success', '响应已复制到剪贴板')
  }
}

function clearHistory() {
  requestHistory.value = []
}
</script>

<template>
  <div class="test-api page-enter">
    <div class="ghibli-container">
      <header class="test-api__header">
        <div>
          <h1 class="test-api__title">
            <span class="test-api__icon">🔌</span>
            API 接口测试
          </h1>
          <p class="test-api__subtitle">手动测试各个后端接口，查看请求响应详情</p>
        </div>
        <div class="test-api__status">
          <span class="ghibli-badge" :class="authStore.isLoggedIn ? 'ghibli-badge--success' : 'ghibli-badge--warning'">
            {{ authStore.isLoggedIn ? '已登录' : '未登录' }}
          </span>
          <span v-if="authStore.isLoggedIn" class="ghibli-badge ghibli-badge--primary">
            Token: {{ authStore.token?.slice(0, 20) }}...
          </span>
        </div>
      </header>

      <div class="test-api__layout">
        <!-- 侧边栏：接口列表 -->
        <aside class="test-api__sidebar">
          <div v-for="category in categories" :key="category" class="test-api__category">
            <h3 class="test-api__category-title">{{ category }}</h3>
            <ul class="test-api__endpoint-list">
              <li
                v-for="endpoint in endpoints.filter(e => e.category === category)"
                :key="endpoint.id"
                :class="['test-api__endpoint', { 'test-api__endpoint--active': activeEndpoint === endpoint.id }]"
                @click="loadEndpointConfig(endpoint)"
              >
                <span class="test-api__endpoint-name">{{ endpoint.name }}</span>
                <span class="test-api__endpoint-desc">{{ endpoint.desc }}</span>
                <span v-if="endpoint.auth" class="ghibli-badge ghibli-badge--warning ghibli-badge--sm">需认证</span>
              </li>
            </ul>
          </div>
        </aside>

        <!-- 主面板：请求构造与响应 -->
        <div class="test-api__main">
          <!-- 请求配置 -->
          <section class="test-api__section">
            <div class="test-api__section-header">
              <h2 class="test-api__section-title">请求配置</h2>
              <div class="test-api__section-actions">
                <button class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm" @click="sendRequest" :disabled="loading">
                  <svg v-if="loading" class="ghibli-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
                  </svg>
                  发送请求
                </button>
                <label class="ghibli-checkbox">
                  <input type="checkbox" v-model="saveAsTest" class="ghibli-checkbox__input" />
                  <span class="ghibli-checkbox__box"></span>
                  保存为测试用例
                </label>
              </div>
            </div>

            <div class="ghibli-grid ghibli-grid-cols-2 ghibli-grid-gap-4">
              <div class="test-api__field">
                <label class="ghibli-label">HTTP 方法</label>
                <select v-model="requestConfig.method" class="ghibli-input ghibli-input--select">
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="PATCH">PATCH</option>
                  <option value="DELETE">DELETE</option>
                  <option value="OPTIONS">OPTIONS</option>
                </select>
              </div>
              <div class="test-api__field">
                <label class="ghibli-label">URL</label>
                <input v-model="requestConfig.url" type="text" class="ghibli-input" placeholder="/api/..." />
              </div>
            </div>

            <!-- Headers -->
            <div class="test-api__field test-api__field--full">
              <label class="ghibli-label">Headers (JSON)</label>
              <textarea
                v-model="requestConfig.headers"
                class="ghibli-input ghibli-input--textarea ghibli-font-mono"
                placeholder='{"Authorization": "Bearer <token>", "Content-Type": "application/json"}'
                rows="3"
              ></textarea>
            </div>

            <!-- Query Params -->
            <div class="test-api__field test-api__field--full">
              <label class="ghibli-label">Query Parameters (JSON)</label>
              <textarea
                v-model="requestConfig.params"
                class="ghibli-input ghibli-input--textarea ghibli-font-mono"
                placeholder='{"page": 1, "page_size": 10}'
                rows="3"
              ></textarea>
            </div>

            <!-- Request Body -->
            <div class="test-api__field test-api__field--full" v-if="['POST', 'PUT', 'PATCH'].includes(requestConfig.method)">
              <label class="ghibli-label">Request Body (JSON)</label>
              <textarea
                v-model="requestConfig.body"
                class="ghibli-input ghibli-input--textarea ghibli-font-mono"
                placeholder='{"username": "test", "password": "123456"}'
                rows="6"
              ></textarea>
            </div>
          </section>

          <!-- 响应结果 -->
          <section class="test-api__section">
            <div class="test-api__section-header">
              <h2 class="test-api__section-title">响应结果</h2>
              <div class="test-api__section-actions">
                <span v-if="responseTime > 0" class="test-api__duration">
                  耗时: {{ responseTime.toFixed(0) }}ms
                </span>
                <button class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm" @click="copyResponse" v-if="response">
                  复制响应
                </button>
              </div>
            </div>

            <div class="test-api__response" v-if="response">
              <div class="test-api__response-status" :class="{ 'test-api__response-status--success': response.ok, 'test-api__response-status--error': !response.ok && !response.error, 'test-api__response-status--network-error': response.error }">
                <span class="test-api__status-code">{{ response.status || 'Error' }}</span>
                <span class="test-api__status-text">
                  {{ response.ok ? '成功' : (response.error ? '网络错误' : '失败') }}
                </span>
              </div>

              <div class="test-api__response-tabs">
                <button
                  class="test-api__response-tab"
                  :class="{ 'test-api__response-tab--active': responseTab === 'body' }"
                  @click="responseTab = 'body'"
                >
                  响应体
                </button>
                <button
                  class="test-api__response-tab"
                  :class="{ 'test-api__response-tab--active': responseTab === 'headers' }"
                  @click="responseTab = 'headers'"
                >
                  响应头
                </button>
              </div>

              <pre class="test-api__response-body ghibli-font-mono" v-if="responseTab === 'body'">{{ formatJSON(response.data) }}</pre>
              <pre class="test-api__response-body ghibli-font-mono" v-else>{{ formatJSON(response.headers) }}</pre>
            </div>

            <div class="test-api__empty" v-else>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="test-api__empty-icon">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <p>暂无响应数据，点击「发送请求」开始测试</p>
            </div>
          </section>
        </div>
      </div>

      <!-- 请求历史 -->
      <section class="test-api__history" v-if="requestHistory.length > 0">
        <h2 class="test-api__section-title">请求历史</h2>
        <div class="test-api__history-header">
          <button class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm" @click="clearHistory">清除历史</button>
        </div>
        <div class="test-api__history-list">
          <div
            v-for="item in requestHistory"
            :key="item.id"
            class="test-api__history-item"
            :class="{ 'test-api__history-item--success': item.success, 'test-api__history-item--error': !item.success }"
          >
            <span class="test-api__history-method">{{ item.method }}</span>
            <span class="test-api__history-url">{{ item.url }}</span>
            <span class="test-api__history-status" :class="item.success ? 'ghibli-text-success' : 'ghibli-text-error'">{{ item.status }}</span>
            <span class="test-api__history-time">{{ item.duration }}</span>
            <span class="test-api__history-timestamp">{{ item.timestamp }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      responseTab: 'body'
    }
  }
}
</script>

<style scoped>
.test-api {
  padding: var(--space-8) 0 var(--space-16);
}

.test-api__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.test-api__title {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.test-api__icon {
  font-size: var(--text-3xl);
}

.test-api__subtitle {
  font-size: var(--text-lg);
  color: var(--color-text-muted);
  margin: 0;
}

.test-api__status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.test-api__layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--space-6);
}

@media (max-width: 1024px) {
  .test-api__layout {
    grid-template-columns: 1fr;
  }

  .test-api__sidebar {
    display: none;
  }
}

.test-api__sidebar {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-4);
  max-height: calc(100vh - 300px);
  overflow-y: auto;
  position: sticky;
  top: 90px;
}

.test-api__category {
  margin-bottom: var(--space-6);
}

.test-api__category:last-child {
  margin-bottom: 0;
}

.test-api__category-title {
  font-family: var(--font-display);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 var(--space-3);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-divider);
}

.test-api__endpoint-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.test-api__endpoint {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: var(--transition-gentle);
  border: 1px solid transparent;
}

.test-api__endpoint:hover {
  background: var(--ghibli-paper-100);
  border-color: var(--color-border);
}

.test-api__endpoint--active {
  background: var(--ghibli-sky-50);
  border-color: var(--ghibli-sky-300);
}

.test-api__endpoint-name {
  display: block;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
  margin-bottom: var(--space-1);
}

.test-api__endpoint-desc {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.test-api__main {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.test-api__section {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.test-api__section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-divider);
  background: var(--ghibli-paper-50);
}

.test-api__section-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0;
}

.test-api__section-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.test-api__duration {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  background: var(--ghibli-paper-100);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
}

.test-api__field {
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-divider);
}

.test-api__field:last-child {
  border-bottom: none;
}

.test-api__field--full {
  grid-column: 1 / -1;
}

.ghibli-input--select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--space-4) center;
  padding-right: var(--space-10);
}

.ghibli-input--textarea {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.6;
  resize: vertical;
  min-height: 100px;
}

.test-api__response {
  padding: var(--space-6);
}

.test-api__response-status {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-4);
}

.test-api__response-status--success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.test-api__response-status--error {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.test-api__response-status--network-error {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.test-api__status-code {
  font-family: var(--font-mono);
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
}

.test-api__status-text {
  font-size: var(--text-base);
  font-weight: var(--font-medium);
}

.test-api__response-tabs {
  display: flex;
  gap: var(--space-1);
  margin-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-divider);
  padding-bottom: var(--space-1);
}

.test-api__response-tab {
  padding: var(--space-2) var(--space-4);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  cursor: pointer;
  transition: var(--transition-gentle);
}

.test-api__response-tab:hover {
  color: var(--color-text);
}

.test-api__response-tab--active {
  color: var(--ghibli-sky-600);
  border-bottom: 2px solid var(--ghibli-sky-500);
  margin-bottom: -1px;
}

.test-api__response-body {
  background: var(--ghibli-ink-800);
  color: var(--ghibli-paper-100);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  overflow-x: auto;
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 500px;
  overflow-y: auto;
}

.test-api__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-8);
  text-align: center;
  color: var(--color-text-muted);
}

.test-api__empty-icon {
  width: 64px;
  height: 64px;
  opacity: 0.3;
  margin-bottom: var(--space-4);
}

.test-api__history {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.test-api__history-header {
  display: flex;
  justify-content: flex-end;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-divider);
  background: var(--ghibli-paper-50);
}

.test-api__history-list {
  max-height: 300px;
  overflow-y: auto;
}

.test-api__history-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-6);
  border-bottom: 1px solid var(--color-divider);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.test-api__history-item:last-child {
  border-bottom: none;
}

.test-api__history-method {
  min-width: 60px;
  padding: var(--space-1) var(--space-2);
  font-weight: var(--font-bold);
  border-radius: var(--radius-md);
  text-align: center;
  background: var(--ghibli-sky-100);
  color: var(--ghibli-sky-700);
}

.test-api__history-item--success .test-api__history-method {
  background: var(--ghibli-forest-100);
  color: var(--ghibli-forest-700);
}

.test-api__history-url {
  flex: 1;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.test-api__history-status {
  min-width: 50px;
  text-align: center;
  font-weight: var(--font-semibold);
}

.test-api__history-time {
  min-width: 80px;
  text-align: right;
  color: var(--color-text-muted);
}

.test-api__history-timestamp {
  min-width: 70px;
  text-align: right;
  color: var(--color-text-muted);
}

/* 响应式 */
@media (max-width: 768px) {
  .test-api__title {
    font-size: var(--text-3xl);
  }

  .ghibli-grid {
    grid-template-columns: 1fr;
  }

  .test-api__history-item {
    flex-wrap: wrap;
  }

  .test-api__history-url {
    order: 99;
    flex-basis: 100%;
    margin-top: var(--space-2);
  }
}
</style>