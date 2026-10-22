<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { favoriteApi, userApi } from '@/api'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

// 与后端 utils/verify_code.py 的 CODE_RESEND_INTERVAL 保持一致
const RESEND_SECONDS = 60

const router = useRouter()
const authStore = useAuthStore()

const editing = ref(false)
const editForm = ref({
  nickname: '',
  email: '',
  code: '',
})
const saving = ref(false)
const saveError = ref('')
const saveSuccess = ref('')

// 换绑邮箱的验证码：只有邮箱真的改了才需要
const codeSending = ref(false)
const countdown = ref(0)
const codeMessage = ref('')
let countdownTimer = null

// 手机号绑定（非强制）：与基础资料的编辑互不干扰，走独立的小编辑态
const editingPhone = ref(false)
const phoneInput = ref('')
const phoneSaving = ref(false)
const phoneError = ref('')
const phoneSuccess = ref('')

// ===== 我的收藏 =====
const favoritesOpen = ref(false)
const favoritesLoading = ref(false)
const favoritesError = ref('')
const favoritesList = ref([])
const favoritesTotal = ref(0)
const favoritesPage = ref(1)
const favoritesPageSize = 6

// ===== 账号安全：密码修改 =====
const pwdOpen = ref(false)
const pwdForm = ref({ old_password: '', new_password: '', confirm: '' })
const pwdSaving = ref(false)
const pwdError = ref('')
const pwdSuccess = ref('')

// ===== 账号安全：登录记录 =====
const logsOpen = ref(false)
const logsLoading = ref(false)
const logsError = ref('')
const logsList = ref([])
const logsTotal = ref(0)
const logsPage = ref(1)
const logsPageSize = 10

// ===== 账号安全：账号注销 =====
const cancelOpen = ref(false)
const cancelStep = ref(1) // 1-风险提示 2-输入密码确认
const cancelForm = ref({ password: '' })
const cancelSaving = ref(false)
const cancelError = ref('')

// ===== 站点风格确认弹窗（替代原生 confirm） =====
const unbindPhoneConfirm = ref(false)
const unfavConfirm = ref(false)
let unfavTargetId = null

const userInfo = computed(() => authStore.user)

// 邮箱从「已验证」变成任意未验证邮箱会绕过强制验证，所以改动时必须带验证码
const emailChanged = computed(() => {
  return editing.value && editForm.value.email.trim() !== (userInfo.value?.email || '')
})

const startEdit = () => {
  if (userInfo.value) {
    editForm.value.nickname = userInfo.value.nickname || ''
    editForm.value.email = userInfo.value.email || ''
    editForm.value.code = ''
    codeMessage.value = ''
    editing.value = true
  }
}

const cancelEdit = () => {
  editing.value = false
  saveError.value = ''
  saveSuccess.value = ''
  stopCountdown()
}

const startCountdown = () => {
  stopCountdown()
  countdown.value = RESEND_SECONDS
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      stopCountdown()
    }
  }, 1000)
}

const stopCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  countdown.value = 0
}

const handleSendEmailCode = async () => {
  codeMessage.value = ''
  const email = editForm.value.email.trim()

  codeSending.value = true
  try {
    const response = await userApi.sendBindEmailCode({ email })
    codeMessage.value = response.message || '验证码已发送'
    if (response.code === 0) {
      startCountdown()
    }
  } catch (err) {
    codeMessage.value = err.message || '验证码发送失败，请重试'
  } finally {
    codeSending.value = false
  }
}

const handleSave = async () => {
  saveError.value = ''
  saveSuccess.value = ''
  saving.value = true

  const payload = {
    nickname: editForm.value.nickname,
    email: editForm.value.email,
  }
  // 邮箱没变就不传验证码，后端也不要求
  if (emailChanged.value) {
    payload.code = editForm.value.code.trim()
  }

  const result = await authStore.updateProfile(payload)

  saving.value = false

  if (result.success) {
    // 资料已落库，authStore 里同步了后端返回的最新值
    editing.value = false
    saveSuccess.value = '保存成功'
    stopCountdown()
    codeMessage.value = ''
  } else {
    saveError.value = result.message || '保存失败，请重试'
  }
}

const startEditPhone = () => {
  phoneInput.value = userInfo.value?.phone || ''
  phoneError.value = ''
  phoneSuccess.value = ''
  editingPhone.value = true
}

const cancelEditPhone = () => {
  editingPhone.value = false
  phoneError.value = ''
  phoneSuccess.value = ''
}

const savePhone = async (phone) => {
  phoneSaving.value = true
  phoneError.value = ''
  phoneSuccess.value = ''

  const result = await authStore.updatePhone({ phone })

  phoneSaving.value = false

  if (result.success) {
    editingPhone.value = false
    phoneSuccess.value = result.message || '保存成功'
  } else {
    phoneError.value = result.message || '保存失败，请重试'
  }
}

const handleSavePhone = () => {
  savePhone(phoneInput.value.trim())
}

