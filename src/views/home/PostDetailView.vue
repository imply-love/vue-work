<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { favoriteApi, postApi, userApi } from '@/api'
import ReplyNode from '@/components/ReplyNode.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const post = ref(null)
const loading = ref(true)
// 帖子不存在或无权限（后端返回 1009）
const notFound = ref(false)
const loadError = ref('')

const liking = ref(false)
const favoriting = ref(false)
const following = ref(false)

// 评论树
const replies = ref([])
const repliesTotal = ref(0)
const repliesLoading = ref(false)
const repliesError = ref('')
const replyContent = ref('')
// 当前正在回复的评论：{ id, nickname }，为 null 时表示发表根评论
const replyTo = ref(null)
const replySending = ref(false)
const replyBoxRef = ref(null)

const tagList = computed(() => {
  if (!post.value?.tags) return []
  return post.value.tags
    .split(/[,，]/)
    .map((t) => t.trim())
    .filter(Boolean)
    .slice(0, 8)
})

const authorInitial = computed(() => (post.value?.author_nickname || '同').charAt(0).toUpperCase())

const currentUserId = computed(() => authStore.userInfo?.id ?? null)
const isAdmin = computed(() => authStore.isAdmin)

// 仅作者可见的审查提示
const reviewInfo = computed(() => {
  if (!post.value) return null
  if (post.value.review_status !== 2 && post.value.review_status !== 3) return null
  if (!post.value.is_self && !post.value.can_edit) return null
  return {
    isBan: post.value.review_status === 3,
    title: post.value.review_status === 3 ? '该帖子已被封禁' : '该帖子已被打回',
    note: post.value.review_note || '',
  }
})

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const goLogin = () => router.push({ name: 'Login', query: { redirect: route.fullPath } })
const goHome = () => router.push('/')

// ===== 帖子详情 =====
const fetchPost = async () => {
  loading.value = true
  notFound.value = false
  loadError.value = ''
  post.value = null
  replies.value = []
  repliesTotal.value = 0
  repliesError.value = ''
  replyTo.value = null
  replyContent.value = ''
  try {
    const res = await postApi.getDetail(route.params.id)
    if (res.code === 0) {
      post.value = res.data
      loadReplies()
    } else if (res.code === 1009) {
      notFound.value = true
    } else {
      loadError.value = res.message || '获取帖子详情失败'
    }
  } catch (err) {
    if (err.code === 1009) {
      notFound.value = true
    } else {
      loadError.value = err.message || '获取帖子详情失败'
    }
  } finally {
    loading.value = false
  }
}

// ===== 评论树 =====
const loadReplies = async () => {
  repliesLoading.value = true
  repliesError.value = ''
  try {
    const res = await postApi.getReplyTree(route.params.id)
    if (res.code === 0) {
      replies.value = res.data.list || []
      repliesTotal.value = res.data.total || 0
      if (post.value) post.value.reply_count = repliesTotal.value
    } else {
      repliesError.value = res.message || '评论加载失败'
    }
  } catch (err) {
    repliesError.value = err.message || '评论加载失败'
  } finally {
    repliesLoading.value = false
  }
}

// ===== 点赞 / 收藏 / 关注 =====
const toggleLike = async () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  if (liking.value || !post.value) return
  liking.value = true
  try {
    const res = await postApi.like(post.value.id)
    if (res.code === 0) {
      post.value.is_liked = !!res.data?.liked
      post.value.like_count = res.data?.like_count ?? post.value.like_count
    }
  } catch (err) {
    window.$ghibli?.showToast({
      type: 'error',
      title: '操作失败',
      message: err.message || '点赞失败，请稍后重试',
    })
  } finally {
    liking.value = false
  }
}

const toggleFavorite = async () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  if (favoriting.value || !post.value) return
  favoriting.value = true
  const willFavorite = !post.value.is_favorited
  try {
    const res = willFavorite
      ? await favoriteApi.add(post.value.id)
      : await favoriteApi.remove(post.value.id)
    if (res.code === 0) {
      post.value.is_favorited = willFavorite
      window.$ghibli?.showToast({
        type: 'success',
        title: willFavorite ? '已加入收藏' : '已取消收藏',
        message: willFavorite ? '可在个人中心查看收藏' : '已从收藏中移除',
      })
    } else {
      window.$ghibli?.showToast({ type: 'error', title: '操作失败', message: res.message || '请稍后重试' })
    }
  } catch (err) {
    window.$ghibli?.showToast({ type: 'error', title: '操作失败', message: err.message || '请稍后重试' })
  } finally {
    favoriting.value = false
  }
}

