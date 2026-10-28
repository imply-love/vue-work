<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="page-wrap">
    <lay-card>
      <div class="empty-box">
        <div class="not-found__code">404</div>
        <h1 class="empty-box__title">这个页面掉进异次元了</h1>
        <p>链接可能已经失效，或者它被传送到了别的次元，先回首页继续追番吧。</p>
        <lay-button type="primary" @click="router.push('/')">回到首页</lay-button>
      </div>
    </lay-card>
  </div>
</template>

<style scoped>
.not-found__code {
  font-family: var(--font-display);
  font-size: var(--text-6xl);
  font-weight: var(--font-bold);
  line-height: 1;
  background: linear-gradient(135deg, var(--ghibli-sky-500), var(--ghibli-sakura-500), var(--ghibli-sun-400));
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
