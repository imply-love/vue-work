<script setup>
import { computed } from 'vue'

const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
})

const emits = defineEmits(['click'])

const formattedTime = computed(() => {
  if (!props.post.create_time) return ''
  const date = new Date(props.post.create_time)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
})

const handleClick = (e) => {
  // 防止点击交互元素时触发卡片点击
  if (e.target.closest('a, button')) return
  emits('click')
}
</script>

<template>
  <article
    class="post-card"
    @click="handleClick"
    tabindex="0"
    role="button"
    aria-label="查看帖子详情"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >
    <div class="post-card__header">
      <div class="post-card__author">
        <img
          v-if="post.author_avatar"
          :src="post.author_avatar"
          :alt="post.author_nickname"
          class="post-card__avatar"
        />
        <div v-else class="post-card__avatar placeholder" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <div class="post-card__author-info">
          <span class="post-card__author-name">{{ post.author_nickname }}</span>
          <time class="post-card__time" :datetime="post.create_time">{{ formattedTime }}</time>
        </div>
      </div>
    </div>

    <div class="post-card__cover" v-if="post.cover">
      <img :src="post.cover" :alt="post.title" loading="lazy" />
    </div>

    <div class="post-card__content">
      <h3 class="post-card__title">{{ post.title }}</h3>
      <p v-if="post.content" class="post-card__excerpt">
        {{ post.content.replace(/<[^>]*>/g, '').substring(0, 120) }}{{ post.content.length > 120 ? '...' : '' }}
      </p>
    </div>

    <div class="post-card__footer">
      <div class="post-card__stats">
        <span class="post-card__stat" title="浏览数">
          <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          {{ post.view_count }}
        </span>
        <span class="post-card__stat" title="点赞数">
          <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
          {{ post.like_count }}
        </span>
        <span class="post-card__stat" title="回复数">
          <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          {{ post.reply_count }}
        </span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.post-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.post-card:hover {
  border-color: #c9a84c;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
  transform: translateY(-4px);
}

.post-card:focus-visible {
  outline: 2px solid #c9a84c;
  outline-offset: 2px;
}

/* Header */
.post-card__header {
  padding: 20px 20px 0;
}

.post-card__author {
  display: flex;
  align-items: center;
  gap: 12px;
}

.post-card__avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #333;
  transition: border-color 0.2s ease;
}

.post-card:hover .post-card__avatar {
  border-color: #c9a84c;
}

.post-card__avatar.placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #333 0%, #222 100%);
  border: 2px solid #333;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.post-card__avatar.placeholder svg {
  width: 20px;
  height: 20px;
}

.post-card__author-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.post-card__author-name {
  font-weight: 600;
  color: #e8e8e8;
  font-size: 0.9375rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.post-card__time {
  font-size: 0.75rem;
  color: #666;
  white-space: nowrap;
}

/* Cover */
.post-card__cover {
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.post-card__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.post-card:hover .post-card__cover img {
  transform: scale(1.05);
}

/* Content */
.post-card__content {
  padding: 16px 20px 12px;
}

.post-card__title {
  font-family: 'Noto Serif SC', 'Source Han Serif', 'PingFang SC', 'Microsoft YaHei', serif;
  font-size: 1.125rem;
  font-weight: 600;
  color: #e8e8e8;
  margin: 0 0 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-card__excerpt {
  font-size: 0.875rem;
  color: #999;
  line-height: 1.6;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Footer */
.post-card__footer {
  padding: 12px 20px 16px;
  border-top: 1px solid #333;
}

.post-card__stats {
  display: flex;
  gap: 20px;
}

.post-card__stat {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  color: #999;
  white-space: nowrap;
}

.stat-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: #666;
}

.post-card:hover .post-card__stat {
  color: #c9a84c;
}

.post-card:hover .stat-icon {
  color: #c9a84c;
}

/* 响应式 */
@media (max-width: 768px) {
  .post-card__content {
    padding: 12px 16px 8px;
  }

  .post-card__footer {
    padding: 10px 16px 14px;
  }

  .post-card__stats {
    gap: 16px;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .post-card,
  .post-card__cover img {
    transition: none;
  }
}
</style>