<script setup>
const plans = [
  { title: '站点缘起', desc: '为什么做「番剧同好会」，以及这个名字的来历' },
  { title: '技术栈', desc: '前端 Vue 3 + Layui Vue，后端 Flask + MySQL，逐步开源' },
  { title: '反馈与共建', desc: '把遇到的问题和想法告诉我们，一起把这个同好会办得更好' },
]
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero">
      <h1 class="page-title">关于我们</h1>
      <p class="page-sub">追番、安利、找同好。这里是一个安静又热闹的二次元角落。</p>
    </section>

    <div class="about-grid">
      <lay-card v-for="plan in plans" :key="plan.title">
        <div class="about-card">
          <lay-tag type="primary" variant="light">规划中</lay-tag>
          <h3>{{ plan.title }}</h3>
          <p class="muted">{{ plan.desc }}</p>
        </div>
      </lay-card>
    </div>

    <div class="about-actions">
      <lay-button type="primary" @click="$router.push('/')">返回首页</lay-button>
    </div>
  </div>
</template>

<style scoped>
.about-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-6);
}

.about-card h3 {
  font-family: var(--font-display);
  margin: var(--space-4) 0 var(--space-2);
}

.about-card p {
  margin: 0;
  line-height: var(--leading-relaxed);
}

.about-actions {
  margin-top: var(--space-8);
  text-align: center;
}
</style>
