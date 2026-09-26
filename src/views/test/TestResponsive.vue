<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const breakpoints = [
  { name: '超小屏', width: '320px', label: 'Mobile S', icon: '📱' },
  { name: '小屏', width: '375px', label: 'Mobile M', icon: '📱' },
  { name: '中屏', width: '428px', label: 'Mobile L', icon: '📱' },
  { name: '平板竖屏', width: '768px', label: 'Tablet', icon: '📲' },
  { name: '平板横屏', width: '1024px', label: 'Tablet L', icon: '📲' },
  { name: '桌面小', width: '1280px', label: 'Desktop S', icon: '💻' },
  { name: '桌面中', width: '1440px', label: 'Desktop M', icon: '💻' },
  { name: '桌面大', width: '1920px', label: 'Desktop L', icon: '💻' },
]

const selectedBreakpoint = ref('375px')
const customWidth = ref(375)
const showRuler = ref(true)
const showGrid = ref(false)
const orientation = ref('portrait')
const deviceFrame = ref(true)

const testComponents = ref([
  { name: '导航栏', selector: '.ghibli-header' },
  { name: '按钮组', selector: '.ghibli-btn' },
  { name: '卡片网格', selector: '.ghibli-cards' },
  { name: '表单输入', selector: '.ghibli-input' },
  { name: '模态框', selector: '.ghibli-modal' },
  { name: '下拉菜单', selector: '.ghibli-dropdown__menu' },
])

const iframeRef = ref(null)
const previewUrl = ref('/')

function setBreakpoint(bp) {
  selectedBreakpoint.value = bp
  customWidth.value = parseInt(bp)
  updateIframeSize()
}

function setCustomWidth() {
  const width = Math.max(200, Math.min(2560, customWidth.value))
  customWidth.value = width
  selectedBreakpoint.value = `${width}px`
  updateIframeSize()
}

function updateIframeSize() {
  if (!iframeRef.value) return
  const width = customWidth.value
  const height = orientation.value === 'portrait' ? Math.round(width * 1.78) : Math.round(width / 1.78)
  iframeRef.value.style.width = `${width}px`
  iframeRef.value.style.height = `${height}px`
}

function toggleOrientation() {
  orientation.value = orientation.value === 'portrait' ? 'landscape' : 'portrait'
  updateIframeSize()
}

function reloadIframe() {
  if (iframeRef.value) {
    iframeRef.value.src = iframeRef.value.src
  }
}

function navigateTo(path) {
  previewUrl.value = path
  if (iframeRef.value) {
    iframeRef.value.src = path
  }
}

const currentBreakpointInfo = computed(() => {
  return breakpoints.find(b => b.width === selectedBreakpoint.value) || breakpoints[1]
})

