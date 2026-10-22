<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { favoriteApi, postApi, userApi } from '@/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const post = ref(null)
const loading = ref(true)
const error = ref('')
const favoriting = ref(false)
const favMessage = ref('')

// 点赞
const liking = ref(false)

// 评论区
const repliesList = ref([])
const repliesLoading = ref(false)
const repliesTotal = ref(0)
const replyForm = ref({ content: '' })
const replySending = ref(false)
const replyError = ref('')
const replySuccess = ref('')

const fetchPost = async () => {
  loading.value = true
  error.value = ''
  post.value = null
  favMessage.value = ''
  try {
    const response = await postApi.getDetail(route.params.id)
    if (response.code === 0) {
      post.value = response.data
      loadReplies()
    } else {
      error.value = response.message || '获取帖子详情失败'
    }
  } catch (err) {
    error.value = err.message || '获取帖子详情失败'
  } finally {
    loading.value = false
  }
}

// 评论列表（公开）
const loadReplies = async () => {
  repliesLoading.value = true
  try {
    const response = await postApi.getReplies(route.params.id, { page: 1, page_size: 100 })
    if (response.code === 0) {
      repliesList.value = response.data.list
      repliesTotal.value = response.data.total
    }
  } catch (err) {
    // 评论加载失败不阻塞正文展示
  } finally {
    repliesLoading.value = false
  }
}

// 发表评论（需登录）
const submitReply = async () => {
  replyError.value = ''
  replySuccess.value = ''
  const content = replyForm.value.content.trim()
  if (!content) {
    replyError.value = '评论内容不能为空'
    return
  }
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  replySending.value = true
  try {
    const response = await postApi.addReply(post.value.id, { content })
    if (response.code === 0) {
      replyForm.value.content = ''
      repliesList.value.push(response.data)
      repliesTotal.value += 1
      post.value.reply_count = (post.value.reply_count || 0) + 1
      replySuccess.value = '评论发表成功'
    } else {
      replyError.value = response.message || '发表失败，请重试'
    }
  } catch (err) {
    replyError.value = err.message || '发表失败，请重试'
  } finally {
    replySending.value = false
    setTimeout(() => { replySuccess.value = '' }, 2500)
  }
}

onMounted(() => {
  fetchPost()
})

// 同一路由组件切换帖子 id 时（如从详情页跳到另一篇帖子），组件会被复用，
// onMounted 不会再次触发，这里监听参数变化重新加载，避免页面停留在旧内容。
watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      fetchPost()
    }
  }
)

const goBack = () => {
  router.back()
}

// 点赞 / 取消点赞（仅登录用户）
const toggleLike = async () => {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  if (liking.value || !post.value) return

  liking.value = true
  try {
    const response = await postApi.like(post.value.id)
    if (response.code === 0) {
      post.value.is_liked = response.data.liked
      post.value.like_count = response.data.like_count
    }
  } catch (err) {
    // 网络失败不改变本地状态
  } finally {
    liking.value = false
  }
}

// 关注 / 取消关注作者（仅登录用户，自己帖子不显示按钮）
const following = ref(false)
const toggleFollow = async () => {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  if (following.value || !post.value) return

  following.value = true
  try {
    const response = await userApi.follow(post.value.user_id)
    if (response.code === 0) {
      post.value.is_following = response.data.following
    }
  } catch (err) {
    // 网络失败保持原状态
  } finally {
    following.value = false
  }
}

// 收藏 / 取消收藏（仅登录用户）
const toggleFavorite = async () => {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  if (favoriting.value || !post.value) return

  favoriting.value = true
  favMessage.value = ''
  try {
    const willFavorite = !post.value.is_favorited
    const response = willFavorite
      ? await favoriteApi.add(post.value.id)
      : await favoriteApi.remove(post.value.id)
    if (response.code === 0) {
      post.value.is_favorited = willFavorite
      favMessage.value = willFavorite ? '已加入收藏' : '已取消收藏'
    } else {
      favMessage.value = response.message || '操作失败'
    }
  } catch (err) {
    favMessage.value = err.message || '操作失败，请稍后重试'
  } finally {
    favoriting.value = false
    // 提示 2 秒后自动消失
    setTimeout(() => {
      favMessage.value = ''
    }, 2000)
  }
}
</script>

