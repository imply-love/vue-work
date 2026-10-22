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
        <h1 id="banner-title" class="banner-title">番剧同好会</h1>
        <p class="banner-subtitle">追番、安利、找同好</p>
        <p class="banner-desc">在这里记录你的追番进度，分享让你熬夜的神作，认识一群聊得来的同好</p>
        <div class="banner-actions">
          <button
            v-if="!authStore.isLoggedIn"
            class="ghibli-btn ghibli-btn--primary ghibli-btn--lg"
            @click="goLogin"
          >
            <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="8.5" cy="7" r="4"/>
              <line x1="20" y1="8" x2="20" y2="14"/>
              <line x1="23" y1="11" x2="17" y2="11"/>
            </svg>
            加入同好会
          </button>
          <a
            v-else
            class="ghibli-btn ghibli-btn--primary ghibli-btn--lg"
            href="#posts-list"
          >
            <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            看看大家在聊什么
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
    <section id="posts-list" class="ghibli-section home-posts" aria-labelledby="posts-title">
      <header class="ghibli-section__header">
        <h2 id="posts-title" class="ghibli-section__title">最新讨论</h2>
        <p class="ghibli-section__desc">刚出锅的帖子还热乎，点进去一起聊</p>
      </header>

      <div class="ghibli-section__content">
        <div v-if="postStore.posts.length === 0 && !loading" class="ghibli-empty">
          <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <h3 class="ghibli-empty__title">还没有人开口</h3>
          <p class="ghibli-empty__desc">成为第一个开帖的同好吧，安利你最爱的番</p>
        </div>

        <div v-else class="posts-grid ghibli-cards">
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
            class="ghibli-btn ghibli-btn--outline"
            @click="handleLoadMore"
            :disabled="loading"
          >
            <span v-if="loading" class="ghibli-btn__loading">
              <span class="ghibli-spinner" aria-hidden="true"></span>
              加载中...
            </span>
            <span v-else class="ghibli-btn__loading">
              <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <polyline points="23 4 12 15 1 4"/>
              </svg>
              加载更多
            </span>
          </button>
        </div>

        <!-- 加载错误 -->
        <div v-if="postStore.error && postStore.posts.length === 0" class="ghibli-empty">
          <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <h3 class="ghibli-empty__title">帖子走丢了</h3>
          <p class="ghibli-empty__desc">{{ postStore.error }}</p>
          <button class="ghibli-btn ghibli-btn--warm" @click="loadPosts">
            <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
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
  min-height: 100%;
}

/* ===== 顶部横幅 ===== */
.home-banner {
  position: relative;
  min-height: 52vh;
  max-height: 640px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-20) var(--space-6) var(--space-16);
  overflow: hidden;
}

.banner-content {
  position: relative;
  z-index: 2;
  text-align: center;
  max-width: 800px;
}

.banner-title {
  font-family: var(--font-display);
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: 0.04em;
  margin: 0 0 var(--space-4);
  background: linear-gradient(135deg, var(--ghibli-sky-600) 0%, var(--ghibli-sakura-500) 50%, var(--ghibli-sun-400) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.banner-subtitle {
  font-family: var(--font-handwriting);
  font-size: clamp(1rem, 2.5vw, 1.375rem);
  color: var(--ghibli-sakura-600);
  letter-spacing: 0.2em;
  margin: 0 0 var(--space-6);
}

.banner-desc {
  font-size: clamp(1rem, 1.5vw, 1.125rem);
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
  margin: 0 auto var(--space-10);
  max-width: 620px;
}

.banner-actions {
  display: flex;
  gap: var(--space-6);
  justify-content: center;
  flex-wrap: wrap;
}

.banner-decor {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.banner-line {
  position: absolute;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, transparent, var(--ghibli-sky-300), transparent);
  opacity: 0.5;
}

.banner-line:nth-child(1) { left: 20%; animation: lineFlow 8s ease-in-out infinite; }
.banner-line:nth-child(2) { left: 50%; animation: lineFlow 8s ease-in-out infinite 1.5s; }
.banner-line:nth-child(3) { left: 80%; animation: lineFlow 8s ease-in-out infinite 3s; }

@keyframes lineFlow {
  0%, 100% { opacity: 0.15; transform: scaleY(0.5); }
  50% { opacity: 0.6; transform: scaleY(1); }
}

/* ===== 帖子列表 ===== */
.home-posts {
  scroll-margin-top: 96px;
}

.load-more {
  text-align: center;
  margin-top: var(--space-12);
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .home-banner {
    min-height: 46vh;
    padding: var(--space-16) var(--space-4) var(--space-12);
  }
}

@media (max-width: 480px) {
  .banner-actions {
    flex-direction: column;
    align-items: center;
  }

  .banner-actions .ghibli-btn {
    width: 100%;
    max-width: 280px;
  }
}

/* ===== 减少动画偏好 ===== */
@media (prefers-reduced-motion: reduce) {
  .banner-line {
    animation: none;
  }
}
</style>