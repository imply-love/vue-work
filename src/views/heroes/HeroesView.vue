<script setup>
// 占位页：番剧库板块尚未实现，先保证导航可访问，后续接入真实数据后替换本页内容
const plans = [
  { title: '番剧资料页', desc: '收录番剧信息、播出季度、制作公司与主要角色' },
  { title: '追番清单', desc: '标记「在看 / 想看 / 看完」，进度一目了然' },
  { title: '评分与短评', desc: '给看过的番打个分，一条短评留住当时的心情' },
]
</script>

<template>
  <section class="ghibli-section" aria-labelledby="heroes-title">
    <header class="ghibli-section__header">
      <h1 id="heroes-title" class="ghibli-section__title">番剧库</h1>
      <p class="ghibli-section__desc">从当季新番到经典老番，你的追番清单就从这里开始</p>
    </header>

    <div class="ghibli-section__content">
      <div class="ghibli-empty">
        <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
          <rect x="2" y="7" width="20" height="14" rx="2"/>
          <polyline points="17 2 12 7 7 2"/>
          <path d="M10 12.5 L15 15 L10 17.5 Z"/>
        </svg>
        <h2 class="ghibli-empty__title">敬请期待</h2>
        <p class="ghibli-empty__desc">「番剧库」正在建档中，先到首页看看大家在聊什么番吧</p>
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