<template>
  <div class="post-detail-page">
    <div class="detail-container">
      <!-- 返回按钮 -->
      <button class="back-btn" @click="goBack" aria-label="返回">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        <span>返回</span>
      </button>

      <div v-if="loading" class="detail-loading">
        <div class="spinner" aria-hidden="true"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="error" class="detail-error">
        <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <p>{{ error }}</p>
        <button class="ghibli-btn ghibli-btn--warm" @click="fetchPost">重试</button>
      </div>

      <article v-else-if="post" class="post-detail">
        <header class="post-detail__header">
          <div class="post-detail__author">
            <img
              v-if="post.author_avatar"
              :src="post.author_avatar"
              :alt="post.author_nickname"
              class="post-detail__avatar"
            />
            <div v-else class="post-detail__avatar placeholder" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div class="post-detail__author-info">
              <span class="post-detail__author-name">{{ post.author_nickname }}</span>
              <time class="post-detail__time" :datetime="post.create_time">
                {{ formatDate(post.create_time) }}
              </time>
            </div>
            <button
              v-if="authStore.isLoggedIn && !post.is_self"
              type="button"
              class="follow-btn"
              :class="{ 'follow-btn--following': post.is_following }"
              :disabled="following"
              @click="toggleFollow"
            >
              <span v-if="following" class="ghibli-spinner" aria-hidden="true"></span>
              {{ post.is_following ? '已关注' : '关注' }}
            </button>
          </div>
        </header>

        <div v-if="post.cover" class="post-detail__cover">
          <img :src="post.cover" :alt="post.title" />
        </div>

        <div class="post-detail__content">
          <div v-if="post.category || post.tags" class="post-detail__badges">
            <span v-if="post.category" class="post-detail__category">{{ post.category }}</span>
            <span
              v-for="tag in tagList"
              :key="tag"
              class="post-detail__tag"
            >#{{ tag }}</span>
          </div>
          <h1 class="post-detail__title">{{ post.title }}</h1>
          <p v-if="post.summary" class="post-detail__summary">{{ post.summary }}</p>
          <div v-if="post.content" class="post-detail__body" v-html="post.content"></div>
        </div>

        <footer class="post-detail__footer">
          <div class="post-detail__stats">
            <span class="post-detail__stat" title="浏览数">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              {{ post.view_count }}
            </span>
            <!-- 点赞按钮：可点击切换，登录用户可用 -->
            <button
              type="button"
              class="stat-btn"
              :class="{ 'stat-btn--active': post.is_liked }"
              :disabled="liking"
              :title="post.is_liked ? '取消点赞' : '点赞'"
              @click="toggleLike"
            >
              <svg class="stat-icon" viewBox="0 0 24 24" :fill="post.is_liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              {{ post.like_count }}
            </button>
            <span class="post-detail__stat" title="评论数">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              {{ post.reply_count }}
            </span>
          </div>

          <!-- 收藏按钮：登录用户可收藏/取消收藏 -->
          <div class="post-detail__fav-zone">
            <button
              type="button"
              class="ghibli-btn fav-btn"
              :class="{ 'fav-btn--active': post.is_favorited }"
              :disabled="favoriting"
              @click="toggleFavorite"
            >
              <svg class="fav-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
              </svg>
              <span v-if="favoriting">处理中...</span>
              <span v-else>{{ post.is_favorited ? '已收藏' : '收藏' }}</span>
            </button>
            <span v-if="favMessage" class="fav-message" role="status">{{ favMessage }}</span>
          </div>
        </footer>
      </article>

      <!-- 评论区：post 未加载完成时不渲染，避免空对象访问报错 -->
      <section v-if="post" class="replies-section">
        <h2 class="replies-title">
          评论<span class="replies-title__count">{{ post.reply_count }}</span>
        </h2>

        <!-- 发表评论：登录用户可见表单，未登录提示去登录 -->
        <div v-if="authStore.isLoggedIn" class="reply-form">
          <textarea
            v-model="replyForm.content"
            class="reply-input"
            rows="3"
            maxlength="500"
            placeholder="写下你的评论…"
          ></textarea>
          <div class="reply-form__foot">
            <span class="reply-count-hint">{{ replyForm.content.length }}/500</span>
            <button
              type="button"
              class="ghibli-btn ghibli-btn--primary"
              :disabled="replySending"
              @click="submitReply"
            >
              <span v-if="replySending" class="ghibli-btn__loading">
                <span class="ghibli-spinner" aria-hidden="true"></span>
                发表中...
              </span>
              <span v-else>发表评论</span>
            </button>
          </div>
          <p v-if="replyError" class="reply-hint reply-hint--error" role="alert">{{ replyError }}</p>
          <p v-if="replySuccess" class="reply-hint reply-hint--success" role="status">{{ replySuccess }}</p>
        </div>
        <div v-else class="reply-login-tip">
          <span>登录后即可参与评论</span>
          <button type="button" class="ghibli-btn ghibli-btn--primary" @click="router.push('/login')">去登录</button>
        </div>

        <!-- 评论列表 -->
        <p v-if="repliesLoading" class="reply-tip">加载中…</p>
        <p v-else-if="repliesList.length === 0" class="reply-tip">还没有评论，来抢沙发吧～</p>
        <ul v-else class="reply-list">
          <li v-for="item in repliesList" :key="item.id" class="reply-item">
            <img
              v-if="item.author_avatar"
              :src="item.author_avatar"
              :alt="item.author_nickname"
              class="reply-avatar"
            />
            <div v-else class="reply-avatar placeholder" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div class="reply-body">
              <div class="reply-meta">
                <span class="reply-author">{{ item.author_nickname }}</span>
                <time class="reply-time">{{ formatDate(item.create_time) }}</time>
              </div>
              <p class="reply-content">{{ item.content }}</p>
            </div>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script>