// 键盘快捷键
function handleKeydown(e) {
  if (e.target.tagName === 'INPUT') return

  switch (e.key) {
    case '1': setBreakpoint('320px'); break
    case '2': setBreakpoint('375px'); break
    case '3': setBreakpoint('428px'); break
    case '4': setBreakpoint('768px'); break
    case '5': setBreakpoint('1024px'); break
    case '6': setBreakpoint('1280px'); break
    case '7': setBreakpoint('1440px'); break
    case '8': setBreakpoint('1920px'); break
    case 'o': toggleOrientation(); break
    case 'r': reloadIframe(); break
    case 'g': showGrid.value = !showGrid.value; break
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  updateIframeSize()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="test-responsive page-enter">
    <div class="ghibli-container">
      <header class="test-responsive__header">
        <div>
          <h1 class="test-responsive__title">
            <span class="test-responsive__icon">📐</span>
            响应式断点测试
          </h1>
          <p class="test-responsive__subtitle">在不同设备尺寸下预览页面布局，验证响应式设计</p>
        </div>
        <div class="test-responsive__device-info">
          <span class="ghibli-badge ghibli-badge--primary">
            {{ currentBreakpointInfo.name }} ({{ currentBreakpointInfo.width }})
          </span>
          <span class="ghibli-badge" :class="orientation === 'portrait' ? 'ghibli-badge--success' : 'ghibli-badge--warm'">
            {{ orientation === 'portrait' ? '竖屏' : '横屏' }}
          </span>
        </div>
      </header>

      <div class="test-responsive__toolbar">
        <!-- 断点选择器 -->
        <div class="test-responsive__breakpoints">
          <span class="test-responsive__breakpoints-label">预设设备:</span>
          <button
            v-for="bp in breakpoints"
            :key="bp.width"
            class="test-responsive__bp-btn"
            :class="{ 'test-responsive__bp-btn--active': selectedBreakpoint === bp.width }"
            @click="setBreakpoint(bp.width)"
            :title="bp.name"
          >
            <span class="test-responsive__bp-icon">{{ bp.icon }}</span>
            <span class="test-responsive__bp-label">{{ bp.label }}</span>
          </button>
        </div>

        <!-- 自定义宽度 -->
        <div class="test-responsive__custom">
          <label class="ghibli-label">自定义宽度</label>
          <div class="test-responsive__custom-input">
            <input
              type="number"
              v-model.number="customWidth"
              class="ghibli-input"
              @change="setCustomWidth"
              @keydown.enter="setCustomWidth"
              min="200"
              max="2560"
              style="width: 100px;"
            />
            <span class="test-responsive__px">px</span>
          </div>
        </div>

        <!-- 控制按钮 -->
        <div class="test-responsive__controls">
          <label class="ghibli-checkbox">
            <input type="checkbox" v-model="deviceFrame" class="ghibli-checkbox__input" />
            <span class="ghibli-checkbox__box"></span>
            设备外框
          </label>
          <label class="ghibli-checkbox">
            <input type="checkbox" v-model="showRuler" class="ghibli-checkbox__input" />
            <span class="ghibli-checkbox__box"></span>
            显示标尺
          </label>
          <label class="ghibli-checkbox">
            <input type="checkbox" v-model="showGrid" class="ghibli-checkbox__input" />
            <span class="ghibli-checkbox__box"></span>
            网格对齐
          </label>
          <button class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm" @click="toggleOrientation" :title="orientation === 'portrait' ? '切换到横屏 (O)' : '切换到竖屏 (O)'">
            <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path v-if="orientation === 'portrait'" d="M21 12H3M17 18V6M7 6v12"/>
              <path v-else d="M12 21V3M6 17h12M18 7H6v12"/>
            </svg>
            旋转
          </button>
          <button class="ghibli-btn ghibli-btn--ghost ghibli-btn--sm" @click="reloadIframe" title="刷新预览 (R)">
            <svg class="ghibli-btn__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6"/>
              <path d="M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            刷新
          </button>
        </div>
      </div>

      <!-- 页面导航快捷键 -->
      <div class="test-responsive__nav">
        <span class="test-responsive__nav-label">快速跳转:</span>
        <button
          v-for="path in ['/', '/login', '/register', '/profile', '/test']"
          :key="path"
          class="test-responsive__nav-btn"
          @click="navigateTo(path)"
        >
          {{ path === '/' ? '首页' : path.replace('/', '') }}
        </button>
      </div>

      <!-- 预览区域 -->
      <div class="test-responsive__preview">
        <!-- 标尺 -->
        <div v-if="showRuler" class="test-responsive__rulers">
          <div class="test-responsive__ruler test-responsive__ruler--horizontal">
            <div
              v-for="i in Math.ceil(customWidth / 50)"
              :key="i"
              class="test-responsive__ruler-mark"
              :style="{ left: `${(i - 1) * 50}px` }"
            >
              <span v-if="((i - 1) * 50) % 100 === 0">{{ (i - 1) * 50 }}</span>
            </div>
          </div>
          <div class="test-responsive__ruler test-responsive__ruler--vertical">
            <div
              v-for="i in Math.ceil((orientation === 'portrait' ? customWidth * 1.78 : customWidth / 1.78) / 50)"
              :key="i"
              class="test-responsive__ruler-mark"
              :style="{ top: `${(i - 1) * 50}px` }"
            >
              <span v-if="((i - 1) * 50) % 100 === 0">{{ (i - 1) * 50 }}</span>
            </div>
          </div>
        </div>

        <!-- 设备外框 -->
        <div
          class="test-responsive__device"
          :class="{
            'test-responsive__device--mobile': customWidth < 768,
            'test-responsive__device--tablet': customWidth >= 768 && customWidth < 1024,
            'test-responsive__device--desktop': customWidth >= 1024,
            'test-responsive__device--landscape': orientation === 'landscape',
            'test-responsive__device--portrait': orientation === 'portrait',
          }"
          v-if="deviceFrame"
        >
          <div class="test-responsive__device-screen">
            <iframe
              ref="iframeRef"
              :src="previewUrl"
              class="test-responsive__iframe"
              @load="onIframeLoad"
            ></iframe>
          </div>
          <div class="test-responsive__device-notch" v-if="customWidth < 768 && orientation === 'portrait'"></div>
          <div class="test-responsive__device-home" v-if="customWidth < 768 && orientation === 'portrait'"></div>
        </div>

        <!-- 无外框模式 -->
        <div v-else class="test-responsive__iframe-wrapper">
          <iframe
            ref="iframeRef"
            :src="previewUrl"
            class="test-responsive__iframe"
            :style="{ width: customWidth + 'px', height: (orientation === 'portrait' ? Math.round(customWidth * 1.78) : Math.round(customWidth / 1.78)) + 'px' }"
            @load="onIframeLoad"
          ></iframe>
        </div>

        <!-- 网格叠加 -->
        <div v-if="showGrid" class="test-responsive__grid-overlay" :style="{ width: customWidth + 'px' }">
          <div v-for="i in 12" :key="i" class="test-responsive__grid-col"></div>
        </div>
      </div>

      <!-- 当前尺寸信息 -->
      <div class="test-responsive__info">
        <div class="test-responsive__info-item">
          <span class="test-responsive__info-label">视口宽度</span>
          <span class="test-responsive__info-value">{{ customWidth }}px</span>
        </div>
        <div class="test-responsive__info-item">
          <span class="test-responsive__info-label">视口高度</span>
          <span class="test-responsive__info-value">{{ orientation === 'portrait' ? Math.round(customWidth * 1.78) : Math.round(customWidth / 1.78) }}px</span>
        </div>
        <div class="test-responsive__info-item">
          <span class="test-responsive__info-label">设备像素比</span>
          <span class="test-responsive__info-value">{{ window.devicePixelRatio || 1 }}x</span>
        </div>
        <div class="test-responsive__info-item">
          <span class="test-responsive__info-label">CSS 断点</span>
          <span class="test-responsive__info-value">
            <span v-for="bp in breakpoints" :key="bp.width" class="ghibli-badge" :class="customWidth <= parseInt(bp.width) ? 'ghibli-badge--primary' : 'ghibli-badge--outline'">
              {{ bp.label }}: {{ bp.width }}
            </span>
          </span>
        </div>
      </div>

      <!-- 快捷键提示 -->
      <details class="test-responsive__shortcuts">
        <summary>键盘快捷键</summary>
        <div class="test-responsive__shortcuts-list">
          <div class="test-responsive__shortcut">
            <kbd>1-8</kbd> <span>切换预设断点</span>
          </div>
          <div class="test-responsive__shortcut">
            <kbd>O</kbd> <span>切换横竖屏</span>
          </div>
          <div class="test-responsive__shortcut">
            <kbd>R</kbd> <span>刷新预览</span>
          </div>
          <div class="test-responsive__shortcut">
            <kbd>G</kbd> <span>切换网格</span>
          </div>
        </div>
      </details>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    onIframeLoad() {
      // iframe 加载完成
      console.log('Preview loaded')
    }
  }
}
</script>

