<script setup>
import { ref, computed } from 'vue'

// 组件测试数据
const componentTests = [
  {
    category: '基础组件',
    components: [
      { name: 'Button 按钮', variants: ['primary', 'secondary', 'warm', 'ghost', 'outline', 'danger'], states: ['default', 'hover', 'active', 'disabled', 'loading'], sizes: ['sm', 'md', 'lg', 'xl'] },
      { name: 'Input 输入框', variants: ['default', 'error'], states: ['default', 'focus', 'disabled', 'with-icon'], sizes: ['sm', 'md', 'lg'] },
      { name: 'Checkbox 复选框', variants: ['default'], states: ['unchecked', 'checked', 'indeterminate', 'disabled'] },
      { name: 'Radio 单选框', variants: ['default'], states: ['unchecked', 'checked', 'disabled'] },
      { name: 'Select 下拉选择', variants: ['default', 'error'], states: ['default', 'focus', 'disabled', 'multiple'] },
      { name: 'Textarea 文本域', variants: ['default', 'error'], states: ['default', 'focus', 'disabled', 'auto-resize'] },
    ]
  },
  {
    category: '反馈组件',
    components: [
      { name: 'Alert 警告提示', variants: ['info', 'success', 'warning', 'error'], states: ['default', 'with-title', 'closable'] },
      { name: 'Toast 轻提示', variants: ['info', 'success', 'warning', 'error'], states: ['default', 'with-title', 'action'] },
      { name: 'Modal 模态框', variants: ['default', 'confirm', 'form'], states: ['open', 'closing', 'nested'] },
      { name: 'Dropdown 下拉菜单', variants: ['default', 'danger'], states: ['open', 'hover-item', 'keyboard-nav'] },
      { name: 'Tooltip 工具提示', variants: ['top', 'bottom', 'left', 'right'], states: ['hover', 'focus'] },
      { name: 'Progress 进度条', variants: ['default', 'stripe', 'circle'], states: ['0%', '25%', '50%', '75%', '100%'] },
      { name: 'Skeleton 骨架屏', variants: ['text', 'card', 'avatar', 'table'], states: ['loading', 'loaded'] },
    ]
  },
  {
    category: '数据展示',
    components: [
      { name: 'Card 卡片', variants: ['default', 'elevated', 'outlined', 'filled'], states: ['default', 'hover', 'interactive', 'with-header-footer'] },
      { name: 'Badge 徽标', variants: ['primary', 'secondary', 'accent', 'warm', 'sakura', 'success', 'warning', 'error', 'outline', 'dot'], states: ['default', 'removable'] },
      { name: 'Tag 标签', variants: ['default', 'removable'], states: ['default', 'hover', 'removing'] },
      { name: 'Avatar 头像', variants: ['image', 'initial', 'icon'], sizes: ['sm', 'md', 'lg', 'xl', '2xl'], states: ['default', 'with-ring', 'group'] },
      { name: 'Table 表格', variants: ['default', 'striped', 'bordered'], states: ['default', 'sortable', 'selectable', 'expandable'] },
      { name: 'List 列表', variants: ['default', 'divided'], states: ['default', 'with-actions', 'loading'] },
      { name: 'Empty 空状态', variants: ['default', 'with-action', 'custom-icon'], states: ['default'] },
    ]
  },
  {
    category: '导航组件',
    components: [
      { name: 'Tabs 标签页', variants: ['default', 'card'], states: ['default', 'disabled-tab', 'scrollable', 'animated'] },
      { name: 'Pagination 分页', variants: ['default', 'simple', 'jumper'], states: ['first-page', 'middle-page', 'last-page', 'disabled'] },
      { name: 'Breadcrumb 面包屑', variants: ['default', 'separator'], states: ['default', 'collapsed', 'with-dropdown'] },
      { name: 'Dropdown 复杂下拉', variants: ['menu', 'cascader'], states: ['open', 'submenu', 'search'] },
    ]
  },
  {
    category: '表单组件',
    components: [
      { name: 'Form 表单', variants: ['horizontal', 'vertical', 'inline'], states: ['default', 'validating', 'submitting', 'error-summary'] },
      { name: 'FormField 表单字段', variants: ['required', 'optional', 'with-hint', 'with-error'], states: ['default', 'focus', 'error', 'disabled'] },
      { name: 'Switch 开关', variants: ['default', 'loading'], states: ['on', 'off', 'disabled'] },
      { name: 'Slider 滑块', variants: ['default', 'range', 'marks'], states: ['default', 'dragging', 'disabled'] },
      { name: 'Rate 评分', variants: ['star', 'heart', 'custom'], states: ['default', 'half', 'readonly', 'disabled'] },
      { name: 'Upload 上传', variants: ['drag', 'select', 'picture-card'], states: ['default', 'uploading', 'preview', 'error'] },
    ]
  },
  {
    category: '特色吉卜力组件',
    components: [
      { name: 'GhibliCard 吉卜力卡片', variants: ['default', 'with-cover', 'interactive'], states: ['default', 'hover', 'focus', 'loading'] },
      { name: 'PostCard 帖子卡片', variants: ['with-cover', 'without-cover'], states: ['default', 'hover', 'focus', 'skeleton'] },
      { name: 'GhibliHeader 导航栏', variants: ['desktop', 'mobile', 'scrolled'], states: ['default', 'user-menu-open', 'mobile-menu-open', 'auth-buttons'] },
      { name: 'MagicParticles 魔法粒子', variants: ['firefly', 'petal', 'sparkle'], states: ['idle', 'burst', 'continuous'] },
      { name: 'WatercolorBG 水彩背景', variants: ['sky', 'forest', 'warm', 'rainbow'], states: ['static', 'animated'] },
      { name: 'FloatingClouds 浮动云朵', variants: ['few', 'many', 'layered'], states: ['drifting', 'paused'] },
      { name: 'GrassBlades 草叶摆动', variants: ['sparse', 'dense'], states: ['swaying', 'wind-gust', 'still'] },
    ]
  }
]

