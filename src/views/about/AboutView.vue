<script setup>
// 占位页：关于我们板块尚未实现，先保证导航可访问，后续补充正式内容
const plans = [
  { title: '站点缘起', desc: '为什么做「番剧同好会」，以及这个名字的来历' },
  { title: '技术栈', desc: '前端 Vue 3 + Vite，后端 Flask + MySQL，逐步开源' },
  { title: '反馈与共建', desc: '把遇到的问题和想法告诉我们，一起把这个同好会办得更好' },
]
</script>

<template>
  <section class="ghibli-section" aria-labelledby="about-title">
    <header class="ghibli-section__header">
      <h1 id="about-title" class="ghibli-section__title">关于我们</h1>
      <p class="ghibli-section__desc">追番、安利、找同好</p>
    </header>

    <div class="ghibli-section__content">
      <div class="ghibli-empty">
        <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <h2 class="ghibli-empty__title">敬请期待</h2>
        <p class="ghibli-empty__desc">这里将写下「番剧同好会」的来龙去脉，目前先到首页逛逛吧</p>
        <router-link class="ghibli-btn ghibli-btn--primary" to="/">返回首页</router-link>
      </div>

      <ul class="page-plan ghibli-cards">
        <li v-for="plan in plans" :key="plan.title" class="ghibli-card ghibli-card--outlined">
          <div class="ghibli-card__content">
            <span class="ghibli-badge ghibli-badge--outline">规划中</span>
            <h3 class="page-plan__title">{{ plan.title }}</h3>
            <p class="page-plan__desc">{{ plan.desc }}</p>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.page-plan {
  margin: var(--space-12) 0 0;
  padding: 0;
  list-style: none;
}

.page-plan__title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: var(--space-4) 0 var(--space-2);
}

.page-plan__desc {
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
  margin: 0;
}
</style>