const handleUnbindPhone = () => {
  unbindPhoneConfirm.value = true
}

const confirmUnbindPhone = () => {
  savePhone('')
}

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}

// ===== 收藏相关逻辑 =====
const loadFavorites = async (page = 1) => {
  favoritesLoading.value = true
  favoritesError.value = ''
  try {
    const response = await favoriteApi.getList({ page, page_size: favoritesPageSize })
    if (response.code === 0) {
      favoritesList.value = response.data.list
      favoritesTotal.value = response.data.total
      favoritesPage.value = response.data.page
    } else {
      favoritesError.value = response.message || '加载失败'
    }
  } catch (err) {
    favoritesError.value = err.message || '加载失败，请稍后重试'
  } finally {
    favoritesLoading.value = false
  }
}

const openFavorites = () => {
  closeOtherPanels('favorites')
  favoritesOpen.value = !favoritesOpen.value
  if (favoritesOpen.value) {
    favoritesPage.value = 1
    loadFavorites(1)
  }
}

const gotoPost = (id) => {
  router.push(`/posts/${id}`)
}

const removeFavorite = (id) => {
  unfavTargetId = id
  unfavConfirm.value = true
}

const confirmRemoveFavorite = async () => {
  const id = unfavTargetId
  unfavTargetId = null
  if (!id) return
  try {
    const response = await favoriteApi.remove(id)
    if (response.code === 0) {
      // 若当前页被删空且不是第一页，回退一页
      const remaining = favoritesList.value.length - 1
      const target = remaining === 0 && favoritesPage.value > 1
        ? favoritesPage.value - 1
        : favoritesPage.value
      await loadFavorites(target)
    }
  } catch (err) {
    favoritesError.value = err.message || '操作失败，请稍后重试'
  }
}

// ===== 密码修改 =====
const openPasswordPanel = () => {
  closeOtherPanels('password')
  pwdOpen.value = !pwdOpen.value
  if (pwdOpen.value) {
    pwdForm.value = { old_password: '', new_password: '', confirm: '' }
    pwdError.value = ''
    pwdSuccess.value = ''
  }
}

const submitPassword = async () => {
  pwdError.value = ''
  pwdSuccess.value = ''
  const { old_password, new_password, confirm } = pwdForm.value
  if (!old_password || !new_password) {
    pwdError.value = '请填写原密码和新密码'
    return
  }
  if (new_password.length < 6 || new_password.length > 20) {
    pwdError.value = '新密码长度需为 6-20 位'
    return
  }
  if (new_password !== confirm) {
    pwdError.value = '两次输入的新密码不一致'
    return
  }

  pwdSaving.value = true
  try {
    const response = await userApi.changePassword({ old_password, new_password })
    if (response.code === 0) {
      pwdSuccess.value = response.message || '密码修改成功'
      pwdForm.value = { old_password: '', new_password: '', confirm: '' }
    } else {
      pwdError.value = response.message || '修改失败，请重试'
    }
  } catch (err) {
    pwdError.value = err.message || '修改失败，请重试'
  } finally {
    pwdSaving.value = false
  }
}

const goRelogin = () => {
  authStore.logout()
  router.push('/login')
}

// ===== 登录记录 =====
const loadLoginLogs = async (page = 1) => {
  logsLoading.value = true
  logsError.value = ''
  try {
    const response = await userApi.getLoginLogs({ page, page_size: logsPageSize })
    if (response.code === 0) {
      logsList.value = response.data.list
      logsTotal.value = response.data.total
      logsPage.value = response.data.page
    } else {
      logsError.value = response.message || '加载失败'
    }
  } catch (err) {
    logsError.value = err.message || '加载失败，请稍后重试'
  } finally {
    logsLoading.value = false
  }
}

const openLoginLogs = () => {
  closeOtherPanels('logs')
  logsOpen.value = !logsOpen.value
  if (logsOpen.value) {
    logsPage.value = 1
    loadLoginLogs(1)
  }
}

// ===== 账号注销 =====
const openCancelPanel = () => {
  closeOtherPanels('cancel')
  cancelOpen.value = !cancelOpen.value
  if (cancelOpen.value) {
    cancelStep.value = 1
    cancelForm.value = { password: '' }
    cancelError.value = ''
  }
}

const submitCancel = async () => {
  cancelError.value = ''
  if (!cancelForm.value.password) {
    cancelError.value = '请输入当前密码以确认注销'
    return
  }
  cancelSaving.value = true
  try {
    const response = await userApi.deleteAccount({ password: cancelForm.value.password })
    if (response.code === 0) {
      // 账号已删除，清除本地登录态并返回首页
      authStore.logout()
      router.push('/')
    } else {
      cancelError.value = response.message || '注销失败，请重试'
    }
  } catch (err) {
    cancelError.value = err.message || '注销失败，请重试'
  } finally {
    cancelSaving.value = false
  }
}

