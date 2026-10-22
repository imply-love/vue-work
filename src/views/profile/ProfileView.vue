<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const editing = ref(false)
const editForm = ref({
  nickname: '',
  email: '',
})
const saving = ref(false)
const saveError = ref('')
const saveSuccess = ref('')

const userInfo = computed(() => authStore.user)

const startEdit = () => {
  if (userInfo.value) {
    editForm.value.nickname = userInfo.value.nickname || ''
    editForm.value.email = userInfo.value.email || ''
    editing.value = true
  }
}

const cancelEdit = () => {
  editing.value = false
  saveError.value = ''
  saveSuccess.value = ''
}

const handleSave = async () => {
  saveError.value = ''
  saveSuccess.value = ''
  saving.value = true

  const result = await authStore.updateProfile({
    nickname: editForm.value.nickname,
    email: editForm.value.email,
  })

  saving.value = false

  if (result.success) {
    // 资料已落库，authStore 里同步了后端返回的最新值
    editing.value = false
    saveSuccess.value = '保存成功'
  } else {
    saveError.value = result.message || '保存失败，请重试'
  }
}

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}

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
              </template>
              <span v-else class="info-value">{{ userInfo?.email || '未设置' }}</span>
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

/* Badges */
.status-disabled {
  background: var(--ghibli-paper-200);
  color: var(--ghibli-paper-700);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-8);
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
  .save-message {
    animation: none;
    transition: none;
  }
}
</style>