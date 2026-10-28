<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userApi } from '@/api'

const route = useRoute()
const router = useRouter()

const PAGE_SIZE = 20

const tabs = [
  { key: 'following', label: '我的关注', path: '/profile/following', desc: '你关注的人都会出现在这里。' },
  { key: 'followers', label: '我的粉丝', path: '/profile/followers', desc: '关注了你的人都在这里。' },
  { key: 'likes', label: '获赞列表', path: '/profile/likes', desc: '你发布过的帖子收到的点赞。' },
]

const relation = computed(() => route.meta.relation || 'following')
const currentTab = computed(() => tabs.find((tab) => tab.key === relation.value) || tabs[0])
const isLikes = computed(() => relation.value === 'likes')

const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const error = ref('')
const followingId = ref(null)

const emptyText = computed(() => {
  if (relation.value === 'following') return '还没有关注任何人'
  if (relation.value === 'followers') return '还没有粉丝'
  return '还没有收到点赞'
})

const toast = (type, title, message) => {
  window.$ghibli?.showToast({ type, title, message })
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = { page: page.value, page_size: PAGE_SIZE }
    let res
    if (relation.value === 'following') {
      res = await userApi.getFollowing(params)
    } else if (relation.value === 'followers') {
      res = await userApi.getFollowers(params)
    } else {
      res = await userApi.getReceivedLikes(params)
    }
    if (res.code === 0) {
      list.value = res.data.list || []
      total.value = res.data.total || 0
      page.value = res.data.page || page.value
    } else {
      error.value = res.message || '加载失败'
    }
  } catch (err) {
    error.value = err.message || '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const changePage = (value) => {
  page.value = value
  load()
}

const toggleFollow = async (item) => {
  followingId.value = item.id
  try {
    const res = await userApi.follow(item.id)
    if (res.code === 0) {
      item.is_following = res.data.following
      item.followers_count = res.data.followers_count
      toast('success', res.data.following ? '已关注' : '已取消关注', res.message)
    }
  } catch (err) {
    toast('error', '操作失败', err.message || '请稍后重试')
  } finally {
    followingId.value = null
  }
}

const goPost = (id) => router.push(`/posts/${id}`)

const avatarText = (item) => {
  const name = item.nickname || item.username || ''
  return name ? name.slice(0, 1).toUpperCase() : '?'
}

watch(
  () => route.meta.relation,
  () => {
    page.value = 1
    list.value = []
    total.value = 0
    load()
  }
)

onMounted(load)
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero">
      <h1 class="page-title">{{ currentTab.label }}</h1>
      <p class="page-sub">{{ currentTab.desc }}</p>
    </section>

    <div class="page-toolbar">
      <lay-button
        v-for="tab in tabs"
        :key="tab.key"
        :type="relation === tab.key ? 'primary' : undefined"
        @click="router.push(tab.path)"
      >
        {{ tab.label }}
      </lay-button>
      <span class="page-toolbar__spacer"></span>
      <lay-button @click="router.push('/profile')">返回个人中心</lay-button>
    </div>

    <lay-card>
      <div v-if="loading" class="muted">加载中…</div>
      <div v-else-if="error" class="empty-box">
        <h3 class="empty-box__title">加载失败</h3>
        <p>{{ error }}</p>
        <lay-button type="primary" @click="load">重试</lay-button>
      </div>
      <lay-empty v-else-if="list.length === 0" :description="emptyText" />

      <div v-else>
        <template v-if="!isLikes">
          <div v-for="item in list" :key="item.id" class="list-row">
            <img v-if="item.avatar" :src="item.avatar" :alt="item.nickname" class="row-avatar" />
            <div v-else class="avatar-circle">{{ avatarText(item) }}</div>
            <div class="list-row__main">
              <p class="list-row__title">{{ item.nickname || item.username }}</p>
              <div class="meta">
                <span>关注 {{ item.following_count ?? 0 }}</span>
                <span>粉丝 {{ item.followers_count ?? 0 }}</span>
                <span v-if="item.is_friend" class="status-tag status-tag--friends">好友</span>
              </div>
            </div>
            <lay-button
              size="sm"
              :type="item.is_following ? undefined : 'primary'"
              :loading="followingId === item.id"
              :disabled="followingId === item.id"
              @click="toggleFollow(item)"
            >
              {{ item.is_following ? '已关注' : '关注' }}
            </lay-button>
          </div>
        </template>

        <template v-else>
          <div
            v-for="item in list"
            :key="item.id"
            class="list-row list-row--clickable"
            role="button"
            tabindex="0"
            @click="goPost(item.id)"
            @keydown.enter="goPost(item.id)"
          >
            <div class="list-row__main">
              <p class="list-row__title">{{ item.title }}</p>
              <div class="meta">
                <span>点赞 {{ item.like_count ?? 0 }}</span>
                <span>评论 {{ item.reply_count ?? 0 }}</span>
                <span>浏览 {{ item.view_count ?? 0 }}</span>
                <span v-if="item.publish_time">{{ item.publish_time }}</span>
              </div>
            </div>
          </div>
        </template>

        <div v-if="total > PAGE_SIZE" class="pagination-wrap">
          <lay-page
            v-model="page"
            :total="total"
            :limit="PAGE_SIZE"
            :layout="['prev', 'page', 'next', 'count']"
            @change="changePage"
          />
        </div>
      </div>
    </lay-card>
  </div>
</template>

<style scoped>
.row-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.list-row--clickable {
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-gentle);
}

.list-row--clickable:hover,
.list-row--clickable:focus-visible {
  background: var(--ghibli-sky-50);
  outline: none;
}
</style>
