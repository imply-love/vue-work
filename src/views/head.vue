<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const siteTitle = ref('云墨江湖')
const siteSubtitle = ref('一笔云墨，绘尽江湖梦')
const navItems = ref([
  { name: '首页', path: '/', active: true },
  { name: '江湖动态', path: '/news', active: false },
  { name: '侠客行', path: '/heroes', active: false },
  { name: '武功秘籍', path: '/skills', active: false },
  { name: '关于我们', path: '/about', active: false },
  { name: '测试中心', path: '/test', active: false }
])

const isScrolled = ref(false)
const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)

const userInfo = computed(() => authStore.user)
const isLoggedIn = computed(() => authStore.isLoggedIn)

let lastScrollY = 0

const handleScroll = () => {
  const currentScrollY = window.scrollY
  isScrolled.value = currentScrollY > 50

  // 隐藏/显示导航栏逻辑
  if (currentScrollY > lastScrollY && currentScrollY > 100) {
    // 向下滚动 - 隐藏
    headerEl.value?.classList.add('header--hidden')
  } else {
    // 向上滚动 - 显示
    headerEl.value?.classList.remove('header--hidden')
  }
  lastScrollY = currentScrollY
}

const headerEl = ref(null)

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  // 入场动画
  setTimeout(() => {
    headerEl.value?.classList.add('header--entered')
  }, 100)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
  document.body.style.overflow = mobileMenuOpen.value ? 'hidden' : ''
}

const navigateTo = (path) => {
  router.push(path)
  mobileMenuOpen.value = false
  document.body.style.overflow = ''
}

const goLogin = () => {
  router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
  mobileMenuOpen.value = false
  userMenuOpen.value = false
  document.body.style.overflow = ''
}

const goRegister = () => {
  router.push({ name: 'Register', query: { redirect: router.currentRoute.value.fullPath } })
  mobileMenuOpen.value = false
  userMenuOpen.value = false
  document.body.style.overflow = ''
}

const goProfile = () => {
  router.push('/profile')
  userMenuOpen.value = false
}

const handleLogout = () => {
  authStore.logout()
  router.push('/')
  userMenuOpen.value = false
}

const toggleUserMenu = (e) => {
  e.stopPropagation()
  userMenuOpen.value = !userMenuOpen.value
}

// 点击外部关闭用户菜单
const closeUserMenu = (e) => {
  if (userMenuOpen.value && !e.target.closest('.header__user-menu')) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', closeUserMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeUserMenu)
})

const getAvatarInitial = (nickname) => {
  if (!nickname) return '云'
  return nickname.charAt(0).toUpperCase()
}
</script>

