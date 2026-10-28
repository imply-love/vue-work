<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { resourceApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// ===== 资源列表 =====
const resources = ref([])
const loading = ref(false)
const listError = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)

const loadResources = async () => {
  loading.value = true
  listError.value = ''
  try {
    const res = await resourceApi.getList({ page: page.value, page_size: pageSize })
    if (res.code === 0) {
      resources.value = res.data.list || []
      total.value = res.data.total || 0
    } else {
      listError.value = res.message
    }
  } catch (err) {
    listError.value = err.message || '获取资源列表失败'
  } finally {
    loading.value = false
  }
}

const changePage = (payload) => {
  const current = typeof payload === 'number' ? payload : payload?.current
  if (!current) return
  page.value = current
  loadResources()
}

// ===== 内嵌分享表单 =====
const composerOpen = ref(false)
const shareForm = ref({ title: '', link: '', description: '', visibility: '0' })
const submitting = ref(false)
const formError = ref('')

// 查看条件：0-所有同好 1-仅管理员与特殊身份 2-仅自己
const VISIBILITY_META = {
  0: { label: '所有同好', type: 'normal' },
  1: { label: '仅管理员与特殊身份', type: 'warm' },
  2: { label: '仅自己', type: 'primary' },
}

const visibilityMeta = (value) => VISIBILITY_META[value] || VISIBILITY_META[0]

const openComposer = () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  formError.value = ''
  composerOpen.value = true
}

const closeComposer = () => {
  composerOpen.value = false
  formError.value = ''
}

const submitShare = async () => {
  if (submitting.value) return
  formError.value = ''
  const title = shareForm.value.title.trim()
  const link = shareForm.value.link.trim()
  if (!title) {
    formError.value = '请填写资源标题'
    return
  }
  if (!link) {
    formError.value = '请填写资源链接'
    return
  }

  submitting.value = true
  try {
    const res = await resourceApi.create({
      title,
      link,
      description: shareForm.value.description.trim(),
      visibility: Number(shareForm.value.visibility),
    })
    if (res.code === 0) {
      shareForm.value = { title: '', link: '', description: '', visibility: '0' }
      window.$ghibli?.showToast({ type: 'success', title: '分享成功', message: '资源已分享给大家' })
      if (page.value !== 1) page.value = 1
      await loadResources()
    } else {
      formError.value = res.message
    }
  } catch (err) {
    formError.value = err.message || '分享失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

const goLogin = () => router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
const avatarText = (name) => (name || '同好').slice(0, 1)

// 打开资源链接：新标签页跳转，原列表标题不再作为链接
const openResource = (item) => {
  if (!item.link) return
  window.open(item.link, '_blank', 'noopener,noreferrer')
}

// 发布者本人或管理员可删除资源
const canDelete = (item) =>
  authStore.isLoggedIn &&
  (item.user_id === authStore.user?.id || authStore.user?.role === 1)

const deletingId = ref(0)

const deleteResource = async (item) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '删除资源',
    message: `确定删除「${item.title}」吗？该操作不可撤销。`,
  })
  if (!confirmed) return

  deletingId.value = item.id
  try {
    const res = await resourceApi.remove(item.id)
    if (res.code === 0) {
      window.$ghibli?.showToast({ type: 'success', title: '已删除', message: res.message || '资源已删除' })
      // 删掉当前页最后一条时回退一页，避免留在空页
      if (resources.value.length === 1 && page.value > 1) page.value -= 1
      await loadResources()
    } else {
      window.$ghibli?.showToast({ type: 'error', title: '删除失败', message: res.message || '请稍后重试' })
    }
  } catch (err) {
    window.$ghibli?.showToast({ type: 'error', title: '删除失败', message: err.message || '请稍后重试' })
  } finally {
    deletingId.value = 0
  }
}

