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
  try {
    // 这里暂时用列表接口模拟，实际应该有详情接口
    const response = await postApi.getList({ page: 1, page_size: 1 })
    if (response.code === 0 && response.data.list.length > 0) {
      // 找到对应ID的帖子（实际项目中应该有专门的详情接口）
      post.value = response.data.list.find(p => p.id === parseInt(route.params.id)) || response.data.list[0]
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
        <button class="btn btn-primary" @click="fetchPost">重试</button>
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
  min-height: 100vh;
  background: #0d0d0d;
  padding-top: 72px;
}

.detail-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* Back Button */
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #333;
  border-radius: 50px;
  color: #999;
  font-family: inherit;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 24px;
}

.back-btn:hover {
  border-color: #c9a84c;
  color: #c9a84c;
  background: rgba(201, 168, 76, 0.1);
}

.back-btn:focus-visible {
  outline: 2px solid #c9a84c;
  outline-offset: 2px;
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
  min-height: 400px;
  text-align: center;
  gap: 16px;
  color: #999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top-color: #c9a84c;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  width: 64px;
  height: 64px;
  color: #dc3545;
}

/* Post Detail */
.post-detail {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 16px;
  overflow: hidden;
}

.post-detail__header {
  padding: 24px;
  border-bottom: 1px solid #333;
}

.post-detail__author {
  display: flex;
  align-items: center;
  gap: 14px;
}

.post-detail__avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #333;
}

.post-detail__avatar.placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #333 0%, #222 100%);
  border: 2px solid #333;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
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
  font-weight: 600;
  color: #e8e8e8;
  font-size: 1rem;
}

.post-detail__time {
  font-size: 0.8125rem;
  color: #666;
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
  padding: 32px 24px;
}

.post-detail__title {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 700;
  color: #e8e8e8;
  margin: 0 0 24px;
  line-height: 1.4;
  letter-spacing: 0.02em;
}

.post-detail__body {
  font-size: 1rem;
  color: #e8e8e8;
  line-height: 1.9;
}

.post-detail__body p {
  margin: 0 0 1.5em;
}

.post-detail__body img {
  max-width: 100%;
  border-radius: 8px;
  margin: 1.5em 0;
}

.post-detail__footer {
  padding: 20px 24px;
  border-top: 1px solid #333;
  background: #0d0d0d;
}

.post-detail__stats {
  display: flex;
  gap: 28px;
}

.post-detail__stat {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9375rem;
  color: #999;
}

.stat-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #666;
}

/* 响应式 */
@media (max-width: 768px) {
  .detail-container {
    padding: 24px 20px 60px;
  }

  .post-detail__content {
    padding: 24px 20px;
  }

  .post-detail__stats {
    gap: 20px;
  }
}

@media (max-width: 480px) {
  .post-detail__title {
    font-size: 1.375rem;
  }

  .post-detail__stats {
    flex-wrap: wrap;
    gap: 16px;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .spinner,
  .back-btn {
    animation: none;
    transition: none;
  }
}
</style>