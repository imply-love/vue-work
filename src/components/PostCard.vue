<script setup>
import { computed } from 'vue'

const props = defineProps({
  post: { type: Object, required: true },
})
const emits = defineEmits(['click'])

const tagList = computed(() => {
  if (!props.post.tags) return []
  return props.post.tags
    .split(/[,，]/)
    .map((t) => t.trim())
    .filter(Boolean)
    .slice(0, 3)
})

const timeText = computed(() => {
  const raw = props.post.publish_time || props.post.create_time
  if (!raw) return ''
  const date = new Date(raw.replace(' ', 'T'))
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return raw.slice(0, 10)
})

const reviewTag = computed(() => {
  const map = { 1: ['推荐', 'recommend'], 2: ['已打回', 'reject'], 3: ['已封禁', 'ban'] }
  return map[props.post.review_status] || null
})

const visibilityTag = computed(() => {
  const map = { 1: ['私密', 'private'], 2: ['仅好友', 'friends'] }
  return map[props.post.visibility] || null
})

const avatarText = computed(() => (props.post.author_nickname || '番').charAt(0).toUpperCase())

const open = () => emits('click')
</script>

<template>
  <lay-card class="post-card" @click="open">
    <div class="post-card__top">
      <span class="avatar-circle post-card__avatar">{{ avatarText }}</span>
      <div class="post-card__author">
        <span class="post-card__name">{{ post.author_nickname || '匿名同好' }}</span>
        <span class="post-card__time">{{ timeText }}</span>
      </div>
      <div class="post-card__tags">
        <span v-if="reviewTag" class="status-tag" :class="`status-tag--${reviewTag[1]}`">{{ reviewTag[0] }}</span>
        <span v-if="visibilityTag" class="status-tag" :class="`status-tag--${visibilityTag[1]}`">
          {{ visibilityTag[0] }}
        </span>
      </div>
    </div>

    <h3 class="post-card__title">
      {{ post.title || '无标题' }}
      <span v-if="post.edit_label" class="post-card__edit">{{ post.edit_label }}</span>
    </h3>
    <p class="post-card__excerpt">{{ post.excerpt || post.summary || '这个同好还没有写摘要' }}</p>

    <div class="post-card__bottom">
      <span v-if="post.category" class="post-card__category">{{ post.category }}</span>
      <span v-for="tag in tagList" :key="tag" class="post-card__tag">#{{ tag }}</span>
      <span class="post-card__spacer"></span>
      <span class="post-card__stat">赞 {{ post.like_count || 0 }}</span>
      <span class="post-card__stat">评 {{ post.reply_count || 0 }}</span>
      <span class="post-card__stat">阅 {{ post.view_count || 0 }}</span>
    </div>
  </lay-card>
</template>

<style scoped>
.post-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: transform var(--duration-normal) var(--ease-gentle), box-shadow var(--duration-normal) var(--ease-gentle);
}

.post-card :deep(.layui-card-body) {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.post-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}

.post-card__top {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.post-card__avatar {
  width: 34px;
  height: 34px;
  font-size: var(--text-sm);
}

.post-card__author {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.post-card__name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.post-card__time {
  font-size: 11px;
  color: var(--color-text-muted);
}

.post-card__tags {
  margin-left: auto;
  display: flex;
  gap: var(--space-2);
}

.post-card__title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.post-card__edit {
  font-size: 11px;
  color: var(--ghibli-sakura-600);
  background: var(--ghibli-sakura-50);
  border-radius: var(--radius-full);
  padding: 1px var(--space-2);
}

.post-card__excerpt {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  margin: 0 0 var(--space-4);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-card__bottom {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: var(--space-3);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.post-card__category {
  padding: 1px var(--space-3);
  border-radius: var(--radius-full);
  background: var(--ghibli-sky-50);
  color: var(--ghibli-sky-700);
}

.post-card__tag {
  color: var(--ghibli-forest-600);
}

.post-card__spacer {
  flex: 1;
}

.post-card__stat {
  color: var(--color-text-muted);
}
</style>
