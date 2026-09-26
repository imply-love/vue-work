<script setup>
import { onMounted, onUnmounted } from 'vue'
import Head from './views/head.vue'

// 页面加载进度条
const loadProgress = ref(0)
let progressTimer = null

onMounted(() => {
  // 模拟页面加载进度
  progressTimer = setInterval(() => {
    loadProgress.value += Math.random() * 15
    if (loadProgress.value >= 90) {
      clearInterval(progressTimer)
    }
  }, 100)

  // 页面完全加载后完成进度条
  window.addEventListener('load', () => {
    if (progressTimer) clearInterval(progressTimer)
    loadProgress.value = 100
    setTimeout(() => {
      loadProgress.value = 0
    }, 500)
  })
})

onUnmounted(() => {
  if (progressTimer) clearInterval(progressTimer)
})
</script>

<template>
  <div id="app" class="ghibli-app">
    <!-- 页面加载进度条 -->
    <transition name="ghibli-load-bar">
      <div
        v-if="loadProgress > 0 && loadProgress < 100"
        class="ghibli-load-bar ghibli-load-bar--active"
        :style="{ transform: `scaleX(${loadProgress / 100})` }"
        aria-hidden="true"
      ></div>
    </transition>

    <!-- 全局背景装饰 -->
    <div class="ghibli-app__bg" aria-hidden="true">
      <!-- 远景山脉 -->
      <svg class="ghibli-app__mountains" viewBox="0 0 1440 200" preserveAspectRatio="none">
        <path
          d="M0,180 C200,120 400,160 720,140 C1040,120 1240,150 1440,130 L1440,200 L0,200 Z"
          fill="var(--ghibli-sky-200)"
          opacity="0.4"
        />
        <path
          d="M0,190 C250,140 500,170 720,150 C940,130 1200,160 1440,140 L1440,200 L0,200 Z"
          fill="var(--ghibli-sky-300)"
          opacity="0.3"
        />
      </svg>

      <!-- 飞行粒子 -->
      <div class="ghibli-app__particles" ref="particlesContainer"></div>
    </div>

    <Head />

    <main class="ghibli-app__main" role="main">
      <router-view v-slot="{ Component }">
        <transition name="page-transition" mode="out-in">
          <component :is="Component" class="page-enter" />
        </transition>
      </router-view>
    </main>

    <footer class="ghibli-app__footer" role="contentinfo">
      <div class="ghibli-app__footer-content">
        <div class="ghibli-app__footer-decor" aria-hidden="true">
          <svg viewBox="0 0 200 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 10 Q50 0 100 10 T200 10" stroke="var(--ghibli-sky-300)" stroke-width="1.5" opacity="0.5">
              <animate attributeName="d" values="M0 10 Q50 0 100 10 T200 10; M0 10 Q50 20 100 10 T200 10; M0 10 Q50 0 100 10 T200 10" dur="6s" repeatCount="indefinite"/>
            </path>
          </svg>
        </div>
        <p class="ghibli-app__footer-copyright">
          <span class="ghibli-text-gradient-warm">云墨江湖</span> ·
          <span class="ghibli-font-handwriting">一笔云墨，绘尽江湖梦</span>
        </p>
        <p class="ghibli-app__footer-tagline">
          愿风指引你的方向，愿阳光温暖你的旅程 🍃
        </p>
      </div>
    </footer>

    <!-- 全局吐司容器 -->
    <Teleport to="body">
      <div class="ghibli-toast" ref="toastContainer" aria-live="polite" aria-atomic="true"></div>
    </Teleport>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  setup() {
    const loadProgress = ref(0)
    const particlesContainer = ref(null)
    const toastContainer = ref(null)

    // 创建飞行粒子
    const createParticles = () => {
      if (!particlesContainer.value) return

      for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div')
        particle.className = 'ghibli-app__particle'
        particle.style.cssText = `
          --tx: ${(Math.random() - 0.5) * 200}px;
          --ty: ${-Math.random() * 100}px;
          left: ${Math.random() * 100}%;
          top: ${80 + Math.random() * 20}%;
          animation-delay: ${Math.random() * 8}s;
          animation-duration: ${10 + Math.random() * 10}s;
          background: ${['var(--ghibli-sun-300)', 'var(--ghibli-sky-300)', 'var(--ghibli-forest-300)', 'var(--ghibli-sakura-300)'][Math.floor(Math.random() * 4)]};
        `
        particlesContainer.value.appendChild(particle)
      }
    }

    // 显示吐司
    const showToast = (options) => {
      if (!toastContainer.value) return

      const toast = document.createElement('div')
      toast.className = `ghibli-toast__item ghibli-toast__item--${options.type || 'info'}`
      toast.innerHTML = `
        <svg class="ghibli-toast__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          ${options.type === 'success' ? '<polyline points="20 6 9 17 4 12"/>' : ''}
          ${options.type === 'error' ? '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>' : ''}
          ${options.type === 'warning' ? '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>' : ''}
          ${options.type === 'info' ? '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>' : ''}
        </svg>
        <div class="ghibli-toast__content">
          ${options.title ? `<div class="ghibli-toast__title">${options.title}</div>` : ''}
          ${options.message ? `<div class="ghibli-toast__message">${options.message}</div>` : ''}
        </div>
        <button class="ghibli-toast__close" aria-label="关闭">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      `

      toast.querySelector('.ghibli-toast__close')?.addEventListener('click', () => {
        toast.style.animation = 'toastEnter 0.2s var(--ease-gentle) reverse forwards'
        setTimeout(() => toast.remove(), 200)
      })

      toastContainer.value.appendChild(toast)

      // 自动移除
      setTimeout(() => {
        if (toast.parentNode) {
          toast.style.animation = 'toastEnter 0.3s var(--ease-gentle) reverse forwards'
          setTimeout(() => toast.remove(), 300)
        }
      }, options.duration || 4000)
    }

    // 暴露给全局
    window.$ghibli = { showToast, createParticles }

    return { loadProgress, particlesContainer, toastContainer }
  }
}
</script>