// 面板互斥：同一时间只展开一个
const closeOtherPanels = (keep) => {
  if (keep !== 'favorites') favoritesOpen.value = false
  if (keep !== 'password') pwdOpen.value = false
  if (keep !== 'logs') logsOpen.value = false
  if (keep !== 'cancel') cancelOpen.value = false
}

onUnmounted(() => {
  stopCountdown()
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const getRoleText = (role) => {
  return role === 1 ? '管理员' : '普通用户'
}

const getStatusText = (status) => {
  return status === 1 ? '正常' : '禁用'
}

onMounted(() => {
  if (authStore.isLoggedIn) {
    authStore.fetchProfile()
    // 预载收藏列表与收藏数，让「我的收藏」卡片直接显示数量
    loadFavorites(1)
  }
})
</script>

<template>
  <div class="profile-page">
    <div class="profile-container">
      <!-- 页面头部 -->
      <header class="profile-header">
        <div class="profile-header__bg" aria-hidden="true"></div>
        <div class="profile-header__content">
          <div class="profile-avatar-wrapper">
            <img
              v-if="userInfo?.avatar"
              :src="userInfo.avatar"
              :alt="userInfo.nickname"
              class="profile-avatar"
            />
            <div v-else class="profile-avatar placeholder" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <button
              v-if="editing"
              class="avatar-edit-btn"
              @click.stop="() => {}"
              aria-label="更换头像"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
          </div>
          <div class="profile-name-section">
            <template v-if="editing">
              <input
                v-model="editForm.nickname"
                type="text"
                class="profile-name-input"
                placeholder="请输入昵称"
                maxlength="50"
                @keydown.enter="handleSave"
              />
            </template>
            <h1 v-else class="profile-name">{{ userInfo?.nickname || '未设置昵称' }}</h1>
            <p v-if="!editing && userInfo?.username" class="profile-username">@{{ userInfo.username }}</p>
          </div>
        </div>
      </header>

      <!-- 信息卡片 -->
      <div class="profile-info">
        <!-- 基础信息 -->
        <section class="info-section">
          <h2 class="section-title">基础信息</h2>

          <div class="info-grid">
            <div class="info-item">
              <label class="info-label">用户ID</label>
              <span class="info-value monospace">{{ userInfo?.id }}</span>
            </div>

            <div class="info-item">
              <label class="info-label">邮箱</label>
              <template v-if="editing">
                <input
                  v-model="editForm.email"
                  type="email"
                  class="info-input"
                  placeholder="请输入邮箱"
                  @keydown.enter="handleSave"
                />
                <!-- 换绑邮箱必须通过新邮箱的验证码，未改动时不显示，避免干扰 -->
                <div v-if="emailChanged" class="code-row">
                  <input
                    v-model="editForm.code"
                    type="text"
                    class="info-input code-input"
                    placeholder="6 位验证码"
                    maxlength="6"
                    inputmode="numeric"
                    @keydown.enter="handleSave"
                  />
                  <button
                    type="button"
                    class="code-btn"
                    :disabled="countdown > 0 || codeSending"
                    @click="handleSendEmailCode"
                  >
                    <span v-if="countdown > 0">{{ countdown }}s</span>
                    <span v-else-if="codeSending">发送中</span>
                    <span v-else>获取验证码</span>
                  </button>
                </div>
                <p v-if="emailChanged" class="info-hint">
                  {{ codeMessage || '更换邮箱需要新邮箱的验证码，验证通过后才会生效' }}
                </p>
              </template>
              <span v-else class="info-value">{{ userInfo?.email || '未设置' }}</span>
            </div>

            <div class="info-item">
              <label class="info-label">手机号</label>
              <div v-if="editingPhone" class="code-row">
                <input
                  v-model="phoneInput"
                  type="tel"
                  class="info-input"
                  placeholder="11 位手机号"
                  maxlength="11"
                  inputmode="numeric"
                  @keydown.enter="handleSavePhone"
                />
                <button
                  type="button"
                  class="ghibli-btn ghibli-btn--primary ghibli-btn--sm"
                  :disabled="phoneSaving"
                  @click="handleSavePhone"
                >
                  <span v-if="phoneSaving" class="ghibli-btn__loading">
                    <span class="ghibli-spinner" aria-hidden="true"></span>
                    保存
                  </span>
                  <span v-else>保存</span>
                </button>
                <button
                  type="button"
                  class="ghibli-btn ghibli-btn--outline ghibli-btn--sm"
                  :disabled="phoneSaving"
                  @click="cancelEditPhone"
                >
                  取消
                </button>
              </div>
              <div v-else class="info-value phone-value">
                <span>{{ userInfo?.phone || '未绑定' }}</span>
                <span
                  :class="['ghibli-badge', userInfo?.phone ? 'ghibli-badge--secondary' : 'ghibli-badge--outline']"
                >
                  {{ userInfo?.phone ? '已绑定' : '未绑定' }}
                </span>
                <button type="button" class="link-btn" @click="startEditPhone">
                  {{ userInfo?.phone ? '更换' : '绑定手机号' }}
                </button>
                <button
                  v-if="userInfo?.phone"
                  type="button"
                  class="link-btn link-btn--danger"
                  @click="handleUnbindPhone"
                >
                  解绑
                </button>
              </div>
              <p class="info-hint">选填项，绑定后便于找回账号，不影响正常使用</p>
              <p v-if="phoneError" class="info-hint info-hint--error" role="alert">{{ phoneError }}</p>
              <p v-else-if="phoneSuccess" class="info-hint info-hint--success" role="status">{{ phoneSuccess }}</p>
            </div>

            <div class="info-item">
              <label class="info-label">身份</label>
              <span class="info-value">
                <span :class="['ghibli-badge', userInfo?.role === 1 ? 'ghibli-badge--sakura' : 'ghibli-badge--primary']">
                  {{ getRoleText(userInfo?.role) }}
                </span>
              </span>
            </div>

            <div class="info-item">
              <label class="info-label">状态</label>
              <span class="info-value">
                <span :class="['ghibli-badge', userInfo?.status === 1 ? 'ghibli-badge--secondary' : 'status-disabled']">
                  {{ getStatusText(userInfo?.status) }}
                </span>
              </span>
            </div>

            <div class="info-item full-width">
              <label class="info-label">注册时间</label>
              <span class="info-value">{{ formatDate(userInfo?.create_time) }}</span>
            </div>
          </div>
        </section>

        <!-- 统计数据 -->
        <section class="info-section">
          <h2 class="section-title">同好数据</h2>

          <div class="stats-grid">
            <div class="stat-card">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <div class="stat-content">
                <span class="stat-value">{{ userInfo?.followers_count || 0 }}</span>
                <span class="stat-label">粉丝</span>
              </div>
            </div>

            <div class="stat-card">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              <div class="stat-content">
                <span class="stat-value">{{ userInfo?.likes_count || 0 }}</span>
                <span class="stat-label">获赞</span>
              </div>
            </div>

            <div class="stat-card">
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <div class="stat-content">
                <span class="stat-value">{{ userInfo?.following_count || 0 }}</span>
                <span class="stat-label">关注</span>
              </div>
            </div>

            <!-- 我的收藏：可点击展开收藏列表 -->
            <button
              type="button"
              class="stat-card stat-card--clickable"
              :class="{ 'stat-card--active': favoritesOpen }"
              @click="openFavorites"
              :aria-expanded="favoritesOpen"
            >
              <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
              </svg>
              <div class="stat-content">
                <span class="stat-value">{{ favoritesTotal }}</span>
                <span class="stat-label">我的收藏</span>
              </div>
            </button>
          </div>

          <!-- 我的收藏列表面板 -->
          <div v-if="favoritesOpen" class="profile-panel">
            <div class="panel-header">
              <span class="panel-title">我的收藏（{{ favoritesTotal }}）</span>
              <button type="button" class="panel-close" @click="openFavorites" aria-label="收起收藏列表">收起</button>
            </div>

            <p v-if="favoritesLoading" class="panel-tip">加载中…</p>
            <p v-else-if="favoritesError" class="panel-tip panel-tip--error" role="alert">{{ favoritesError }}</p>
            <p v-else-if="favoritesList.length === 0" class="panel-tip">还没有收藏任何帖子，去讨论区逛逛，看到喜欢的帖子点「收藏」吧。</p>

            <ul v-else class="fav-list">
              <li v-for="item in favoritesList" :key="item.favorite_id" class="fav-item">
                <button type="button" class="fav-main" @click="gotoPost(item.post_id)">
                  <span v-if="item.cover" class="fav-cover-wrap">
                    <img :src="item.cover" :alt="item.title" class="fav-cover" loading="lazy" />
                  </span>
                  <span class="fav-info">
                    <span class="fav-title">{{ item.title }}</span>
                    <span class="fav-desc">
                      <span v-if="item.category" class="ghibli-badge ghibli-badge--outline">{{ item.category }}</span>
                      {{ item.excerpt || '（无摘要）' }}
                    </span>
                    <span class="fav-meta">收藏于 {{ item.favorite_time }}</span>
                  </span>
                </button>
                <span class="fav-actions">
                  <button type="button" class="link-btn" @click="gotoPost(item.post_id)">查看</button>
                  <button type="button" class="link-btn link-btn--danger" @click="removeFavorite(item.post_id)">取消收藏</button>
                </span>
              </li>
            </ul>

            <div v-if="favoritesTotal > favoritesPageSize" class="pager">
              <button
                type="button"
                class="ghibli-btn ghibli-btn--outline ghibli-btn--sm"
                :disabled="favoritesPage <= 1"
                @click="loadFavorites(favoritesPage - 1)"
              >
                上一页
              </button>
              <span class="pager-info">{{ favoritesPage }} / {{ Math.ceil(favoritesTotal / favoritesPageSize) }}</span>
              <button
                type="button"
                class="ghibli-btn ghibli-btn--outline ghibli-btn--sm"
                :disabled="favoritesPage * favoritesPageSize >= favoritesTotal"
                @click="loadFavorites(favoritesPage + 1)"
              >
                下一页
              </button>
            </div>
          </div>
        </section>

        <!-- 账号安全 -->
        <section class="info-section">
          <h2 class="section-title">账号安全</h2>

          <div class="security-entries">
            <button
              type="button"
              class="security-entry"
              :class="{ 'security-entry--active': pwdOpen }"
              @click="openPasswordPanel"
            >
              <svg class="security-entry__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <span class="security-entry__main">
                <span class="security-entry__title">密码修改</span>
                <span class="security-entry__desc">定期修改密码，保护账号安全</span>
              </span>
              <span class="security-entry__arrow" aria-hidden="true">›</span>
            </button>

            <button
              type="button"
              class="security-entry"
              :class="{ 'security-entry--active': logsOpen }"
              @click="openLoginLogs"
            >
              <svg class="security-entry__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span class="security-entry__main">
                <span class="security-entry__title">登录记录</span>
                <span class="security-entry__desc">查看最近的登录时间、IP 与设备</span>
              </span>
              <span class="security-entry__arrow" aria-hidden="true">›</span>
            </button>

            <button
              type="button"
              class="security-entry security-entry--danger"
              :class="{ 'security-entry--active': cancelOpen }"
              @click="openCancelPanel"
            >
              <svg class="security-entry__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M3 6h18"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                <line x1="10" y1="11" x2="10" y2="17"/>
                <line x1="14" y1="11" x2="14" y2="17"/>
              </svg>
              <span class="security-entry__main">
                <span class="security-entry__title">账号注销</span>
                <span class="security-entry__desc">永久删除账号及其所有数据</span>
              </span>
              <span class="security-entry__arrow" aria-hidden="true">›</span>
            </button>
          </div>

          <!-- 密码修改面板 -->
          <div v-if="pwdOpen" class="profile-panel">
            <div class="panel-header">
              <span class="panel-title">密码修改</span>
              <button type="button" class="panel-close" @click="openPasswordPanel">收起</button>
            </div>

            <form class="security-form" @submit.prevent="submitPassword">
              <div class="security-field">
                <label class="info-label" for="old-password">原密码</label>
                <input
                  id="old-password"
                  v-model="pwdForm.old_password"
                  type="password"
                  class="info-input"
                  placeholder="请输入当前密码"
                  autocomplete="current-password"
                />
              </div>
              <div class="security-field">
                <label class="info-label" for="new-password">新密码</label>
                <input
                  id="new-password"
                  v-model="pwdForm.new_password"
                  type="password"
                  class="info-input"
                  placeholder="6-20 位新密码"
                  autocomplete="new-password"
                />
              </div>
              <div class="security-field">
                <label class="info-label" for="confirm-password">确认新密码</label>
                <input
                  id="confirm-password"
                  v-model="pwdForm.confirm"
                  type="password"
                  class="info-input"
                  placeholder="再次输入新密码"
                  autocomplete="new-password"
                />
              </div>

              <p v-if="pwdError" class="info-hint info-hint--error" role="alert">{{ pwdError }}</p>
              <p v-if="pwdSuccess" class="info-hint info-hint--success" role="status">{{ pwdSuccess }}</p>

              <div class="security-form__actions">
                <button type="submit" class="ghibli-btn ghibli-btn--primary" :disabled="pwdSaving">
                  <span v-if="pwdSaving" class="ghibli-btn__loading">
                    <span class="ghibli-spinner" aria-hidden="true"></span>
                    提交中...
                  </span>
                  <span v-else>确认修改</span>
                </button>
                <button
                  v-if="pwdSuccess"
                  type="button"
                  class="ghibli-btn ghibli-btn--outline"
                  @click="goRelogin"
                >
                  去重新登录
                </button>
              </div>
            </form>
          </div>

          <!-- 登录记录面板 -->
          <div v-if="logsOpen" class="profile-panel">
            <div class="panel-header">
              <span class="panel-title">登录记录（最近 {{ logsTotal }} 条）</span>
              <button type="button" class="panel-close" @click="openLoginLogs">收起</button>
            </div>

            <p v-if="logsLoading" class="panel-tip">加载中…</p>
            <p v-else-if="logsError" class="panel-tip panel-tip--error" role="alert">{{ logsError }}</p>
            <p v-else-if="logsList.length === 0" class="panel-tip">暂无登录记录。登录后这里会展示最近登录的时间、IP 和设备。</p>

            <ul v-else class="log-list">
              <li v-for="item in logsList" :key="item.id" class="log-item">
                <span class="log-item__time">{{ item.create_time }}</span>
                <span class="log-item__device">{{ item.device || '未知设备' }}</span>
                <span class="log-item__ip">{{ item.ip || '未知 IP' }}</span>
              </li>
            </ul>

            <div v-if="logsTotal > logsPageSize" class="pager">
              <button
                type="button"
                class="ghibli-btn ghibli-btn--outline ghibli-btn--sm"
                :disabled="logsPage <= 1"
                @click="loadLoginLogs(logsPage - 1)"
              >
                上一页
              </button>
              <span class="pager-info">{{ logsPage }} / {{ Math.ceil(logsTotal / logsPageSize) }}</span>
              <button
                type="button"
                class="ghibli-btn ghibli-btn--outline ghibli-btn--sm"
                :disabled="logsPage * logsPageSize >= logsTotal"
                @click="loadLoginLogs(logsPage + 1)"
              >
                下一页
              </button>
            </div>
          </div>

          <!-- 账号注销面板 -->
          <div v-if="cancelOpen" class="profile-panel">
            <div class="panel-header">
              <span class="panel-title">账号注销</span>
              <button type="button" class="panel-close" @click="openCancelPanel">收起</button>
            </div>

            <template v-if="cancelStep === 1">
              <div class="cancel-warning" role="alert">
                <p><strong>注销前请确认：</strong></p>
                <ul>
                  <li>账号注销后<b>无法恢复</b>，登录后所有数据将永久删除；</li>
                  <li>你发布的帖子、求番、分享的资源以及收藏内容都会被一并删除；</li>
                  <li>注销操作不可撤销，请谨慎操作。</li>
                </ul>
              </div>
              <div class="security-form__actions">
                <button type="button" class="ghibli-btn ghibli-btn--danger" @click="cancelStep = 2">
                  我已了解，继续注销
                </button>
                <button type="button" class="ghibli-btn ghibli-btn--outline" @click="openCancelPanel">
                  再想想
                </button>
              </div>
            </template>

            <template v-else>
              <p class="panel-tip">请输入当前密码确认注销，此操作不可撤销。</p>
              <form class="security-form" @submit.prevent="submitCancel">
                <div class="security-field">
                  <label class="info-label" for="cancel-password">当前密码</label>
                  <input
                    id="cancel-password"
                    v-model="cancelForm.password"
                    type="password"
                    class="info-input"
                    placeholder="请输入当前密码"
                    autocomplete="current-password"
                  />
                </div>
                <p v-if="cancelError" class="info-hint info-hint--error" role="alert">{{ cancelError }}</p>
                <div class="security-form__actions">
                  <button type="submit" class="ghibli-btn ghibli-btn--danger" :disabled="cancelSaving">
                    <span v-if="cancelSaving" class="ghibli-btn__loading">
                      <span class="ghibli-spinner" aria-hidden="true"></span>
                      注销中...
                    </span>
                    <span v-else>确认注销账号</span>
                  </button>
                  <button
                    type="button"
                    class="ghibli-btn ghibli-btn--outline"
                    :disabled="cancelSaving"
                    @click="cancelStep = 1"
                  >
                    上一步
                  </button>
                </div>
              </form>
            </template>
          </div>
        </section>

        <!-- 操作按钮 -->
        <section class="info-section">
          <div class="profile-actions">
            <button
              v-if="!editing"
              class="ghibli-btn ghibli-btn--primary"
              @click="startEdit"
            >
              <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              编辑资料
            </button>

            <template v-else>
              <button
                class="ghibli-btn ghibli-btn--primary"
                @click="handleSave"
                :disabled="saving"
              >
                <span v-if="saving" class="ghibli-btn__loading">
                  <span class="ghibli-spinner" aria-hidden="true"></span>
                  保存中...
                </span>
                <span v-else class="ghibli-btn__loading">
                  <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  保存
                </span>
              </button>
              <button
                class="ghibli-btn ghibli-btn--outline"
                @click="cancelEdit"
                :disabled="saving"
              >
                <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
                取消
              </button>
            </template>

            <button
              class="ghibli-btn ghibli-btn--danger profile-logout"
              @click="handleLogout"
            >
              <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              退出登录
            </button>
          </div>

          <div v-if="saveError" class="save-message error" role="alert">
            {{ saveError }}
          </div>
          <div v-if="saveSuccess" class="save-message success" role="status">
            {{ saveSuccess }}
          </div>
        </section>
      </div>

      <!-- 站点风格确认弹窗 -->
      <ConfirmDialog
        v-model="unbindPhoneConfirm"
        title="解绑手机号"
        message="确定要解绑手机号吗？解绑后该手机号可用于绑定其他账号。"
        confirm-text="解绑"
        danger
        @confirm="confirmUnbindPhone"
      />
      <ConfirmDialog
        v-model="unfavConfirm"
        title="取消收藏"
        message="确定取消收藏这篇帖子吗？"
        confirm-text="取消收藏"
        danger
        @confirm="confirmRemoveFavorite"
      />
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100%;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-12) var(--space-6) var(--space-20);
}

