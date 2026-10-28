<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { userApi, favoriteApi, notificationApi } from '@/api'

// 与后端 utils/verify_code.py 的 CODE_RESEND_INTERVAL 保持一致
const RESEND_SECONDS = 60
const FAVORITE_PAGE_SIZE = 6
const LOG_PAGE_SIZE = 10

const router = useRouter()
const authStore = useAuthStore()

const userInfo = computed(() => authStore.user)
const isBanned = computed(() => userInfo.value?.status === 2)
const avatarText = computed(() => {
  const name = userInfo.value?.nickname || userInfo.value?.username || ''
  return name ? name.slice(0, 1).toUpperCase() : '?'
})

const toast = (type, title, message) => {
  window.$ghibli?.showToast({ type, title, message })
}

// ===== 特殊身份（番剧大佬 / 我就是资源）=====
const IDENTITY_LABELS = {
  anime_master: '番剧大佬',
  resource_master: '我就是资源',
}

const identityLabels = computed(() => {
  const raw = userInfo.value?.identity || ''
  return raw
    .split(',')
    .filter(Boolean)
    .map((code) => IDENTITY_LABELS[code])
    .filter(Boolean)
})

// ===== 未读通知 =====
const unreadCount = ref(0)

const loadUnread = async () => {
  try {
    const res = await notificationApi.getUnreadCount()
    unreadCount.value = res.code === 0 ? res.data.count : 0
  } catch {
    unreadCount.value = 0
  }
}

const formatDate = (value) => {
  if (!value) return ''
  return String(value)
}

// ===== 基本资料 =====
const profileForm = ref({ nickname: '', email: '', code: '' })
const nicknameSaving = ref(false)
const emailSaving = ref(false)
const codeSending = ref(false)
const countdown = ref(0)
let countdownTimer = null

// 邮箱一旦改动就必须带验证码，否则「邮箱已验证」的状态会被绕过
const emailChanged = computed(() => {
  return profileForm.value.email.trim() !== (userInfo.value?.email || '')
})

const syncProfileForm = () => {
  profileForm.value.nickname = userInfo.value?.nickname || ''
  profileForm.value.email = userInfo.value?.email || ''
  profileForm.value.code = ''
}

const startCountdown = () => {
  stopCountdown()
  countdown.value = RESEND_SECONDS
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) stopCountdown()
  }, 1000)
}

const stopCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  countdown.value = 0
}

const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

const saveNickname = async () => {
  const nickname = profileForm.value.nickname.trim()
  if (!nickname) {
    toast('warning', '无法保存', '昵称不能为空')
    return
  }
  if (nickname.length > 50) {
    toast('warning', '无法保存', '昵称长度不能超过 50 位')
    return
  }
  nicknameSaving.value = true
  const result = await authStore.updateProfile({
    nickname,
    email: userInfo.value?.email || '',
  })
  nicknameSaving.value = false
  if (result.success) {
    syncProfileForm()
    toast('success', '保存成功', '昵称已更新')
  } else {
    toast('error', '保存失败', result.message || '请稍后重试')
  }
}

const handleSendEmailCode = async () => {
  const email = profileForm.value.email.trim()
  if (!isValidEmail(email)) {
    toast('warning', '无法发送', '请先填写正确的邮箱地址')
    return
  }
  codeSending.value = true
  try {
    const res = await userApi.sendBindEmailCode({ email })
    if (res.code === 0) {
      startCountdown()
      toast('success', '验证码已发送', res.message || '请查收新邮箱中的验证码')
    }
  } catch (err) {
    toast('error', '发送失败', err.message || '请稍后重试')
  } finally {
    codeSending.value = false
  }
}

const saveEmail = async () => {
  const email = profileForm.value.email.trim()
  if (!isValidEmail(email)) {
    toast('warning', '无法保存', '请填写正确的邮箱地址')
    return
  }
  if (emailChanged.value && !profileForm.value.code.trim()) {
    toast('warning', '无法保存', '更换邮箱需要填写验证码')
    return
  }
  const payload = { nickname: userInfo.value?.nickname || '', email }
  if (emailChanged.value) payload.code = profileForm.value.code.trim()

  emailSaving.value = true
  const result = await authStore.updateProfile(payload)
  emailSaving.value = false
  if (result.success) {
    syncProfileForm()
    stopCountdown()
    toast('success', '保存成功', '邮箱已更新')
  } else {
    toast('error', '保存失败', result.message || '请稍后重试')
  }
}

