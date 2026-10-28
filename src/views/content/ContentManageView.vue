<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { postApi, userApi } from '@/api'

const route = useRoute()
const router = useRouter()

const PAGE_SIZE = 10
// 不展示每页条数切换，避免分页器内部页大小与请求参数不一致
const PAGE_LAYOUT = ['prev', 'page', 'next', 'count']

// lay-page 的 change 事件回调参数为 { current, limit }
const resolvePage = (payload, fallback) => {
  if (typeof payload === 'number') return payload
  if (payload && typeof payload.current === 'number') return payload.current
  return fallback
}

// 当前分区完全由路由决定，切换分区就是切换路由
const activeTab = computed(() => route.meta.tab || 'posts')

const TABS = [
  { key: 'posts', label: '帖子管理', path: '/content/posts' },
  { key: 'comments', label: '评论管理', path: '/content/comments' },
  { key: 'drafts', label: '草稿箱', path: '/content/drafts' },
]

const toast = (type, title, message) => {
  window.$ghibli?.showToast({ type, title, message })
}

const switchTab = (tab) => {
  if (tab.key !== activeTab.value) router.push(tab.path)
}

const goNewPost = () => router.push('/posts/new')
const goPost = (id) => router.push(`/posts/${id}`)
const goEdit = (id) => router.push(`/posts/${id}/edit`)

// ===== 帖子管理 =====
const posts = ref([])
const postsLoading = ref(false)
const postsError = ref('')
const postsPage = ref(1)
const postsTotal = ref(0)

const loadPosts = async (page = postsPage.value) => {
  postsLoading.value = true
  postsError.value = ''
  try {
    const res = await postApi.getMine({ page, page_size: PAGE_SIZE, status: 'published' })
    if (res.code === 0) {
      posts.value = res.data.list || []
      postsTotal.value = res.data.total || 0
      postsPage.value = res.data.page || page
    } else {
      postsError.value = res.message || '加载失败'
    }
  } catch (err) {
    postsError.value = err.message || '加载失败，请稍后重试'
  } finally {
    postsLoading.value = false
  }
}

const onPostsPageChange = (payload) => {
  loadPosts(resolvePage(payload, postsPage.value))
}

const VISIBILITY_META = {
  1: { label: '私密', className: 'status-tag--private' },
  2: { label: '仅好友', className: 'status-tag--friends' },
}

const REVIEW_META = {
  1: { label: '推荐', className: 'status-tag--recommend' },
  2: { label: '已打回', className: 'status-tag--reject' },
  3: { label: '已封禁', className: 'status-tag--ban' },
  4: { label: '待审核', className: 'status-tag--pending' },
}