/* Header */
.profile-header {
  position: relative;
  border-radius: var(--radius-2xl);
  overflow: hidden;
  margin-bottom: var(--space-12);
  box-shadow: var(--shadow-md);
}

.profile-header__bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--ghibli-sky-100) 0%, var(--ghibli-sakura-100) 50%, var(--ghibli-sun-100) 100%);
  border: 1px solid var(--color-border);
  z-index: 0;
}

.profile-header__bg::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--ghibli-sky-400), var(--ghibli-sakura-400), var(--ghibli-sun-400));
}

.profile-header__content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-end;
  gap: var(--space-12);
  padding: var(--space-16);
  min-height: 200px;
}

.profile-avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.profile-avatar {
  width: 100px;
  height: 100px;
  border-radius: var(--radius-xl);
  object-fit: cover;
  border: 3px solid var(--color-bg-elevated);
  box-shadow: var(--shadow-lg);
}

.profile-avatar.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--ghibli-sky-200) 0%, var(--ghibli-forest-200) 100%);
  color: var(--ghibli-sky-700);
  box-shadow: var(--shadow-lg);
}

.profile-avatar.placeholder svg {
  width: 48px;
  height: 48px;
}

.avatar-edit-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--ghibli-sky-500);
  border: 3px solid var(--color-bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  transition: var(--transition-spring);
}

