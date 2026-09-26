<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  nickname: '',
  agree: false,
})

const submitLoading = ref(false)
const errorMessage = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const validateForm = () => {
  if (!form.username.trim()) {
    return '请输入用户名'
  }
  if (!form.email.trim()) {
    return '请输入邮箱'
  }
  if (!/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(form.email)) {
    return '邮箱格式不正确'
  }
  if (!form.password) {
    return '请输入密码'
  }
  if (form.password.length < 6 || form.password.length > 20) {
    return '密码长度需为 6-20 位'
  }
  if (form.password !== form.confirmPassword) {
    return '两次输入的密码不一致'
  }
  if (!form.agree) {
    return '请阅读并同意用户协议与隐私政策'
  }
  return null
}

const handleSubmit = async () => {
  errorMessage.value = ''
  const validationError = validateForm()
  if (validationError) {
    errorMessage.value = validationError
    return
  }

  submitLoading.value = true

  const result = await authStore.register({
    username: form.username.trim(),
    email: form.email.trim(),
    password: form.password,
    nickname: form.nickname.trim() || form.username.trim(),
  })

  submitLoading.value = false

  if (result.success) {
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } else {
    errorMessage.value = result.message || '注册失败，请重试'
  }
}

const goLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <!-- Logo -->
        <div class="auth-header">
          <svg class="auth-logo" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <circle cx="24" cy="24" r="22" stroke="currentColor" stroke-width="2" class="logo-ring"/>
            <path d="M14 24 Q24 14 34 24 Q24 34 14 24" stroke="currentColor" stroke-width="2" fill="none" class="logo-yin-yang"/>
            <circle cx="24" cy="24" r="6" fill="currentColor" class="logo-center"/>
            <path d="M24 14 L24 34" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4" class="logo-divider"/>
          </svg>
          <h1 class="auth-title">云墨江湖</h1>
          <p class="auth-subtitle">一笔云墨，绘尽江湖梦</p>
        </div>

        <!-- 注册表单 -->
        <form class="auth-form" @submit.prevent="handleSubmit">
          <div v-if="errorMessage" class="auth-error" role="alert">
            {{ errorMessage }}
          </div>

          <div class="form-group">
            <label for="username" class="form-label">用户名 <span class="required">*</span></label>
            <div class="form-input-wrapper">
              <svg class="form-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <input
                id="username"
                v-model="form.username"
                type="text"
                class="form-input"
                placeholder="可选，留空将自动生成"
                autocomplete="username"
              />
            </div>
            <p class="form-hint">留空将自动生成以 yunmo_ 开头的用户名</p>
          </div>

          <div class="form-group">
            <label for="email" class="form-label">邮箱 <span class="required">*</span></label>
            <div class="form-input-wrapper">
              <svg class="form-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              <input
                id="email"
                v-model="form.email"
                type="email"
                class="form-input"
                placeholder="请输入邮箱"
                autocomplete="email"
                required
                @keydown.enter="handleSubmit"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="nickname" class="form-label">昵称</label>
            <div class="form-input-wrapper">
              <svg class="form-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <input
                id="nickname"
                v-model="form.nickname"
                type="text"
                class="form-input"
                placeholder="默认同用户名"
                autocomplete="name"
                @keydown.enter="handleSubmit"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="password" class="form-label">密码 <span class="required">*</span></label>
            <div class="form-input-wrapper">
              <svg class="form-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                placeholder="6-20 位字符"
                autocomplete="new-password"
                required
                @keydown.enter="handleSubmit"
              />
              <button
                type="button"
                class="form-toggle-password"
                @click="showPassword = !showPassword"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              >
                <svg v-if="!showPassword" class="toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else class="toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
            <p class="form-hint">6-20 位字符，建议包含字母、数字和符号</p>
          </div>

          <div class="form-group">
            <label for="confirmPassword" class="form-label">确认密码 <span class="required">*</span></label>
            <div class="form-input-wrapper">
              <svg class="form-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input
                id="confirmPassword"
                v-model="form.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                class="form-input"
                placeholder="再次输入密码"
                autocomplete="new-password"
                required
                @keydown.enter="handleSubmit"
              />
              <button
                type="button"
                class="form-toggle-password"
                @click="showConfirmPassword = !showConfirmPassword"
                :aria-label="showConfirmPassword ? '隐藏密码' : '显示密码'"
              >
                <svg v-if="!showConfirmPassword" class="toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else class="toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-wrapper">
              <input
                type="checkbox"
                v-model="form.agree"
                class="checkbox-input"
              />
              <span class="checkbox-custom" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </span>
              <span class="checkbox-label">
                我已阅读并同意
                <a href="#" class="link">《用户协议》</a>
                与
                <a href="#" class="link">《隐私政策》</a>
              </span>
            </label>
          </div>

          <button type="submit" class="auth-submit" :disabled="submitLoading">
            <span v-if="submitLoading" class="btn-loading">
              <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
              </svg>
              注册中...
            </span>
            <span v-else>注册</span>
          </button>
        </form>

        <!-- 底部链接 -->
        <div class="auth-footer">
          <p>已有账号？ <a @click.prevent="goLogin" class="link">立即登录</a></p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: #0d0d0d;
}