<template>
  <header
    ref="headerEl"
    class="ghibli-header"
    :class="{ 'ghibli-header--scrolled': isScrolled, 'ghibli-header--hidden': false, 'ghibli-header--entered': true }"
    role="banner"
  >
    <!-- 背景装饰层 -->
    <div class="ghibli-header__bg" aria-hidden="true">
      <div class="ghibli-header__clouds">
        <div class="ghibli-cloud cloud-1"></div>
        <div class="ghibli-cloud cloud-2"></div>
        <div class="ghibli-cloud cloud-3"></div>
      </div>
      <div class="ghibli-header__birds">
        <div class="ghibli-bird bird-1"></div>
        <div class="ghibli-bird bird-2"></div>
        <div class="ghibli-bird bird-3"></div>
      </div>
      <!-- 飞艇装饰 -->
      <svg class="ghibli-header__airship" viewBox="0 0 120 60" aria-hidden="true">
        <ellipse cx="60" cy="35" rx="45" ry="15" fill="var(--ghibli-warm-300)" opacity="0.3"/>
        <ellipse cx="60" cy="25" rx="30" ry="10" fill="var(--ghibli-warm-400)" opacity="0.4"/>
        <rect x="30" y="35" width="60" height="8" rx="4" fill="var(--ghibli-warm-500)" opacity="0.3"/>
        <circle cx="45" cy="39" r="3" fill="var(--ghibli-sky-400)" opacity="0.5"/>
        <circle cx="60" cy="39" r="3" fill="var(--ghibli-sun-400)" opacity="0.5"/>
        <circle cx="75" cy="39" r="3" fill="var(--ghibli-forest-400)" opacity="0.5"/>
      </svg>
    </div>

    <div class="ghibli-header__container">
      <!-- Logo 区域 -->
      <div class="ghibli-header__brand">
        <router-link to="/" class="ghibli-logo" aria-label="云墨江湖 - 返回首页">
          <svg class="ghibli-logo__icon" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <!-- 吉卜力风格 Logo：龙猫轮廓 + 飞行石 -->
            <ellipse cx="24" cy="34" rx="18" ry="14" stroke="currentColor" stroke-width="2.5" fill="var(--ghibli-warm-200)" opacity="0.3"/>
            <ellipse cx="24" cy="28" rx="14" ry="10" stroke="currentColor" stroke-width="2" fill="var(--ghibli-warm-100)" opacity="0.4"/>
            <!-- 耳朵 -->
            <path d="M10 22 Q8 12 14 16" stroke="currentColor" stroke-width="2" fill="var(--ghibli-warm-100)" opacity="0.3"/>
            <path d="M38 22 Q40 12 34 16" stroke="currentColor" stroke-width="2" fill="var(--ghibli-warm-100)" opacity="0.3"/>
            <!-- 眼睛 -->
            <circle cx="17" cy="28" r="3" fill="var(--ghibli-ink-700)"/>
            <circle cx="31" cy="28" r="3" fill="var(--ghibli-ink-700)"/>
            <!-- 鼻子 -->
            <ellipse cx="24" cy="32" rx="2" ry="1.5" fill="var(--ghibli-sakura-400)"/>
            <!-- 胡须 -->
            <g stroke="var(--ghibli-ink-500)" stroke-width="1.5" opacity="0.6">
              <line x1="14" y1="31" x2="6" y2="29"/>
              <line x1="14" y1="33" x2="5" y2="34"/>
              <line x1="14" y1="35" x2="6" y2="39"/>
              <line x1="34" y1="31" x2="42" y2="29"/>
              <line x1="34" y1="33" x2="43" y2="34"/>
              <line x1="34" y1="35" x2="42" y2="39"/>
            </g>
            <!-- 肚子花纹 -->
            <path d="M24 36 Q20 38 18 42" stroke="currentColor" stroke-width="1.5" fill="none" opacity="0.4"/>
            <path d="M24 36 Q28 38 30 42" stroke="currentColor" stroke-width="1.5" fill="none" opacity="0.4"/>
            <!-- 飞行石 -->
            <polygon points="24,8 28,18 38,18 30,24 34,34 24,28 14,34 18,24 10,18 20,18" fill="var(--ghibli-sky-300)" stroke="var(--ghibli-sky-500)" stroke-width="1.5" opacity="0.9">
              <animate attributeName="opacity" values="0.9;1;0.9" dur="2s" repeatCount="indefinite"/>
            </polygon>
            <circle cx="24" cy="20" r="3" fill="var(--ghibli-sun-300)" opacity="0.8">
              <animate attributeName="r" values="3;4;3" dur="1.5s" repeatCount="indefinite"/>
            </circle>
          </svg>
          <span class="ghibli-logo__text">
            <span class="ghibli-logo__main">{{ siteTitle }}</span>
            <span class="ghibli-logo__sub">{{ siteSubtitle }}</span>
          </span>
        </router-link>
      </div>

      <!-- 导航菜单 -->
      <nav class="ghibli-header__nav" role="navigation" aria-label="主导航">
        <ul class="ghibli-header__nav-list">
          <li v-for="item in navItems" :key="item.path" class="ghibli-header__nav-item">
            <router-link
              :to="item.path"
              class="ghibli-header__nav-link"
              :class="{ 'ghibli-header__nav-link--active': item.active }"
              :aria-current="item.active ? 'page' : undefined"
            >
              <span class="ghibli-header__nav-text">{{ item.name }}</span>
              <span class="ghibli-header__nav-indicator" aria-hidden="true"></span>
            </router-link>
          </li>
        </ul>
      </nav>

      <!-- 用户操作区域 -->
      <div class="ghibli-header__actions">
        <template v-if="isLoggedIn">
          <!-- 用户下拉菜单 -->
          <div class="ghibli-dropdown ghibli-header__user-menu">
            <button
              class="ghibli-dropdown__trigger ghibli-header__user-trigger"
              @click="toggleUserMenu"
              :aria-expanded="userMenuOpen"
              :aria-label="userMenuOpen ? '关闭用户菜单' : '打开用户菜单'"
              aria-haspopup="true"
            >
              <div class="ghibli-avatar ghibli-avatar--sm ghibli-header__user-avatar" :style="{ background: userInfo?.avatar ? 'none' : 'linear-gradient(135deg, var(--ghibli-sky-400), var(--ghibli-forest-400))' }">
                <img v-if="userInfo?.avatar" :src="userInfo.avatar" :alt="userInfo.nickname" />
                <span v-else class="ghibli-avatar__text">{{ getAvatarInitial(userInfo?.nickname) }}</span>
              </div>
              <span class="ghibli-header__user-name">{{ userInfo?.nickname }}</span>
              <svg class="ghibli-header__user-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <polyline points="18 15 12 9 6 15"/>
              </svg>
            </button>

            <transition name="dropdown-transition">
              <div
                v-show="userMenuOpen"
                class="ghibli-dropdown__menu ghibli-header__user-dropdown"
                role="menu"
                aria-label="用户菜单"
              >
                <router-link
                  to="/profile"
                  class="ghibli-dropdown__item"
                  role="menuitem"
                  @click="goProfile"
                >
                  <svg class="ghibli-dropdown__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                  个人中心
                </router-link>
                <hr class="ghibli-dropdown__divider" aria-hidden="true" />
                <button
                  class="ghibli-dropdown__item ghibli-dropdown__item--danger"
                  role="menuitem"
                  @click="handleLogout"
                >
                  <svg class="ghibli-dropdown__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                    <polyline points="16 17 21 12 16 7"/>
                    <line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                  退出登录
                </button>
              </div>
            </transition>
          </div>
        </template>

        <template v-else>
          <!-- 未登录状态：登录/注册按钮 -->
          <div class="ghibli-header__auth-buttons">
            <button
              class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm"
              @click="goLogin"
            >
              <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                <polyline points="10 17 15 12 10 7"/>
                <line x1="15" y1="12" x2="3" y2="12"/>
              </svg>
              登录
            </button>
            <button
              class="ghibli-btn ghibli-btn--primary ghibli-btn--sm"
              @click="goRegister"
            >
              <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="8.5" cy="7" r="4"/>
                <line x1="20" y1="8" x2="20" y2="14"/>
                <line x1="23" y1="11" x2="17" y2="11"/>
              </svg>
              注册
            </button>
          </div>
        </template>
      </div>

      <!-- 移动端菜单按钮 -->
      <button
        class="ghibli-header__mobile-toggle"
        @click="toggleMobileMenu"
        :aria-expanded="mobileMenuOpen"
        :aria-label="mobileMenuOpen ? '关闭菜单' : '打开菜单'"
        aria-controls="mobile-menu"
      >
        <span class="ghibli-header__hamburger" aria-hidden="true">
          <span class="ghibli-header__hamburger-line"></span>
          <span class="ghibli-header__hamburger-line"></span>
          <span class="ghibli-header__hamburger-line"></span>
        </span>
      </button>
    </div>

    <!-- 移动端菜单面板 -->
    <transition name="slide-transition">
      <div
        v-show="mobileMenuOpen"
        id="mobile-menu"
        class="ghibli-header__mobile-menu"
        role="dialog"
        aria-modal="true"
        aria-label="移动端导航菜单"
      >
        <div class="ghibli-header__mobile-bg" aria-hidden="true">
          <div class="ghibli-header__mobile-grass"></div>
        </div>

        <nav class="ghibli-header__mobile-nav">
          <ul class="ghibli-header__mobile-nav-list">
            <li v-for="item in navItems" :key="item.path" class="ghibli-header__mobile-nav-item">
              <router-link
                :to="item.path"
                class="ghibli-header__mobile-nav-link"
                :class="{ 'ghibli-header__mobile-nav-link--active': item.active }"
                @click="navigateTo(item.path)"
              >
                <span>{{ item.name }}</span>
              </router-link>
            </li>
          </ul>

          <!-- 移动端用户操作 -->
          <div class="ghibli-header__mobile-user" v-if="isLoggedIn">
            <div class="ghibli-header__mobile-user-info">
              <div class="ghibli-avatar ghibli-avatar--md ghibli-header__mobile-user-avatar" :style="{ background: userInfo?.avatar ? 'none' : 'linear-gradient(135deg, var(--ghibli-sky-400), var(--ghibli-forest-400))' }">
                <img v-if="userInfo?.avatar" :src="userInfo.avatar" :alt="userInfo.nickname" />
                <span v-else class="ghibli-avatar__text">{{ getAvatarInitial(userInfo?.nickname) }}</span>
              </div>
              <div class="ghibli-header__mobile-user-details">
                <span class="ghibli-header__mobile-user-name">{{ userInfo?.nickname }}</span>
                <span class="ghibli-header__mobile-user-username">@{{ userInfo?.username }}</span>
              </div>
            </div>
            <router-link
              to="/profile"
              class="ghibli-header__mobile-nav-link"
              @click="goProfile"
            >
              <svg class="ghibli-header__mobile-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              个人中心
            </router-link>
            <button
              class="ghibli-header__mobile-nav-link ghibli-header__mobile-nav-link--danger"
              @click="handleLogout"
            >
              <svg class="ghibli-header__mobile-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              退出登录
            </button>
          </div>

          <div class="ghibli-header__mobile-auth" v-else>
            <button
              class="ghibli-header__mobile-nav-link ghibli-header__mobile-nav-link--primary"
              @click="goLogin"
            >
              <svg class="ghibli-header__mobile-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                <polyline points="10 17 15 12 10 7"/>
                <line x1="15" y1="12" x2="3" y2="12"/>
              </svg>
              登录
            </button>
            <button
              class="ghibli-header__mobile-nav-link ghibli-header__mobile-nav-link--primary"
              @click="goRegister"
            >
              <svg class="ghibli-header__mobile-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="8.5" cy="7" r="4"/>
                <line x1="20" y1="8" x2="20" y2="14"/>
                <line x1="23" y1="11" x2="17" y2="11"/>
              </svg>
              注册
            </button>
          </div>
        </nav>
      </div>
    </transition>

    <!-- 底部分割线装饰 -->
    <div class="ghibli-header__divider" aria-hidden="true">
      <svg viewBox="0 0 100 4" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0 2 Q25 0 50 2 T100 2" stroke="var(--ghibli-sky-300)" stroke-width="1.5" opacity="0.5">
          <animate attributeName="d" values="M0 2 Q25 0 50 2 T100 2; M0 2 Q25 4 50 2 T100 2; M0 2 Q25 0 50 2 T100 2" dur="4s" repeatCount="indefinite"/>
        </path>
      </svg>
    </div>
  </header>
