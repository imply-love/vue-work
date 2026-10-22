<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { postApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import PostCard from '@/components/PostCard.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const router = useRouter()
const authStore = useAuthStore()

// ===== 分类与排序选项 =====
const CATEGORIES = ['新番讨论', '老番怀旧', '安利分享', '求推荐', '同人创作', '其他']
const SORT_OPTIONS = [
  { value: 'latest', label: '最新发布' },
  { value: 'hot', label: '最热' },
  { value: 'replies', label: '最多回复' },
]

// ===== 帖子列表（排序 / 搜索 / 分类） =====
const posts = ref([])
const loading = ref(false)
const listError = ref('')
const page = ref(1)
const pageSize = 10
const totalPages = ref(0)
const hasMore = computed(() => page.value < totalPages.value)

const filters = ref({ sort: 'latest', q: '', category: '' })

const loadPosts = async (reset = false) => {
  if (reset) {
    page.value = 1
    posts.value = []
  }
  loading.value = true
  listError.value = ''
  try {
    const res = await postApi.getList({
      page: page.value,
      page_size: pageSize,
      sort: filters.value.sort,
      q: filters.value.q.trim(),
      category: filters.value.category,
    })
    if (res.code === 0) {
      posts.value = reset ? res.data.list : [...posts.value, ...res.data.list]
      totalPages.value = res.data.total_pages
    } else {
      listError.value = res.message
    }
  } catch (err) {
    listError.value = err.message || '获取帖子失败'
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  if (loading.value || !hasMore.value) return
  page.value += 1
  loadPosts()
}

// 排序 / 分类变化时重置并刷新列表
watch(
  () => [filters.value.sort, filters.value.category],
  () => loadPosts(true)
)

const applySearch = () => loadPosts(true)

// ===== 草稿箱 =====
const showDrafts = ref(false)
const drafts = ref([])
const draftsLoading = ref(false)
const draftsPage = ref(1)
const draftsTotalPages = ref(0)
const draftsTotal = ref(0)
const draftsHasMore = computed(() => draftsPage.value < draftsTotalPages.value)

const loadDrafts = async (reset = false) => {
  if (reset) {
    draftsPage.value = 1
    drafts.value = []
  }
  draftsLoading.value = true
  try {
    const res = await postApi.getDrafts({ page: draftsPage.value, page_size: pageSize })
    if (res.code === 0) {
      drafts.value = reset ? res.data.list : [...drafts.value, ...res.data.list]
      draftsTotalPages.value = res.data.total_pages
      draftsTotal.value = res.data.total
    }
  } catch (err) {
    // 草稿加载失败静默处理，主列表不受影响
    console.error('获取草稿失败:', err)
  } finally {
    draftsLoading.value = false
  }
}

const toggleDrafts = () => {
  showDrafts.value = !showDrafts.value
  if (showDrafts.value && drafts.value.length === 0) {
    loadDrafts(true)
  }
}

const loadMoreDrafts = () => {
  if (draftsLoading.value || !draftsHasMore.value) return
  draftsPage.value += 1
  loadDrafts()
}

// ===== 发帖面板（浮动按钮触发） =====
const panelOpen = ref(false)
const submitting = ref(false)
const formError = ref('')
const editingId = ref(null) // null 表示新建；非空表示编辑草稿

// ===== 删除草稿确认弹窗（站点风格，替代原生 confirm） =====
const draftConfirm = ref(false)
const draftTarget = ref(null)

const emptyForm = () => ({
  title: '',
  cover: '',
  tags: '',
  summary: '',
  category: '',
  content: '',
})
const form = ref(emptyForm())

const openComposer = () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  editingId.value = null
  form.value = emptyForm()
  formError.value = ''
  panelOpen.value = true
  document.body.style.overflow = 'hidden'
}

const closePanel = () => {
  panelOpen.value = false
  document.body.style.overflow = ''
}

// 从草稿进入编辑：加载草稿内容到表单
const editDraft = async (draft) => {
  try {
    const res = await postApi.getDetail(draft.id)
    if (res.code === 0) {
      const item = res.data
      editingId.value = item.id
      form.value = {
        title: item.title || '',
        cover: item.cover || '',
        tags: item.tags || '',
        summary: item.summary || '',
        category: item.category || '',
        content: item.content || '',
      }
      formError.value = ''
      panelOpen.value = true
      document.body.style.overflow = 'hidden'
    }
  } catch (err) {
    window.$ghibli?.showToast({ type: 'error', title: '加载草稿失败', message: err.message || '请稍后重试' })
  }
}

const deleteDraft = (draft) => {
  draftTarget.value = draft
  draftConfirm.value = true
}

const confirmDeleteDraft = async () => {
  const draft = draftTarget.value
  draftTarget.value = null
  if (!draft) return
  try {
    const res = await postApi.remove(draft.id)
    if (res.code === 0) {
      window.$ghibli?.showToast({ type: 'success', title: '已删除', message: '草稿已删除' })
      await loadDrafts(true)
    }
  } catch (err) {
    window.$ghibli?.showToast({ type: 'error', title: '删除失败', message: err.message || '请稍后重试' })
  }
}

const publishDraft = async (draft) => {
  try {
    const res = await postApi.update(draft.id, { ...draft, draft: 0 })
    if (res.code === 0) {
      window.$ghibli?.showToast({ type: 'success', title: '发布成功', message: '帖子已发布到讨论区' })
      await loadDrafts(true)
      await loadPosts(true)
    }
  } catch (err) {
    window.$ghibli?.showToast({ type: 'error', title: '发布失败', message: err.message || '请稍后重试' })
  }
}

// 提交：发布（draft=0）或保存草稿（draft=1）
const submitPost = async (asDraft) => {
  formError.value = ''
  const payload = {
    title: form.value.title.trim(),
    content: form.value.content.trim(),
    cover: form.value.cover.trim(),
    tags: form.value.tags.trim(),
    summary: form.value.summary.trim(),
    category: form.value.category,
    draft: asDraft ? 1 : 0,
  }
  if (!asDraft && !payload.title) {
    formError.value = '请填写帖子标题'
    return
  }
  if (asDraft && !(payload.title || payload.content || payload.summary)) {
    formError.value = '草稿至少需要填写标题、摘要或正文之一'
    return
  }
  submitting.value = true
  try {
    const res = editingId.value
      ? await postApi.update(editingId.value, payload)
      : await postApi.create(payload)
    if (res.code === 0) {
      form.value = emptyForm()
      editingId.value = null
      closePanel()
      window.$ghibli?.showToast({
        type: 'success',
        title: asDraft ? '已保存到草稿箱' : '发帖成功',
        message: asDraft ? '可在「我的草稿」中继续编辑' : '帖子已发布到讨论区',
      })
      await loadPosts(true)
      await refreshDraftCount()
      if (showDrafts.value) await loadDrafts(true)
    } else {
      formError.value = res.message
    }
  } catch (err) {
    formError.value = err.message || '操作失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

const goPostDetail = (id) => router.push(`/posts/${id}`)
const goLogin = () => router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })

// 仅刷新草稿总数徽标，不重置草稿列表（在任意视图下保存/删除/发布草稿后调用）
const refreshDraftCount = async () => {
  if (!authStore.isLoggedIn) return
  try {
    const res = await postApi.getDrafts({ page: 1, page_size: 1 })
    if (res.code === 0) draftsTotal.value = res.data.total
  } catch (err) {
    // 静默：数量徽标刷新失败不阻塞主流程
  }
}

onMounted(() => {
  loadPosts(true)
  refreshDraftCount()
})
</script>

<template>
  <section class="ghibli-section news-page" aria-labelledby="news-title">
    <header class="ghibli-section__header">
      <h1 id="news-title" class="ghibli-section__title">讨论区</h1>
      <p class="ghibli-section__desc">新番吐槽、旧番安利、结局锐评，都来这里开一楼</p>
    </header>

    <div class="ghibli-section__content">
      <!-- 列表工具条：搜索 / 分类 / 排序 / 草稿箱入口 -->
      <div class="news-toolbar" role="search" aria-label="帖子筛选">
        <div class="news-toolbar__search">
          <svg class="news-toolbar__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            v-model="filters.q"
            type="search"
            class="news-toolbar__input"
            placeholder="搜索帖子标题或内容"
            @keyup.enter="applySearch"
          />
          <button class="ghibli-btn ghibli-btn--sm ghibli-btn--primary" @click="applySearch">搜索</button>
        </div>

        <div class="news-toolbar__filters">
          <label class="news-toolbar__field">
            <span class="news-toolbar__label">分类</span>
            <select v-model="filters.category" class="news-toolbar__select">
              <option value="">全部</option>
              <option v-for="cat in CATEGORIES" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </label>
          <label class="news-toolbar__field">
            <span class="news-toolbar__label">排序</span>
            <select v-model="filters.sort" class="news-toolbar__select">
              <option v-for="opt in SORT_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </label>
          <button
            v-if="authStore.isLoggedIn"
            class="ghibli-btn ghibli-btn--sm ghibli-btn--outline"
            :class="{ 'ghibli-btn--active': showDrafts }"
            @click="toggleDrafts"
          >
            {{ showDrafts ? '返回帖子' : '我的草稿' }}
            <span v-if="!showDrafts && draftsTotal > 0" class="draft-count-badge">{{ draftsTotal }}</span>
          </button>
        </div>
      </div>

      <!-- 帖子列表 / 草稿列表 -->
      <div class="news-list">
        <!-- 草稿箱视图 -->
        <template v-if="showDrafts">
          <div v-if="draftsLoading" class="news-list__loading">
            <span class="ghibli-spinner" aria-hidden="true"></span> 加载草稿中...
          </div>
          <div v-else-if="drafts.length === 0" class="ghibli-empty">
            <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <h3 class="ghibli-empty__title">草稿箱空空的</h3>
            <p class="ghibli-empty__desc">点击右下角「写帖子」按钮，可以把没写完的帖子先存进草稿箱</p>
          </div>
          <ul v-else class="draft-list">
            <li v-for="item in drafts" :key="item.id" class="draft-item ghibli-card ghibli-card--outlined">
              <div class="draft-item__main">
                <h3 class="draft-item__title">{{ item.title || '（无标题）' }}</h3>
                <p v-if="item.excerpt" class="draft-item__excerpt">{{ item.excerpt }}</p>
              </div>
              <div class="draft-item__meta">
                <span class="draft-item__time">更新于 {{ item.create_time }}</span>
                <div class="draft-item__actions">
                  <button class="ghibli-btn ghibli-btn--sm ghibli-btn--ghost" @click="editDraft(item)">继续编辑</button>
                  <button class="ghibli-btn ghibli-btn--sm ghibli-btn--primary" @click="publishDraft(item)">发布</button>
                  <button class="ghibli-btn ghibli-btn--sm ghibli-btn--ghost ghibli-btn--danger" @click="deleteDraft(item)">删除</button>
                </div>
              </div>
            </li>
          </ul>
          <div v-if="draftsHasMore" class="news-loadmore">
            <button class="ghibli-btn ghibli-btn--outline" @click="loadMoreDrafts" :disabled="draftsLoading">
              <span v-if="draftsLoading" class="ghibli-spinner" aria-hidden="true"></span>
              {{ draftsLoading ? '加载中...' : '加载更多' }}
            </button>
          </div>
        </template>

        <!-- 帖子列表视图 -->
        <template v-else>
          <div v-if="posts.length === 0 && !loading && !listError" class="ghibli-empty">
            <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <h3 class="ghibli-empty__title">还没有人开口</h3>
            <p class="ghibli-empty__desc">点击右下角「写帖子」按钮，成为第一个开帖的同好吧</p>
          </div>

          <div v-if="listError" class="ghibli-empty">
            <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <h3 class="ghibli-empty__title">帖子走丢了</h3>
            <p class="ghibli-empty__desc">{{ listError }}</p>
            <button class="ghibli-btn ghibli-btn--warm" @click="loadPosts(true)">重试</button>
          </div>

          <div v-else-if="posts.length" class="ghibli-cards">
            <PostCard
              v-for="post in posts"
              :key="post.id"
              :post="post"
              @click="goPostDetail(post.id)"
            />
          </div>

          <div v-if="hasMore" class="news-loadmore">
            <button class="ghibli-btn ghibli-btn--outline" @click="loadMore" :disabled="loading">
              <span v-if="loading" class="ghibli-spinner" aria-hidden="true"></span>
              {{ loading ? '加载中...' : '加载更多' }}
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- 浮动按钮：常驻右下角，无关闭方式，点击开合发帖面板 -->
    <button
      class="news-fab"
      :aria-label="panelOpen ? '收起发帖面板' : '写帖子'"
      :aria-expanded="panelOpen"
      @click="panelOpen ? closePanel() : openComposer()"
    >
      <svg class="news-fab__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M12 5v14M5 12h14"/>
      </svg>
      <span class="news-fab__text">{{ authStore.isLoggedIn ? (panelOpen ? '收起' : '写帖子') : '写帖子' }}</span>
    </button>

    <!-- 发帖面板：Teleport 到 body 顶层，遮罩层自身滚动，保证能滑到顶部、看到按钮 -->
    <Teleport to="body">
      <div v-if="panelOpen" class="news-modal">
        <div class="news-modal__backdrop" @click="closePanel" aria-hidden="true"></div>
        <div class="news-modal__panel" role="dialog" aria-modal="true" aria-labelledby="composer-title">
        <h2 id="composer-title" class="news-modal__title">
          <svg class="news-modal__title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M12 20h9"/>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
          </svg>
          {{ editingId ? '编辑草稿' : '开一个新帖' }}
        </h2>

        <form class="news-modal__form" @submit.prevent="submitPost(false)">
          <div v-if="formError" class="news-modal__error" role="alert">{{ formError }}</div>

          <div class="form-group">
            <label for="post-title" class="form-label">标题 <span class="form-required">*</span></label>
            <div class="ghibli-input-wrapper">
              <input
                id="post-title"
                v-model="form.title"
                type="text"
                class="ghibli-input"
                placeholder="一句话说清你想聊什么，例如：有人看过《哈尔的移动城堡》吗？"
                maxlength="200"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="post-cover" class="form-label">封面图地址</label>
            <div class="ghibli-input-wrapper">
              <input
                id="post-cover"
                v-model="form.cover"
                type="url"
                class="ghibli-input"
                placeholder="选填，以 http:// 或 https:// 开头的图片地址"
                maxlength="255"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="post-tags" class="form-label">标签</label>
            <div class="ghibli-input-wrapper">
              <input
                id="post-tags"
                v-model="form.tags"
                type="text"
                class="ghibli-input"
                placeholder="选填，多个标签用逗号分隔，例如：宫崎骏,治愈,经典"
                maxlength="255"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="post-summary" class="form-label">摘要</label>
            <div class="ghibli-input-wrapper">
              <textarea
                id="post-summary"
                v-model="form.summary"
                class="ghibli-textarea"
                rows="2"
                placeholder="选填，一句话概括帖子内容，让列表卡片更醒目"
                maxlength="255"
              ></textarea>
            </div>
          </div>

          <div class="form-group">
            <label for="post-category" class="form-label">分类</label>
            <select id="post-category" v-model="form.category" class="news-modal__select">
              <option value="">不选择分类</option>
              <option v-for="cat in CATEGORIES" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>

          <div class="form-group">
            <label for="post-content" class="form-label">详情</label>
            <textarea
              id="post-content"
              v-model="form.content"
              class="ghibli-textarea"
              rows="6"
              placeholder="展开聊聊：剧情、角色、观后感，想到什么写什么"
              maxlength="20000"
            ></textarea>
          </div>

          <div class="news-modal__actions">
            <button type="button" class="ghibli-btn ghibli-btn--outline" @click="closePanel">取消</button>
            <button type="button" class="ghibli-btn ghibli-btn--ghost" :disabled="submitting" @click="submitPost(true)">
              <span v-if="submitting" class="ghibli-spinner" aria-hidden="true"></span>
              保存到草稿箱
            </button>
            <button type="submit" class="ghibli-btn ghibli-btn--primary" :disabled="submitting">
              <span v-if="submitting" class="ghibli-spinner" aria-hidden="true"></span>
              {{ submitting ? '提交中...' : '发布帖子' }}
            </button>
          </div>
        </form>
        </div>
      </div>
    </Teleport>

    <!-- 删除草稿确认弹窗（站点风格） -->
    <ConfirmDialog
      v-model="draftConfirm"
      title="删除草稿"
      :message="`确定删除草稿「${draftTarget?.title || '无标题'}」吗？`"
      confirm-text="删除"
      danger
      @confirm="confirmDeleteDraft"
    />
  </section>
</template>

<style scoped>
.news-page {
  padding: var(--space-12) 0 var(--space-20);
}

/* ===== 工具条 ===== */
.news-toolbar {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-10);
  padding: var(--space-6);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-sm);
}