export default {
  computed: {
    tagList() {
      if (!this.post || !this.post.tags) return []
      return this.post.tags
        .split(/[,，]/)
        .map((t) => t.trim())
        .filter(Boolean)
        .slice(0, 5)
    }
  },
  methods: {
    formatDate(dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    }
  }
}
</script>

<style scoped>
.post-detail-page {
  min-height: 100%;
}

.detail-container {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-12) var(--space-6) var(--space-20);
}

/* Back Button */
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-8);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: var(--text-sm);
  cursor: pointer;
  transition: var(--transition-gentle);
  margin-bottom: var(--space-12);
}

.back-btn:hover {
  border-color: var(--ghibli-sky-300);
  color: var(--ghibli-sky-600);
  background: var(--ghibli-sky-50);
}

.back-btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

/* Loading & Error */
.detail-loading,
.detail-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  text-align: center;
  gap: var(--space-8);
  color: var(--color-text-muted);
}

.detail-error p {
  margin: 0;
  color: var(--color-text-muted);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--ghibli-sky-100);
  border-top-color: var(--ghibli-sky-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  width: 64px;
  height: 64px;
  color: var(--ghibli-sakura-400);
}

/* Post Detail */
.post-detail {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.post-detail__header {
  padding: var(--space-12);
  border-bottom: 1px dashed var(--color-divider);
}

.post-detail__author {
  display: flex;
  align-items: center;
  gap: var(--space-8);
}

.post-detail__avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--color-border);
}

.post-detail__avatar.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--ghibli-sky-100) 0%, var(--ghibli-forest-100) 100%);
  color: var(--ghibli-sky-600);
}

.post-detail__avatar.placeholder svg {
  width: 24px;
  height: 24px;
}

.post-detail__author-info {
  display: flex;
  flex-direction: column;
}

.post-detail__author-name {
  font-weight: var(--font-semibold);
  color: var(--color-text);
  font-size: var(--text-base);
}

.post-detail__time {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.follow-btn {
  margin-left: auto;
  padding: var(--space-2) var(--space-6);
  border: 1px solid var(--ghibli-sky-400);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--ghibli-sky-600);
  font-family: inherit;
  font-size: var(--text-sm);
  cursor: pointer;
  transition: var(--transition-gentle);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.follow-btn:hover:not(:disabled) {
  background: var(--ghibli-sky-50);
  border-color: var(--ghibli-sky-500);
}

.follow-btn--following {
  border-color: var(--color-border);
  background: var(--color-bg-soft);
  color: var(--color-text-muted);
}

.follow-btn:disabled {
  opacity: 0.7;
  cursor: default;
}

.post-detail__cover {
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.post-detail__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.post-detail__content {
  padding: var(--space-16) var(--space-12);
}

.post-detail__title {
  font-family: var(--font-display);
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-8);
  line-height: var(--leading-tight);
  letter-spacing: 0.02em;
}

.post-detail__badges {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.post-detail__category {
  padding: 3px 12px;
  background: linear-gradient(135deg, var(--ghibli-sky-100), var(--ghibli-sky-200));
  color: var(--ghibli-sky-700);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.post-detail__tag {
  padding: 3px 10px;
  background: var(--ghibli-sakura-50);
  color: var(--ghibli-sakura-600);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
}

.post-detail__summary {
  margin: 0 0 var(--space-12);
  padding: var(--space-4) var(--space-6);
  background: var(--ghibli-sky-50);
  border-left: 4px solid var(--ghibli-sky-400);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
}

.post-detail__body {
  font-size: var(--text-base);
  color: var(--color-text);
  line-height: var(--leading-loose);
}

.post-detail__body p {
  margin: 0 0 1.5em;
  color: inherit;
}

.post-detail__body img {
  max-width: 100%;
  border-radius: var(--radius-lg);
  margin: 1.5em 0;
}

.post-detail__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-6);
  padding: var(--space-10) var(--space-12);
  border-top: 1px dashed var(--color-divider);
  background: var(--ghibli-paper-100);
}

.post-detail__stats {
  display: flex;
  gap: var(--space-16);
}

.post-detail__stat {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

.stat-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: var(--ghibli-paper-500);
}

/* 收藏按钮 */
.post-detail__fav-zone {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.fav-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-8);
  border: 1px solid var(--ghibli-sakura-300);
  background: var(--color-bg-card);
  color: var(--ghibli-sakura-600);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: var(--transition-gentle);
}