</template>

<style scoped>
/* ===== 导航栏容器 ===== */
.ghibli-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-fixed);
  height: 72px;
  background: rgba(250, 250, 246, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--color-border);
  transition: all var(--duration-normal) var(--ease-gentle);
  transform: translateY(0);
}

.ghibli-header--entered {
  animation: slideDown var(--duration-slow) var(--ease-spring);
}

.ghibli-header--hidden {
  transform: translateY(-100%);
}

.ghibli-header--scrolled {
  height: 68px;
  background: rgba(250, 250, 246, 0.95);
  box-shadow: var(--shadow-md);
  border-bottom-color: var(--ghibli-sky-200);
}

.ghibli-header__container {
  max-width: var(--container-2xl);
  margin: 0 auto;
  padding: 0 var(--space-6);
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  position: relative;
  z-index: 2;
}

/* ===== 背景装饰层 ===== */
.ghibli-header__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.ghibli-header__clouds {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
}

.ghibli-header__cloud {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0.4) 100%);
  filter: blur(1px);
  opacity: 0.5;
  animation: cloudDrift linear infinite;
}

.ghibli-header__cloud::before,
.ghibli-header__cloud::after {
  content: '';
  position: absolute;
  background: inherit;
  border-radius: 50%;
  filter: inherit;
}