const toggleFollow = async () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  if (following.value || !post.value) return
  following.value = true
  try {
    const res = await userApi.follow(post.value.user_id)
    if (res.code === 0) {
      post.value.is_following = !!res.data?.following
      if (post.value.is_following) {
        window.$ghibli?.showToast({ type: 'success', title: '已关注', message: '可以在关注列表中看到 ta' })
      }
    }
  } catch (err) {
    window.$ghibli?.showToast({ type: 'error', title: '操作失败', message: err.message || '请稍后重试' })
  } finally {
    following.value = false
  }
}

// ===== 发表 / 删除评论 =====
const startReply = (node) => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  replyTo.value = { id: node.id, nickname: node.author_nickname || '匿名同好' }
  // 滚动到输入框，方便直接继续输入
  nextTick(() => {
    replyBoxRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

const cancelReply = () => {
  replyTo.value = null
}

const submitReply = async () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  if (replySending.value || !post.value) return
  const content = replyContent.value.trim()
  if (!content) {
    window.$ghibli?.showToast({ type: 'info', title: '先写点什么吧', message: '评论内容不能为空' })
    return
  }
  replySending.value = true
  try {
    const res = await postApi.addReply(post.value.id, {
      content,
      parent_id: replyTo.value ? replyTo.value.id : 0,
    })
    if (res.code === 0) {
      replyContent.value = ''
      replyTo.value = null
      await loadReplies()
      window.$ghibli?.showToast({ type: 'success', title: '发表成功', message: '评论已发布' })
    } else {
      window.$ghibli?.showToast({ type: 'error', title: '发表失败', message: res.message || '请稍后重试' })
    }
  } catch (err) {
    window.$ghibli?.showToast({ type: 'error', title: '发表失败', message: err.message || '请稍后重试' })
  } finally {
    replySending.value = false
  }
}

const removeReply = async (node) => {
  try {
    const res = await postApi.removeReply(node.id)
    if (res.code === 0) {
      await loadReplies()
      window.$ghibli?.showToast({ type: 'success', title: '已删除', message: '评论已删除' })
    } else {
      window.$ghibli?.showToast({ type: 'error', title: '删除失败', message: res.message || '请稍后重试' })
    }
  } catch (err) {
    window.$ghibli?.showToast({ type: 'error', title: '删除失败', message: err.message || '请稍后重试' })
  }
}

onMounted(fetchPost)

// 同一组件内切换帖子 id 时重新加载
watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      fetchPost()
    }
  }
)
</script>