.news-toolbar__search {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.news-toolbar__icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.news-toolbar__input {
  flex: 1;
  min-width: 0;
  padding: var(--space-3) var(--space-5);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  font-size: var(--text-base);
  color: var(--color-text);
  transition: var(--transition-gentle);
}

.news-toolbar__input::placeholder {
  color: var(--color-text-muted);
  opacity: 0.7;
}

.news-toolbar__input:focus {
  outline: none;
  border-color: var(--ghibli-sky-400);
  box-shadow: var(--focus-ring);
}

.news-toolbar__filters {
  display: flex;
  align-items: flex-end;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.news-toolbar__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.news-toolbar__label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-muted);
}

.news-toolbar__select {
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
  transition: var(--transition-gentle);
}

.news-toolbar__select:focus {
  outline: none;
  border-color: var(--ghibli-sky-400);
  box-shadow: var(--focus-ring);
}

/* ===== 列表 ===== */
.news-list {
  min-height: 200px;
}

.news-list__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-16) 0;
  color: var(--color-text-muted);
}

.news-loadmore {
  text-align: center;
  margin-top: var(--space-12);
}

/* ===== 草稿数量徽标 ===== */
.draft-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  margin-left: 6px;
  border-radius: var(--radius-full);
  background: var(--ghibli-sakura-300);
  color: #7a3b2e;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  line-height: 1;
}