.avatar-edit-btn:hover {
  background: var(--ghibli-sky-600);
  transform: scale(1.1);
}

.avatar-edit-btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.avatar-edit-btn svg {
  width: 18px;
  height: 18px;
}

.profile-name-section {
  flex: 1;
  min-width: 0;
}

.profile-name {
  font-family: var(--font-display);
  font-size: clamp(1.75rem, 3vw, 2.5rem);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-4);
  letter-spacing: 0.02em;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.6);
}

.profile-name-input {
  width: 100%;
  max-width: 300px;
  padding: var(--space-6) var(--space-8);
  background: var(--color-bg-elevated);
  border: 2px solid var(--ghibli-sky-400);
  border-radius: var(--radius-lg);
  color: var(--color-text);
  font-family: inherit;
  font-size: clamp(1.5rem, 2.5vw, 2rem);
  font-weight: var(--font-bold);
  outline: none;
  box-shadow: var(--focus-ring);
}

.profile-username {
  font-size: var(--text-base);
  color: var(--color-text-light);
  margin: 0;
  font-family: var(--font-mono);
}

/* Info Sections */
.profile-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-12);
}

.info-section {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  padding: var(--space-12);
  box-shadow: var(--shadow-sm);
}

.section-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-10);
  padding-bottom: var(--space-6);
  border-bottom: 1px dashed var(--color-divider);
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-8);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: var(--font-medium);
}