.cloud-1 {
  width: 80px;
  height: 40px;
  top: 10%;
  left: -100px;
  animation-duration: 80s;
}
.cloud-1::before { width: 35px; height: 35px; top: -18px; left: 12px; }
.cloud-1::after { width: 28px; height: 28px; top: -10px; right: 6px; }

.cloud-2 {
  width: 100px;
  height: 50px;
  top: 30%;
  right: -120px;
  animation-duration: 100s;
  animation-direction: reverse;
}
.cloud-2::before { width: 40px; height: 40px; top: -20px; left: 20px; }
.cloud-2::after { width: 32px; height: 32px; top: -12px; right: 10px; }

.cloud-3 {
  width: 70px;
  height: 35px;
  bottom: 15%;
  left: -90px;
  animation-duration: 70s;
}
.cloud-3::before { width: 30px; height: 30px; top: -15px; left: 10px; }
.cloud-3::after { width: 25px; height: 25px; top: -8px; right: 5px; }

@keyframes cloudDrift {
  from { transform: translateX(0); }
  to { transform: translateX(calc(100vw + 200px)); }
}

.ghibli-header__birds {
  position: absolute;
  inset: 0;
}

.ghibli-header__bird {
  position: absolute;
  width: 16px;
  height: 16px;
  animation: birdFly 6s ease-in-out infinite;
}

