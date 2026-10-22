<script setup>
// 通用确认弹窗：替代原生 window.confirm，沿用站点吉卜力风
// 用法：<ConfirmDialog v-model="show" title="提示" message="确定删除吗？" @confirm="onDelete" />
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '提示' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' },
  danger: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const close = () => emit('update:modelValue', false)
const onConfirm = () => {
  emit('confirm')
  close()
}
const onCancel = () => {
  emit('cancel')
  close()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="cd-overlay" @click.self="onCancel">
      <div class="cd-dialog" role="alertdialog" aria-modal="true" :aria-label="title">
        <h3 class="cd-title">{{ title }}</h3>
        <p class="cd-message">{{ message }}</p>
        <div class="cd-actions">
          <button type="button" class="ghibli-btn ghibli-btn--outline" @click="onCancel">
            {{ cancelText }}
          </button>
          <button
            type="button"
            :class="['ghibli-btn', danger ? 'ghibli-btn--danger' : 'ghibli-btn--primary']"
            @click="onConfirm"
          >
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.cd-overlay {
  position: fixed;
  inset: 0;
  background: rgba(60, 50, 40, 0.35);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: cd-fade 0.2s ease;
}

.cd-dialog {
  width: min(420px, calc(100vw - 48px));
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  padding: var(--space-10);
  box-shadow: var(--shadow-lg);
  animation: cd-pop 0.22s cubic-bezier(0.34, 1.4, 0.64, 1);
}

.cd-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-4);
}

.cd-message {
  margin: 0 0 var(--space-8);
  font-size: var(--text-base);
  color: var(--color-text-light);
  line-height: var(--leading-relaxed);
  white-space: pre-line;
}

.cd-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-4);
}

@keyframes cd-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes cd-pop {
  from { opacity: 0; transform: translateY(8px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
