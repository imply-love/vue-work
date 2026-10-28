<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { announcementApi, postApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import PostCard from '@/components/PostCard.vue'

const router = useRouter()
const authStore = useAuthStore()

const announcements = ref([])

const loadAnnouncements = async () => {
  try {
    const res = await announcementApi.getList()
    if (res.code === 0) {
      announcements.value = res.data.list || []
    }
  } catch {
    // 公告加载失败不影响首页主体内容
    announcements.value = []
  }
}

const posts = ref([])
const loading = ref(false)
const error = ref('')
const page = ref(1)
const total = ref(0)
const pageSize = 12
const sort = ref('latest')

const SORTS = [
  { value: 'latest', label: '最新' },
  { value: 'hot', label: '最热' },
  { value: 'recommended', label: '小编推荐' },
]

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await postApi.getList({ page: page.value, page_size: pageSize, sort: sort.value })
    if (res.code === 0) {
      posts.value = res.data.list
      total.value = res.data.total
    } else {
      error.value = res.message
    }
  } catch (err) {
    error.value = err.message || '获取帖子失败'
  } finally {
    loading.value = false
  }
}

const changeSort = (value) => {
  sort.value = value
  page.value = 1
  load()
}

const changePage = (value) => {
  page.value = value
  load()
}

const goDetail = (id) => router.push(`/posts/${id}`)
const goLogin = () => router.push({ name: 'Login', query: { redirect: '/' } })

onMounted(() => {
  load()
  loadAnnouncements()
})
</script>

<template>
  <div class="page-wrap">
    <section class="home-hero page-hero">
      <div class="home-hero__text">
        <h1 class="page-title">番剧同好会</h1>
        <p class="home-hero__sub">追番、安利、找同好</p>
        <p class="page-sub">
          在这里记录你的追番进度，分享让你熬夜的神作，认识一群聊得来的同好。
        </p>
        <div class="home-hero__actions">
          <lay-button v-if="!authStore.isLoggedIn" type="primary" size="lg" @click="goLogin">
            加入同好会
          </lay-button>
          <lay-button v-else type="primary" size="lg" @click="router.push('/posts/new')">
            发个新帖
          </lay-button>
          <lay-button size="lg" @click="router.push('/content/posts')">内容管理</lay-button>
        </div>
      </div>
      <div class="home-hero__decor" aria-hidden="true">
        <div class="home-hero__sun"></div>
        <div class="home-hero__cloud home-hero__cloud--1"></div>
        <div class="home-hero__cloud home-hero__cloud--2"></div>
      </div>
    </section>

    <!-- 公告栏：管理员在后台发布，前台公开展示 -->
    <section v-if="announcements.length" class="announce-section">
      <div class="page-toolbar">
        <h2 class="home-section-title">公告</h2>
        <div class="page-toolbar__spacer"></div>
        <span class="muted announce-count">共 {{ announcements.length }} 条</span>
      </div>
      <lay-card>
        <div
          v-for="(item, index) in announcements"
          :key="item.id"
          class="announce-item"
          :class="{ 'announce-item--last': index === announcements.length - 1 }"
        >
          <span class="announce-item__badge">公告</span>
          <div class="announce-item__main">
            <h3 class="announce-item__title">{{ item.title }}</h3>
            <p class="announce-item__content">{{ item.content }}</p>
          </div>
          <span v-if="item.publish_time" class="announce-item__time">{{ item.publish_time }}</span>
        </div>
      </lay-card>
    </section>

    <section>
      <div class="page-toolbar">
        <h2 class="home-section-title">最新讨论</h2>
        <div class="page-toolbar__spacer"></div>
        <div class="home-sorts">
          <button
            v-for="item in SORTS"
            :key="item.value"
            type="button"
            class="home-sort"
            :class="{ 'home-sort--active': sort === item.value }"
            @click="changeSort(item.value)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>

      <lay-card v-if="loading && posts.length === 0">
        <div class="empty-box">正在召集同好们……</div>
      </lay-card>

      <lay-card v-else-if="error">
        <div class="empty-box">
          <h3 class="empty-box__title">帖子走丢了</h3>
          <p>{{ error }}</p>
          <lay-button type="primary" @click="load">重试</lay-button>
        </div>
      </lay-card>

      <lay-card v-else-if="posts.length === 0">
        <div class="empty-box">
          <h3 class="empty-box__title">还没有人开口</h3>
          <p>成为第一个开帖的同好吧，安利你最爱的番。</p>
          <lay-button type="primary" @click="router.push('/posts/new')">去发帖</lay-button>
        </div>
      </lay-card>

      <div v-else class="post-grid">
        <PostCard v-for="post in posts" :key="post.id" :post="post" @click="goDetail(post.id)" />
      </div>

      <div v-if="total > pageSize" class="pagination-wrap">
        <lay-page
          v-model="page"
          :total="total"
          :limit="pageSize"
          :limits="[12, 24, 36]"
          :layout="['prev', 'page', 'next', 'count']"
          @change="changePage"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-8);
  padding: var(--space-16) var(--space-10);
}

