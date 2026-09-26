<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePostStore } from '@/stores/posts'
import { useAuthStore } from '@/stores/auth'
import PostCard from '@/components/PostCard.vue'

const router = useRouter()
const postStore = usePostStore()
const authStore = useAuthStore()

const loading = ref(false)
const showLoadMore = ref(false)

const loadPosts = async (append = false) => {
  loading.value = true
  const result = await postStore.fetchPosts(append ? postStore.pagination.page + 1 : 1, append)
  loading.value = false
  showLoadMore.value = postStore.hasMore && result.success
}

const handleLoadMore = async () => {
  if (loading.value || !postStore.hasMore) return
  loading.value = true
  const result = await postStore.loadMore()
  loading.value = false
  showLoadMore.value = postStore.hasMore && result.success
}

const handleScroll = () => {
  // 可选：实现无限滚动加载
  const { scrollTop, scrollHeight, clientHeight } = document.documentElement
  if (scrollTop + clientHeight >= scrollHeight - 200 && !loading.value && postStore.hasMore) {
    handleLoadMore()
  }
}

onMounted(() => {
  loadPosts()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const goPostDetail = (id) => {
  router.push(`/posts/${id}`)
}

const goLogin = () => {
  router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
}
</script>

<template>
  <div class="home-page">
    <!-- 顶部横幅 -->
    <section class="home-banner" aria-labelledby="banner-title">
      <div class="banner-content">
        <h1 id="banner-title" class="banner-title">云墨江湖</h1>
        <p class="banner-subtitle">一笔云墨，绘尽江湖梦</p>
        <p class="banner-desc">在此记录你的侠客行，分享江湖见闻，结识志同道合的武林同道</p>
        <div class="banner-actions">
          <button
            v-if="!authStore.isLoggedIn"
            class="btn btn-primary"
            @click="goLogin"
          >
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
              <polyline points="10 17 15 12 10 7"/>
              <line x1="15" y1="12" x2="3" y2="12"/>
            </svg>
            开始你的江湖之旅
          </button>
          <a
            v-else
            class="btn btn-primary"
            href="#posts-list"
          >
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            浏览最新动态
          </a>
        </div>
      </div>
      <div class="banner-decor" aria-hidden="true">
        <div class="banner-line"></div>
        <div class="banner-line"></div>
        <div class="banner-line"></div>
      </div>
    </section>

    <!-- 帖子列表 -->
    <section id="posts-list" class="posts-section" aria-labelledby="posts-title">
      <div class="section-container">
        <header class="section-header">
          <h2 id="posts-title" class="section-title">江湖动态</h2>
          <p class="section-desc">最新的侠客见闻与武林轶事</p>
        </header>

        <div v-if="postStore.posts.length === 0 && !loading" class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
          <p class="empty-text">暂无江湖动态</p>
          <p class="empty-hint">成为第一位记录江湖的侠客吧</p>
        </div>

        <div v-else class="posts-grid">
          <PostCard
            v-for="post in postStore.posts"
            :key="post.id"
            :post="post"
            @click="goPostDetail(post.id)"
          />
        </div>

        <!-- 加载更多 -->
        <div v-if="showLoadMore" class="load-more">
          <button
            class="btn btn-secondary"
            @click="handleLoadMore"
            :disabled="loading"
          >
            <span v-if="loading" class="btn-loading">
              <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
              </svg>
              加载中...
            </span>
            <span v-else>
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <polyline points="23 4 12 15 1 4"/>
              </svg>
              加载更多
            </span>
          </button>
        </div>

        <!-- 加载错误 -->
        <div v-if="postStore.error && postStore.posts.length === 0" class="error-state">
          <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <p class="error-text">{{ postStore.error }}</p>
          <button class="btn btn-secondary" @click="loadPosts">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M23 4v6h-6"/>
              <path d="M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            重试
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #0d0d0d;
}

/* Banner */
.home-banner {
  position: relative;
  min-height: 60vh;
  max-height: 700px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 24px 60px;
  overflow: hidden;
}

.banner-content {
  position: relative;
  z-index: 2;
  text-align: center;
  max-width: 800px;
}

.banner-title {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0.04em;
  margin: 0 0 16px;
  background: linear-gradient(135deg, #e8e8e8 0%, #c9a84c 50%, #e8d57a 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.banner-subtitle {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: clamp(1rem, 2.5vw, 1.375rem);
  color: #c9a84c;
  letter-spacing: 0.2em;
  margin: 0 0 24px;
  opacity: 0.9;
}

.banner-desc {
  font-size: clamp(1rem, 1.5vw, 1.125rem);
  color: #999;
  line-height: 1.8;
  margin: 0 0 40px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.banner-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  border-radius: 50px;
  font-family: inherit;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  text-decoration: none;
}

.btn:focus-visible {
  outline: 2px solid #c9a84c;
  outline-offset: 3px;
}

.btn-primary {
  background: linear-gradient(135deg, #c9a84c 0%, #a68a3a 100%);
  color: #0d0d0d;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(201, 168, 76, 0.4);
}

.btn-secondary {
  background: transparent;
  color: #e8e8e8;
  border: 1px solid #333;
}

.btn-secondary:hover:not(:disabled) {
  border-color: #c9a84c;
  color: #c9a84c;
  background: rgba(201, 168, 76, 0.1);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.btn-loading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.banner-decor {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.banner-line {
  position: absolute;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, transparent, rgba(201, 168, 76, 0.3), transparent);
}

.banner-line:nth-child(1) { left: 20%; animation: lineFlow 8s ease-in-out infinite; }
.banner-line:nth-child(2) { left: 50%; animation: lineFlow 8s ease-in-out infinite 1.5s; }
.banner-line:nth-child(3) { left: 80%; animation: lineFlow 8s ease-in-out infinite 3s; }

@keyframes lineFlow {
  0%, 100% { opacity: 0.1; transform: scaleY(0.5); }
  50% { opacity: 0.5; transform: scaleY(1); }
}

/* Posts Section */
.posts-section {
  padding: 60px 24px 80px;
}

.section-container {
  max-width: 900px;
  margin: 0 auto;
}

.section-header {
  text-align: center;
  margin-bottom: 48px;
}

.section-title {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: clamp(1.75rem, 3vw, 2.25rem);
  font-weight: 700;
  color: #e8e8e8;
  margin: 0 0 12px;
  letter-spacing: 0.04em;
}

.section-desc {
  color: #999;
  font-size: 1rem;
  margin: 0;
}

.posts-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Load More */
.load-more {
  text-align: center;
  margin-top: 40px;
  padding-top: 40px;
  border-top: 1px solid #333;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 80px 24px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: #333;
  margin-bottom: 24px;
}

.empty-text {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: 1.5rem;
  color: #e8e8e8;
  margin: 0 0 8px;
}

.empty-hint {
  color: #666;
  margin: 0;
}

/* Error State */
.error-state {
  text-align: center;
  padding: 60px 24px;
}

.error-icon {
  width: 64px;
  height: 64px;
  color: #dc3545;
  margin-bottom: 16px;
}

.error-text {
  color: #dc3545;
  margin: 0 0 24px;
  font-size: 1rem;
}

/* 响应式 */
@media (max-width: 768px) {
  .home-banner {
    min-height: 50vh;
    padding: 60px 20px 40px;
  }

  .posts-section {
    padding: 40px 20px 60px;
  }

  .section-header {
    margin-bottom: 32px;
  }
}

@media (max-width: 480px) {
  .btn {
    padding: 14px 24px;
    font-size: 0.9375rem;
  }

  .banner-actions {
    flex-direction: column;
    align-items: center;
  }

  .btn {
    width: 100%;
    max-width: 280px;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .banner-line,
  .spinner {
    animation: none;
  }

  .btn,
  .PostCard {
    transition: none;
  }
}
</style>