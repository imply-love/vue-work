<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { postApi } from '@/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const post = ref(null)
const loading = ref(true)
const error = ref('')

const fetchPost = async () => {
  loading.value = true
  error.value = ''
  post.value = null
  try {
    const response = await postApi.getDetail(route.params.id)
    if (response.code === 0) {
      post.value = response.data
    } else {
      error.value = response.message || '获取帖子详情失败'
    }
  } catch (err) {
    error.value = err.message || '获取帖子详情失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPost()
})

const goBack = () => {
  router.back()
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
          </div>
        </header>

        <div v-if="post.cover" class="post-detail__cover">
          <img :src="post.cover" :alt="post.title" />
        </div>

        <div class="post-detail__content">
          <h1 class="post-detail__title">{{ post.title }}</h1>
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
            <span class="post-detail__stat" title="点赞数">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              {{ post.like_count }}
            </span>
            <span class="post-detail__stat" title="回复数">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              {{ post.reply_count }}
            </span>
          </div>
        </footer>
      </article>
    </div>
  </div>
</template>

<script>
export default {
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
  margin: 0 0 var(--space-12);
  line-height: var(--leading-tight);
  letter-spacing: 0.02em;
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