.info-value {
  font-size: var(--text-base);
  color: var(--color-text);
  word-break: break-all;
}

.info-value.monospace {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--color-text-light);
}

.info-input {
  padding: var(--space-5) var(--space-6);
  background: var(--ghibli-paper-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-family: inherit;
  font-size: var(--text-base);
  outline: none;
  transition: var(--transition-gentle);
}

.info-input:focus {
  border-color: var(--ghibli-sky-400);
  box-shadow: var(--focus-ring);
}

/* 邮箱 / 手机号的行内编辑与验证码 */
.code-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.code-row .info-input {
  flex: 1;
  min-width: 0;
}

.code-btn {
  flex-shrink: 0;
  padding: var(--space-4) var(--space-6);
  border-radius: var(--radius-md);
  background: var(--ghibli-sky-100);
  color: var(--ghibli-sky-700);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  white-space: nowrap;
  transition: var(--transition-gentle);
}

.code-btn:hover:not(:disabled) {
  background: var(--ghibli-sky-200);
  color: var(--ghibli-sky-800);
}

.code-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.code-btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.info-hint {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: var(--leading-normal);
}

.info-hint--error {
  color: var(--color-error);
}

.info-hint--success {
  color: var(--ghibli-forest-700);
}

.phone-value {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-4);
}