<template>
  <div class="page-wrap">
    <div class="page-toolbar">
      <lay-button @click="router.back()">返回</lay-button>
      <lay-button @click="goHome">回首页</lay-button>
      <div class="page-toolbar__spacer"></div>
    </div>

    <!-- 加载中 -->
    <lay-card v-if="loading">
      <div class="empty-box">
        <p class="muted">正在展开帖子……</p>
      </div>
    </lay-card>

    <!-- 帖子不存在 / 无权限 -->
    <lay-card v-else-if="notFound">
      <div class="empty-box">
        <h3 class="empty-box__title">帖子不存在</h3>
        <p>它可能已被删除，或者你没有权限查看。</p>
        <div class="form-actions empty-actions">
          <lay-button type="primary" @click="goHome">返回首页</lay-button>
        </div>
      </div>
    </lay-card>

    <!-- 加载失败 -->
    <lay-card v-else-if="loadError">
      <div class="empty-box">
        <h3 class="empty-box__title">帖子走丢了</h3>
        <p>{{ loadError }}</p>
        <div class="form-actions empty-actions">
          <lay-button type="primary" @click="fetchPost">重新加载</lay-button>
          <lay-button @click="goHome">返回首页</lay-button>
        </div>
      </div>
    </lay-card>

    <template v-else-if="post">
      <!-- 顶部卡片：作者、统计、标签、标题、正文 -->
      <lay-card class="detail-card">
        <div class="detail-head">
          <lay-avatar
            v-if="post.author_avatar"
            :src="post.author_avatar"
            :alt="post.author_nickname"
            size="md"
            radius
          />
          <span v-else class="avatar-circle detail-avatar">{{ authorInitial }}</span>
          <div class="detail-author">
            <span class="detail-author__name">{{ post.author_nickname || '匿名同好' }}</span>
            <span class="detail-author__time">{{ formatDate(post.publish_time || post.create_time) }}</span>
          </div>
          <div class="detail-head__ops">
            <lay-button
              v-if="!post.is_self && !post.is_following"
              type="primary"
              size="sm"
              :loading="following"
              @click="toggleFollow"
            >
              关注作者
            </lay-button>
            <lay-button v-if="post.can_edit || post.is_self" size="sm" @click="router.push(`/posts/${post.id}/edit`)">
              编辑
            </lay-button>
          </div>
        </div>

        <div class="meta detail-meta">
          <span>浏览 {{ post.view_count || 0 }}</span>
          <span>点赞 {{ post.like_count || 0 }}</span>
          <span>评论 {{ post.reply_count || 0 }}</span>
        </div>

        <div v-if="post.category || tagList.length" class="tag-row detail-tags">
          <lay-tag v-if="post.category" type="normal" variant="light">{{ post.category }}</lay-tag>
          <lay-tag v-for="tag in tagList" :key="tag" type="primary" variant="light">#{{ tag }}</lay-tag>
        </div>

        <h1 class="detail-title">
          {{ post.title }}
          <span v-if="post.edit_label" class="detail-edit-label">{{ post.edit_label }}</span>
        </h1>

        <p v-if="post.summary" class="detail-summary">{{ post.summary }}</p>

        <!-- 作者可见的打回 / 封禁提示 -->
        <div
          v-if="reviewInfo"
          class="review-alert"
          :class="reviewInfo.isBan ? 'review-alert--ban' : 'review-alert--reject'"
        >
          <strong>{{ reviewInfo.title }}</strong>
          <span v-if="reviewInfo.note">：{{ reviewInfo.note }}</span>
        </div>

        <div v-if="post.cover" class="detail-cover">
          <img :src="post.cover" :alt="post.title" />
        </div>

        <div class="detail-body" v-html="post.content"></div>

        <div class="detail-actions">
          <lay-button :type="post.is_liked ? 'primary' : undefined" :loading="liking" @click="toggleLike">
            {{ post.is_liked ? '已点赞' : '点赞' }} {{ post.like_count || 0 }}
          </lay-button>
          <lay-button :type="post.is_favorited ? 'warm' : undefined" :loading="favoriting" @click="toggleFavorite">
            {{ post.is_favorited ? '已收藏' : '收藏' }}
          </lay-button>
          <div class="page-toolbar__spacer"></div>
          <span class="muted detail-publish">发布于 {{ formatDate(post.publish_time || post.create_time) }}</span>
        </div>
      </lay-card>

      <!-- 评论区 -->
      <lay-card class="reply-card">
        <div class="reply-card__head">
          <h2 class="reply-card__title">评论</h2>
          <span class="reply-card__count">{{ repliesTotal }}</span>
        </div>

        <!-- 登录后可发表评论 / 回复 -->
        <div v-if="authStore.isLoggedIn" ref="replyBoxRef" class="reply-form">
          <div v-if="replyTo" class="reply-target">
            <span>回复 @{{ replyTo.nickname }}</span>
            <lay-button size="xs" @click="cancelReply">取消</lay-button>
          </div>
          <lay-textarea
            v-model="replyContent"
            :rows="3"
            :maxlength="500"
            show-count
            placeholder="写下你的评论…"
          />
          <div class="form-actions reply-form__actions">
            <span class="muted">友善交流，一起聊番</span>
            <div class="page-toolbar__spacer"></div>
            <lay-button
              type="primary"
              :loading="replySending"
              :disabled="!replyContent.trim()"
              @click="submitReply"
            >
              {{ replyTo ? '回复' : '发布评论' }}
            </lay-button>
          </div>
        </div>
        <div v-else class="reply-login">
          <lay-button type="primary" @click="goLogin">登录后参与讨论</lay-button>
        </div>

        <!-- 评论树 -->
        <div v-if="repliesLoading" class="empty-box">
          <p class="muted">评论加载中……</p>
        </div>
        <div v-else-if="repliesError" class="empty-box">
          <p>{{ repliesError }}</p>
          <div class="form-actions empty-actions">
            <lay-button type="primary" @click="loadReplies">重试</lay-button>
          </div>
        </div>
        <div v-else-if="!replies.length" class="empty-box">
          <p class="muted">还没有评论，来抢沙发吧～</p>
        </div>
        <div v-else class="reply-tree">
          <ReplyNode
            v-for="node in replies"
            :key="node.id"
            :node="node"
            :current-user-id="currentUserId"
            :is-admin="isAdmin"
            class="reply-node--root"
            @reply="startReply"
            @remove="removeReply"
          />
        </div>
      </lay-card>
    </template>
  </div>