const selectedComponent = ref(null)
const selectedVariant = ref('default')
const selectedState = ref('default')
const selectedSize = ref('md')
const darkMode = ref(false)
const reducedMotion = ref(false)

function selectComponent(comp) {
  selectedComponent.value = comp
  selectedVariant.value = comp.variants?.[0] || 'default'
  selectedState.value = comp.states?.[0] || 'default'
  selectedSize.value = comp.sizes?.[0] || 'md'
}

const variants = computed(() => selectedComponent.value?.variants || ['default'])
const states = computed(() => selectedComponent.value?.states || ['default'])
const sizes = computed(() => selectedComponent.value?.sizes || ['md'])

function toggleDarkMode() {
  darkMode.value = !darkMode.value
  document.documentElement.classList.toggle('ghibli-dark', darkMode.value)
  localStorage.setItem('ghibli-dark', darkMode.value)
}

function toggleReducedMotion() {
  reducedMotion.value = !reducedMotion.value
  document.documentElement.classList.toggle('ghibli-reduced-motion', reducedMotion.value)
}

onMounted(() => {
  if (localStorage.getItem('ghibli-dark') === 'true') {
    darkMode.value = true
    document.documentElement.classList.add('ghibli-dark')
  }
  if (localStorage.getItem('ghibli-reduced-motion') === 'true') {
    reducedMotion.value = true
    document.documentElement.classList.add('ghibli-reduced-motion')
  }
})
</script>

