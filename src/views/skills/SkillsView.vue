<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { resourceApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// ===== 资源列表 =====
const resources = ref([])
const loading = ref(false)
const listError = ref('')
const page = ref(1)
const pageSize = 10
const totalPages = ref(0)
const hasMore = computed(() => page.value < totalPages.value)

const loadResources = async (reset = false) => {
  if (reset) {
    page.value = 1
    resources.value = []
  }
  loading.value = true
  listError.value = ''
  try {
    const res = await resourceApi.getList({ page: page.value, page_size: pageSize })
    if (res.code === 0) {
      resources.value = reset ? res.data.list : [...resources.value, ...res.data.list]
      totalPages.value = res.data.total_pages
    } else {
      listError.value = res.message
    }
  } catch (err) {
    listError.value = err.message || '获取资源列表失败'
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  if (loading.value || !hasMore.value) return
  page.value += 1
  loadResources()
}

// ===== 分享面板（浮动按钮触发） =====
const shareForm = ref({ title: '', link: '', description: '' })
const submitting = ref(false)
const formError = ref('')
const panelOpen = ref(false)

const openComposer = () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  shareForm.value = { title: '', link: '', description: '' }
  formError.value = ''
  panelOpen.value = true
  document.body.style.overflow = 'hidden'
}

const closePanel = () => {
  panelOpen.value = false
  document.body.style.overflow = ''
}

const submitShare = async () => {
  formError.value = ''
  const title = shareForm.value.title.trim()
  const link = shareForm.value.link.trim()
  if (!title) {
    formError.value = '请填写资源标题'
    return
  }
  if (!link) {
    formError.value = '请填写资源链接'
    return
  }
  submitting.value = true
  try {
    const res = await resourceApi.create({ title, link, description: shareForm.value.description.trim() })
    if (res.code === 0) {
      shareForm.value = { title: '', link: '', description: '' }
      closePanel()
      window.$ghibli?.showToast({ type: 'success', title: '分享成功', message: '资源已分享给大家' })
      await loadResources(true)
    } else {
      formError.value = res.message
    }
  } catch (err) {
    formError.value = err.message || '分享失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

const goLogin = () => router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })

onMounted(() => loadResources(true))
</script>

<template>
  <section class="ghibli-section skills-page" aria-labelledby="skills-title">
    <header class="ghibli-section__header">
      <h1 id="skills-title" class="ghibli-section__title">资源分享</h1>
      <p class="ghibli-section__desc">高清资源、字幕组、周边情报，同好们的好东西都放在这儿</p>
    </header>

    <div class="ghibli-section__content">
      <!-- 资源列表 -->
      <div class="resource-list">
        <div v-if="resources.length === 0 && !loading && !listError" class="ghibli-empty">
          <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <h3 class="ghibli-empty__title">还没有人分享</h3>
          <p class="ghibli-empty__desc">手上有好东西？点击右下角「分享」按钮，把好东西交给同好们</p>
        </div>

        <div v-if="listError" class="ghibli-empty">
          <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <h3 class="ghibli-empty__title">资源列表走丢了</h3>
          <p class="ghibli-empty__desc">{{ listError }}</p>
          <button class="ghibli-btn ghibli-btn--warm" @click="loadResources(true)">重试</button>
        </div>

        <ul v-else-if="resources.length" class="resource-list__items">
          <li v-for="item in resources" :key="item.id" class="resource-item ghibli-card ghibli-card--outlined">
            <div class="resource-item__main">
              <h3 class="resource-item__title">
                <a
                  :href="item.link"
                  target="_blank"
                  rel="noopener noreferrer nofollow"
                  class="resource-item__link"
                >
                  {{ item.title }}
                </a>
                <svg class="resource-item__external" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                  <polyline points="15 3 21 3 21 9"/>
                  <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
              </h3>
              <p v-if="item.description" class="resource-item__desc">{{ item.description }}</p>
            </div>
            <div class="resource-item__meta">
              <span class="resource-item__author">{{ item.author_nickname }}</span>
              <time class="resource-item__time" :datetime="item.create_time">{{ item.create_time }}</time>
            </div>
          </li>
        </ul>

        <div v-if="hasMore" class="resource-loadmore">
          <button class="ghibli-btn ghibli-btn--outline" @click="loadMore" :disabled="loading">
            <span v-if="loading" class="ghibli-spinner" aria-hidden="true"></span>
            {{ loading ? '加载中...' : '加载更多' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 浮动按钮：常驻右下角，无关闭方式，点击开合分享面板 -->
    <button
      class="skills-fab"
      :aria-label="panelOpen ? '收起分享面板' : '分享资源'"
      :aria-expanded="panelOpen"
      @click="panelOpen ? closePanel() : openComposer()"
    >
      <svg class="skills-fab__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M12 5v14M5 12h14"/>
      </svg>
      <span class="skills-fab__text">{{ authStore.isLoggedIn ? (panelOpen ? '收起' : '分享') : '分享' }}</span>
    </button>

    <!-- 分享面板 -->
    <div v-if="panelOpen" class="skills-modal">
      <div class="skills-modal__backdrop" @click="closePanel" aria-hidden="true"></div>
      <div class="skills-modal__panel" role="dialog" aria-modal="true" aria-labelledby="share-title">
        <h2 id="share-title" class="skills-modal__title">
          <svg class="skills-modal__title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          分享一个好资源
        </h2>

        <form class="skills-modal__form" @submit.prevent="submitShare">
          <div v-if="formError" class="skills-modal__error" role="alert">{{ formError }}</div>
          <div class="form-group">
            <label for="share-title" class="form-label">资源标题 <span class="form-required">*</span></label>
            <div class="ghibli-input-wrapper">
              <input
                id="share-title"
                v-model="shareForm.title"
                type="text"
                class="ghibli-input"
                placeholder="例如：千与千寻 蓝光 1080P 字幕合集"
                maxlength="200"
              />
            </div>
          </div>
          <div class="form-group">
            <label for="share-link" class="form-label">资源链接 <span class="form-required">*</span></label>
            <div class="ghibli-input-wrapper">
              <input
                id="share-link"
                v-model="shareForm.link"
                type="url"
                class="ghibli-input"
                placeholder="以 http:// 或 https:// 开头的有效地址"
                maxlength="500"
              />
            </div>
          </div>
          <div class="form-group">
            <label for="share-desc" class="form-label">资源描述（选填）</label>
            <textarea
              id="share-desc"
              v-model="shareForm.description"
              class="skills-modal__textarea"
              rows="4"
              placeholder="清晰度、字幕组、大小等补充信息，帮大家判断值不值得下"
              maxlength="5000"
            ></textarea>
          </div>
          <div class="skills-modal__actions">
            <button type="button" class="ghibli-btn ghibli-btn--outline" @click="closePanel">取消</button>
            <button type="submit" class="ghibli-btn ghibli-btn--primary" :disabled="submitting">
              <span v-if="submitting" class="ghibli-spinner" aria-hidden="true"></span>
              {{ submitting ? '分享中...' : '分享资源' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<style scoped>
.skills-page {
  padding: var(--space-12) 0 var(--space-20);
}

/* ===== 资源列表 ===== */
.resource-list {
  min-height: 200px;
}

.resource-list__items {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  margin: 0;
  padding: 0;
}

.resource-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-6) var(--space-8);
}

.resource-item__title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  margin: 0;
}

.resource-item__link {
  color: var(--ghibli-forest-700);
  text-decoration: none;
  word-break: break-all;
  transition: color var(--duration-fast) var(--ease-gentle);
}

.resource-item__link:hover {
  color: var(--ghibli-sky-600);
  text-decoration: underline;
}

.resource-item__link:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
  border-radius: var(--radius-sm);
}

.resource-item__external {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--color-text-muted);
  opacity: 0.7;
}