/* ===== 草稿列表 ===== */
.draft-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  margin: 0;
  padding: 0;
}

.draft-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-6) var(--space-8);
}

.draft-item__title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0;
}

.draft-item__excerpt {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.draft-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px dashed var(--color-divider);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  flex-wrap: wrap;
}

.draft-item__actions {
  display: flex;
  gap: var(--space-2);
}

/* ===== 浮动按钮（常驻右下角，无关闭方式） ===== */
.news-fab {
  position: fixed;
  right: 28px;
  bottom: 32px;
  z-index: var(--z-index-fixed);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6);
  background: linear-gradient(135deg, var(--ghibli-sky-500), var(--ghibli-forest-500));
  color: #fff;
  border: none;
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  box-shadow: var(--shadow-lg), 0 8px 24px rgba(14, 165, 233, 0.35);
  transition: var(--transition-spring);
}

.news-fab:hover {
  transform: translateY(-3px) scale(1.03);
  box-shadow: var(--shadow-xl), 0 10px 28px rgba(14, 165, 233, 0.45);
}

.news-fab:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring), var(--shadow-lg);
}

.news-fab__icon {
  width: 20px;
  height: 20px;
}

/* ===== 发帖面板：挂在 body 顶层，遮罩层自身滚动 ===== */
.news-modal {
  position: fixed;
  inset: 0;
  z-index: 3000;
  overflow-y: auto;
  padding: 40px 16px 64px;
}