<template>
  <div class="test-components page-enter">
    <div class="ghibli-container">
      <header class="test-components__header">
        <div>
          <h1 class="test-components__title">
            <span class="test-components__icon">🎨</span>
            组件视觉测试
          </h1>
          <p class="test-components__subtitle">预览所有吉卜力风格组件的各种变体、状态与尺寸</p>
        </div>
        <div class="test-components__toggles">
          <button class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm" @click="toggleDarkMode" :aria-pressed="darkMode">
            <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>
              <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
            {{ darkMode ? '浅色' : '深色' }}
          </button>
          <button class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm" @click="toggleReducedMotion" :aria-pressed="reducedMotion">
            <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            减少动画
          </button>
        </div>
      </header>

      <div class="test-components__layout">
        <!-- 组件列表侧边栏 -->
        <aside class="test-components__sidebar">
          <div
            v-for="group in componentTests"
            :key="group.category"
            class="test-components__group"
          >
            <h3 class="test-components__group-title">{{ group.category }}</h3>
            <ul class="test-components__list">
              <li
                v-for="comp in group.components"
                :key="comp.name"
                :class="['test-components__item', { 'test-components__item--selected': selectedComponent === comp }]"
                @click="selectComponent(comp)"
              >
                <span class="test-components__item-name">{{ comp.name }}</span>
                <span class="test-components__item-count">
                  {{ (comp.variants?.length || 1) }} 变体
                </span>
              </li>
            </ul>
          </div>
        </aside>

        <!-- 预览区域 -->
        <div class="test-components__preview">
          <div v-if="!selectedComponent" class="test-components__empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="test-components__empty-icon">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <path d="M9 9h6v6H9z"/>
              <path d="M14 14h4v4h-4z"/>
            </svg>
            <h3>选择一个组件开始预览</h3>
            <p>从左侧列表选择组件，查看其所有变体与状态</p>
          </div>

          <div v-else class="test-components__canvas">
            <!-- 组件信息栏 -->
            <div class="test-components__info-bar">
              <h2 class="test-components__comp-name">{{ selectedComponent.name }}</h2>
              <div class="test-components__controls">
                <div class="test-components__control">
                  <label class="ghibli-label">变体</label>
                  <select v-model="selectedVariant" class="ghibli-input ghibli-input--select ghibli-input--sm">
                    <option v-for="v in variants" :key="v" :value="v">{{ v }}</option>
                  </select>
                </div>
                <div class="test-components__control">
                  <label class="ghibli-label">状态</label>
                  <select v-model="selectedState" class="ghibli-input ghibli-input--select ghibli-input--sm">
                    <option v-for="s in states" :key="s" :value="s">{{ s }}</option>
                  </select>
                </div>
                <div class="test-components__control" v-if="sizes.length > 1">
                  <label class="ghibli-label">尺寸</label>
                  <select v-model="selectedSize" class="ghibli-input ghibli-input--select ghibli-input--sm">
                    <option v-for="s in sizes" :key="s" :value="s">{{ s }}</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- 预览网格 -->
            <div class="test-components__preview-grid">
              <!-- 根据组件类型渲染不同预览 -->
              <component
                :is="getPreviewComponent(selectedComponent.name)"
                :variant="selectedVariant"
                :state="selectedState"
                :size="selectedSize"
                :dark-mode="darkMode"
              />
            </div>

            <!-- 代码片段 -->
            <div class="test-components__code">
              <h4 class="test-components__code-title">使用示例</h4>
              <pre class="test-components__code-block">{{ getCodeExample(selectedComponent.name, selectedVariant, selectedState, selectedSize) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    getPreviewComponent(name) {
      // 这里应该根据组件名返回对应的预览组件
      // 简化处理：返回通用预览
      return {
        template: `
          <div class="component-preview-placeholder">
            <p>组件预览: {{ name }}</p>
            <p>变体: {{ variant }} | 状态: {{ state }} | 尺寸: {{ size }}</p>
            <div class="preview-showcase">
              <ghibli-btn :class="['ghibli-btn--' + variant, 'ghibli-btn--' + size]" v-for="i in 3" :key="i">按钮 {{ i }}</ghibli-btn>
              <ghibli-input :class="['ghibli-input--' + variant, 'ghibli-input--' + size]" placeholder="输入框预览" v-for="i in 2" :key="'input'+i" />
              <ghibli-card class="ghibli-card--" :variant="variant">卡片内容</ghibli-card>
            </div>
          </div>
        `,
        props: ['variant', 'state', 'size', 'darkMode', 'name']
      }
    },
    getCodeExample(name, variant, state, size) {
      const examples = {
        'Button 按钮': `<ghibli-btn class="ghibli-btn--${variant} ghibli-btn--${size}">按钮文本</ghibli-btn>`,
        'Input 输入框': `<ghibli-input class="ghibli-input--${variant} ghibli-input--${size}" placeholder="请输入内容" />`,
        'Card 卡片': `<ghibli-card class="ghibli-card--${variant}">卡片内容</ghibli-card>`,
        'Badge 徽标': `<ghibli-badge class="ghibli-badge--${variant}">徽标</ghibli-badge>`,
        'Alert 警告提示': `<ghibli-alert class="ghibli-alert--${variant}">提示内容</ghibli-alert>`,
        'Toast 轻提示': `this.$ghibli.showToast({ type: '${variant}', message: '提示消息' })`,
        'Modal 模态框': `<ghibli-modal v-model:open="show" title="标题">内容</ghibli-modal>`,
        'Dropdown 下拉菜单': `<ghibli-dropdown><template #trigger>触发器</template><ghibli-dropdown__item>选项</ghibli-dropdown__item></ghibli-dropdown>`,
        'Avatar 头像': `<ghibli-avatar class="ghibli-avatar--${size}" :src="avatarUrl">云</ghibli-avatar>`,
        'Tabs 标签页': `<ghibli-tabs v-model="active"><ghibli-tab name="tab1">标签一</ghibli-tab></ghibli-tabs>`,
        'Pagination 分页': `<ghibli-pagination v-model:page="page" :total="100" />`,
        'Progress 进度条': `<ghibli-progress :value="50" />`,
        'Skeleton 骨架屏': `<ghibli-skeleton class="ghibli-skeleton--text" />`,
        'GhibliCard 吉卜力卡片': `<ghibli-card class="ghibli-card--${variant}">...</ghibli-card>`,
        'PostCard 帖子卡片': `<PostCard :post="postData" @click="goDetail" />`,
      }
      return examples[name] || `<!-- ${name} 组件用法 -->\n<${name.toLowerCase().replace(' ', '-')} class="${variant} ${state} ${size}">内容</${name.toLowerCase().replace(' ', '-')}>`
    }
  }
}
</script>