.resource-item__desc {
  margin: 0;
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
}

.resource-item__meta {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px dashed var(--color-divider);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.resource-item__author {
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.resource-loadmore {
  text-align: center;
  margin-top: var(--space-12);
}

/* ===== 浮动按钮（常驻右下角，无关闭方式） ===== */
.skills-fab {
  position: fixed;
  right: 28px;
  bottom: 32px;
  z-index: var(--z-index-fixed);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6);
  background: linear-gradient(135deg, var(--ghibli-forest-500), var(--ghibli-sky-500));
  color: #fff;
  border: none;
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  box-shadow: var(--shadow-lg), 0 8px 24px rgba(63, 155, 115, 0.35);
  transition: var(--transition-spring);
}

.skills-fab:hover {
  transform: translateY(-3px) scale(1.03);
  box-shadow: var(--shadow-xl), 0 10px 28px rgba(63, 155, 115, 0.45);
}

.skills-fab:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring), var(--shadow-lg);
}

.skills-fab__icon {
  width: 20px;
  height: 20px;
}

/* ===== 分享面板 ===== */
.skills-modal {
  position: fixed;
  inset: 0;
  z-index: var(--z-index-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
}

.skills-modal__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(20, 24, 32, 0.55);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.skills-modal__panel {
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

.skills-modal__title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-6);
}

.skills-modal__title-icon {
  width: 22px;
  height: 22px;
  color: var(--ghibli-forest-600);
}

.skills-modal__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.skills-modal__error {
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-bg);
  color: var(--color-error);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
}

.skills-modal__textarea {
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

.skills-modal__textarea::placeholder {
  color: var(--color-text-muted);
  opacity: 0.7;
}

.skills-modal__textarea:hover:not(:disabled) {
  border-color: var(--ghibli-forest-300);
}

.skills-modal__textarea:focus {
  outline: none;
  border-color: var(--ghibli-forest-400);
  box-shadow: var(--focus-ring);
}

.skills-modal__actions {
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
  .skills-page {
    padding: var(--space-8) 0 var(--space-16);
  }

  .skills-fab {
    right: 16px;
    bottom: 20px;
    padding: var(--space-3) var(--space-5);
  }

  .skills-modal {
    padding: var(--space-3);
    align-items: flex-end;
  }

  .skills-modal__panel {
    max-height: 92vh;
    border-radius: var(--radius-2xl) var(--radius-2xl) 0 0;
    padding: var(--space-6);
  }

  .skills-modal__actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .skills-modal__actions .ghibli-btn {
    width: 100%;
  }
}
</style>