.ghibli-header__bird::before,
.ghibli-header__bird::after {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  border-top: 1.5px solid var(--ghibli-ink-400);
  border-right: 1.5px solid var(--ghibli-ink-400);
  border-radius: 0 100% 0 0;
  transform-origin: bottom left;
  opacity: 0.4;
}

.ghibli-header__bird::before {
  left: 0;
  bottom: 0;
  transform: rotate(-45deg);
}

.ghibli-header__bird::after {
  right: 0;
  bottom: 0;
  transform: rotate(45deg) scaleX(-1);
  border-right: none;
  border-left: 1.5px solid var(--ghibli-ink-400);
  border-radius: 100% 0 0 0;
  transform-origin: bottom right;
}

.bird-1 { top: 15%; left: 8%; animation-duration: 8s; animation-delay: 0s; }
.bird-2 { top: 25%; right: 10%; animation-duration: 10s; animation-delay: -2s; }
.bird-3 { top: 10%; left: 55%; animation-duration: 7s; animation-delay: -4s; }

@keyframes birdFly {
  0%, 100% { transform: translateX(0) translateY(0) scale(1); }
  25% { transform: translateX(20px) translateY(-10px) scale(1.1); }
  50% { transform: translateX(40px) translateY(3px) scale(0.9); }
  75% { transform: translateX(20px) translateY(6px) scale(1.05); }
}

/* 飞艇 */
.ghibli-header__airship {
  position: absolute;
  top: 5%;
  right: 5%;
  width: 140px;
  height: 70px;
  opacity: 0.4;
  animation: airshipFloat 15s ease-in-out infinite;
}

@keyframes airshipFloat {
  0%, 100% { transform: translateY(0) translateX(0); }
  25% { transform: translateY(-8px) translateX(4px); }
  50% { transform: translateY(4px) translateX(-2px); }
  75% { transform: translateY(-4px) translateX(2px); }
}

/* ===== Logo ===== */
.ghibli-logo {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  text-decoration: none;
  color: inherit;
  transition: transform var(--duration-fast) var(--ease-spring);
}