.fav-btn:hover {
  border-color: var(--ghibli-sakura-400);
  background: var(--ghibli-sakura-50);
  transform: translateY(-1px);
}

.fav-btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.fav-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.fav-btn--active {
  background: linear-gradient(135deg, var(--ghibli-sakura-400), var(--ghibli-sakura-500));
  border-color: var(--ghibli-sakura-500);
  color: #fff;
}

.fav-btn__icon {
  width: 16px;
  height: 16px;
}

.fav-message {
  font-size: var(--text-xs);
  color: var(--ghibli-forest-700);
  animation: fadeIn 0.3s ease;
}

/* 点赞按钮（footer 统计区里的可点击项） */
.stat-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
  background: none;
  border: none;
  border-radius: var(--radius-full);
  font-size: var(--text-base);
  color: var(--color-text-muted);
  font-family: inherit;
  cursor: pointer;
  transition: var(--transition-gentle);
}

.stat-btn:hover:not(:disabled) {
  color: var(--ghibli-sakura-500);
  background: var(--ghibli-sakura-50);
}

.stat-btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.stat-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.stat-btn--active {
  color: var(--ghibli-sakura-500);
}

/* ===== 评论区 ===== */
.replies-section {
  margin-top: var(--space-12);
  padding: var(--space-12);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-sm);
}

.replies-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-8);
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.replies-title__count {
  font-family: var(--font-mono);
  font-size: var(--text-base);
  color: var(--ghibli-sakura-500);
}

.reply-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding-bottom: var(--space-8);
  border-bottom: 1px dashed var(--color-divider);
  margin-bottom: var(--space-8);
}

.reply-input {
  width: 100%;
  padding: var(--space-5) var(--space-6);
  background: var(--ghibli-paper-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text);
  font-family: inherit;
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  resize: vertical;
  outline: none;
  transition: var(--transition-gentle);
}

.reply-input:focus {
  border-color: var(--ghibli-sky-400);
  box-shadow: var(--focus-ring);
}

.reply-form__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.reply-count-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.reply-hint {
  margin: 0;
  font-size: var(--text-sm);
}

.reply-hint--error {
  color: var(--color-error);
}

.reply-hint--success {
  color: var(--ghibli-forest-700);
}

.reply-login-tip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-6);
  background: var(--ghibli-paper-50);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  margin-bottom: var(--space-8);
}

.reply-tip {
  margin: 0;
  padding: var(--space-6) 0;
  text-align: center;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.reply-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.reply-item {
  display: flex;
  gap: var(--space-5);
}

.reply-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid var(--color-border);
}

.reply-avatar.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--ghibli-sky-100) 0%, var(--ghibli-forest-100) 100%);
  color: var(--ghibli-sky-600);
}

.reply-avatar.placeholder svg {
  width: 20px;
  height: 20px;
}

.reply-body {
  flex: 1;
  min-width: 0;
}

.reply-meta {
  display: flex;
  align-items: baseline;
  gap: var(--space-4);
  margin-bottom: var(--space-2);
}

.reply-author {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.reply-time {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.reply-content {
  margin: 0;
  font-size: var(--text-base);
  color: var(--color-text);
  line-height: var(--leading-normal);
  word-break: break-word;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-2px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 响应式 */
@media (max-width: 768px) {
  .detail-container {
    padding: var(--space-10) var(--space-4) var(--space-16);
  }

  .post-detail__header,
  .post-detail__content,
  .post-detail__footer {
    padding-left: var(--space-8);
    padding-right: var(--space-8);
  }

  .post-detail__stats {
    gap: var(--space-12);
  }
}

@media (max-width: 480px) {
  .post-detail__title {
    font-size: var(--text-2xl);
  }

  .post-detail__stats {
    flex-wrap: wrap;
    gap: var(--space-8);
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }

  .back-btn {
    transition: none;
  }
}
</style>