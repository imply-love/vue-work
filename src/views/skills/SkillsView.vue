<script setup>
// 占位页：资源分享板块尚未实现，先保证导航可访问，后续接入真实数据后替换本页内容
const plans = [
  { title: '资源分类', desc: '按番剧、类型与清晰度整理的资源合集' },
  { title: '收藏与笔记', desc: '收藏好用的资源，随手记下自己的观看笔记' },
  { title: '分享者榜', desc: '把资源无私分享出来的同好，都会记在这里' },
]
</script>

<template>
  <section class="ghibli-section" aria-labelledby="skills-title">
    <header class="ghibli-section__header">
      <h1 id="skills-title" class="ghibli-section__title">资源分享</h1>
      <p class="ghibli-section__desc">高清资源、字幕组、周边情报，同好们的好东西都放在这儿</p>
    </header>

    <div class="ghibli-section__content">
      <div class="ghibli-empty">
        <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        <h2 class="ghibli-empty__title">敬请期待</h2>
        <p class="ghibli-empty__desc">「资源分享」正在整理中，先到首页看看大家最近的安利吧</p>
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