<script setup>
// 递归评论节点：支持多级回复树的渲染
import { computed } from 'vue'

const props = defineProps({
  // 评论节点：{ id, user_id, content, like_count, create_time, author_nickname, author_avatar, children }
  node: { type: Object, required: true },
  currentUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false },
})

const emit = defineEmits(['reply', 'remove'])

const avatarText = computed(() => (props.node.author_nickname || '同').charAt(0).toUpperCase())

// 自己的评论或管理员可删除
const canDelete = computed(() => {
  if (props.isAdmin) return true
  return props.currentUserId != null && String(props.currentUserId) === String(props.node.user_id)
})

const timeText = computed(() => {
  const raw = props.node.create_time
  if (!raw) return ''
  const date = new Date(String(raw).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return raw
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`
})

const onReply = () => emit('reply', props.node)
const onRemove = () => emit('remove', props.node)
</script>

<template>
  <div class="reply-node">
    <div class="reply-node__head">
      <span class="avatar-circle reply-node__avatar">{{ avatarText }}</span>
      <div class="reply-node__who">
        <span class="reply-node__name">{{ node.author_nickname || '匿名同好' }}</span>
        <span class="reply-node__time">{{ timeText }}</span>
      </div>
      <div class="reply-node__ops">
        <lay-button size="xs" @click="onReply">回复</lay-button>
        <lay-button v-if="canDelete" size="xs" type="danger" @click="onRemove">删除</lay-button>
      </div>
    </div>

    <p class="reply-node__content">{{ node.content }}</p>

    <div v-if="node.children && node.children.length" class="reply-node__children">
      <ReplyNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :current-user-id="currentUserId"
        :is-admin="isAdmin"
        @reply="emit('reply', $event)"
        @remove="emit('remove', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.reply-node__head {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.reply-node__avatar {
  width: 32px;
  height: 32px;
  font-size: var(--text-sm);
}

.reply-node__who {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.reply-node__name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.reply-node__time {
  font-size: 11px;
  color: var(--color-text-muted);
}

.reply-node__ops {
  margin-left: auto;
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.reply-node__content {
  margin: var(--space-3) 0 0;
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text);
  word-break: break-word;
  white-space: pre-wrap;
}

.reply-node__children {
  margin-top: var(--space-3);
}
</style>