</template>

<style scoped>
.detail-card :deep(.layui-card-body),
.reply-card :deep(.layui-card-body) {
  padding: var(--space-6);
}

.detail-avatar {
  width: 44px;
  height: 44px;
}

.detail-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.detail-author {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.detail-author__name {
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.detail-author__time {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.detail-head__ops {
  margin-left: auto;
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.detail-meta {
  margin-top: var(--space-4);
}

.detail-tags {
  margin-top: var(--space-4);
}

.detail-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  font-family: var(--font-display);
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  color: var(--color-text);
  margin: var(--space-5) 0 var(--space-3);
}

.detail-edit-label {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--ghibli-sakura-600);
  background: var(--ghibli-sakura-50);
  border-radius: var(--radius-full);
  padding: 2px var(--space-3);
}

.detail-summary {
  margin: 0 0 var(--space-6);
  padding: var(--space-4) var(--space-5);
  background: var(--ghibli-sky-50);
  border-left: 4px solid var(--ghibli-sky-400);
  border-radius: var(--radius-md);
  color: var(--color-text-light);
  line-height: var(--leading-relaxed);
}

.review-alert {
  margin-bottom: var(--space-6);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

.review-alert--reject {
  background: var(--color-warning-bg);
  color: var(--ghibli-warm-800);
  border: 1px solid var(--ghibli-sun-300);
}

.review-alert--ban {
  background: var(--color-error-bg);
  color: var(--color-error);
  border: 1px solid var(--color-error);
}

.detail-cover {
  margin-bottom: var(--space-6);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.detail-cover img {
  display: block;
  width: 100%;
  max-height: 420px;
  object-fit: cover;
}

.detail-body {
  color: var(--color-text);
  line-height: var(--leading-loose);
  word-break: break-word;
}

.detail-body :deep(p) {
  margin: 0 0 1.2em;
}

.detail-body :deep(img) {
  max-width: 100%;
  border-radius: var(--radius-lg);
  margin: 1em 0;
}

.detail-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-8);
  padding-top: var(--space-5);
  border-top: 1px dashed var(--color-divider);
}

.detail-publish {
  font-size: var(--text-xs);
}

.reply-card {
  margin-top: var(--space-6);
}

.reply-card__head {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.reply-card__title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  color: var(--color-text);
  margin: 0;
}

.reply-card__count {
  font-weight: var(--font-semibold);
  color: var(--ghibli-sakura-600);
}

.reply-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.reply-target {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--ghibli-sky-50);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--ghibli-sky-700);
}

.reply-form__actions {
  align-items: center;
}

.reply-login {
  margin-bottom: var(--space-6);
  padding: var(--space-6);
  background: var(--ghibli-paper-50);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
}

.empty-actions {
  justify-content: center;
  margin-top: var(--space-4);
}

@media (max-width: 768px) {
  .detail-title {
    font-size: var(--text-2xl);
  }

  .detail-head {
    flex-wrap: wrap;
  }
}
</style>