<style scoped>
.test-responsive {
  padding: var(--space-8) 0 var(--space-16);
}

.test-responsive__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.test-responsive__title {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.test-responsive__icon {
  font-size: var(--text-3xl);
}

.test-responsive__subtitle {
  font-size: var(--text-lg);
  color: var(--color-text-muted);
  margin: 0;
}

.test-responsive__device-info {
  display: flex;
  gap: var(--space-2);
}

.test-responsive__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  margin-bottom: var(--space-6);
}

.test-responsive__breakpoints {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  flex: 1;
  min-width: 300px;
}

.test-responsive__breakpoints-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-right: var(--space-2);
}

.test-responsive__bp-btn {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  background: var(--ghibli-paper-100);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: var(--transition-gentle);
  font-size: var(--text-xs);
}

.test-responsive__bp-btn:hover {
  background: var(--ghibli-sky-50);
  border-color: var(--ghibli-sky-300);
}

.test-responsive__bp-btn--active {
  background: var(--ghibli-sky-100);
  border-color: var(--ghibli-sky-500);
  color: var(--ghibli-sky-700);
}

.test-responsive__bp-icon {
  font-size: var(--text-base);
}

.test-responsive__bp-label {
  font-weight: var(--font-medium);
}

.test-responsive__custom {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.test-responsive__custom .ghibli-label {
  margin-bottom: 0;
  font-size: var(--text-sm);
}

.test-responsive__custom-input {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.test-responsive__px {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.test-responsive__controls {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-left: auto;
}

.test-responsive__nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--ghibli-paper-50);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-6);
  font-size: var(--text-sm);
}

.test-responsive__nav-label {
  color: var(--color-text-muted);
  margin-right: var(--space-2);
}

.test-responsive__nav-btn {
  padding: var(--space-1) var(--space-3);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text);
  cursor: pointer;
  transition: var(--transition-gentle);
}

.test-responsive__nav-btn:hover {
  border-color: var(--ghibli-sky-300);
  color: var(--ghibli-sky-600);
}

.test-responsive__preview {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-6);
  background: var(--ghibli-paper-100);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  min-height: 400px;
}

/* 标尺 */
.test-responsive__rulers {
  position: absolute;
  top: var(--space-6);
  left: var(--space-6);
  right: var(--space-6);
  bottom: var(--space-6);
  pointer-events: none;
  z-index: 10;
}

