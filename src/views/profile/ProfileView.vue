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

  // 这里需要后端提供更新用户信息的接口
  // 暂时模拟保存成功
  await new Promise(resolve => setTimeout(resolve, 1000))

  // 实际项目中应该调用 API 更新用户信息
  // const response = await userApi.updateProfile(editForm.value)

  // 暂时更新本地状态
  if (userInfo.value) {
    authStore.user = {
      ...userInfo.value,
      nickname: editForm.value.nickname,
      email: editForm.value.email,
    }
    localStorage.setItem('user', JSON.stringify(authStore.user))
  }

  saving.value = false
  editing.value = false
  saveSuccess.value = '保存成功'
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
                <span :class="['role-badge', userInfo?.role === 1 ? 'role-admin' : 'role-user']">
                  {{ getRoleText(userInfo?.role) }}
                </span>
              </span>
            </div>

            <div class="info-item">
              <label class="info-label">状态</label>
              <span class="info-value">
                <span :class="['status-badge', userInfo?.status === 1 ? 'status-active' : 'status-disabled']">
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
          <h2 class="section-title">江湖数据</h2>

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
              class="btn btn-primary"
              @click="startEdit"
            >
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              编辑资料
            </button>

            <template v-else>
              <button
                class="btn btn-primary"
                @click="handleSave"
                :disabled="saving"
              >
                <span v-if="saving" class="btn-loading">
                  <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
                  </svg>
                  保存中...
                </span>
                <span v-else>
                  <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  保存
                </span>
              </button>
              <button
                class="btn btn-secondary"
                @click="cancelEdit"
                :disabled="saving"
              >
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
                取消
              </button>
            </template>

            <button
              class="btn btn-danger"
              @click="handleLogout"
            >
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
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
  min-height: 100vh;
  background: #0d0d0d;
  padding-top: 72px;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 24px 80px;
}

/* Header */
.profile-header {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 32px;
}

.profile-header__bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
  border: 1px solid #333;
  z-index: 0;
}

.profile-header__bg::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #c9a84c 0%, #e8d57a 50%, #c9a84c 100%);
  opacity: 0.8;
}

.profile-header__content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-end;
  gap: 24px;
  padding: 40px;
  min-height: 200px;
}

.profile-avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.profile-avatar {
  width: 100px;
  height: 100px;
  border-radius: 16px;
  object-fit: cover;
  border: 3px solid #333;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.profile-avatar.placeholder {
  width: 100px;
  height: 100px;
  border-radius: 16px;
  background: linear-gradient(135deg, #333 0%, #222 100%);
  border: 3px solid #333;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
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
  background: #c9a84c;
  border: 3px solid #0d0d0d;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #0d0d0d;
  transition: all 0.2s ease;
}

.avatar-edit-btn:hover {
  background: #e8d57a;
  transform: scale(1.1);
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
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: clamp(1.75rem, 3vw, 2.5rem);
  font-weight: 700;
  color: #e8e8e8;
  margin: 0 0 8px;
  letter-spacing: 0.02em;
}

.profile-name-input {
  width: 100%;
  max-width: 300px;
  padding: 12px 16px;
  background: #0d0d0d;
  border: 2px solid #c9a84c;
  border-radius: 10px;
  color: #e8e8e8;
  font-family: inherit;
  font-size: clamp(1.5rem, 2.5vw, 2rem);
  font-weight: 700;
  outline: none;
}

.profile-username {
  font-size: 1rem;
  color: #999;
  margin: 0;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* Info Sections */
.profile-info {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-section {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
}

.section-title {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: 1.125rem;
  font-weight: 600;
  color: #e8e8e8;
  margin: 0 0 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #333;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.75rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 500;
}

.info-value {
  font-size: 0.9375rem;
  color: #e8e8e8;
  word-break: break-all;
}

.info-value.monospace {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.875rem;
  color: #999;
}

.info-input {
  padding: 10px 12px;
  background: #0d0d0d;
  border: 1px solid #333;
  border-radius: 8px;
  color: #e8e8e8;
  font-family: inherit;
  font-size: 0.9375rem;
  outline: none;
  transition: border-color 0.2s ease;
}

.info-input:focus {
  border-color: #c9a84c;
}

/* Badges */
.role-badge,
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.role-admin {
  background: rgba(220, 53, 69, 0.2);
  color: #dc3545;
  border: 1px solid rgba(220, 53, 69, 0.3);
}

.role-user {
  background: rgba(201, 168, 76, 0.2);
  color: #c9a84c;
  border: 1px solid rgba(201, 168, 76, 0.3);
}

.status-active {
  background: rgba(40, 167, 69, 0.2);
  color: #28a745;
  border: 1px solid rgba(40, 167, 69, 0.3);
}

.status-disabled {
  background: rgba(108, 117, 125, 0.2);
  color: #6c757d;
  border: 1px solid rgba(108, 117, 125, 0.3);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px;
  background: #0d0d0d;
  border: 1px solid #333;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #c9a84c;
  transform: translateY(-2px);
}

.stat-icon {
  width: 28px;
  height: 28px;
  color: #c9a84c;
}

.stat-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-value {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 1.75rem;
  font-weight: 700;
  color: #e8e8e8;
  line-height: 1;
}

.stat-label {
  font-size: 0.8125rem;
  color: #999;
}

/* Actions */
.profile-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 50px;
  font-family: inherit;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn:focus-visible {
  outline: 2px solid #c9a84c;
  outline-offset: 2px;
}

.btn-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.btn-primary {
  background: linear-gradient(135deg, #c9a84c 0%, #a68a3a 100%);
  color: #0d0d0d;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(201, 168, 76, 0.3);
}

.btn-secondary {
  background: transparent;
  color: #e8e8e8;
  border: 1px solid #333;
}

.btn-secondary:hover:not(:disabled) {
  border-color: #c9a84c;
  color: #c9a84c;
  background: rgba(201, 168, 76, 0.1);
}

.btn-danger {
  background: transparent;
  color: #dc3545;
  border: 1px solid rgba(220, 53, 69, 0.3);
  margin-left: auto;
}

.btn-danger:hover:not(:disabled) {
  background: rgba(220, 53, 69, 0.1);
  border-color: #dc3545;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-loading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  width: 18px;
  height: 18px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Save Messages */
.save-message {
  width: 100%;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 0.875rem;
  margin-top: 12px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.save-message.error {
  background: rgba(220, 53, 69, 0.15);
  border: 1px solid rgba(220, 53, 69, 0.3);
  color: #dc3545;
}

.save-message.success {
  background: rgba(40, 167, 69, 0.15);
  border: 1px solid rgba(40, 167, 69, 0.3);
  color: #28a745;
}

/* 响应式 */
@media (max-width: 768px) {
  .profile-header__content {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 32px 24px;
    gap: 16px;
  }

  .profile-avatar {
    width: 80px;
    height: 80px;
  }

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
    width: 100%;
  }

  .btn {
    width: 100%;
  }

  .btn-danger {
    margin-left: 0;
  }
}

@media (max-width: 480px) {
  .profile-container {
    padding: 0 16px 60px;
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
  .btn,
  .avatar-edit-btn,
  .spinner,
  .save-message {
    animation: none;
    transition: none;
  }
}
</style>