<style>
/* ===== 应用根容器 ===== */
.ghibli-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  background: var(--color-bg);
}

/* ===== 全局背景装饰 ===== */
.ghibli-app__bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  overflow: hidden;
}

.ghibli-app__mountains {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 200px;
}

.ghibli-app__particles {
  position: absolute;
  inset: 0;
}

.ghibli-app__particle {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  box-shadow: 0 0 8px 2px currentColor;
  animation: particleFloat linear infinite;
  opacity: 0;
  will-change: transform, opacity;
}

@keyframes particleFloat {
  0% {
    transform: translateY(0) translateX(0) scale(1);
    opacity: 0;
  }
  10% { opacity: 0.8; }
  100% {
    transform: translateY(-120vh) translateX(var(--tx, 0)) scale(0);
    opacity: 0;
  }
}

/* ===== 主内容区 ===== */
.ghibli-app__main {
  flex: 1;
  width: 100%;
  padding-top: 72px;
  position: relative;
  z-index: 1;
}

@media (max-width: 768px) {
  .ghibli-app__main {
    padding-top: 64px;
  }
}

/* ===== 页脚 ===== */
.ghibli-app__footer {
  background: linear-gradient(180deg, var(--ghibli-paper-100) 0%, var(--ghibli-warm-50) 100%);
  border-top: 1px solid var(--color-divider);
  padding: var(--space-10) 0 var(--space-6);
  margin-top: auto;
  position: relative;
  z-index: 1;
}

.ghibli-app__footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--ghibli-sky-300), var(--ghibli-forest-300), var(--ghibli-sun-300), transparent);
}

.ghibli-app__footer-content {
  max-width: var(--container-2xl);
  margin: 0 auto;
  padding: 0 var(--space-6);
  text-align: center;
}