.ghibli-logo:hover {
  transform: scale(1.03);
}

.ghibli-logo:focus-visible {
  outline: none;
  border-radius: var(--radius-lg);
  box-shadow: var(--focus-ring);
}

.ghibli-logo__icon {
  width: 44px;
  height: 44px;
  color: var(--ghibli-warm-500);
  filter: drop-shadow(0 2px 8px rgba(212, 138, 58, 0.3));
}

.ghibli-logo__text {
  display: flex;
  flex-direction: column;
  line-height: 1;
}

.ghibli-logo__main {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  letter-spacing: 0.04em;
  background: linear-gradient(135deg, var(--ghibli-ink-700) 0%, var(--ghibli-sky-500) 50%, var(--ghibli-forest-500) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.ghibli-logo__sub {
  font-family: var(--font-handwriting);
  font-size: var(--text-xs);
  color: var(--ghibli-sky-600);
  letter-spacing: 0.2em;
  margin-top: 2px;
  opacity: 0.9;
}

/* ===== 导航菜单 ===== */
.ghibli-header__nav {
  flex: 1;
  display: flex;
  justify-content: center;
}

.ghibli-header__nav-list {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  margin: 0;
  padding: 0;
}

.ghibli-header__nav-item {
  position: relative;
}

.ghibli-header__nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-5);
  color: var(--color-text-muted);
  text-decoration: none;
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  border-radius: var(--radius-xl);
  transition: var(--transition-gentle);
  position: relative;
  overflow: hidden;
}

.ghibli-header__nav-link::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--ghibli-sky-100) 0%, var(--ghibli-forest-100) 100%);
  opacity: 0;
  transform: scaleY(0);
  transform-origin: bottom;
  transition: var(--transition-normal);
  border-radius: var(--radius-xl);
  z-index: -1;
}

.ghibli-header__nav-link:hover {
  color: var(--ghibli-sky-700);
}

.ghibli-header__nav-link:hover::before {
  opacity: 1;
  transform: scaleY(1);
}

.ghibli-header__nav-link--active {
  color: var(--ghibli-sky-600);
  font-weight: var(--font-semibold);
}

.ghibli-header__nav-link--active::before {
  opacity: 1;
  transform: scaleY(1);
}

.ghibli-header__nav-link:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.ghibli-header__nav-text {
  position: relative;
  z-index: 1;
}

.ghibli-header__nav-indicator {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  width: 24px;
  height: 3px;
  background: linear-gradient(90deg, var(--ghibli-sky-400), var(--ghibli-forest-400), var(--ghibli-sun-400));
  border-radius: 2px;
  transition: transform var(--duration-normal) var(--ease-spring);
  z-index: 1;
}

.ghibli-header__nav-link--active .ghibli-header__nav-indicator,
.ghibli-header__nav-link:hover .ghibli-header__nav-indicator {
  transform: translateX(-50%) scaleX(1);
}

/* ===== 用户操作区域 ===== */
.ghibli-header__actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* 认证按钮 */
.ghibli-header__auth-buttons {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* 用户下拉菜单触发器 */
.ghibli-header__user-trigger {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-4) var(--space-1) var(--space-2);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: var(--transition-gentle);
  box-shadow: var(--shadow-xs);
}

.ghibli-header__user-trigger:hover {
  border-color: var(--ghibli-sky-300);
  box-shadow: var(--shadow-sm);
  background: var(--ghibli-sky-50);
}

.ghibli-header__user-trigger:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring), var(--shadow-md);
}

.ghibli-header__user-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  object-fit: cover;
  border: 2px solid var(--color-border);
  transition: border-color var(--duration-fast) var(--ease-gentle);
}

.ghibli-header__user-trigger:hover .ghibli-header__user-avatar {
  border-color: var(--ghibli-sky-400);
}

.ghibli-avatar__text {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: var(--font-bold);
  color: var(--ghibli-paper-50);
}