.auth-container {
  width: 100%;
  max-width: 420px;
}

.auth-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 16px;
  padding: 48px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

/* Header */
.auth-header {
  text-align: center;
  margin-bottom: 40px;
}

.auth-logo {
  width: 64px;
  height: 64px;
  color: #c9a84c;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 16px rgba(201, 168, 76, 0.4));
  animation: logoRotate 20s linear infinite;
}

@keyframes logoRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.auth-title {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: 2rem;
  font-weight: 700;
  color: #e8e8e8;
  margin: 0 0 8px;
  letter-spacing: 0.08em;
  background: linear-gradient(135deg, #e8e8e8 0%, #c9a84c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.auth-subtitle {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: 0.875rem;
  color: #c9a84c;
  letter-spacing: 0.15em;
  margin: 0;
  opacity: 0.9;
}

/* Form */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group.checkbox-group {
  gap: 0;
}

.form-label {
  font-size: 0.875rem;
  color: #e8e8e8;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.required {
  color: #dc3545;
  margin-left: 2px;
}

.form-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.form-icon {
  position: absolute;
  left: 14px;
  width: 20px;
  height: 20px;
  color: #999;
  pointer-events: none;
  transition: color 0.2s ease;
}

.form-input {
  width: 100%;
  padding: 14px 16px 14px 48px;
  background: #0d0d0d;
  border: 1px solid #333;
  border-radius: 10px;
  color: #e8e8e8;
  font-size: 1rem;
  font-family: inherit;
  transition: all 0.2s ease;
}

.form-input::placeholder {
  color: #666;
}

.form-input:focus {
  outline: none;
  border-color: #c9a84c;
  box-shadow: 0 0 0 3px rgba(201, 168, 76, 0.2);
}

.form-input:focus + .form-icon,
.form-input-wrapper:focus-within .form-icon {
  color: #c9a84c;
}

.form-toggle-password {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #999;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease;
}

.form-toggle-password:hover {
  color: #c9a84c;
}

.toggle-icon {
  width: 20px;
  height: 20px;
}

.form-hint {
  margin: 4px 0 0;
  font-size: 0.75rem;
  color: #666;
}

/* Checkbox */
.checkbox-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  color: #999;
  line-height: 1.6;
  font-size: 0.8125rem;
}

.checkbox-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-custom {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border: 1px solid #333;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  color: transparent;
  margin-top: 2px;
}

.checkbox-input:checked + .checkbox-custom {
  background: #c9a84c;
  border-color: #c9a84c;
  color: #0d0d0d;
}

.checkbox-input:focus-visible + .checkbox-custom {
  outline: 2px solid #c9a84c;
  outline-offset: 2px;
}

.checkbox-label {
  user-select: none;
}

.checkbox-label .link {
  color: #c9a84c;
  text-decoration: none;
  transition: color 0.2s ease;
}

.checkbox-label .link:hover {
  color: #e8d57a;
  text-decoration: underline;
}

/* Submit */
.auth-submit {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #c9a84c 0%, #a68a3a 100%);
  border: none;
  border-radius: 10px;
  color: #0d0d0d;
  font-family: inherit;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 8px;
}

.auth-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(201, 168, 76, 0.3);
}

.auth-submit:active:not(:disabled) {
  transform: translateY(0);
}

.auth-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.auth-submit:focus-visible {
  outline: 2px solid #c9a84c;
  outline-offset: 2px;
}

.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.spinner {
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error */
.auth-error {
  padding: 12px 16px;
  background: rgba(220, 53, 69, 0.15);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 8px;
  color: #dc3545;
  font-size: 0.875rem;
  animation: shake 0.4s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
}

/* Footer */
.auth-footer {
  text-align: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #333;
  color: #999;
  font-size: 0.9375rem;
}

.auth-footer .link {
  color: #c9a84c;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.auth-footer .link:hover {
  color: #e8d57a;
  text-decoration: underline;
}

/* 响应式 */
@media (max-width: 480px) {
  .auth-card {
    padding: 32px 24px;
  }

  .auth-title {
    font-size: 1.75rem;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .auth-logo,
  .spinner {
    animation: none;
  }

  .form-input,
  .form-toggle-password,
  .checkbox-custom,
  .auth-submit,
  .link {
    transition: none;
  }
}
</style>