// ===== 手机号（选填，空串表示解绑） =====
const phoneInput = ref('')
const phoneSaving = ref(false)

const savePhone = async () => {
  const phone = phoneInput.value.trim()
  if (phone && !/^1[3-9]\d{9}$/.test(phone)) {
    toast('warning', '无法保存', '手机号需为 11 位中国大陆号码')
    return
  }
  phoneSaving.value = true
  const result = await authStore.updatePhone({ phone })
  phoneSaving.value = false
  if (result.success) {
    phoneInput.value = userInfo.value?.phone || ''
    toast('success', result.message || '保存成功', phone ? '手机号已绑定' : '已解绑手机号')
  } else {
    toast('error', '保存失败', result.message || '请稍后重试')
  }
}

// ===== 修改密码 =====
const pwdForm = ref({ old_password: '', new_password: '', confirm: '' })
const pwdSaving = ref(false)

const submitPassword = async () => {
  const { old_password, new_password, confirm } = pwdForm.value
  if (!old_password || !new_password) {
    toast('warning', '无法提交', '请填写原密码和新密码')
    return
  }
  if (new_password.length < 6 || new_password.length > 20) {
    toast('warning', '无法提交', '新密码长度需为 6-20 位')
    return
  }
  if (new_password !== confirm) {
    toast('warning', '无法提交', '两次输入的新密码不一致')
    return
  }
  pwdSaving.value = true
  try {
    const res = await userApi.changePassword({ old_password, new_password })
    if (res.code === 0) {
      pwdForm.value = { old_password: '', new_password: '', confirm: '' }
      toast('success', '修改成功', res.message || '密码已更新')
    }
  } catch (err) {
    toast('error', '修改失败', err.message || '请稍后重试')
  } finally {
    pwdSaving.value = false
  }
}

// ===== 我的收藏 =====
const favorites = ref([])
const favoritesTotal = ref(0)
const favoritesPage = ref(1)
const favoritesLoading = ref(false)

