<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationApi } from '@/api'

const router = useRouter()

const PAGE_SIZE = 10
const notifications = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const loadError = ref('')
const unreadOnly = ref(false)
const reading = ref(false)

const toast = (type, title, message) => {
  window.$ghibli?.showToast({ type, title, message })
}

const typeLabel = (type) => {
  if (type === 'anime_request') return '求番'
  if (type === 'identity') return '身份申请'
  return '系统'
}

const loadNotifications = async (target = page.value) => {
  loading.value = true
  loadError.value = ''
  try {
    const params = { page: target, page_size: PAGE_SIZE }
    if (unreadOnly.value) params.unread = 1
    const res = await notificationApi.getList(params)
    if (res.code === 0) {
      notifications.value = res.data.list || []
      total.value = res.data.total || 0
      page.value = res.data.page || target
    } else {
      loadError.value = res.message || '加载失败'
    }
  } catch (err) {
    loadError.value = err.message || '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const toggleUnreadOnly = (value) => {
  if (unreadOnly.value === value) return
  unreadOnly.value = value
  loadNotifications(1)
}

const changePage = (payload) => {
  const current = typeof payload === 'number' ? payload : payload?.current
  if (!current) return
  loadNotifications(current)
}

const markAllRead = async () => {
  reading.value = true
  try {
    const res = await notificationApi.readAll()
    if (res.code === 0) {
      toast('success', '已全部已读', '所有通知已标记为已读')
      await loadNotifications(page.value)
    }
  } catch (err) {
    toast('error', '操作失败', err.message || '请稍后重试')
  } finally {
    reading.value = false
  }
}

const openNotification = async (item) => {
  if (!item.is_read) {
    try {
      await notificationApi.read(item.id)
    } catch {
      // 标记已读失败不阻塞跳转
    }
  }
  if (item.link) {
    router.push(item.link)
  } else {
    loadNotifications(page.value)
  }
}

onMounted(() => loadNotifications(1))
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero">
      <h1 class="page-title">消息通知</h1>
      <p class="page-sub">求番提醒、身份申请结果都会出现在这里</p>
    </section>

    <div class="page-toolbar notify-toolbar">
      <div class="tab-row">
        <lay-button
          :type="!unreadOnly ? 'primary' : undefined"
          @click="toggleUnreadOnly(false)"
        >
          全部通知
        </lay-button>
        <lay-button
          :type="unreadOnly ? 'primary' : undefined"
          @click="toggleUnreadOnly(true)"
        >
          仅看未读
        </lay-button>
      </div>
      <span class="page-toolbar__spacer"></span>
      <span class="muted notify-count">共 {{ total }} 条</span>
      <lay-button :loading="reading" @click="markAllRead">全部已读</lay-button>
    </div>

    <lay-card>
      <div v-if="loading" class="empty-box">正在加载通知…</div>
      <div v-else-if="loadError" class="empty-box">
        <p class="danger-text">{{ loadError }}</p>
        <lay-button type="primary" @click="loadNotifications(page)">重试</lay-button>
      </div>
      <lay-empty v-else-if="!notifications.length" description="暂无通知" />
      <template v-else>
        <div
          v-for="item in notifications"
          :key="item.id"
          class="list-row notify-row"
          :class="{ 'notify-row--unread': !item.is_read }"
          @click="openNotification(item)"
        >
          <span class="notify-dot" :class="{ 'notify-dot--read': item.is_read }" aria-hidden="true"></span>
          <div class="list-row__main">
            <h3 class="list-row__title">
              {{ item.title || '通知' }}
              <span class="notify-type">{{ typeLabel(item.type) }}</span>
            </h3>
            <p class="notify-content">{{ item.content }}</p>
            <div class="meta">
              <time :datetime="item.create_time">{{ item.create_time }}</time>
              <span v-if="!item.is_read" class="notify-unread">未读</span>
            </div>
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
      </template>
    </lay-card>
  </div>
</template>

<style scoped>
.notify-toolbar {
  align-items: center;
}

.notify-count {
  font-size: var(--text-sm);
}

.notify-row {
  cursor: pointer;
  align-items: flex-start;
}

.notify-row--unread .list-row__title {
  color: var(--ghibli-sky-700);
}

.notify-dot {
  width: 8px;
  height: 8px;
  margin-top: 8px;
  border-radius: 50%;
  background: var(--ghibli-sakura-500);
  flex-shrink: 0;
}

.notify-dot--read {
  background: var(--color-divider);
}

.notify-type {
  margin-left: var(--space-2);
  padding: 1px var(--space-2);
  border-radius: var(--radius-full);
  background: var(--ghibli-sky-50);
  color: var(--ghibli-sky-700);
  font-size: var(--text-xs);
  font-weight: var(--font-normal);
}

.notify-content {
  margin: var(--space-2) 0 0;
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text);
  word-break: break-word;
}

.notify-unread {
  color: var(--ghibli-sakura-500);
}
</style>
