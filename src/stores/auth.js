import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, userApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const loading = ref(false)
  const error = ref('')

  // Getters
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const userInfo = computed(() => user.value)

  // Actions
  async function login(credentials) {
    loading.value = true
    error.value = ''
    try {
      const response = await authApi.login(credentials)
      if (response.code === 0) {
        const { token: newToken, ...userData } = response.data
        token.value = newToken
        user.value = userData
        localStorage.setItem('token', newToken)
        localStorage.setItem('user', JSON.stringify(userData))
        return { success: true }
      }
      error.value = response.message
      return { success: false, message: response.message }
    } catch (err) {
      error.value = err.message || '登录失败'
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  async function register(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await authApi.register(data)
      if (response.code === 0) {
        // 注册成功后自动登录。
        // 注意：用户名可留空（后端会随机生成 yunmo_xxx），所以必须用注册接口返回的
        // username 登录，不能拿表单里的值，否则会以空用户名登录而报「缺少必填参数」。
        const loginResult = await login({
          username: response.data.username,
          password: data.password,
        })
        return loginResult
      }
      error.value = response.message
      return { success: false, message: response.message }
    } catch (err) {
      error.value = err.message || '注册失败'
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await userApi.updateProfile(data)
      if (response.code === 0) {
        // 用后端返回的最新资料覆盖本地缓存，保证刷新前页面显示的也是落库后的值
        user.value = { ...user.value, ...response.data }
        localStorage.setItem('user', JSON.stringify(user.value))
        return { success: true }
      }
      error.value = response.message
      return { success: false, message: response.message }
    } catch (err) {
      error.value = err.message || '保存失败'
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  async function fetchProfile() {
    if (!token.value) return
    try {
      const response = await userApi.getProfile()
      if (response.code === 0) {
        user.value = { ...user.value, ...response.data }
        localStorage.setItem('user', JSON.stringify(user.value))
      }
    } catch (err) {
      console.error('获取用户资料失败:', err)
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function clearError() {
    error.value = ''
  }

  return {
    token,
    user,
    loading,
    error,
    isLoggedIn,
    userInfo,
    login,
    register,
    updateProfile,
    fetchProfile,
    logout,
    clearError,
  }
})