.ghibli-header__user-name {
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ghibli-header__user-chevron {
  width: 16px;
  height: 16px;
  color: var(--color-text-muted);
  transition: transform var(--duration-fast) var(--ease-spring);
}

.ghibli-dropdown__trigger[aria-expanded="true"] .ghibli-header__user-chevron {
  transform: rotate(180deg);
}

/* 下拉菜单 */
.ghibli-header__user-dropdown {
  min-width: 180px;
  padding: var(--space-2);
}

.ghibli-header__user-dropdown .ghibli-dropdown__icon {
  color: var(--color-text-muted);
}

.ghibli-header__user-dropdown .ghibli-dropdown__item:hover .ghibli-dropdown__icon {
  color: var(--ghibli-sky-600);
}

.ghibli-header__user-dropdown .ghibli-dropdown__item--danger:hover .ghibli-dropdown__icon {
  color: var(--color-error);
}

/* ===== 移动端菜单按钮 ===== */
.ghibli-header__mobile-toggle {
  display: none;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 44px;
  height: 44px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: var(--transition-gentle);
  box-shadow: var(--shadow-xs);
}

.ghibli-header__mobile-toggle:hover {
  border-color: var(--ghibli-sky-300);
  background: var(--ghibli-sky-50);
  box-shadow: var(--shadow-sm);
}

.ghibli-header__mobile-toggle:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring), var(--shadow-md);
}

.ghibli-header__hamburger {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 22px;
  transition: transform var(--duration-normal) var(--ease-spring);
}

.ghibli-header__hamburger-line {
  display: block;
  width: 100%;
  height: 2px;
  background: var(--color-text);
  border-radius: 1px;
  transition: var(--duration-normal) var(--ease-spring);
  transform-origin: center;
}

.ghibli-header__mobile-toggle[aria-expanded="true"] .ghibli-header__hamburger-line:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
  background: var(--ghibli-sky-500);
}

.ghibli-header__mobile-toggle[aria-expanded="true"] .ghibli-header__hamburger-line:nth-child(2) {
  opacity: 0;
}

.ghibli-header__mobile-toggle[aria-expanded="true"] .ghibli-header__hamburger-line:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
  background: var(--ghibli-sky-500);
}

/* ===== 移动端菜单面板 ===== */
.ghibli-header__mobile-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

.ghibli-header__mobile-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: linear-gradient(180deg, var(--ghibli-sky-50) 0%, var(--ghibli-paper-50) 100%);
}

.ghibli-header__mobile-grass {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: linear-gradient(0deg, var(--ghibli-forest-200) 0%, transparent 100%);
  opacity: 0.3;
}

.ghibli-header__mobile-nav {
  position: relative;
  z-index: 1;
  padding: var(--space-6) var(--space-4) var(--space-8);
}

.ghibli-header__mobile-nav-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: 0 0 var(--space-6);
  padding: 0;
}

.ghibli-header__mobile-nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  color: var(--color-text);
  text-decoration: none;
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-medium);
  border-radius: var(--radius-xl);
  transition: var(--transition-spring);
  border-left: 4px solid transparent;
  background: var(--color-bg-card);
  box-shadow: var(--shadow-xs);
}

.ghibli-header__mobile-nav-link:hover,
.ghibli-header__mobile-nav-link--active {
  background: var(--ghibli-sky-50);
  color: var(--ghibli-sky-700);
  border-left-color: var(--ghibli-sky-400);
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}

.ghibli-header__mobile-nav-link--active {
  font-weight: var(--font-semibold);
}

.ghibli-header__mobile-nav-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  color: var(--color-text-muted);
  transition: var(--duration-fast) var(--ease-gentle);
}

.ghibli-header__mobile-nav-link:hover .ghibli-header__mobile-nav-icon {
  color: var(--ghibli-sky-500);
}

/* 移动端用户区域 */
.ghibli-header__mobile-user {
  padding: var(--space-4) 0;
  border-top: 1px solid var(--color-divider);
  border-bottom: 1px solid var(--color-divider);
  margin: var(--space-4) 0;
}