.home-hero__text {
  position: relative;
  z-index: 2;
  max-width: 560px;
}

.home-hero__sub {
  font-family: var(--font-handwriting);
  font-size: var(--text-lg);
  color: var(--ghibli-sakura-600);
  letter-spacing: 0.18em;
  margin: 0 0 var(--space-4);
}

.home-hero__actions {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
  margin-top: var(--space-6);
}

.home-hero__decor {
  position: relative;
  width: 260px;
  height: 180px;
  flex-shrink: 0;
}

.home-hero__sun {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--ghibli-sun-200), var(--ghibli-sun-400));
  box-shadow: 0 0 60px rgba(251, 191, 36, 0.45);
}

.home-hero__cloud {
  position: absolute;
  height: 26px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 6px 18px rgba(125, 211, 252, 0.35);
}

.home-hero__cloud--1 {
  width: 130px;
  left: 0;
  bottom: 40px;
}

.home-hero__cloud--2 {
  width: 90px;
  right: 20px;
  bottom: 0;
}

.home-section-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  color: var(--color-text);
  margin: 0;
}

/* 公告栏 */
.announce-section {
  margin-bottom: var(--space-8);
}

.announce-count {
  font-size: var(--text-sm);
}

.announce-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-4) 0;
}

.announce-item--last {
  padding-bottom: 0;
}

.announce-item__badge {
  flex-shrink: 0;
  padding: 1px var(--space-3);
  border-radius: var(--radius-full);
  font-size: 11px;
  line-height: 18px;
  background: var(--ghibli-sky-100, #e0f2fe);
  color: var(--ghibli-sky-800, #1e3a8a);
}

.announce-item__main {
  flex: 1;
  min-width: 0;
}

.announce-item__title {
  margin: 0 0 var(--space-1);
  font-size: var(--text-base);
  color: var(--color-text);
}

.announce-item__content {
  margin: 0;
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text-muted);
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.announce-item__time {
  flex-shrink: 0;
  font-size: var(--text-xs);
  color: var(--color-text-light);
  white-space: nowrap;
}

.home-sorts {
  display: flex;
  gap: var(--space-2);
  background: var(--ghibli-paper-200);
  padding: var(--space-1);
  border-radius: var(--radius-full);
}

.home-sort {
  border: none;
  background: transparent;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  color: var(--color-text-light);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-gentle);
}

.home-sort--active {
  background: var(--color-bg-elevated);
  color: var(--ghibli-sky-700);
  font-weight: var(--font-semibold);
  box-shadow: var(--shadow-xs);
}

@media (max-width: 768px) {
  .home-hero {
    padding: var(--space-10) var(--space-6);
  }

  .home-hero__decor {
    display: none;
  }

  .announce-item {
    flex-direction: column;
    gap: var(--space-2);
  }

  .announce-item__time {
    white-space: normal;
  }
}
</style>