onMounted(loadResources)
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero skills-hero">
      <div class="skills-hero__text">
        <h1 class="page-title">资源分享</h1>
        <p class="page-sub">高清资源、字幕组、周边情报，同好们的好东西都放在这儿</p>
      </div>
      <lay-button type="normal" size="lg" @click="openComposer">分享资源</lay-button>
    </section>

    <lay-card v-if="composerOpen" class="composer-card">
      <div class="composer-head">
        <h2 class="composer-title">分享一个好资源</h2>
        <lay-button size="sm" @click="closeComposer">收起</lay-button>
      </div>

      <lay-form class="composer-form" label-position="top" @submit="submitShare">
        <div v-if="formError" class="form-error" role="alert">{{ formError }}</div>

        <lay-form-item label="标题" required>
          <lay-input
            v-model="shareForm.title"
            placeholder="例如：千与千寻 蓝光 1080P 字幕合集"
            maxlength="200"
            allow-clear
          />
        </lay-form-item>

        <lay-form-item label="链接" required>
          <lay-input
            v-model="shareForm.link"
            type="url"
            placeholder="以 http:// 或 https:// 开头的有效地址"
            maxlength="500"
            allow-clear
          />
        </lay-form-item>

        <lay-form-item label="查看条件" required>
          <lay-select v-model="shareForm.visibility" :allow-clear="false" style="width: 240px">
            <lay-select-option label="所有同好" value="0" />
            <lay-select-option label="仅管理员与特殊身份" value="1" />
            <lay-select-option label="仅自己" value="2" />
          </lay-select>
        </lay-form-item>

        <lay-form-item label="描述（选填）">
          <lay-textarea
            v-model="shareForm.description"
            :rows="4"
            :maxlength="5000"
            show-count
            placeholder="清晰度、字幕组、大小等补充信息，帮大家判断值不值得下"
          />
        </lay-form-item>

        <div class="form-actions">
          <lay-button type="primary" native-type="submit" :loading="submitting">
            {{ submitting ? '分享中...' : '分享资源' }}
          </lay-button>
          <lay-button native-type="button" @click="closeComposer">取消</lay-button>
        </div>
      </lay-form>
    </lay-card>

    <lay-card v-if="loading && resources.length === 0">
      <div class="empty-box">正在把同好们的分享搬过来……</div>
    </lay-card>

    <lay-card v-else-if="listError">
      <div class="empty-box">
        <h3 class="empty-box__title">资源列表走丢了</h3>
        <p class="muted">{{ listError }}</p>
        <lay-button type="warm" @click="loadResources">重试</lay-button>
      </div>
    </lay-card>

    <lay-card v-else-if="resources.length === 0">
      <div class="empty-box">
        <h3 class="empty-box__title">还没有人分享</h3>
        <p class="muted">手上有好东西？点右上角「分享资源」，把好东西交给同好们</p>
        <lay-button type="primary" @click="openComposer">分享资源</lay-button>
      </div>
    </lay-card>

    <lay-card v-else class="list-card">
      <ul class="resource-list">
        <li v-for="item in resources" :key="item.id" class="list-row">
          <span class="avatar-circle" aria-hidden="true">{{ avatarText(item.author_nickname) }}</span>
          <div class="list-row__main">
            <h3 class="list-row__title">{{ item.title }}</h3>
            <p v-if="item.description" class="resource-desc">{{ item.description }}</p>
            <div class="meta">
              <span>{{ item.author_nickname || '热心同好' }}</span>
              <time :datetime="item.create_time">{{ item.create_time }}</time>
              <lay-tag
                :type="visibilityMeta(item.visibility).type"
                variant="light"
                shape="round"
                size="sm"
              >
                {{ visibilityMeta(item.visibility).label }}
              </lay-tag>
            </div>
          </div>
          <div class="resource-actions">
            <lay-button size="sm" type="primary" @click="openResource(item)">打开</lay-button>
            <lay-button
              v-if="canDelete(item)"
              size="sm"
              type="danger"
              :loading="deletingId === item.id"
              @click="deleteResource(item)"
            >
              删除
            </lay-button>
          </div>
        </li>
      </ul>
    </lay-card>

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
.skills-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-6);
}

.skills-hero__text {
  min-width: 0;
}

.skills-hero .page-title {
  margin-bottom: var(--space-2);
}

.composer-card {
  margin-bottom: var(--space-6);
  border-color: var(--ghibli-forest-200);
}

.composer-card :deep(.layui-card-body) {
  padding: var(--space-6) var(--space-8);
}

.composer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.composer-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0;
}

.composer-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.composer-form :deep(.layui-form-item) {
  margin-bottom: 0;
}

.form-error {
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-bg);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-lg);
  color: var(--color-error);
  font-size: var(--text-sm);
}

.list-card :deep(.layui-card-body) {
  padding: var(--space-4) var(--space-8);
}

.resource-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.resource-desc {
  margin: var(--space-2) 0 0;
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
}

.meta {
  margin-top: var(--space-2);
}

.resource-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .skills-hero {
    padding: var(--space-8) var(--space-6);
  }

  .composer-card :deep(.layui-card-body),
  .list-card :deep(.layui-card-body) {
    padding: var(--space-4) var(--space-5);
  }
}
</style>
