<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: '',
})

const submitLoading = ref(false)
const errorMessage = ref('')

const redirectTarget = computed(() => {
  const redirect = route.query.redirect
  return typeof redirect === 'string' && redirect ? redirect : '/'
})

const registerLink = computed(() => {
  const redirect = route.query.redirect
  return {
    name: 'Register',
    query: typeof redirect === 'string' && redirect ? { redirect } : {},
  }
})

const handleSubmit = async () => {
  if (submitLoading.value) return
  errorMessage.value = ''

  if (!form.username.trim()) {
    errorMessage.value = '请输入用户名'
    return
  }
  if (!form.password) {
    errorMessage.value = '请输入密码'
    return
  }

  submitLoading.value = true
  const result = await authStore.login({
    username: form.username.trim(),
    password: form.password,
  })
  submitLoading.value = false

  if (!result.success) {
    errorMessage.value = result.message || '登录失败，请重试'
    return
  }

  // 封禁用户可登录，但不能发言，直接引导到申诉页
  if (authStore.userInfo?.status === 2) {
    window.$ghibli?.showToast({
      type: 'warning',
      title: '账号已被封禁',
      message: authStore.userInfo.ban_reason || '你的账号处于封禁状态，暂时无法发言，可提交申诉',
    })
    router.push('/appeal')
    return
  }

  router.push(redirectTarget.value)
}
</script>

<template>
  <div class="auth-page">
    <lay-card class="auth-card">
      <div class="auth-header">
        <div class="auth-mark" aria-hidden="true">同好会</div>
        <h1 class="auth-title">番剧同好会</h1>
        <p class="auth-sub">追番、安利、找同好</p>
      </div>

      <lay-form class="auth-form" label-position="top" @submit="handleSubmit">
        <div v-if="errorMessage" class="auth-error" role="alert">{{ errorMessage }}</div>

        <lay-form-item label="用户名" required>
          <lay-input
            v-model="form.username"
            placeholder="请输入用户名"
            autocomplete="username"
            allow-clear
          />
        </lay-form-item>

        <lay-form-item label="密码" required>
          <lay-input
            v-model="form.password"
            type="password"
            password
            placeholder="请输入密码"
            autocomplete="current-password"
          />
        </lay-form-item>

        <lay-button
          class="auth-submit"
          type="primary"
          size="lg"
          native-type="submit"
          fluid
          :loading="submitLoading"
        >
          {{ submitLoading ? '登录中...' : '登录' }}
        </lay-button>
      </lay-form>

      <div class="auth-footer">
        <span class="muted">还没有账号？</span>
        <router-link class="auth-link" :to="registerLink">去注册</router-link>
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
  padding: var(--space-16) var(--space-6);
}

.auth-card {
  width: 100%;
  max-width: 440px;
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
  background: var(--ghibli-sky-100);
  color: var(--ghibli-sky-700);
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
    padding: var(--space-10) var(--space-4);
  }

  .auth-card :deep(.layui-card-body) {
    padding: var(--space-6);
  }
}
</style>
