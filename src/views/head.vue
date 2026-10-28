<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { friendApi, notificationApi } from '@/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const navItems = computed(() => {
  const items = [
    { name: '首页', path: '/' },
    { name: '讨论区', path: '/news' },
    { name: '番剧库', path: '/heroes' },
    { name: '资源分享', path: '/skills' },
    { name: '关于我们', path: '/about' },
  ]
  if (authStore.isAdmin) {
    items.push({ name: '管理后台', path: '/admin' })
  }
  return items
})

const isNavActive = (path) => (path === '/' ? route.path === '/' : route.path.startsWith(path))

const isScrolled = ref(false)
const mobileOpen = ref(false)
const pendingCount = ref(0)
const notifCount = ref(0)

const userInfo = computed(() => authStore.user)
const isLoggedIn = computed(() => authStore.isLoggedIn)
const isBanned = computed(() => userInfo.value?.status === 2)

const handleScroll = () => {
  isScrolled.value = window.scrollY > 40
}

const loadPending = async () => {
  if (!isLoggedIn.value) return
  try {
    const res = await friendApi.getPendingCount()
    pendingCount.value = res.code === 0 ? res.data.count : 0
  } catch {
    pendingCount.value = 0
  }
}

const loadNotifications = async () => {
  if (!isLoggedIn.value) return
  try {
    const res = await notificationApi.getUnreadCount()
    notifCount.value = res.code === 0 ? res.data.count : 0
  } catch {
    notifCount.value = 0
  }
}

const go = (path) => {
  mobileOpen.value = false
  router.push(path)
}

const goLogin = () => router.push({ name: 'Login', query: { redirect: route.fullPath } })
const goRegister = () => router.push({ name: 'Register', query: { redirect: route.fullPath } })

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}

const avatarText = computed(() => (userInfo.value?.nickname || '番').charAt(0).toUpperCase())

watch(
  () => route.fullPath,
  () => {
    mobileOpen.value = false
    loadPending()
    loadNotifications()
  }
)

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  loadPending()
  loadNotifications()
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <header class="site-header" :class="{ 'site-header--scrolled': isScrolled }">
    <div class="site-header__inner">
      <router-link to="/" class="site-brand" aria-label="番剧同好会首页">
        <svg class="site-brand__icon" viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <rect x="7" y="14" width="34" height="26" rx="6" stroke="currentColor" stroke-width="2.5" fill="var(--ghibli-sky-100)" opacity="0.7" />
          <rect x="12" y="20" width="24" height="14" rx="4" fill="var(--ghibli-sky-200)" opacity="0.8" />
          <path d="M18 14 L24 7 L30 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" />
          <circle cx="24" cy="7" r="2.5" fill="var(--ghibli-sun-400)" />
          <path d="M21.5 23.5 L28.5 27 L21.5 30.5 Z" fill="var(--ghibli-sakura-400)" />
        </svg>
        <span class="site-brand__text">
          <span class="site-brand__main">番剧同好会</span>
          <span class="site-brand__sub">追番、安利、找同好</span>
        </span>
      </router-link>

      <nav class="site-nav" role="navigation" aria-label="主导航">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="site-nav__link"
          :class="{ 'site-nav__link--active': isNavActive(item.path) }"
        >
          {{ item.name }}
        </router-link>
      </nav>

      <div class="site-actions">
        <template v-if="isLoggedIn">
          <lay-button type="primary" size="sm" @click="go('/posts/new')">发帖</lay-button>

          <lay-dropdown trigger="click" placement="bottom-end" click-outside-to-close>
            <div class="site-user" role="button" tabindex="0">
              <span class="site-user__avatar">{{ avatarText }}</span>
              <span class="site-user__name">{{ userInfo?.nickname || userInfo?.username }}</span>
              <lay-badge v-if="pendingCount > 0" :value="pendingCount" type="danger" />
            </div>
            <template #content>
              <div class="site-menu">
                <div class="site-menu__item" @click="go('/profile')">个人中心</div>
                <div class="site-menu__item" @click="go('/content/drafts')">草稿箱</div>
                <div class="site-menu__divider"></div>
                <div class="site-menu__item" @click="go('/content/posts')">内容管理</div>
                <div class="site-menu__item" @click="go('/friends')">
                  好友
                  <span v-if="pendingCount > 0" class="site-menu__count">{{ pendingCount }}</span>
                </div>
                <div class="site-menu__item" @click="go('/notifications')">
                  消息通知
                  <span v-if="notifCount > 0" class="site-menu__count">{{ notifCount }}</span>
                </div>
                <div class="site-menu__item" @click="go('/profile/identity')">
                  身份申请
                </div>
                <div v-if="isBanned" class="site-menu__item site-menu__item--danger" @click="go('/appeal')">
                  账号申诉
                </div>
                <div v-if="authStore.isAdmin" class="site-menu__item" @click="go('/admin')">管理后台</div>
                <div class="site-menu__divider"></div>
                <div class="site-menu__item site-menu__item--muted" @click="handleLogout">退出登录</div>
              </div>
            </template>
          </lay-dropdown>
        </template>
        <template v-else>
          <lay-button size="sm" @click="goLogin">登录</lay-button>
          <lay-button type="primary" size="sm" @click="goRegister">注册</lay-button>
        </template>

        <button class="site-mobile-toggle" type="button" aria-label="展开导航" @click="mobileOpen = !mobileOpen">
          <span></span><span></span><span></span>
        </button>
      </div>
    </div>

    <div v-if="mobileOpen" class="site-mobile">
      <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="site-mobile__link">
        {{ item.name }}
      </router-link>
      <template v-if="isLoggedIn">
        <router-link to="/content/posts" class="site-mobile__link">内容管理</router-link>
        <router-link to="/friends" class="site-mobile__link">好友</router-link>
      </template>
    </div>

    <div v-if="isLoggedIn && isBanned" class="site-banned">
      账号已被封禁：{{ userInfo?.ban_reason || '违反社区规范' }}
      <router-link to="/appeal">立即申诉</router-link>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-fixed);
  background: rgba(250, 250, 246, 0.92);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid transparent;
  transition: all var(--duration-normal) var(--ease-gentle);
}

