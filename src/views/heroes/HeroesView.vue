<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { animeRequestApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// ===== 求番列表 =====
const requests = ref([])
const loading = ref(false)
const listError = ref('')
const page = ref(1)
const pageSize = 10
const totalPages = ref(0)
const hasMore = computed(() => page.value < totalPages.value)

const loadRequests = async (reset = false) => {
  if (reset) {
    page.value = 1
    requests.value = []
  }
  loading.value = true
  listError.value = ''
  try {
    const res = await animeRequestApi.getList({ page: page.value, page_size: pageSize })
    if (res.code === 0) {
      requests.value = reset ? res.data.list : [...requests.value, ...res.data.list]
      totalPages.value = res.data.total_pages
    } else {
      listError.value = res.message
    }
  } catch (err) {
    listError.value = err.message || '获取求番列表失败'
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  if (loading.value || !hasMore.value) return
  page.value += 1
  loadRequests()
}

// ===== 求番面板（浮动按钮触发） =====
const requestForm = ref({ anime_name: '', reason: '' })
const submitting = ref(false)
const formError = ref('')
const panelOpen = ref(false)

const openComposer = () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  requestForm.value = { anime_name: '', reason: '' }
  formError.value = ''
  panelOpen.value = true
  document.body.style.overflow = 'hidden'
}

const closePanel = () => {
  panelOpen.value = false
  document.body.style.overflow = ''
}

const submitRequest = async () => {
  formError.value = ''
  const animeName = requestForm.value.anime_name.trim()
  if (!animeName) {
    formError.value = '请填写想求的番剧名称'
    return
  }
  submitting.value = true
  try {
    const res = await animeRequestApi.create({ anime_name: animeName, reason: requestForm.value.reason.trim() })
    if (res.code === 0) {
      requestForm.value = { anime_name: '', reason: '' }
      closePanel()
      window.$ghibli?.showToast({ type: 'success', title: '求番成功', message: '管理员看到后会尽快收录' })
      await loadRequests(true)
    } else {
      formError.value = res.message
    }
  } catch (err) {
    formError.value = err.message || '求番失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

const goLogin = () => router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })

onMounted(() => loadRequests(true))
</script>

<template>
  <section class="ghibli-section heroes-page" aria-labelledby="heroes-title">
    <header class="ghibli-section__header">
      <h1 id="heroes-title" class="ghibli-section__title">番剧库</h1>
      <p class="ghibli-section__desc">从当季新番到经典老番，找不到的番就求一求</p>
    </header>

    <div class="ghibli-section__content">
      <!-- 求番列表 -->
      <div class="request-list">
        <div v-if="requests.length === 0 && !loading && !listError" class="ghibli-empty">
          <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <rect x="2" y="7" width="20" height="14" rx="2"/>
            <polyline points="17 2 12 7 7 2"/>
            <path d="M10 12.5 L15 15 L10 17.5 Z"/>
          </svg>
          <h3 class="ghibli-empty__title">还没有人求番</h3>
          <p class="ghibli-empty__desc">想看的番不在库里？点击右下角「求番」按钮，让管理员安排上</p>
        </div>

        <div v-if="listError" class="ghibli-empty">
          <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <h3 class="ghibli-empty__title">求番列表走丢了</h3>
          <p class="ghibli-empty__desc">{{ listError }}</p>
          <button class="ghibli-btn ghibli-btn--warm" @click="loadRequests(true)">重试</button>
        </div>

        <ul v-else-if="requests.length" class="request-list__items">
          <li v-for="item in requests" :key="item.id" class="request-item ghibli-card ghibli-card--outlined">
            <div class="request-item__main">
              <div class="request-item__head">
                <h3 class="request-item__name">{{ item.anime_name }}</h3>
                <span
                  class="ghibli-badge"
                  :class="item.status === 1 ? 'ghibli-badge--success' : 'ghibli-badge--warning'"
                >
                  {{ item.status === 1 ? '已收录' : '待收录' }}
                </span>
              </div>
              <p v-if="item.reason" class="request-item__reason">{{ item.reason }}</p>
            </div>
            <div class="request-item__meta">
              <span class="request-item__author">{{ item.author_nickname }}</span>
              <time class="request-item__time" :datetime="item.create_time">{{ item.create_time }}</time>
            </div>
          </li>
        </ul>

        <div v-if="hasMore" class="request-loadmore">
          <button class="ghibli-btn ghibli-btn--outline" @click="loadMore" :disabled="loading">
            <span v-if="loading" class="ghibli-spinner" aria-hidden="true"></span>
            {{ loading ? '加载中...' : '加载更多' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 浮动按钮：常驻右下角，无关闭方式，点击开合求番面板 -->
    <button
      class="heroes-fab"
      :aria-label="panelOpen ? '收起求番面板' : '求番'"
      :aria-expanded="panelOpen"
      @click="panelOpen ? closePanel() : openComposer()"
    >
      <svg class="heroes-fab__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M12 5v14M5 12h14"/>
      </svg>
      <span class="heroes-fab__text">{{ authStore.isLoggedIn ? (panelOpen ? '收起' : '求番') : '求番' }}</span>
    </button>

    <!-- 求番面板 -->
    <div v-if="panelOpen" class="heroes-modal">
      <div class="heroes-modal__backdrop" @click="closePanel" aria-hidden="true"></div>
      <div class="heroes-modal__panel" role="dialog" aria-modal="true" aria-labelledby="request-title">
        <h2 id="request-title" class="heroes-modal__title">
          <svg class="heroes-modal__title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
          求一部番
        </h2>

        <form class="heroes-modal__form" @submit.prevent="submitRequest">
          <div v-if="formError" class="heroes-modal__error" role="alert">{{ formError }}</div>
          <div class="form-group">
            <label for="anime-name" class="form-label">番剧名称 <span class="form-required">*</span></label>
            <div class="ghibli-input-wrapper">
              <input
                id="anime-name"
                v-model="requestForm.anime_name"
                type="text"
                class="ghibli-input"
                placeholder="想看的番叫什么？例如：你想求《千与千寻》的资源库收录"
                maxlength="100"
              />
            </div>
          </div>
          <div class="form-group">
            <label for="request-reason" class="form-label">求番理由（选填）</label>
            <textarea
              id="request-reason"
              v-model="requestForm.reason"
              class="heroes-modal__textarea"
              rows="4"
              placeholder="为什么想看这部番？有推荐人也可以写上，方便管理员优先收录"
              maxlength="5000"
            ></textarea>
          </div>
          <div class="heroes-modal__actions">
            <button type="button" class="ghibli-btn ghibli-btn--outline" @click="closePanel">取消</button>
            <button type="submit" class="ghibli-btn ghibli-btn--primary" :disabled="submitting">
              <span v-if="submitting" class="ghibli-spinner" aria-hidden="true"></span>
              {{ submitting ? '提交中...' : '提交求番' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<style scoped>
.heroes-page {
  padding: var(--space-12) 0 var(--space-20);
}

/* ===== 求番列表 ===== */
.request-list {
  min-height: 200px;
}

.request-list__items {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  margin: 0;
  padding: 0;
}

.request-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-6) var(--space-8);
}

.request-item__head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.request-item__name {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0;
}

.request-item__reason {
  margin: 0;
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
}

.request-item__meta {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px dashed var(--color-divider);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.request-item__author {
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.request-loadmore {
  text-align: center;
  margin-top: var(--space-12);
}

/* ===== 浮动按钮（常驻右下角，无关闭方式） ===== */
.heroes-fab {
  position: fixed;
  right: 28px;
  bottom: 32px;
  z-index: var(--z-index-fixed);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6);
  background: linear-gradient(135deg, var(--ghibli-sakura-500), var(--ghibli-warm-500));
  color: #fff;
  border: none;
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  box-shadow: var(--shadow-lg), 0 8px 24px rgba(244, 114, 182, 0.35);
  transition: var(--transition-spring);
}

.heroes-fab:hover {
  transform: translateY(-3px) scale(1.03);
  box-shadow: var(--shadow-xl), 0 10px 28px rgba(244, 114, 182, 0.45);
}

.heroes-fab:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring), var(--shadow-lg);
}

.heroes-fab__icon {
  width: 20px;
  height: 20px;
}

/* ===== 求番面板 ===== */
.heroes-modal {
  position: fixed;
  inset: 0;
  z-index: var(--z-index-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
}

.heroes-modal__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(20, 24, 32, 0.55);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.heroes-modal__panel {
  position: relative;
  width: 100%;
  max-width: 560px;
  max-height: 88vh;
  overflow-y: auto;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  padding: var(--space-8);
  box-shadow: var(--shadow-xl);
  animation: modalIn var(--duration-normal) var(--ease-spring);
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.heroes-modal__title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-6);
}

.heroes-modal__title-icon {
  width: 22px;
  height: 22px;
  color: var(--ghibli-sakura-600);
}

.heroes-modal__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.heroes-modal__error {
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-bg);
  color: var(--color-error);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
}

.heroes-modal__textarea {
  width: 100%;
  padding: var(--space-4) var(--space-5);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--color-text);
  resize: vertical;
  min-height: 96px;
  transition: var(--transition-gentle);
}

.heroes-modal__textarea::placeholder {
  color: var(--color-text-muted);
  opacity: 0.7;
}

.heroes-modal__textarea:hover:not(:disabled) {
  border-color: var(--ghibli-sakura-300);
}

.heroes-modal__textarea:focus {
  outline: none;
  border-color: var(--ghibli-sakura-400);
  box-shadow: var(--focus-ring);
}

.heroes-modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

/* ===== 表单字段 ===== */
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-label {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.form-required {
  color: var(--color-error);
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .heroes-page {
    padding: var(--space-8) 0 var(--space-16);
  }

  .heroes-fab {
    right: 16px;
    bottom: 20px;
    padding: var(--space-3) var(--space-5);
  }

  .heroes-modal {
    padding: var(--space-3);
    align-items: flex-end;
  }

  .heroes-modal__panel {
    max-height: 92vh;
    border-radius: var(--radius-2xl) var(--radius-2xl) 0 0;
    padding: var(--space-6);
  }

  .heroes-modal__actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .heroes-modal__actions .ghibli-btn {
    width: 100%;
  }
}
</style>