.news-modal__backdrop {
  position: fixed;
  inset: 0;
  background: rgba(20, 24, 32, 0.55);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.news-modal__panel {
  position: relative;
  width: 100%;
  max-width: 680px;
  margin: 0 auto;
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

.news-modal__title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-6);
}

.news-modal__title-icon {
  width: 22px;
  height: 22px;
  color: var(--ghibli-sky-600);
}

.news-modal__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.news-modal__error {
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-bg);
  color: var(--color-error);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
}

.news-modal__select {
  width: 100%;
  padding: var(--space-3) var(--space-5);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  font-size: var(--text-base);
  color: var(--color-text);
  cursor: pointer;
  transition: var(--transition-gentle);
}

.news-modal__select:focus {
  outline: none;
  border-color: var(--ghibli-sky-400);
  box-shadow: var(--focus-ring);
}

.news-modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-top: var(--space-6);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

/* ===== 通用表单 ===== */
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

.ghibli-textarea {
  width: 100%;
  padding: var(--space-4) var(--space-5);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--color-text);
  resize: vertical;
  min-height: 80px;
  transition: var(--transition-gentle);
}

.ghibli-textarea::placeholder {
  color: var(--color-text-muted);
  opacity: 0.7;
}

.ghibli-textarea:hover:not(:disabled) {
  border-color: var(--ghibli-sky-300);
}

.ghibli-textarea:focus {
  outline: none;
  border-color: var(--ghibli-sky-400);
  box-shadow: var(--focus-ring);
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .news-page {
    padding: var(--space-8) 0 var(--space-16);
  }

  .news-toolbar {
    padding: var(--space-4);
  }

  .news-toolbar__search {
    flex-wrap: wrap;
  }

  .news-toolbar__search .ghibli-btn {
    width: 100%;
  }

  .news-toolbar__filters {
    flex-direction: column;
    align-items: stretch;
  }

  .news-fab {
    right: 16px;
    bottom: 20px;
    padding: var(--space-3) var(--space-5);
  }

  .news-modal {
    padding: 12px 8px 32px;
  }

  .news-modal__panel {
    border-radius: var(--radius-2xl);
    padding: var(--space-6);
  }

  .news-modal__actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .news-modal__actions .ghibli-btn {
    width: 100%;
  }
}
</style>