.ghibli-app__footer-decor {
  margin-bottom: var(--space-4);
  opacity: 0.6;
}

.ghibli-app__footer-copyright {
  font-family: var(--font-display);
  font-size: var(--text-base);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
  font-weight: var(--font-medium);
}

.ghibli-app__footer-tagline {
  font-family: var(--font-handwriting);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0;
  opacity: 0.8;
}

/* ===== 加载进度条 ===== */
.ghibli-load-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--ghibli-sky-400), var(--ghibli-forest-400), var(--ghibli-sun-400), var(--ghibli-warm-400), var(--ghibli-sakura-400));
  background-size: 200% 100%;
  animation: loadBarShine 1.5s ease-in-out infinite;
  border-radius: 0 0 var(--radius-full) 0;
  transform-origin: left center;
  transform: scaleX(0);
  z-index: 9999;
  transition: transform var(--duration-normal) var(--ease-gentle);
}

@keyframes loadBarShine {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.ghibli-load-bar--active {
  transform: scaleX(1);
}

/* 进度条转场 */
.ghibli-load-bar-enter-active,
.ghibli-load-bar-leave-active {
  transition: opacity var(--duration-fast) var(--ease-gentle), transform var(--duration-fast) var(--ease-gentle);
}

.ghibli-load-bar-enter-from,
.ghibli-load-bar-leave-to {
  opacity: 0;
  transform: scaleX(0);
}

/* ===== 页面转场 ===== */
.page-transition-enter-active,
.page-transition-leave-active {
  transition: all var(--duration-slow) var(--ease-gentle);
}

.page-transition-enter-from,
.page-transition-leave-to {
  opacity: 0;
  transform: translateX(20px);
  filter: blur(4px);
}

.page-enter {
  animation: pageEnter var(--duration-slower) var(--ease-gentle) forwards;
}

@keyframes pageEnter {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.99);
    filter: blur(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

/* ===== 吐司容器 ===== */
.ghibli-toast {
  position: fixed;
  bottom: var(--space-6);
  right: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  z-index: var(--z-toast);
  pointer-events: none;
  max-width: 400px;
}

@media (max-width: 480px) {
  .ghibli-toast {
    left: var(--space-4);
    right: var(--space-4);
    bottom: var(--space-4);
    max-width: none;
  }
}

/* ===== 滚动条 ===== */
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: var(--ghibli-paper-100);
  border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--ghibli-sky-300), var(--ghibli-forest-300), var(--ghibli-sun-300));
  border-radius: var(--radius-full);
  border: 2px solid var(--ghibli-paper-100);
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, var(--ghibli-sky-400), var(--ghibli-forest-400), var(--ghibli-sun-400));
}

* {
  scrollbar-width: thin;
  scrollbar-color: var(--ghibli-sky-400) var(--ghibli-paper-100);
}

/* ===== 选择文本 ===== */
::selection {
  background: var(--ghibli-sky-200);
  color: var(--ghibli-ink-800);
}

/* ===== 焦点可见 ===== */
:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
  outline-offset: var(--focus-ring-offset);
}

/* ===== 减少动画偏好 ===== */
@media (prefers-reduced-motion: reduce) {
  .ghibli-app__particle,
  .ghibli-load-bar,
  .ghibli-app__footer-decor path,
  .page-enter {
    animation: none !important;
    transition: none !important;
  }

  .page-transition-enter-active,
  .page-transition-leave-active {
    transition: none;
  }

  .page-transition-enter-from,
  .ghibli-load-bar-enter-from {
    opacity: 1;
    transform: none;
    filter: none;
  }
}

/* ===== 打印样式 ===== */
@media print {
  .ghibli-app__bg,
  .ghibli-load-bar,
  .ghibli-toast {
    display: none !important;
  }

  .ghibli-app__main {
    padding-top: 0;
  }

  body {
    background: white !important;
    color: black !important;
  }
}
</style>