// 0-公开 1-私密 2-仅好友
const changeVisibility = async (post, visibility) => {
  if (post.visibility === visibility) return
  try {
    const res = await postApi.setVisibility(post.id, visibility)
    if (res.code === 0) {
      toast('success', '可见性已更新', res.message || '设置成功')
      await loadPosts(postsPage.value)
    } else {
      toast('error', '设置失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '设置失败', err.message || '请稍后重试')
  }
}

const removePost = async (post) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '删除帖子',
    message: `确定删除「${post.title || '未命名草稿'}」吗？删除后无法恢复。`,
  })
  if (!confirmed) return
  try {
    const res = await postApi.remove(post.id)
    if (res.code === 0) {
      toast('success', '已删除', '这篇帖子已从你的列表中移除')
      const target = posts.value.length === 1 && postsPage.value > 1
        ? postsPage.value - 1
        : postsPage.value
      await loadPosts(target)
    } else {
      toast('error', '删除失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '删除失败', err.message || '请稍后重试')
  }
}

// ===== 草稿箱 =====
const drafts = ref([])
const draftsLoading = ref(false)
const draftsError = ref('')
const draftsPage = ref(1)
const draftsTotal = ref(0)

const loadDrafts = async (page = draftsPage.value) => {
  draftsLoading.value = true
  draftsError.value = ''
  try {
    const res = await postApi.getMine({ page, page_size: PAGE_SIZE, status: 'draft' })
    if (res.code === 0) {
      drafts.value = res.data.list || []
      draftsTotal.value = res.data.total || 0
      draftsPage.value = res.data.page || page
    } else {
      draftsError.value = res.message || '加载失败'
    }
  } catch (err) {
    draftsError.value = err.message || '加载失败，请稍后重试'
  } finally {
    draftsLoading.value = false
  }
}

const onDraftsPageChange = (payload) => {
  loadDrafts(resolvePage(payload, draftsPage.value))
}

const removeDraft = async (draft) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '删除草稿',
    message: `确定删除草稿「${draft.title || '未命名草稿'}」吗？删除后无法恢复。`,
  })
  if (!confirmed) return
  try {
    const res = await postApi.remove(draft.id)
    if (res.code === 0) {
      toast('success', '已删除', '草稿已删除')
      const target = drafts.value.length === 1 && draftsPage.value > 1
        ? draftsPage.value - 1
        : draftsPage.value
      await loadDrafts(target)
    } else {
      toast('error', '删除失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '删除失败', err.message || '请稍后重试')
  }
}

// ===== 评论管理 =====
const comments = ref([])
const commentsLoading = ref(false)
const commentsError = ref('')
const commentsPage = ref(1)
const commentsTotal = ref(0)

const loadComments = async (page = commentsPage.value) => {
  commentsLoading.value = true
  commentsError.value = ''
  try {
    const res = await userApi.getMyReplies({ page, page_size: PAGE_SIZE })
    if (res.code === 0) {
      comments.value = res.data.list || []
      commentsTotal.value = res.data.total || 0
      commentsPage.value = res.data.page || page
    } else {
      commentsError.value = res.message || '加载失败'
    }
  } catch (err) {
    commentsError.value = err.message || '加载失败，请稍后重试'
  } finally {
    commentsLoading.value = false
  }
}

const onCommentsPageChange = (payload) => {
  loadComments(resolvePage(payload, commentsPage.value))
}

const removeComment = async (comment) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '删除评论',
    message: '确定删除这条评论吗？删除后无法恢复。',
  })
  if (!confirmed) return
  try {
    const res = await postApi.removeReply(comment.id)
    if (res.code === 0) {
      toast('success', '已删除', '评论已删除')
      const target = comments.value.length === 1 && commentsPage.value > 1
        ? commentsPage.value - 1
        : commentsPage.value
      await loadComments(target)
    } else {
      toast('error', '删除失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '删除失败', err.message || '请稍后重试')
  }
}

// ===== 分区切换时加载对应列表（每次切换都刷新，保证状态最新） =====
const loadActiveTab = () => {
  if (activeTab.value === 'comments') {
    loadComments(1)
  } else if (activeTab.value === 'drafts') {
    loadDrafts(1)
  } else {
    loadPosts(1)
  }
}

watch(activeTab, loadActiveTab, { immediate: true })
</script>

<template>
  <div class="page-wrap">
    <!-- 顶部说明 -->
    <section class="page-hero">
      <div class="hero-row">
        <div>
          <h1 class="page-title">内容管理</h1>
          <p class="page-sub">只管自己的内容：帖子、评论和没写完的草稿，都在这里打理。</p>
        </div>
        <lay-button type="primary" @click="goNewPost">发帖</lay-button>
      </div>
    </section>

    <!-- 分区切换 -->
    <div class="page-toolbar">
      <div class="tab-row">
        <lay-button
          v-for="tab in TABS"
          :key="tab.key"
          :type="activeTab === tab.key ? 'primary' : undefined"
          @click="switchTab(tab)"
        >
          {{ tab.label }}
        </lay-button>
      </div>
      <span class="page-toolbar__spacer"></span>
      <span class="muted tab-count">
        <template v-if="activeTab === 'posts'">{{ postsTotal }} 篇帖子</template>
        <template v-else-if="activeTab === 'comments'">{{ commentsTotal }} 条评论</template>
        <template v-else>{{ draftsTotal }} 篇草稿</template>
      </span>
    </div>

    <lay-card>
      <!-- ===== 帖子管理 ===== -->
      <template v-if="activeTab === 'posts'">
        <div v-if="postsLoading" class="loading-box">正在加载帖子…</div>

        <div v-else-if="postsError" class="empty-box">
          <p class="danger-text">{{ postsError }}</p>
          <lay-button type="primary" @click="loadPosts(postsPage)">重试</lay-button>
        </div>

        <div v-else-if="!posts.length" class="empty-box">
          <lay-empty description="还没有发布过帖子">
            <template #extra>
              <lay-button type="primary" @click="goNewPost">去发第一个帖子</lay-button>
            </template>
          </lay-empty>
        </div>

        <template v-else>
          <div v-for="post in posts" :key="post.id" class="list-row">
            <div class="list-row__main">
              <h3 class="list-row__title row-link" @click="goPost(post.id)">
                {{ post.title || '未命名帖子' }}
              </h3>
              <div class="meta">
                <span v-if="post.publish_time">{{ post.publish_time }}</span>
                <span v-if="post.edit_label">{{ post.edit_label }}</span>
                <span v-if="VISIBILITY_META[post.visibility]" :class="['status-tag', VISIBILITY_META[post.visibility].className]">
                  {{ VISIBILITY_META[post.visibility].label }}
                </span>
                <span v-if="REVIEW_META[post.review_status]" :class="['status-tag', REVIEW_META[post.review_status].className]">
                  {{ REVIEW_META[post.review_status].label }}
                </span>
                <span>{{ post.like_count || 0 }} 赞 · {{ post.reply_count || 0 }} 评论</span>
                <span>{{ post.view_count || 0 }} 浏览</span>
              </div>
              <p
                v-if="post.review_status === 4"
                class="review-note review-note--pending"
              >
                已提交审核，审核通过后才会在讨论区公开显示；当前只有你自己能看到这篇内容
              </p>
              <p
                v-else-if="post.review_status === 2 || post.review_status === 3"
                class="review-note"
              >
                {{ post.review_status === 2 ? '打回理由' : '封禁理由' }}：{{ post.review_note || '未填写' }}
              </p>
            </div>

            <div class="row-actions">
              <lay-button
                size="xs"
                :type="post.visibility === 0 ? 'primary' : undefined"
                @click="changeVisibility(post, 0)"
              >
                公开
              </lay-button>
              <lay-button
                size="xs"
                :type="post.visibility === 1 ? 'primary' : undefined"
                @click="changeVisibility(post, 1)"
              >
                私密
              </lay-button>
              <lay-button
                size="xs"
                :type="post.visibility === 2 ? 'primary' : undefined"
                @click="changeVisibility(post, 2)"
              >
                仅好友
              </lay-button>
              <lay-button size="xs" @click="goEdit(post.id)">编辑</lay-button>
              <lay-button size="xs" type="danger" @click="removePost(post)">删除</lay-button>
            </div>
          </div>

          <div class="pagination-wrap">
            <lay-page
              v-model="postsPage"
              :total="postsTotal"
              :limit="PAGE_SIZE"
              :layout="PAGE_LAYOUT"
              @change="onPostsPageChange"
            />
          </div>
        </template>
      </template>

      <!-- ===== 草稿箱 ===== -->
      <template v-else-if="activeTab === 'drafts'">
        <p class="tab-hint muted">草稿发布后才会进入讨论区，现在只有你自己能看到。</p>

        <div v-if="draftsLoading" class="loading-box">正在加载草稿…</div>

        <div v-else-if="draftsError" class="empty-box">
          <p class="danger-text">{{ draftsError }}</p>
          <lay-button type="primary" @click="loadDrafts(draftsPage)">重试</lay-button>
        </div>

        <div v-else-if="!drafts.length" class="empty-box">
          <lay-empty description="草稿箱空空的">
            <template #extra>
              <lay-button type="primary" @click="goNewPost">去写点什么</lay-button>
            </template>
          </lay-empty>
        </div>

        <template v-else>
          <div v-for="draft in drafts" :key="draft.id" class="list-row">
            <div class="list-row__main">
              <h3 class="list-row__title">{{ draft.title || '未命名草稿' }}</h3>
              <p class="draft-excerpt">{{ draft.excerpt || '（暂无摘要，继续写完再发布吧）' }}</p>
              <div class="meta">
                <span>更新于 {{ draft.create_time || '——' }}</span>
              </div>
            </div>
            <div class="row-actions">
              <lay-button size="xs" type="primary" @click="goEdit(draft.id)">继续编辑</lay-button>
              <lay-button size="xs" type="danger" @click="removeDraft(draft)">删除</lay-button>
            </div>
          </div>

          <div class="pagination-wrap">
            <lay-page
              v-model="draftsPage"
              :total="draftsTotal"
              :limit="PAGE_SIZE"
              :layout="PAGE_LAYOUT"
              @change="onDraftsPageChange"
            />
          </div>
        </template>
      </template>

      <!-- ===== 评论管理 ===== -->
      <template v-else>
        <div v-if="commentsLoading" class="loading-box">正在加载评论…</div>

        <div v-else-if="commentsError" class="empty-box">
          <p class="danger-text">{{ commentsError }}</p>
          <lay-button type="primary" @click="loadComments(commentsPage)">重试</lay-button>
        </div>

        <div v-else-if="!comments.length" class="empty-box">
          <lay-empty description="还没有发过评论">
            <template #extra>
              <lay-button type="primary" @click="router.push('/news')">去讨论区看看</lay-button>
            </template>
          </lay-empty>
        </div>

        <template v-else>
          <div v-for="comment in comments" :key="comment.id" class="list-row">
            <div class="list-row__main">
              <h3 class="list-row__title row-link" @click="goPost(comment.post_id)">
                {{ comment.post_title || '帖子已删除' }}
              </h3>
              <p class="comment-content">{{ comment.content }}</p>
              <div class="meta">
                <span>{{ comment.create_time || '——' }}</span>
                <span v-if="comment.parent_id">回复评论 #{{ comment.parent_id }}</span>
              </div>
            </div>
            <div class="row-actions">
              <lay-button size="xs" type="danger" @click="removeComment(comment)">删除</lay-button>
            </div>
          </div>

          <div class="pagination-wrap">
            <lay-page
              v-model="commentsPage"
              :total="commentsTotal"
              :limit="PAGE_SIZE"
              :layout="PAGE_LAYOUT"
              @change="onCommentsPageChange"
            />
          </div>
        </template>
      </template>
    </lay-card>
  </div>
</template>

<style scoped>
.hero-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.tab-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.tab-count {
  font-size: var(--text-sm);
}

.tab-hint {
  margin: 0 0 var(--space-4);
  font-size: var(--text-sm);
  padding: var(--space-3) var(--space-4);
  background: var(--ghibli-paper-50);
  border: 1px dashed var(--color-divider);
  border-radius: var(--radius-lg);
}

.loading-box {
  padding: var(--space-16) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.row-link {
  cursor: pointer;
  transition: color var(--duration-fast) var(--ease-gentle);
}

.row-link:hover {
  color: var(--ghibli-sky-600);
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: var(--space-2);
  flex-shrink: 0;
}

.draft-excerpt,
.comment-content {
  margin: 0 0 var(--space-2);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text-muted);
  word-break: break-word;
}

.comment-content {
  color: var(--color-text);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.review-note {
  margin: var(--space-2) 0 0;
  font-size: var(--text-xs);
  line-height: var(--leading-relaxed);
  color: var(--ghibli-warm-800);
  word-break: break-word;
}

.review-note--pending {
  color: var(--ghibli-sky-800);
}

@media (max-width: 768px) {
  .list-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .row-actions {
    justify-content: flex-start;
  }
}
</style>
