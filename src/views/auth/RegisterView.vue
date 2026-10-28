<script setup>
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api'

const EMAIL_PATTERN = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/
const CODE_PATTERN = /^\d{6}$/
// 与后端 utils/verify_code.py 的 CODE_RESEND_INTERVAL 保持一致
const RESEND_SECONDS = 60

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
  nickname: '',
  agree: false,
})

const submitLoading = ref(false)
const errorMessage = ref('')

// 邮箱验证码：发送按钮的状态与 60 秒重发倒计时
const codeSending = ref(false)
const countdown = ref(0)
const codeMessage = ref('')
let countdownTimer = null

const loginLink = computed(() => {
  const redirect = route.query.redirect
  return {
    name: 'Login',
    query: typeof redirect === 'string' && redirect ? { redirect } : {},
  }
})

const startCountdown = () => {
  countdown.value = RESEND_SECONDS
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

const handleSendCode = async () => {
  codeMessage.value = ''
  const email = form.email.trim()
  if (!email) {
    codeMessage.value = '请先填写邮箱'
    return
  }
  if (!EMAIL_PATTERN.test(email)) {
    codeMessage.value = '邮箱格式不正确'
    return
  }

  codeSending.value = true
  try {
    const response = await authApi.sendEmailCode({ email })
    if (response.code === 0) {
      codeMessage.value = '验证码已发送，请查收邮箱（开发环境请查看后端控制台）'
      startCountdown()
    } else {
      codeMessage.value = response.message || '验证码发送失败，请重试'
    }
  } catch (err) {
    codeMessage.value = err.message || '验证码发送失败，请重试'
  } finally {
    codeSending.value = false
  }
}

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})

const validateForm = () => {
  // 用户名可以留空，由后端随机生成 yunmo_ 开头的账号（见输入框提示）
  if (!form.email.trim()) {
    return '请输入邮箱'
  }
  if (!EMAIL_PATTERN.test(form.email)) {
    return '邮箱格式不正确'
  }
  // 邮箱为强制绑定项，必须通过验证码验证后才能注册
  if (!form.code.trim()) {
    return '请输入邮箱验证码'
  }
  if (!CODE_PATTERN.test(form.code.trim())) {
    return '邮箱验证码为 6 位数字'
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
  if (submitLoading.value) return
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
    code: form.code.trim(),
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
</script>

<template>
  <div class="auth-page">
    <lay-card class="auth-card">
      <div class="auth-header">
        <div class="auth-mark" aria-hidden="true">加入同好会</div>
        <h1 class="auth-title">创建账号</h1>
        <p class="auth-sub">绑定邮箱，和同好们一起追番</p>
      </div>

      <lay-form class="auth-form" label-position="top" @submit="handleSubmit">
        <div v-if="errorMessage" class="auth-error" role="alert">{{ errorMessage }}</div>

        <lay-form-item label="用户名">
          <lay-input
            v-model="form.username"
            placeholder="可选，留空将自动生成"
            autocomplete="username"
            allow-clear
          />
          <p class="form-hint">留空将自动生成以 yunmo_ 开头的用户名</p>
        </lay-form-item>

        <lay-form-item label="昵称">
          <lay-input
            v-model="form.nickname"
            placeholder="可选，默认同用户名"
            autocomplete="name"
            allow-clear
          />
        </lay-form-item>

        <lay-form-item label="邮箱" required>
          <lay-input
            v-model="form.email"
            type="email"
            placeholder="请输入邮箱"
            autocomplete="email"
            allow-clear
          />
        </lay-form-item>

        <lay-form-item label="邮箱验证码" required>
          <div class="code-row">
            <lay-input
              v-model="form.code"
              placeholder="6 位数字"
              maxlength="6"
              autocomplete="one-time-code"
            />
            <lay-button
              type="normal"
              native-type="button"
              :disabled="countdown > 0 || codeSending"
              :loading="codeSending"
              @click="handleSendCode"
            >
              {{ countdown > 0 ? `${countdown}s 后重发` : '发送验证码' }}
            </lay-button>
          </div>
          <p v-if="codeMessage" class="form-hint form-hint--strong">{{ codeMessage }}</p>
          <p v-else class="form-hint">邮箱为强制绑定项，请先获取验证码（5 分钟内有效）</p>
        </lay-form-item>

        <lay-form-item label="密码" required>
          <lay-input
            v-model="form.password"
            type="password"
            password
            placeholder="6-20 位字符"
            autocomplete="new-password"
          />
          <p class="form-hint">6-20 位字符，建议包含字母、数字和符号</p>
        </lay-form-item>

        <lay-form-item label="确认密码" required>
          <lay-input
            v-model="form.confirmPassword"
            type="password"
            password
            placeholder="再次输入密码"
            autocomplete="new-password"
          />
        </lay-form-item>

        <lay-checkbox v-model="form.agree" value="agree">
          我已阅读并同意《用户协议》与《隐私政策》
        </lay-checkbox>

        <lay-button
          class="auth-submit"
          type="primary"
          size="lg"
          native-type="submit"
          fluid
          :loading="submitLoading"
        >
          {{ submitLoading ? '注册中...' : '注册' }}
        </lay-button>
      </lay-form>

      <div class="auth-footer">
        <span class="muted">已有账号？</span>
        <router-link class="auth-link" :to="loginLink">立即登录</router-link>
      </div>
    </lay-card>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 72px);
  padding: var(--space-12) var(--space-6);
}

.auth-card {
  width: 100%;
  max-width: 480px;
  box-shadow: var(--shadow-xl);
}

.auth-card :deep(.layui-card-body) {
  padding: var(--space-10);
}

.auth-header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.auth-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2) var(--space-4);
  margin-bottom: var(--space-3);
  border-radius: var(--radius-full);
  background: var(--ghibli-sakura-100);
  color: var(--ghibli-sakura-600);
  font-size: var(--text-xs);
  letter-spacing: 0.2em;
}

.auth-title {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--ghibli-sky-800);
  margin: 0 0 var(--space-2);
}

.auth-sub {
  font-family: var(--font-handwriting);
  font-size: var(--text-sm);
  color: var(--ghibli-sakura-600);
  letter-spacing: 0.15em;
  margin: 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.auth-form :deep(.layui-form-item) {
  margin-bottom: 0;
}

.code-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.code-row > :first-child {
  flex: 1;
  min-width: 0;
}

.form-hint {
  margin: var(--space-2) 0 0;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.form-hint--strong {
  color: var(--ghibli-sky-700);
}

.auth-submit {
  margin-top: var(--space-2);
}

.auth-error {
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-bg);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-lg);
  color: var(--color-error);
  font-size: var(--text-sm);
}

.auth-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--space-8);
  padding-top: var(--space-6);
  border-top: 1px dashed var(--color-divider);
  font-size: var(--text-sm);
}

.auth-link {
  color: var(--ghibli-sky-600);
  font-weight: var(--font-medium);
  text-decoration: none;
}

.auth-link:hover {
  color: var(--ghibli-sky-700);
  text-decoration: underline;
}

@media (max-width: 480px) {
  .auth-page {
    padding: var(--space-8) var(--space-4);
  }

  .auth-card :deep(.layui-card-body) {
    padding: var(--space-6);
  }

  .code-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