.ghibli-header__mobile-user-info {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  margin: calc(var(--space-4) * -1);
  background: linear-gradient(135deg, var(--ghibli-sky-50), var(--ghibli-forest-50));
  border-radius: var(--radius-xl);
}

.ghibli-header__mobile-user-avatar {
  width: 56px;
  height: 56px;
  border: 3px solid var(--ghibli-paper-100);
  box-shadow: var(--shadow-md);
}

.ghibli-header__mobile-user-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.ghibli-header__mobile-user-name {
  font-weight: var(--font-semibold);
  color: var(--color-text);
  font-size: var(--text-lg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ghibli-header__mobile-user-username {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

/* 移动端认证按钮 */
.ghibli-header__mobile-auth {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-2) 0;
}

.ghibli-header__mobile-nav-link--primary {
  background: linear-gradient(135deg, var(--ghibli-sky-400), var(--ghibli-sky-600)) !important;
  color: white !important;
  border-left-color: var(--ghibli-sun-400) !important;
  box-shadow: var(--shadow-primary);
}

.ghibli-header__mobile-nav-link--primary:hover {
  transform: translateX(6px);
  box-shadow: var(--shadow-primary), 0 8px 24px rgba(14, 165, 233, 0.35);
}

.ghibli-header__mobile-nav-link--danger {
  color: var(--color-error);
  border-left-color: var(--color-error);
}

.ghibli-header__mobile-nav-link--danger:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.ghibli-header__mobile-nav-link--danger .ghibli-header__mobile-nav-icon {
  color: var(--color-error);
}

/* ===== 底部分割线 ===== */
.ghibli-header__divider {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  overflow: hidden;
}

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .ghibli-header__nav {
    display: none;
  }
}

@media (max-width: 768px) {
  .ghibli-header {
    height: 64px;
  }

  .ghibli-header--scrolled {
    height: 60px;
  }

  .ghibli-header__container {
    padding: 0 var(--space-4);
  }

  .ghibli-logo__main {
    font-size: var(--text-lg);
  }

  .ghibli-logo__sub {
    font-size: 0.6rem;
  }

  .ghibli-logo__icon {
    width: 38px;
    height: 38px;
  }

  .ghibli-header__mobile-toggle {
    display: flex;
  }

  .ghibli-header__actions {
    display: none;
  }

  .ghibli-header__user-name {
    display: none;
  }

  .ghibli-header__user-trigger {
    padding: var(--space-1);
  }
}

@media (max-width: 480px) {
  .ghibli-header__container {
    padding: 0 var(--space-3);
  }

  .ghibli-logo__text {
    display: none;
  }

  .ghibli-logo__icon {
    width: 36px;
    height: 36px;
  }
}

/* ===== 减少动画偏好 ===== */
@media (prefers-reduced-motion: reduce) {
  .ghibli-header,
  .ghibli-header__cloud,
  .ghibli-header__bird,
  .ghibli-header__airship,
  .ghibli-logo__icon,
  .ghibli-header__nav-link::before,
  .ghibli-header__nav-indicator,
  .ghibli-header__hamburger-line,
  .ghibli-header__user-avatar,
  .ghibli-header__user-chevron,
  .ghibli-header__user-dropdown,
  .ghibli-header__mobile-nav-link,
  .ghibli-header__mobile-nav-icon,
  .ghibli-header__divider path {
    animation: none !important;
    transition: none !important;
  }

  .ghibli-header--entered {
    animation: none;
  }
}

/* ===== 高对比度模式 ===== */
@media (prefers-contrast: high) {
  .ghibli-header {
    border-bottom-width: 2px;
    border-bottom-color: var(--color-text);
  }

  .ghibli-header__nav-link {
    border: 2px solid transparent;
  }

  .ghibli-header__nav-link:hover,
  .ghibli-header__nav-link--active {
    border-color: var(--ghibli-sky-500);
  }

  .ghibli-header__user-trigger {
    border-width: 2px;
  }

  .ghibli-header__mobile-nav-link {
    border-width: 2px;
  }
}
</style>