.link-btn {
  padding: 0;
  color: var(--ghibli-sky-600);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: color var(--duration-fast) var(--ease-gentle);
}

.link-btn:hover {
  color: var(--ghibli-sky-700);
  text-decoration: underline;
}

.link-btn:focus-visible {
  outline: none;
  border-radius: var(--radius-sm);
  box-shadow: var(--focus-ring);
}

.link-btn--danger,
.link-btn--danger:hover {
  color: var(--color-error);
}

/* Badges */
.status-disabled {
  background: var(--ghibli-paper-200);
  color: var(--ghibli-paper-700);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-8);
}

@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-10);
  background: var(--ghibli-paper-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  transition: var(--transition-spring);
}

.stat-card:hover {
  border-color: var(--ghibli-sky-300);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* 我的收藏：可点击的统计卡 */
.stat-card--clickable {
  cursor: pointer;
  font-family: inherit;
  color: inherit;
  background: linear-gradient(180deg, var(--ghibli-paper-50) 0%, var(--ghibli-sakura-50) 100%);
}

.stat-card--clickable:hover {
  border-color: var(--ghibli-sakura-300);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card--clickable:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.stat-card--active {
  border-color: var(--ghibli-sakura-400);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 28px;
  height: 28px;
  color: var(--ghibli-sky-500);
}

.stat-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
}

.stat-value {
  font-family: var(--font-mono);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  line-height: 1;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* Actions */
.profile-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
  align-items: center;
}

.profile-logout {
  margin-left: auto;
}

/* ===== 账号安全入口 ===== */
.security-entries {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.security-entry {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  width: 100%;
  padding: var(--space-6) var(--space-8);
  background: var(--ghibli-paper-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text);
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: var(--transition-gentle);
}

.security-entry:hover {
  border-color: var(--ghibli-sky-300);
  background: var(--color-bg-elevated);
  transform: translateX(2px);
}

.security-entry:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.security-entry--active {
  border-color: var(--ghibli-sky-400);
  box-shadow: var(--shadow-sm);
}

.security-entry--danger:hover {
  border-color: var(--color-error);
  background: var(--color-error-bg);
}

.security-entry--danger.security-entry--active {
  border-color: var(--color-error);
}

.security-entry__icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  color: var(--ghibli-sky-500);
}

.security-entry--danger .security-entry__icon {
  color: var(--color-error);
}

.security-entry__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.security-entry__title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.security-entry__desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.security-entry__arrow {
  font-size: var(--text-xl);
  color: var(--color-text-muted);
  line-height: 1;
}

/* ===== 展开面板（收藏 / 密码 / 登录记录 / 注销） ===== */
.profile-panel {
  margin-top: var(--space-8);
  padding-top: var(--space-8);
  border-top: 1px dashed var(--color-divider);
  animation: fadeIn 0.3s ease;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

.panel-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.panel-close {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  transition: var(--transition-gentle);
}

.panel-close:hover {
  color: var(--color-text);
  background: var(--ghibli-paper-200);
}

.panel-tip {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: var(--leading-normal);
}

.panel-tip--error {
  color: var(--color-error);
}

/* 收藏列表 */
.fav-list,
.log-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.fav-item {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-6);
  background: var(--ghibli-paper-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: var(--transition-gentle);
}

.fav-item:hover {
  border-color: var(--ghibli-sky-300);
}

.fav-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: var(--space-6);
  padding: 0;
  background: none;
  border: none;
  color: inherit;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
}

.fav-main:focus-visible {
  outline: none;
  border-radius: var(--radius-md);
  box-shadow: var(--focus-ring);
}

.fav-cover-wrap {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--ghibli-paper-200);
}

