<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: '',
  remember: false,
})

const submitLoading = ref(false)
const errorMessage = ref('')
const showPassword = ref(false)

const handleSubmit = async () => {
  errorMessage.value = ''
  submitLoading.value = true

  const result = await authStore.login({
    username: form.username,
    password: form.password,
  })

  submitLoading.value = false

  if (result.success) {
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } else {
    errorMessage.value = result.message || '登录失败，请重试'
  }
}

const goRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <!-- Logo -->
        <div class="auth-header">
          <svg class="auth-logo" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <!-- 动漫风：老式电视机 + 播放键 -->
            <rect x="6" y="13" width="36" height="28" rx="7" stroke="currentColor" stroke-width="2" fill="var(--ghibli-sky-100)"/>
            <path d="M18 13 L24 6 L30 13" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
            <circle cx="24" cy="6" r="2.5" fill="var(--ghibli-sun-400)"/>
            <path d="M21 24 L29 28 L21 32 Z" fill="var(--ghibli-sakura-400)"/>
            <path d="M35 20 L36.3 23.2 L39.5 24.5 L36.3 25.8 L35 29 L33.7 25.8 L30.5 24.5 L33.7 23.2 Z" fill="var(--ghibli-sun-300)"/>
          </svg>
          <h1 class="auth-title">番剧同好会</h1>
          <p class="auth-subtitle">追番、安利、找同好</p>
        </div>

        <!-- 登录表单 -->
        <form class="auth-form" @submit.prevent="handleSubmit">
          <div v-if="errorMessage" class="auth-error" role="alert">
            {{ errorMessage }}
          </div>

          <div class="form-group">
            <label for="username" class="form-label">用户名</label>
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
                placeholder="请输入用户名"
                autocomplete="username"
                required
                @keydown.enter="handleSubmit"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="password" class="form-label">密码</label>
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
                placeholder="请输入密码"
                autocomplete="current-password"
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
          </div>

          <div class="form-options">
            <label class="checkbox-wrapper">
              <input
                type="checkbox"
                v-model="form.remember"
                class="checkbox-input"
              />
              <span class="checkbox-custom" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </span>
              <span class="checkbox-label">记住我</span>
            </label>
            <a href="#" class="forgot-link">忘记密码？</a>
          </div>

          <button type="submit" class="ghibli-btn ghibli-btn--primary ghibli-btn--lg auth-submit" :disabled="submitLoading">
            <span v-if="submitLoading" class="ghibli-btn__loading">
              <span class="ghibli-spinner" aria-hidden="true"></span>
              登录中...
            </span>
            <span v-else>登录</span>
          </button>
        </form>

        <!-- 底部链接 -->
        <div class="auth-footer">
          <p>还没有账号？ <a @click.prevent="goRegister" class="link">立即注册</a></p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-6);
}

.auth-container {
  width: 100%;
  max-width: 440px;
}

.auth-card {
  position: relative;
  overflow: hidden;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-3xl);
  padding: var(--space-12) var(--space-10);
  box-shadow: var(--shadow-xl);
}

.auth-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--ghibli-sky-400), var(--ghibli-forest-400), var(--ghibli-sun-400), var(--ghibli-sakura-400));
}

/* Header */
.auth-header {
  text-align: center;
  margin-bottom: var(--space-10);
}

.auth-logo {
  width: 64px;
  height: 64px;
  color: var(--ghibli-sky-600);
  margin: 0 auto var(--space-4);
  filter: drop-shadow(0 4px 14px rgba(14, 165, 233, 0.25));
  animation: logoFloat 3.5s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.auth-title {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  margin: 0 0 var(--space-2);
  letter-spacing: 0.04em;
  background: linear-gradient(135deg, var(--ghibli-sky-600) 0%, var(--ghibli-sakura-500) 60%, var(--ghibli-sun-400) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.auth-subtitle {
  font-family: var(--font-handwriting);
  font-size: var(--text-sm);
  color: var(--ghibli-sakura-600);
  letter-spacing: 0.15em;
  margin: 0;
}

/* Form */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-label {
  font-size: var(--text-sm);
  color: var(--color-text);
  font-weight: var(--font-medium);
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
  color: var(--color-text-muted);
  pointer-events: none;
  transition: color var(--duration-fast) var(--ease-gentle);
}

.form-input {
  width: 100%;
  padding: var(--space-8) var(--space-8) var(--space-8) 48px;
  background: var(--ghibli-paper-50);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text);
  font-size: var(--text-base);
  font-family: inherit;
  transition: var(--transition-gentle);
}

.form-input::placeholder {
  color: var(--ghibli-paper-500);
}

.form-input:hover {
  border-color: var(--color-border-strong);
}

.form-input:focus {
  outline: none;
  background: var(--color-bg-elevated);
  border-color: var(--ghibli-sky-400);
  box-shadow: var(--focus-ring);
}

.form-input:focus + .form-icon,
.form-input-wrapper:focus-within .form-icon {
  color: var(--ghibli-sky-500);
}

.form-toggle-password {
  position: absolute;
  right: 12px;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--duration-fast) var(--ease-gentle);
}

.form-toggle-password:hover {
  color: var(--ghibli-sky-600);
}

.form-toggle-password:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.toggle-icon {
  width: 20px;
  height: 20px;
}

/* Options */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  font-size: var(--text-sm);
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  cursor: pointer;
  color: var(--color-text-muted);
}

.checkbox-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition-gentle);
  color: transparent;
}

.checkbox-input:checked + .checkbox-custom {
  background: var(--ghibli-sky-500);
  border-color: var(--ghibli-sky-500);
  color: white;
}

.checkbox-input:focus-visible + .checkbox-custom {
  outline: none;
  box-shadow: var(--focus-ring);
}

.checkbox-label {
  user-select: none;
}

.forgot-link {
  color: var(--ghibli-sky-600);
  text-decoration: none;
  transition: color var(--duration-fast) var(--ease-gentle);
}

.forgot-link:hover {
  color: var(--ghibli-sky-700);
  text-decoration: underline;
}

/* Submit */
.auth-submit {
  width: 100%;
  margin-top: var(--space-2);
}

/* Error */
.auth-error {
  padding: var(--space-6) var(--space-8);
  background: var(--color-error-bg);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-lg);
  color: var(--color-error);
  font-size: var(--text-sm);
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
  margin-top: var(--space-12);
  padding-top: var(--space-10);
  border-top: 1px dashed var(--color-divider);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.auth-footer p {
  margin: 0;
  color: inherit;
}

.auth-footer .link {
  color: var(--ghibli-sky-600);
  text-decoration: none;
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: color var(--duration-fast) var(--ease-gentle);
}

.auth-footer .link:hover {
  color: var(--ghibli-sky-700);
  text-decoration: underline;
}

/* 响应式 */
@media (max-width: 480px) {
  .auth-page {
    padding: var(--space-12) var(--space-4);
  }

  .auth-card {
    padding: var(--space-10) var(--space-6);
    border-radius: var(--radius-2xl);
  }

  .auth-title {
    font-size: var(--text-2xl);
  }

  .form-options {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-4);
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .auth-logo,
  .auth-error {
    animation: none;
  }

  .form-input,
  .form-toggle-password,
  .checkbox-custom,
  .forgot-link,
  .auth-footer .link {
    transition: none;
  }
}
</style>