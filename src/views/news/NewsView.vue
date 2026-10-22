<script setup>
// 占位页：讨论区板块尚未实现，先保证导航可访问，后续接入真实数据后替换本页内容
const plans = [
  { title: '最新讨论流', desc: '按时间倒序展示全站帖子，支持按番剧、季度与标签筛选' },
  { title: '本周热帖榜', desc: '按浏览、点赞、回帖数排出的当周热门话题' },
  { title: '新番集中楼', desc: '每季新番各开一帖，弹幕式吐槽与剧情预测一次聊个够' },
]
</script>

<template>
  <section class="ghibli-section" aria-labelledby="news-title">
    <header class="ghibli-section__header">
      <h1 id="news-title" class="ghibli-section__title">讨论区</h1>
      <p class="ghibli-section__desc">新番吐槽、旧番安利、结局锐评，都来这里开一楼</p>
    </header>

    <div class="ghibli-section__content">
      <div class="ghibli-empty">
        <svg class="ghibli-empty__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <h2 class="ghibli-empty__title">敬请期待</h2>
        <p class="ghibli-empty__desc">「讨论区」正在装修中，先到首页看看大家已经开好的帖子吧</p>
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