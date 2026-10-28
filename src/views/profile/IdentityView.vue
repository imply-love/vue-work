<script setup>
import { ref, computed, onMounted } from 'vue'
import { identityApi } from '@/api'

const loading = ref(false)
const loadError = ref('')
const applying = ref('')
const overview = ref({
  identity: '',
  identity_label: '',
  threshold: 20,
  anime_valid: 0,
  resource_valid: 0,
  applications: [],
})

const toast = (type, title, message) => {
  window.$ghibli?.showToast({ type, title, message })
}

const identityCodes = computed(() =>
  (overview.value.identity || '').split(',').filter(Boolean)
)

const cards = computed(() => [
  {
    type: 'anime_master',
    label: '番剧大佬',
    source: '番剧推荐',
    count: overview.value.anime_valid || 0,
    icon: '番',
    reward: '专属「番剧大佬」称号 + 未公开奖励',
  },
  {
    type: 'resource_master',
    label: '我就是资源',
    source: '资源分享',
    count: overview.value.resource_valid || 0,
    icon: '资',
    reward: '专属「我就是资源」称号 + 未公开奖励',
  },
])

const threshold = computed(() => overview.value.threshold || 20)

const isHeld = (type) => identityCodes.value.includes(type)

const isPending = (type) =>
  (overview.value.applications || []).some(
    (item) => item.identity_type === type && item.status === 0
  )

const canApply = (card) => {
  if (isHeld(card.type) || isPending(card.type)) return false
  return card.count >= threshold.value
}

const percent = (count) => Math.min(100, Math.round((count / threshold.value) * 100))

const statusMeta = (status) => {
  if (status === 1) return { label: '已通过', className: '' }
  if (status === 2) return { label: '已驳回', className: 'status-tag--reject' }
  return { label: '审核中', className: 'status-tag--recommend' }
}

const loadOverview = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const res = await identityApi.getOverview()
    if (res.code === 0) {
      overview.value = res.data || overview.value
    } else {
      loadError.value = res.message || '加载失败'
    }
  } catch (err) {
    loadError.value = err.message || '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const submitApply = async (card) => {
  const reason = await window.$ghibli?.showPrompt({
    title: `申请成为「${card.label}」`,
    placeholder: '填写申请说明（选填），管理员会参考这段说明审批',
  })
  if (reason === null || reason === undefined) return

  applying.value = card.type
  try {
    const res = await identityApi.apply({ identity_type: card.type, reason })
    if (res.code === 0) {
      toast('success', '申请已提交', res.message || '请等待管理员审批')
      await loadOverview()
    } else {
      toast('error', '申请失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '申请失败', err.message || '请稍后重试')
  } finally {
    applying.value = ''
  }
}

onMounted(loadOverview)
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero">
      <h1 class="page-title">身份申请</h1>
      <p class="page-sub">
        有效推荐 / 有效分享满 {{ threshold }} 条即可申请专属身份，通过后获得称号与未公开奖励
      </p>
    </section>

    <div v-if="loading" class="empty-box">正在加载身份信息…</div>
    <lay-card v-else-if="loadError">
      <div class="empty-box">
        <p class="danger-text">{{ loadError }}</p>
        <lay-button type="primary" @click="loadOverview">重试</lay-button>
      </div>
    </lay-card>

    <template v-else>
      <div class="identity-grid">
        <lay-card v-for="card in cards" :key="card.type" class="identity-card">
          <div class="identity-head">
            <span class="identity-icon">{{ card.icon }}</span>
            <div>
              <h2 class="identity-title">{{ card.label }}</h2>
              <p class="muted identity-source">有效{{ card.source }}：{{ card.count }} 条</p>
            </div>
            <lay-tag
              v-if="isHeld(card.type)"
              type="normal"
              variant="light"
              shape="round"
              size="sm"
            >
              已获得
            </lay-tag>
            <lay-tag
              v-else-if="isPending(card.type)"
              type="warm"
              variant="light"
              shape="round"
              size="sm"
            >
              审核中
            </lay-tag>
          </div>

          <div class="progress-row">
            <div class="progress-track">
              <div class="progress-bar" :style="{ width: percent(card.count) + '%' }"></div>
            </div>
            <span class="muted progress-text">{{ card.count }} / {{ threshold }}</span>
          </div>

          <p class="identity-reward">奖励：{{ card.reward }}</p>

          <div class="identity-actions">
            <lay-button
              v-if="!isHeld(card.type) && !isPending(card.type)"
              type="primary"
              :disabled="!canApply(card)"
              :loading="applying === card.type"
              @click="submitApply(card)"
            >
              申请成为{{ card.label }}
            </lay-button>
            <span v-if="isHeld(card.type)" class="muted">你已拥有该称号</span>
            <span v-else-if="isPending(card.type)" class="muted">申请审核中，请耐心等待</span>
            <span v-else-if="!canApply(card)" class="muted">
              还差 {{ threshold - card.count }} 条有效{{ card.source }}
            </span>
          </div>
        </lay-card>
      </div>

      <lay-card title="申请记录">
        <lay-empty v-if="!overview.applications.length" description="还没有提交过身份申请" />
        <div v-else>
          <div v-for="item in overview.applications" :key="item.id" class="list-row">
            <div class="list-row__main">
              <h3 class="list-row__title">{{ item.identity_label }} 申请</h3>
              <div class="meta">
                <span :class="['status-tag', statusMeta(item.status).className]">
                  {{ statusMeta(item.status).label }}
                </span>
                <span>提交于 {{ item.create_time }}</span>
                <span v-if="item.handle_time">处理于 {{ item.handle_time }}</span>
              </div>
              <p class="apply-reason">申请说明：{{ item.reason || '未填写' }}</p>
              <p v-if="item.admin_note" class="apply-reason">审批备注：{{ item.admin_note }}</p>
            </div>
          </div>
        </div>
      </lay-card>
    </template>
  </div>
</template>

<style scoped>
.identity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

.identity-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.identity-icon {
  width: 52px;
  height: 52px;
  flex-shrink: 0;
  border-radius: var(--radius-xl);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: var(--text-xl);
  color: var(--ghibli-sky-700);
  background: var(--ghibli-sky-50);
  border: 1px solid var(--ghibli-sky-200);
}

.identity-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-lg);
  color: var(--color-text);
}

.identity-source {
  margin: var(--space-1) 0 0;
  font-size: var(--text-xs);
}

.progress-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin: var(--space-5) 0 var(--space-3);
}

.progress-track {
  flex: 1;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--ghibli-paper-200);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, var(--ghibli-sky-400), var(--ghibli-forest-400));
  transition: width var(--duration-normal) var(--ease-gentle);
}

.progress-text {
  font-size: var(--text-xs);
  white-space: nowrap;
}

.identity-reward {
  margin: 0 0 var(--space-4);
  font-size: var(--text-sm);
  color: var(--ghibli-warm-800);
}

.identity-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  font-size: var(--text-sm);
}

.apply-reason {
  margin: var(--space-2) 0 0;
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text);
  word-break: break-word;
}
</style>
