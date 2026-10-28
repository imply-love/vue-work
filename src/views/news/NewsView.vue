<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { postApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import PostCard from '@/components/PostCard.vue'

const router = useRouter()
const authStore = useAuthStore()

const posts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const loading = ref(false)
const error = ref('')

const sort = ref('latest')
const category = ref('')
const keyword = ref('')

const SORT_OPTIONS = [
  { value: 'latest', label: '最新发布' },
  { value: 'hot', label: '最热' },
  { value: 'replies', label: '最多回复' },
  { value: 'recommended', label: '小编推荐' },
]

const CATEGORY_OPTIONS = [
  { value: '', label: '全部' },
  { value: '新番讨论', label: '新番讨论' },
  { value: '老番怀旧', label: '老番怀旧' },
  { value: '安利分享', label: '安利分享' },
  { value: '求推荐', label: '求推荐' },
  { value: '同人创作', label: '同人创作' },
  { value: '其他', label: '其他' },
]

const loadPosts = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await postApi.getList({
      page: page.value,
      page_size: pageSize,
      sort: sort.value,
      q: keyword.value.trim(),
      category: category.value || '',
    })
    if (res.code === 0) {
      posts.value = res.data.list || []
      total.value = res.data.total || 0
    } else {
      error.value = res.message || '获取帖子失败'
      posts.value = []
      total.value = 0
    }
  } catch (err) {
    error.value = err.message || '获取帖子失败'
    posts.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 排序 / 分类变化后回到第 1 页重新加载
const resetAndLoad = () => {
  page.value = 1
  loadPosts()
}

const onSearch = () => {
  resetAndLoad()
}

const changePage = (value) => {
  page.value = value
  loadPosts()
}

watch([sort, category], resetAndLoad)

const goPostDetail = (id) => router.push(`/posts/${id}`)

const goCreate = () => {
  if (!authStore.isLoggedIn) {
    router.push({ name: 'Login', query: { redirect: '/posts/new' } })
    return
  }
  router.push('/posts/new')
}

onMounted(loadPosts)
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero news-hero">
      <div class="news-hero__text">
        <h1 class="page-title">讨论区</h1>
        <p class="page-sub">新番吐槽、旧番安利、结局锐评，都来这里开一楼。</p>
      </div>
      <lay-button type="primary" size="lg" @click="goCreate">发帖</lay-button>
    </section>

    <!-- 筛选工具栏 -->
    <div class="page-toolbar">
      <lay-select v-model="sort" :options="SORT_OPTIONS" class="news-filter" placeholder="排序" />
      <lay-select v-model="category" :options="CATEGORY_OPTIONS" class="news-filter" placeholder="分类" />
      <form class="news-search" @submit.prevent="onSearch">
        <lay-input
          v-model="keyword"
          class="news-search__input"
          placeholder="搜索帖子标题或内容"
          allow-clear
        />
        <lay-button type="primary" native-type="submit">搜索</lay-button>
      </form>
      <div class="page-toolbar__spacer"></div>
      <span class="muted news-count">共 {{ total }} 篇帖子</span>
    </div>

    <!-- 加载中 -->
    <lay-card v-if="loading">
      <div class="empty-box">
        <p class="muted">正在召集同好们……</p>
      </div>
    </lay-card>

    <!-- 加载失败 -->
    <lay-card v-else-if="error">
      <div class="empty-box">
        <h3 class="empty-box__title">帖子走丢了</h3>
        <p>{{ error }}</p>
        <div class="form-actions news-actions">
          <lay-button type="primary" @click="loadPosts">重新加载</lay-button>
        </div>
      </div>
    </lay-card>

    <!-- 空列表 -->
    <lay-card v-else-if="posts.length === 0">
      <div class="empty-box">
        <h3 class="empty-box__title">还没有人开口</h3>
        <p>换个关键词试试，或者来开第一楼吧～</p>
        <div class="form-actions news-actions">
          <lay-button @click="loadPosts">刷新看看</lay-button>
          <lay-button type="primary" @click="goCreate">去发帖</lay-button>
        </div>
      </div>
    </lay-card>

    <!-- 帖子列表 -->
    <div v-else class="post-grid">
      <PostCard v-for="post in posts" :key="post.id" :post="post" @click="goPostDetail(post.id)" />
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-wrap">
      <lay-page
        v-model="page"
        :total="total"
        :limit="pageSize"
        :layout="['prev', 'page', 'next', 'count']"
        @change="changePage"
      />
    </div>
  </div>
</template>

<style scoped>
.news-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.news-hero__text {
  max-width: 640px;
}

.news-filter {
  width: 150px;
}

.news-search {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1 1 300px;
  max-width: 440px;
  min-width: 240px;
}

.news-search__input {
  flex: 1;
  min-width: 0;
}

.news-count {
  font-size: var(--text-sm);
}

.news-actions {
  justify-content: center;
  margin-top: var(--space-4);
}

@media (max-width: 768px) {
  .news-filter {
    width: 100%;
  }

  .news-search {
    max-width: none;
    width: 100%;
  }
}
</style>