.test-responsive__ruler {
  position: absolute;
  background: rgba(14, 165, 233, 0.1);
}

.test-responsive__ruler--horizontal {
  top: 0;
  left: 0;
  right: 0;
  height: 24px;
}

.test-responsive__ruler--vertical {
  top: 0;
  left: 0;
  bottom: 0;
  width: 24px;
}

.test-responsive__ruler-mark {
  position: absolute;
  width: 1px;
  height: 100%;
  background: rgba(14, 165, 233, 0.3);
}

.test-responsive__ruler-mark::after {
  content: attr(data-label);
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: var(--ghibli-sky-600);
  white-space: nowrap;
  margin-top: 2px;
}

.test-responsive__ruler--vertical .test-responsive__ruler-mark {
  width: 100%;
  height: 1px;
}

.test-responsive__ruler--vertical .test-responsive__ruler-mark::after {
  top: 50%;
  left: 100%;
  transform: translateY(-50%);
  margin-left: 4px;
  margin-top: 0;
}

/* 设备外框 */
.test-responsive__device {
  position: relative;
  background: var(--ghibli-ink-800);
  border-radius: var(--radius-3xl);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.3),
    0 0 0 8px var(--ghibli-ink-800),
    0 0 0 9px var(--ghibli-ink-700),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  padding: var(--space-4);
  transition: all var(--duration-normal) var(--ease-gentle);
}

.test-responsive__device--mobile {
  border-radius: 2.5rem;
}

.test-responsive__device--tablet {
  border-radius: 1.5rem;
}

.test-responsive__device--desktop {
  border-radius: var(--radius-xl);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.test-responsive__device-screen {
  background: white;
  border-radius: var(--radius-2xl);
  overflow: hidden;
  position: relative;
}

.test-responsive__device--mobile .test-responsive__device-screen {
  border-radius: 2rem;
}

.test-responsive__iframe {
  display: block;
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}

.test-responsive__device-notch {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 120px;
  height: 24px;
  background: var(--ghibli-ink-800);
  border-radius: 0 0 12px 12px;
  z-index: 10;
}

.test-responsive__device-home {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 4px;
  background: var(--ghibli-ink-700);
  border-radius: 2px;
  z-index: 10;
}

.test-responsive__iframe-wrapper {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  background: white;
}

.test-responsive__grid-overlay {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--space-4);
  height: 100%;
  pointer-events: none;
  z-index: 5;
}

.test-responsive__grid-col {
  background: rgba(14, 165, 233, 0.05);
  border: 1px solid rgba(14, 165, 233, 0.1);
  min-height: 100px;
}

/* 信息面板 */
.test-responsive__info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-4);
  margin-top: var(--space-6);
}

.test-responsive__info-item {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.test-responsive__info-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.test-responsive__info-value {
  font-family: var(--font-mono);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  flex-wrap: wrap;
  gap: var(--space-1);
}

.test-responsive__info-value .ghibli-badge {
  font-size: var(--text-xs);
}

/* 快捷键 */
.test-responsive__shortcuts {
  margin-top: var(--space-8);
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
}

.test-responsive__shortcuts summary {
  cursor: pointer;
  font-weight: var(--font-semibold);
  color: var(--color-text);
  padding: var(--space-2) 0;
  list-style: none;
}

.test-responsive__shortcuts summary::-webkit-details-marker {
  display: none;
}

.test-responsive__shortcuts summary::before {
  content: '▸';
  display: inline-block;
  margin-right: var(--space-2);
  transition: transform var(--duration-fast);
}

.test-responsive__shortcuts[open] summary::before {
  transform: rotate(90deg);
}

.test-responsive__shortcuts-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-3);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-divider);
}

.test-responsive__shortcut {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.test-responsive__shortcut kbd {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  padding: var(--space-1) var(--space-2);
  background: var(--ghibli-paper-100);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  min-width: 36px;
  text-align: center;
}

.test-responsive__shortcut span {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* 响应式 */
@media (max-width: 768px) {
  .test-responsive__title {
    font-size: var(--text-3xl);
  }

  .test-responsive__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .test-responsive__breakpoints {
    justify-content: center;
  }

  .test-responsive__controls {
    justify-content: center;
    margin-left: 0;
  }

  .test-responsive__nav {
    justify-content: center;
  }

  .test-responsive__info {
    grid-template-columns: 1fr 1fr;
  }

  .test-responsive__rulers {
    display: none;
  }
}

@media (max-width: 480px) {
  .test-responsive__bp-label {
    display: none;
  }

  .test-responsive__bp-btn {
    padding: var(--space-2);
  }

  .test-responsive__custom {
    display: none;
  }
}
</style>