.site-header--scrolled {
  border-bottom-color: var(--color-divider);
  box-shadow: var(--shadow-sm);
}

.site-header__inner {
  max-width: var(--container-2xl);
  margin: 0 auto;
  height: 72px;
  padding: 0 var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-8);
}

.site-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  text-decoration: none;
  color: var(--color-text);
  flex-shrink: 0;
}

.site-brand__icon {
  width: 38px;
  height: 38px;
  color: var(--ghibli-sky-700);
}

.site-brand__text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.site-brand__main {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--ghibli-sky-700);
}

.site-brand__sub {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  letter-spacing: 0.08em;
}

.site-nav {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  overflow: hidden;
}

.site-nav__link {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
  color: var(--color-text-light);
  font-size: var(--text-sm);
  text-decoration: none;
  white-space: nowrap;
  transition: all var(--duration-fast) var(--ease-gentle);
}

.site-nav__link:hover {
  color: var(--ghibli-sky-600);
  background: var(--ghibli-sky-50);
}

.site-nav__link--active {
  color: var(--ghibli-sky-700);
  background: var(--ghibli-sky-100);
  font-weight: var(--font-semibold);
}

.site-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.site-user {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  transition: background var(--duration-fast) var(--ease-gentle);
}

.site-user:hover {
  background: var(--ghibli-paper-200);
}

.site-user__avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: var(--font-semibold);
  background: linear-gradient(135deg, var(--ghibli-sky-400), var(--ghibli-forest-400));
}

.site-user__name {
  font-size: var(--text-sm);
  color: var(--color-text);
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.site-menu {
  min-width: 168px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: var(--space-2);
}

.site-menu__item {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.site-menu__item:hover {
  background: var(--ghibli-sky-50);
  color: var(--ghibli-sky-700);
}

.site-menu__item--danger {
  color: var(--color-error);
}

.site-menu__item--muted {
  color: var(--color-text-muted);
}

.site-menu__count {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: var(--radius-full);
  background: var(--ghibli-sakura-500);
  color: #fff;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.site-menu__divider {
  height: 1px;
  margin: var(--space-1) var(--space-2);
  background: var(--color-divider);
}

.site-mobile-toggle {
  display: none;
  width: 36px;
  height: 36px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-elevated);
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.site-mobile-toggle span {
  width: 16px;
  height: 2px;
  background: var(--color-text);
  border-radius: 2px;
}

.site-mobile {
  display: none;
  padding: var(--space-2) var(--space-6) var(--space-4);
  border-top: 1px solid var(--color-divider);
  background: var(--color-bg-elevated);
}

.site-mobile__link {
  display: block;
  padding: var(--space-3) 0;
  color: var(--color-text);
  text-decoration: none;
  font-size: var(--text-sm);
  border-bottom: 1px dashed var(--color-divider);
}

.site-banned {
  background: var(--color-warning-bg);
  border-top: 1px solid var(--ghibli-sun-200);
  color: var(--ghibli-warm-800);
  font-size: var(--text-sm);
  text-align: center;
  padding: var(--space-2) var(--space-4);
}

.site-banned a {
  color: var(--ghibli-sky-700);
  margin-left: var(--space-3);
  font-weight: var(--font-semibold);
}

@media (max-width: 900px) {
  .site-nav {
    display: none;
  }

  .site-mobile-toggle {
    display: flex;
  }

  .site-mobile {
    display: block;
  }

  .site-user__name {
    display: none;
  }
}

@media (max-width: 480px) {
  .site-header__inner {
    padding: 0 var(--space-4);
    gap: var(--space-4);
  }

  .site-brand__sub {
    display: none;
  }
}
</style>