const loadFavorites = async (page = 1) => {
  favoritesLoading.value = true
  try {
    const res = await favoriteApi.getList({ page, page_size: FAVORITE_PAGE_SIZE })
    if (res.code === 0) {
      favorites.value = res.data.list || []
      favoritesTotal.value = res.data.total || 0
      favoritesPage.value = res.data.page || page
    } else {
      toast('error', '加载收藏失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '加载收藏失败', err.message || '请稍后重试')
  } finally {
    favoritesLoading.value = false
  }
}

const changeFavoritePage = (page) => {
  favoritesPage.value = page
  loadFavorites(page)
}

const removeFavorite = async (postId) => {
  try {
    const res = await favoriteApi.remove(postId)
    if (res.code === 0) {
      toast('success', '已取消收藏', '该帖子已从收藏中移除')
      const remain = favorites.value.length - 1
      const target = remain === 0 && favoritesPage.value > 1
        ? favoritesPage.value - 1
        : favoritesPage.value
      await loadFavorites(target)
    } else {
      toast('error', '取消失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '取消失败', err.message || '请稍后重试')
  }
}

const goPost = (postId) => router.push(`/posts/${postId}`)

// ===== 登录记录 =====
const loginLogs = ref([])
const logsTotal = ref(0)
const logsPage = ref(1)
const logsLoading = ref(false)

const loadLoginLogs = async (page = 1) => {
  logsLoading.value = true
  try {
    const res = await userApi.getLoginLogs({ page, page_size: LOG_PAGE_SIZE })
    if (res.code === 0) {
      loginLogs.value = res.data.list || []
      logsTotal.value = res.data.total || 0
      logsPage.value = res.data.page || page
    } else {
      toast('error', '加载登录记录失败', res.message || '请稍后重试')
    }
  } catch (err) {
    toast('error', '加载登录记录失败', err.message || '请稍后重试')
  } finally {
    logsLoading.value = false
  }
}

const changeLogPage = (page) => {
  logsPage.value = page
  loadLoginLogs(page)
}

// ===== 注销账号 =====
const dangerOpen = ref(false)
const cancelPassword = ref('')
const cancelSaving = ref(false)

const submitCancel = async () => {
  if (!cancelPassword.value) {
    toast('warning', '无法注销', '请输入当前密码')
    return
  }
  const confirmed = await window.$ghibli?.showConfirm({
    title: '注销账号',
    message: '账号注销后所有数据将永久删除且无法恢复，确定继续吗？',
    yesText: '确认注销',
  })
  if (!confirmed) return

  cancelSaving.value = true
  try {
    const res = await userApi.deleteAccount({ password: cancelPassword.value })
    if (res.code === 0) {
      toast('success', '账号已注销', '期待下次再见')
      authStore.logout()
      router.push('/')
    }
  } catch (err) {
    toast('error', '注销失败', err.message || '请稍后重试')
  } finally {
    cancelSaving.value = false
  }
}

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}

onMounted(async () => {
  await authStore.fetchProfile()
  syncProfileForm()
  phoneInput.value = userInfo.value?.phone || ''
  loadFavorites(1)
  loadLoginLogs(1)
  loadUnread()
})

onUnmounted(stopCountdown)
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero profile-hero">
      <div class="hero-main">
        <img
          v-if="userInfo?.avatar"
          :src="userInfo.avatar"
          :alt="userInfo.nickname"
          class="hero-avatar"
        />
        <div v-else class="avatar-circle hero-avatar-fallback">{{ avatarText }}</div>

        <div class="hero-text">
          <h1 class="page-title">{{ userInfo?.nickname || '未设置昵称' }}</h1>
          <p class="page-sub">
            <span v-if="userInfo?.username">@{{ userInfo.username }}</span>
            <span v-if="userInfo?.create_time"> · 注册于 {{ formatDate(userInfo.create_time) }}</span>
          </p>
          <div class="tag-row hero-tags">
            <span class="status-tag">{{ userInfo?.role === 1 ? '管理员' : '普通用户' }}</span>
            <span v-for="label in identityLabels" :key="label" class="status-tag status-tag--identity">
              {{ label }}
            </span>
            <span v-if="isBanned" class="status-tag status-tag--ban">账号已封禁</span>
          </div>
        </div>
      </div>

      <div v-if="isBanned" class="ban-banner">
        <div>
          <strong>账号已被封禁</strong>
          <p class="muted">理由：{{ userInfo?.ban_reason || '未填写' }}<span v-if="userInfo?.ban_time"> · {{ formatDate(userInfo.ban_time) }}</span></p>
        </div>
        <lay-button type="danger" size="sm" @click="router.push('/appeal')">去申诉</lay-button>
      </div>
    </section>

    <div class="page-toolbar">
      <lay-button @click="router.push('/content/posts')">内容管理</lay-button>
      <lay-button @click="router.push('/content/drafts')">草稿箱</lay-button>
      <lay-button @click="router.push('/friends')">好友</lay-button>
      <lay-button @click="router.push('/profile/identity')">身份申请</lay-button>
      <lay-button @click="router.push('/notifications')">
        消息通知
        <span v-if="unreadCount > 0" class="toolbar-badge">{{ unreadCount }}</span>
      </lay-button>
      <lay-button v-if="authStore.isAdmin" @click="router.push('/admin')">管理后台</lay-button>
      <lay-button v-if="isBanned" type="danger" @click="router.push('/appeal')">账号申诉</lay-button>
      <span class="page-toolbar__spacer"></span>
      <lay-button @click="handleLogout">退出登录</lay-button>
    </div>

    <div class="stat-grid profile-stats">
      <button type="button" class="stat-card" @click="router.push('/profile/following')">
        <div class="stat-card__value">{{ userInfo?.following_count ?? 0 }}</div>
        <div class="stat-card__label">关注</div>
      </button>
      <button type="button" class="stat-card" @click="router.push('/profile/followers')">
        <div class="stat-card__value">{{ userInfo?.followers_count ?? 0 }}</div>
        <div class="stat-card__label">粉丝</div>
      </button>
      <button type="button" class="stat-card" @click="router.push('/profile/likes')">
        <div class="stat-card__value">{{ userInfo?.likes_count ?? 0 }}</div>
        <div class="stat-card__label">获赞</div>
      </button>
    </div>

    <div class="card-stack">
      <lay-card title="基本资料">
        <div class="form-row">
          <label class="form-label">用户 ID</label>
          <div class="form-control">
            <span class="muted">{{ userInfo?.id }}</span>
          </div>
        </div>

        <div class="form-row">
          <label class="form-label">昵称</label>
          <div class="form-control">
            <lay-input v-model="profileForm.nickname" :maxlength="50" placeholder="请输入昵称" />
          </div>
          <lay-button type="primary" :loading="nicknameSaving" :disabled="nicknameSaving" @click="saveNickname">
            保存
          </lay-button>
        </div>

        <div class="form-row form-row--wrap">
          <label class="form-label">邮箱</label>
          <div class="form-control">
            <lay-input v-model="profileForm.email" placeholder="请输入邮箱" />
          </div>
          <lay-button
            :disabled="countdown > 0 || codeSending"
            :loading="codeSending"
            @click="handleSendEmailCode"
          >
            {{ countdown > 0 ? `${countdown}s 后重发` : '发送验证码' }}
          </lay-button>
        </div>

        <div v-if="emailChanged" class="form-row">
          <label class="form-label">验证码</label>
          <div class="form-control">
            <lay-input v-model="profileForm.code" :maxlength="6" placeholder="新邮箱收到的 6 位验证码" />
          </div>
        </div>
        <div class="form-actions email-actions">
          <lay-button type="primary" :loading="emailSaving" :disabled="emailSaving" @click="saveEmail">
            保存邮箱
          </lay-button>
          <span v-if="emailChanged" class="muted email-hint">
            更换邮箱需要新邮箱的验证码，验证通过后才会生效。
          </span>
        </div>

        <div class="form-row">
          <label class="form-label">手机号</label>
          <div class="form-control">
            <lay-input v-model="phoneInput" :maxlength="11" placeholder="11 位手机号，留空表示解绑" />
          </div>
          <lay-button type="primary" :loading="phoneSaving" :disabled="phoneSaving" @click="savePhone">
            保存
          </lay-button>
        </div>
        <p class="muted form-tip">手机号选填，留空保存即解绑。</p>
      </lay-card>

      <lay-card title="修改密码">
        <div class="form-row">
          <label class="form-label">原密码</label>
          <div class="form-control">
            <lay-input v-model="pwdForm.old_password" type="password" placeholder="请输入当前密码" />
          </div>
        </div>
        <div class="form-row">
          <label class="form-label">新密码</label>
          <div class="form-control">
            <lay-input v-model="pwdForm.new_password" type="password" placeholder="6-20 位新密码" />
          </div>
        </div>
        <div class="form-row">
          <label class="form-label">确认新密码</label>
          <div class="form-control">
            <lay-input v-model="pwdForm.confirm" type="password" placeholder="再次输入新密码" />
          </div>
        </div>
        <div class="form-actions">
          <lay-button type="primary" :loading="pwdSaving" :disabled="pwdSaving" @click="submitPassword">
            确认修改
          </lay-button>
        </div>
      </lay-card>

      <lay-card title="我的收藏">
        <div v-if="favoritesLoading" class="muted">加载中…</div>
        <lay-empty v-else-if="favorites.length === 0" description="还没有收藏任何帖子" />
        <div v-else>
          <div v-for="item in favorites" :key="item.favorite_id" class="list-row">
            <div class="avatar-circle">{{ (item.author_nickname || '?').slice(0, 1) }}</div>
            <div class="list-row__main">
              <p class="list-row__title">{{ item.title }}</p>
              <div class="meta">
                <span>{{ item.author_nickname || '匿名' }}</span>
                <span>收藏于 {{ item.favorite_time }}</span>
              </div>
            </div>
            <div class="form-actions">
              <lay-button size="sm" @click="goPost(item.post_id)">查看</lay-button>
              <lay-button size="sm" @click="removeFavorite(item.post_id)">取消收藏</lay-button>
            </div>
          </div>
          <div v-if="favoritesTotal > FAVORITE_PAGE_SIZE" class="pagination-wrap">
            <lay-page
              v-model="favoritesPage"
              :total="favoritesTotal"
              :limit="FAVORITE_PAGE_SIZE"
              :layout="['prev', 'page', 'next', 'count']"
              @change="changeFavoritePage"
            />
          </div>
        </div>
      </lay-card>

      <lay-card title="登录记录">
        <div v-if="logsLoading" class="muted">加载中…</div>
        <lay-empty v-else-if="loginLogs.length === 0" description="暂无登录记录" />
        <div v-else>
          <div v-for="item in loginLogs" :key="item.id" class="list-row">
            <div class="list-row__main">
              <p class="list-row__title">{{ item.create_time }}</p>
              <div class="meta">
                <span>{{ item.device || '未知设备' }}</span>
                <span>IP：{{ item.ip || '未知' }}</span>
              </div>
            </div>
          </div>
          <div v-if="logsTotal > LOG_PAGE_SIZE" class="pagination-wrap">
            <lay-page
              v-model="logsPage"
              :total="logsTotal"
              :limit="LOG_PAGE_SIZE"
              :layout="['prev', 'page', 'next', 'count']"
              @change="changeLogPage"
            />
          </div>
        </div>
      </lay-card>

      <lay-card>
        <div class="danger-head">
          <div>
            <strong class="danger-text">注销账号</strong>
            <p class="muted">注销后账号及全部数据将被永久删除，无法恢复。</p>
          </div>
          <lay-button size="sm" @click="dangerOpen = !dangerOpen">
            {{ dangerOpen ? '收起' : '展开' }}
          </lay-button>
        </div>
        <div v-if="dangerOpen" class="danger-body">
          <div class="form-row">
            <label class="form-label">当前密码</label>
            <div class="form-control">
              <lay-input v-model="cancelPassword" type="password" placeholder="请输入当前密码确认注销" />
            </div>
            <lay-button type="danger" :loading="cancelSaving" :disabled="cancelSaving" @click="submitCancel">
              确认注销账号
            </lay-button>
          </div>
        </div>
      </lay-card>
    </div>
  </div>
</template>

<style scoped>
.profile-hero {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.hero-main {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.hero-avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid var(--color-bg-elevated);
  box-shadow: var(--shadow-md);
  flex-shrink: 0;
}

.hero-avatar-fallback {
  width: 88px;
  height: 88px;
  font-size: var(--text-3xl);
  box-shadow: var(--shadow-md);
}

.hero-text {
  min-width: 0;
}

.hero-tags {
  margin-top: var(--space-2);
}

.status-tag--identity {
  background: var(--ghibli-warm-100);
  color: var(--ghibli-warm-800);
  border-color: var(--ghibli-sun-200);
}

.toolbar-badge {
  min-width: 18px;
  height: 18px;
  margin-left: var(--space-1);
  padding: 0 5px;
  border-radius: var(--radius-full);
  background: var(--ghibli-sakura-500);
  color: #fff;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.ban-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-error);
  background: var(--color-error-bg);
  border-radius: var(--radius-lg);
}

.ban-banner p {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
}

.profile-stats {
  margin: var(--space-6) 0;
}

.form-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.form-row--wrap {
  flex-wrap: wrap;
}

.email-actions {
  align-items: center;
  margin-bottom: var(--space-4);
}

.email-hint {
  font-size: var(--text-xs);
}

.form-label {
  width: 96px;
  flex-shrink: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.form-control {
  flex: 1;
  min-width: 0;
}

.form-tip {
  margin: calc(-1 * var(--space-2)) 0 var(--space-4) 108px;
  font-size: var(--text-xs);
}

.card-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.danger-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.danger-head p {
  margin: var(--space-1) 0 0;
  font-size: var(--text-xs);
}

.danger-body {
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px dashed var(--color-divider);
}

@media (max-width: 640px) {
  .hero-main {
    flex-direction: column;
    align-items: flex-start;
  }

  .form-row {
    flex-wrap: wrap;
  }

  .form-label {
    width: 100%;
  }

  .form-tip {
    margin-left: 0;
  }
}
</style>