.fav-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.fav-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.fav-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fav-desc {
  font-size: var(--text-xs);
  color: var(--color-text-light);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.fav-meta {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.fav-actions {
  flex-shrink: 0;
  display: flex;
  gap: var(--space-5);
}

/* 登录记录列表 */
.log-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-6) var(--space-8);
  background: var(--ghibli-paper-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
}

.log-item__time {
  font-family: var(--font-mono);
  color: var(--color-text);
  min-width: 150px;
}

.log-item__device {
  color: var(--color-text);
  flex: 1;
  min-width: 120px;
}

.log-item__ip {
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

/* 分页 */
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-6);
  margin-top: var(--space-8);
}

.pager-info {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

/* 密码表单 / 注销表单 */
.security-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.security-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.security-form__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
  margin-top: var(--space-2);
}

/* 注销风险提示 */
.cancel-warning {
  padding: var(--space-6) var(--space-8);
  background: var(--color-error-bg);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  color: var(--color-error);
  margin-bottom: var(--space-6);
}

.cancel-warning p {
  margin: 0 0 var(--space-3);
}

.cancel-warning ul {
  margin: 0;
  padding-left: var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* Save Messages */
.save-message {
  width: 100%;
  padding: var(--space-5) var(--space-8);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  margin-top: var(--space-6);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.save-message.error {
  background: var(--color-error-bg);
  border: 1px solid var(--color-error);
  color: var(--color-error);
}

.save-message.success {
  background: var(--color-success-bg);
  border: 1px solid var(--color-success);
  color: var(--ghibli-forest-700);
}

/* 响应式 */
@media (max-width: 768px) {
  .profile-container {
    padding: var(--space-10) var(--space-4) var(--space-16);
  }

  .profile-header__content {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: var(--space-12) var(--space-8);
    gap: var(--space-8);
  }

  .profile-avatar,
  .profile-avatar.placeholder {
    width: 80px;
    height: 80px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-card {
    flex-direction: row;
    justify-content: flex-start;
    text-align: left;
  }

  .stat-content {
    align-items: flex-start;
  }

  .profile-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .profile-actions .ghibli-btn {
    width: 100%;
  }

  .profile-logout {
    margin-left: 0;
  }
}

@media (max-width: 480px) {
  .info-section {
    padding: var(--space-8);
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .info-item.full-width {
    grid-column: auto;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .stat-card,
  .avatar-edit-btn,
  .code-btn,
  .link-btn,
  .save-message {
    animation: none;
    transition: none;
  }
}
</style>