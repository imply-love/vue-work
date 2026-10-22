<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<template>
  <div class="not-found-page">
    <div class="not-found-container">
      <svg class="not-found-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <h1 class="not-found-code">404</h1>
      <h2 class="not-found-title">这个页面掉进异次元了</h2>
      <p class="not-found-desc">链接可能已经失效，或者它被传送到了别的次元，先回首页继续追番吧</p>
      <button class="ghibli-btn ghibli-btn--primary ghibli-btn--lg" @click="goHome">
        <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        回到首页
      </button>
    </div>
  </div>
</template>

<style scoped>
.not-found-page {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-20) var(--space-6);
}

.not-found-container {
  text-align: center;
  max-width: 440px;
}

.not-found-icon {
  width: 80px;
  height: 80px;
  color: var(--ghibli-sakura-400);
  margin: 0 auto var(--space-6);
  filter: drop-shadow(0 4px 16px rgba(244, 114, 182, 0.35));
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 1; }
}

.not-found-code {
  font-family: var(--font-mono);
  font-size: var(--text-6xl);
  font-weight: var(--font-bold);
  line-height: 1;
  margin: 0 0 var(--space-4);
  letter-spacing: 0.1em;
  background: linear-gradient(135deg, var(--ghibli-sky-500) 0%, var(--ghibli-sakura-500) 50%, var(--ghibli-sun-400) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.not-found-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-4);
}

.not-found-desc {
  color: var(--color-text-muted);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  margin: 0 0 var(--space-12);
}

/* 响应式 */
@media (max-width: 480px) {
  .not-found-page {
    padding: var(--space-16) var(--space-4);
  }

  .not-found-code {
    font-size: var(--text-5xl);
  }

  .not-found-title {
    font-size: var(--text-xl);
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .not-found-icon {
    animation: none;
  }
}
</style>