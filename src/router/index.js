import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/home/HomeView.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { title: '登录', guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { title: '注册', guest: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/profile/ProfileView.vue'),
    meta: { title: '个人中心', requiresAuth: true },
  },
  {
    path: '/posts/:id',
    name: 'PostDetail',
    component: () => import('@/views/home/PostDetailView.vue'),
    meta: { title: '帖子详情' },
  },
  // 导航栏里的四个板块（当前为占位页，功能实现后替换对应页面即可）
  {
    path: '/news',
    name: 'News',
    component: () => import('@/views/news/NewsView.vue'),
    meta: { title: '讨论区' },
  },
  {
    path: '/heroes',
    name: 'Heroes',
    component: () => import('@/views/heroes/HeroesView.vue'),
    meta: { title: '番剧库' },
  },
  {
    path: '/skills',
    name: 'Skills',
    component: () => import('@/views/skills/SkillsView.vue'),
    meta: { title: '资源分享' },
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/about/AboutView.vue'),
    meta: { title: '关于我们' },
  },
  // 测试页面路由（仅管理员可见和使用）
  {
    path: '/test',
    name: 'TestDashboard',
    component: () => import('@/views/test/TestDashboard.vue'),
    meta: { title: '测试中心', requiresAdmin: true },
  },
  {
    path: '/test/api',
    name: 'TestAPI',
    component: () => import('@/views/test/TestAPI.vue'),
    meta: { title: 'API 接口测试', requiresAdmin: true },
  },
  {
    path: '/test/components',
    name: 'TestComponents',
    component: () => import('@/views/test/TestComponents.vue'),
    meta: { title: '组件视觉测试', requiresAdmin: true },
  },
  {
    path: '/test/responsive',
    name: 'TestResponsive',
    component: () => import('@/views/test/TestResponsive.vue'),
    meta: { title: '响应式测试', requiresAdmin: true },
  },
  {
    path: '/test/accessibility',
    name: 'TestAccessibility',
    component: () => import('@/views/test/TestAccessibility.vue'),
    meta: { title: '无障碍测试', requiresAdmin: true },
  },
  {
    path: '/test/e2e',
    name: 'TestE2E',
    component: () => import('@/views/test/TestE2E.vue'),
    meta: { title: '端到端测试', requiresAdmin: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '页面未找到' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  },
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  document.title = `${to.meta.title || '番剧同好会'} - 追番、安利、找同好`

  // 需要登录的页面
  if (to.meta.requiresAuth) {
    if (!authStore.isLoggedIn) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    // 可选：刷新用户资料
    await authStore.fetchProfile()
  }

  // 仅游客可访问的页面（登录、注册）
  if (to.meta.guest && authStore.isLoggedIn) {
    next({ name: 'Home' })
    return
  }

  // 仅管理员可访问的页面（测试中心）：未登录或非管理员一律回首页
  if (to.meta.requiresAdmin && (!authStore.isLoggedIn || !authStore.isAdmin)) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router