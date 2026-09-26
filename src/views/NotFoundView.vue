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
      <h2 class="not-found-title">页面迷路了</h2>
      <p class="not-found-desc">这条江湖小径似乎不存在，或是已被时光掩埋</p>
      <button class="btn btn-primary" @click="goHome">
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        返回江湖入口
      </button>
    </div>
  </div>
</template>

<style scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: #0d0d0d;
}

.not-found-container {
  text-align: center;
  max-width: 400px;
}

.not-found-icon {
  width: 80px;
  height: 80px;
  color: #c9a84c;
  margin-bottom: 24px;
  filter: drop-shadow(0 0 16px rgba(201, 168, 76, 0.4));
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 1; }
}

.not-found-code {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 6rem;
  font-weight: 700;
  color: #c9a84c;
  line-height: 1;
  margin: 0 0 16px;
  letter-spacing: 0.1em;
  text-shadow: 0 0 32px rgba(201, 168, 76, 0.3);
}

.not-found-title {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: 1.75rem;
  font-weight: 600;
  color: #e8e8e8;
  margin: 0 0 12px;
}

.not-found-desc {
  color: #999;
  font-size: 1rem;
  line-height: 1.6;
  margin: 0 0 32px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  border-radius: 50px;
  font-family: inherit;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  text-decoration: none;
}

.btn:focus-visible {
  outline: 2px solid #c9a84c;
  outline-offset: 3px;
}

.btn-primary {
  background: linear-gradient(135deg, #c9a84c 0%, #a68a3a 100%);
  color: #0d0d0d;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(201, 168, 76, 0.4);
}

.btn-icon {
  width: 20px;
  height: 20px;
}

/* 响应式 */
@media (max-width: 480px) {
  .not-found-code {
    font-size: 4rem;
  }

  .not-found-title {
    font-size: 1.5rem;
  }

  .btn {
    padding: 14px 24px;
    font-size: 0.9375rem;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .not-found-icon {
    animation: none;
  }

  .btn {
    transition: none;
  }
}
</style>