<style scoped>
.test-components {
  padding: var(--space-8) 0 var(--space-16);
}

.test-components__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.test-components__title {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.test-components__icon {
  font-size: var(--text-3xl);
}

.test-components__subtitle {
  font-size: var(--text-lg);
  color: var(--color-text-muted);
  margin: 0;
}

.test-components__toggles {
  display: flex;
  gap: var(--space-2);
}

.test-components__layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--space-6);
}

@media (max-width: 1024px) {
  .test-components__layout {
    grid-template-columns: 1fr;
  }
  .test-components__sidebar {
    display: none;
  }
}

.test-components__sidebar {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-4);
  max-height: calc(100vh - 250px);
  overflow-y: auto;
  position: sticky;
  top: 90px;
}

.test-components__group {
  margin-bottom: var(--space-6);
}

.test-components__group:last-child {
  margin-bottom: 0;
}

.test-components__group-title {
  font-family: var(--font-display);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 var(--space-3);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-divider);
}

.test-components__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.test-components__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: var(--transition-gentle);
  border: 1px solid transparent;
}

.test-components__item:hover {
  background: var(--ghibli-paper-100);
  border-color: var(--color-border);
}

.test-components__item--selected {
  background: var(--ghibli-sky-50);
  border-color: var(--ghibli-sky-300);
}

.test-components__item-name {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text);
}

.test-components__item-count {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  background: var(--ghibli-paper-100);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
}

.test-components__preview {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  min-height: 500px;
}

.test-components__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-20) var(--space-8);
  text-align: center;
  color: var(--color-text-muted);
  height: 500px;
}

.test-components__empty-icon {
  width: 80px;
  height: 80px;
  opacity: 0.3;
  margin-bottom: var(--space-6);
}

.test-components__empty h3 {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
}

.test-components__empty p {
  margin: 0;
}

.test-components__canvas {
  padding: var(--space-6);
}

.test-components__info-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-divider);
}

.test-components__comp-name {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0;
}

.test-components__controls {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.test-components__control {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.test-components__control .ghibli-label {
  margin-bottom: 0;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ghibli-input--sm {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
  min-width: 120px;
}

.test-components__preview-grid {
  margin-bottom: var(--space-8);
}

.component-preview-placeholder {
  background: var(--ghibli-paper-50);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  text-align: center;
  color: var(--color-text-muted);
}

.preview-showcase {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  justify-content: center;
  margin-top: var(--space-6);
}

.test-components__code {
  background: var(--ghibli-ink-800);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.test-components__code-title {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--ghibli-paper-100);
  margin: 0;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--ghibli-ink-700);
  background: var(--ghibli-ink-900);
}

.test-components__code-block {
  margin: 0;
  padding: var(--space-6);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.7;
  color: var(--ghibli-paper-200);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 深色模式 */
.ghibli-dark .test-components__empty {
  color: var(--ghibli-ink-400);
}

.ghibli-dark .component-preview-placeholder {
  background: var(--ghibli-ink-800);
  border-color: var(--ghibli-ink-600);
}

/* 响应式 */
@media (max-width: 768px) {
  .test-components__title {
    font-size: var(--text-3xl);
  }

  .test-components__info-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .test-components__controls {
    justify-content: stretch;
  }

  .test-components__control {
    flex: 1;
  }

  .test-components__control .ghibli-input {
    flex: 1;
  }
}
</style>