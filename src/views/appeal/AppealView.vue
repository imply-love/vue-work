<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const PAGE_SIZE = 10

const router = useRouter()
const authStore = useAuthStore()

const isBanned = computed(() => authStore.user?.status === 2)

const reason = ref('')
const submitting = ref(false)

const appeals = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)

const toast = (type, title, message) => {
  window.$ghibli?.showToast({ type, title, message })
}

const statusText = (status) => {
  if (status === 0) return '待处理'
  if (status === 1) return '已通过'
  if (status === 2) return '已驳回'
  return '未知'
}

const statusClass = (status) => {
  if (status === 1) return 'status-tag status-tag--friends'
  if (status === 2) return 'status-tag status-tag--reject'
  return 'status-tag'
}

const loadAppeals = async (targetPage = 1) => {
  loading.value = true
  try {
    const res = await userApi.getAppeals({ page: targetPage, page_size: PAGE_SIZE })
    if (res.code === 0) {
      appeals.value = res.data.list || []
      total.value = res.data.total || 0
      page.value = res.data.page || targetPage
    } else {
      toast('error', '加载申诉记录失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '加载申诉记录失败', err.message || '请稍后重试')
  } finally {
    loading.value = false
  }
}

const changePage = (value) => {
  page.value = value
  loadAppeals(value)
}

const submitAppeal = async () => {
  const text = reason.value.trim()
  if (!text) {
    toast('warning', '无法提交', '请填写申诉理由')
    return
  }
  if (text.length > 1000) {
    toast('warning', '无法提交', '申诉理由不能超过 1000 字')
    return
  }
  submitting.value = true
  try {
    const res = await userApi.submitAppeal({ reason: text })
    if (res.code === 0) {
      toast('success', '申诉已提交', res.message || '请耐心等待管理员处理')
      reason.value = ''
      await loadAppeals(1)
    } else {
      toast('error', '提交失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '提交失败', err.message || '请稍后重试')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await authStore.fetchProfile()
  loadAppeals(1)
})
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero">
      <h1 class="page-title">账号申诉</h1>
      <p class="page-sub">如果账号被误封，可以在这里说明情况，等待管理员复核。</p>
    </section>

    <div class="page-toolbar">
      <lay-button @click="router.push('/profile')">返回个人中心</lay-button>
      <span class="page-toolbar__spacer"></span>
      <lay-button @click="router.push('/')">返回首页</lay-button>
    </div>

    <template v-if="isBanned">
      <lay-card title="封禁信息" class="appeal-card">
        <p class="ban-reason">理由：{{ authStore.user?.ban_reason || '管理员未填写具体理由' }}</p>
        <p class="muted">封禁时间：{{ authStore.user?.ban_time || '未知' }}</p>
      </lay-card>

      <lay-card title="提交申诉" class="appeal-card">
        <div class="appeal-field">
          <label class="field-label">申诉理由</label>
          <lay-textarea
            v-model="reason"
            :maxlength="1000"
            :rows="5"
            show-count
            placeholder="请说明账号的使用情况、认为误封的原因等，最多 1000 字"
          />
        </div>
        <div class="form-actions">
          <lay-button type="primary" :loading="submitting" :disabled="submitting" @click="submitAppeal">
            提交申诉
          </lay-button>
        </div>
      </lay-card>
    </template>

    <lay-card v-else>
      <div class="empty-box">
        <h3 class="empty-box__title">当前账号状态正常，无需申诉</h3>
        <p class="muted">继续去追番、安利、找同好吧。</p>
        <lay-button type="primary" @click="router.push('/')">返回首页</lay-button>
      </div>
    </lay-card>

    <lay-card title="我的申诉记录" class="appeal-card">
      <div v-if="loading" class="muted">加载中…</div>
      <lay-empty v-else-if="appeals.length === 0" description="暂无申诉记录" />
      <div v-else>
        <div v-for="item in appeals" :key="item.id" class="list-row">
          <div class="list-row__main">
            <p class="list-row__title appeal-reason">{{ item.reason }}</p>
            <div class="meta">
              <span>提交于 {{ item.create_time }}</span>
              <span :class="statusClass(item.status)">{{ statusText(item.status) }}</span>
              <span v-if="item.handle_time">处理于 {{ item.handle_time }}</span>
            </div>
            <p v-if="item.admin_note" class="admin-note">管理员备注：{{ item.admin_note }}</p>
          </div>
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
.appeal-card {
  margin-bottom: var(--space-6);
}

.ban-reason {
  margin: 0 0 var(--space-2);
  font-weight: var(--font-semibold);
  color: var(--color-error);
}

.appeal-field {
  margin-bottom: var(--space-4);
}

.field-label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.appeal-reason {
  white-space: normal;
  word-break: break-word;
}

.admin-note {
  margin: var(--space-2) 0 0;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: pre-wrap;
}
</style>
