<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { friendApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const PAGE_SIZE = 10

const router = useRouter()
const authStore = useAuthStore()

const tabs = [
  { key: 'incoming', label: '收到的申请' },
  { key: 'outgoing', label: '发出的申请' },
  { key: 'friends', label: '我的好友' },
]

const mode = ref('incoming')
const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const error = ref('')
const handlingId = ref(null)

const emptyText = computed(() => {
  if (mode.value === 'incoming') return '暂无收到的好友申请'
  if (mode.value === 'outgoing') return '暂无发出的好友申请'
  return '还没有好友，去关注列表里认识新同好吧'
})

const toast = (type, title, message) => {
  window.$ghibli?.showToast({ type, title, message })
}

const statusText = (status) => {
  if (status === 0) return '待处理'
  if (status === 1) return '已同意'
  if (status === 2) return '已拒绝'
  return '未知'
}

const statusClass = (status) => {
  if (status === 1) return 'status-tag status-tag--friends'
  if (status === 2) return 'status-tag status-tag--reject'
  return 'status-tag'
}

const avatarText = (item) => {
  const name = item.nickname || item.username || ''
  return name ? name.slice(0, 1).toUpperCase() : '?'
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = { page: page.value, page_size: PAGE_SIZE }
    let res
    if (mode.value === 'friends') {
      res = await friendApi.getFriends(params)
    } else {
      res = await friendApi.getRequests({ direction: mode.value, page: page.value, page_size: PAGE_SIZE })
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

const switchMode = (key) => {
  if (mode.value === key) return
  mode.value = key
  page.value = 1
  list.value = []
  total.value = 0
  load()
}

const changePage = (value) => {
  page.value = value
  load()
}

const handleRequest = async (item, action) => {
  handlingId.value = item.id
  try {
    const res = await friendApi.handleRequest(item.id, { action })
    if (res.code === 0) {
      toast('success', action === 'accept' ? '已添加好友' : '已拒绝申请', res.message)
      await load()
      // 处理完刷新一次待处理数量，导航栏角标才准确
      await friendApi.getPendingCount().catch(() => null)
    }
  } catch (err) {
    toast('error', '操作失败', err.message || '请稍后重试')
  } finally {
    handlingId.value = null
  }
}

const removeFriend = async (item) => {
  const confirmed = await window.$ghibli?.showConfirm({
    title: '解除好友',
    message: `确定解除与「${item.nickname || item.username}」的好友关系吗？`,
  })
  if (!confirmed) return
  try {
    const res = await friendApi.removeFriend(item.id)
    if (res.code === 0) {
      toast('success', '已解除好友关系', res.message)
      if (list.value.length === 1 && page.value > 1) {
        page.value -= 1
      }
      await load()
    }
  } catch (err) {
    toast('error', '操作失败', err.message || '请稍后重试')
  }
}

// ===== 添加好友 =====
const addForm = ref({ user_id: '', message: '' })
const addSaving = ref(false)

const sendRequest = async () => {
  const targetId = addForm.value.user_id.trim()
  if (!targetId) {
    toast('warning', '无法发送', '请填写对方用户 ID')
    return
  }
  if (!/^\d+$/.test(targetId)) {
    toast('warning', '无法发送', '用户 ID 需为数字')
    return
  }
  if (authStore.user && Number(targetId) === Number(authStore.user.id)) {
    toast('warning', '无法发送', '不能添加自己为好友')
    return
  }
  addSaving.value = true
  try {
    const res = await friendApi.sendRequest({
      user_id: Number(targetId),
      message: addForm.value.message.trim(),
    })
    if (res.code === 0) {
      toast('success', '申请已发送', res.message)
      addForm.value = { user_id: '', message: '' }
      if (mode.value === 'outgoing') await load()
    }
  } catch (err) {
    toast('error', '发送失败', err.message || '请稍后重试')
  } finally {
    addSaving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero">
      <h1 class="page-title">好友</h1>
      <p class="page-sub">处理好友申请，看看已经和你成为同好的人。</p>
    </section>

    <div class="page-toolbar">
      <lay-button
        v-for="tab in tabs"
        :key="tab.key"
        :type="mode === tab.key ? 'primary' : undefined"
        @click="switchMode(tab.key)"
      >
        {{ tab.label }}
      </lay-button>
      <span class="page-toolbar__spacer"></span>
      <lay-button @click="router.push('/profile')">返回个人中心</lay-button>
    </div>

    <lay-card title="添加好友" class="friend-add">
      <div class="add-row">
        <div class="add-field add-field--id">
          <label class="field-label">用户 ID</label>
          <lay-input v-model="addForm.user_id" placeholder="对方用户 ID" />
        </div>
        <div class="add-field">
          <label class="field-label">留言</label>
          <lay-input v-model="addForm.message" :maxlength="255" placeholder="简单介绍一下来意（选填）" />
        </div>
        <lay-button type="primary" :loading="addSaving" :disabled="addSaving" @click="sendRequest">
          发送申请
        </lay-button>
      </div>
    </lay-card>

    <lay-card class="friend-list">
      <div v-if="loading" class="muted">加载中…</div>
      <div v-else-if="error" class="empty-box">
        <h3 class="empty-box__title">加载失败</h3>
        <p>{{ error }}</p>
        <lay-button type="primary" @click="load">重试</lay-button>
      </div>
      <lay-empty v-else-if="list.length === 0" :description="emptyText" />

      <div v-else>
        <div v-for="item in list" :key="item.id" class="list-row">
          <img v-if="item.avatar" :src="item.avatar" :alt="item.nickname" class="row-avatar" />
          <div v-else class="avatar-circle">{{ avatarText(item) }}</div>

          <div class="list-row__main">
            <p class="list-row__title">{{ item.nickname || item.username }}</p>
            <div class="meta">
              <template v-if="mode === 'friends'">
                <span>关注 {{ item.following_count ?? 0 }}</span>
                <span>粉丝 {{ item.followers_count ?? 0 }}</span>
                <span v-if="item.create_time">成为好友于 {{ item.create_time }}</span>
              </template>
              <template v-else>
                <span v-if="item.message">留言：{{ item.message }}</span>
                <span v-else>未填写留言</span>
                <span v-if="item.create_time">{{ item.create_time }}</span>
                <span :class="statusClass(item.status)">{{ statusText(item.status) }}</span>
              </template>
            </div>
          </div>

          <div v-if="mode === 'incoming' && item.status === 0" class="form-actions">
            <lay-button
              type="primary"
              size="sm"
              :loading="handlingId === item.id"
              :disabled="handlingId === item.id"
              @click="handleRequest(item, 'accept')"
            >
              同意
            </lay-button>
            <lay-button
              size="sm"
              :disabled="handlingId === item.id"
              @click="handleRequest(item, 'reject')"
            >
              拒绝
            </lay-button>
          </div>

          <lay-button v-if="mode === 'friends'" size="sm" @click="removeFriend(item)">
            解除好友
          </lay-button>
        </div>

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
.friend-add {
  margin-bottom: var(--space-6);
}

.add-row {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.add-field {
  flex: 1;
  min-width: 180px;
}

.add-field--id {
  flex: 0 0 160px;
  min-width: 120px;
}

.field-label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.row-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
</style>
