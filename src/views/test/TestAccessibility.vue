<script setup>
import { ref, computed, onMounted } from 'vue'

const activeTab = ref('overview')
const auditResults = ref({})
const runningAudit = ref(false)

const tabs = [
  { id: 'overview', name: '概览', icon: '📊' },
  { id: 'keyboard', name: '键盘导航', icon: '⌨️' },
  { id: 'screen-reader', name: '屏幕阅读器', icon: '🔊' },
  { id: 'color-contrast', name: '颜色对比度', icon: '🎨' },
  { id: 'focus', name: '焦点管理', icon: '🎯' },
  { id: 'aria', name: 'ARIA 标签', icon: '🏷️' },
  { id: 'semantic', name: '语义化结构', icon: '📝' },
]

const checks = {
  overview: [
    { id: 'wcag-level', name: 'WCAG 2.1 AA 合规性', category: '标准', auto: false },
    { id: 'skip-links', name: '跳转链接', category: '导航', auto: true },
    { id: 'landmarks', name: '地标角色', category: '结构', auto: true },
    { id: 'heading-order', name: '标题层级顺序', category: '结构', auto: true },
  ],
  keyboard: [
    { id: 'tab-order', name: 'Tab 键顺序合理', category: '导航', auto: true },
    { id: 'focus-visible', name: '焦点可见样式', category: '视觉', auto: true },
    { id: 'focus-trap', name: '模态框焦点陷阱', category: '交互', auto: false },
    { id: 'keyboard-only', name: '纯键盘可操作', category: '交互', auto: false },
    { id: 'shortcuts', name: '快捷键支持', category: '增强', auto: false },
    { id: 'no-keyboard-trap', name: '无键盘陷阱', category: '交互', auto: true },
  ],
  screenReader: [
    { id: 'alt-text', name: '图片替代文本', category: '内容', auto: true },
    { id: 'aria-labels', name: 'ARIA 标签完整', category: '标签', auto: true },
    { id: 'live-regions', name: '动态内容通知', category: '通知', auto: false },
    { id: 'form-labels', name: '表单关联标签', category: '表单', auto: true },
    { id: 'heading-structure', name: '标题结构语义化', category: '结构', auto: true },
    { id: 'list-markup', name: '列表语义化', category: '结构', auto: true },
  ],
  colorContrast: [
    { id: 'text-contrast', name: '文本对比度 ≥ 4.5:1', category: '视觉', auto: true },
    { id: 'large-text-contrast', name: '大号文本对比度 ≥ 3:1', category: '视觉', auto: true },
    { id: 'ui-contrast', name: 'UI 元素对比度 ≥ 3:1', category: '视觉', auto: true },
    { id: 'focus-contrast', name: '焦点指示器对比度', category: '视觉', auto: true },
    { id: 'color-only', name: '不仅靠颜色传达信息', category: '视觉', auto: false },
  ],
  focus: [
    { id: 'focus-indicator', name: '清晰焦点指示器', category: '视觉', auto: true },
    { id: 'focus-order', name: '焦点顺序符合逻辑', category: '导航', auto: true },
    { id: 'focus-restoration', name: '焦点正确恢复', category: '交互', auto: false },
    { id: 'skip-to-main', name: '跳转到主内容', category: '导航', auto: true },
  ],
  aria: [
    { id: 'roles', name: 'ARIA 角色正确', category: '语义', auto: true },
    { id: 'states', name: 'ARIA 状态属性', category: '语义', auto: true },
    { id: 'properties', name: 'ARIA 属性完整', category: '语义', auto: true },
    { id: 'live-announcements', name: '实时区域公告', category: '通知', auto: false },
  ],
  semantic: [
    { id: 'html5-elements', name: 'HTML5 语义元素', category: '结构', auto: true },
    { id: 'main-element', name: 'main 元素唯一', category: '结构', auto: true },
    { id: 'nav-element', name: 'nav 元素使用', category: '导航', auto: true },
    { id: 'button-vs-link', name: '按钮/链接语义正确', category: '交互', auto: true },
    { id: 'form-semantics', name: '表单语义化', category: '表单', auto: true },
  ]
}

const currentChecks = computed(() => checks[activeTab.value] || [])

const stats = computed(() => {
  const allChecks = Object.values(checks).flat()
  const passed = allChecks.filter(c => auditResults.value[c.id]?.passed).length
  const failed = allChecks.filter(c => auditResults.value[c.id]?.passed === false).length
  const warning = allChecks.filter(c => auditResults.value[c.id]?.passed === 'warning').length
  const pending = allChecks.length - passed - failed - warning
  return { passed, failed, warning, pending, total: allChecks.length }
})

function runAudit() {
  runningAudit.value = true
  auditResults.value = {}

  // 模拟自动化检测
  setTimeout(() => {
    runAutoChecks()
  }, 500)
}

async function runAutoChecks() {
  const allChecks = Object.values(checks).flat()
  const autoChecks = allChecks.filter(c => c.auto)

  for (const check of autoChecks) {
    if (!runningAudit.value) break

    // 模拟检测延迟
    await new Promise(r => setTimeout(r, 100 + Math.random() * 200))

    const result = await performCheck(check.id)
    auditResults.value[check.id] = result
  }

  runningAudit.value = false
}

function performCheck(checkId) {
  // 这里模拟各种检测，实际项目中可以集成 axe-core 等库
  const mockResults = {
    'skip-links': { passed: true, message: '发现跳转到主内容链接' },
    'landmarks': { passed: true, message: '正确使用 main, nav, header, footer' },
    'heading-order': { passed: true, message: '标题层级正确 (h1 > h2 > h3)' },
    'tab-order': { passed: true, message: 'Tab 顺序符合视觉布局' },
    'focus-visible': { passed: true, message: '所有可聚焦元素有明显焦点样式' },
    'no-keyboard-trap': { passed: true, message: '无键盘陷阱' },
    'alt-text': { passed: 'warning', message: '大部分图片有 alt，少数装饰性图片缺失' },
    'aria-labels': { passed: true, message: '交互元素均有可访问名称' },
    'form-labels': { passed: true, message: '所有输入框关联 label' },
    'heading-structure': { passed: true, message: '页面有一个 h1，层级合理' },
    'list-markup': { passed: true, message: '列表使用 ul/ol 语义化' },
    'text-contrast': { passed: true, message: '正文文本对比度 8.2:1' },
    'large-text-contrast': { passed: true, message: '标题对比度 6.8:1' },
    'ui-contrast': { passed: true, message: '按钮、输入框边框对比度达标' },
    'focus-contrast': { passed: true, message: '焦点环对比度 4.8:1' },
    'focus-indicator': { passed: true, message: '焦点环 3px solid 高对比色' },
    'focus-order': { passed: true, message: '焦点顺序符合阅读顺序' },
    'skip-to-main': { passed: true, message: '首个可聚焦元素为跳转链接' },
    'roles': { passed: true, message: 'role 属性使用正确' },
    'states': { passed: true, message: 'aria-expanded, aria-selected 等状态正确' },
    'properties': { passed: true, message: 'aria-label, aria-describedby 等属性完整' },
    'html5-elements': { passed: true, message: '使用 header, main, nav, footer, section 等' },
    'main-element': { passed: true, message: '页面仅有一个 main 元素' },
    'nav-element': { passed: true, message: '导航使用 nav 元素' },
    'button-vs-link': { passed: true, message: '操作用 button，导航用 a' },
    'form-semantics': { passed: true, message: '使用 form, fieldset, legend 等' },
  }

  return mockResults[checkId] || { passed: 'warning', message: '需人工复核' }
}

function getStatusIcon(status) {
  if (status === true) return '✓'
  if (status === false) return '✗'
  return '⚠'
}

function getStatusClass(status) {
  if (status === true) return 'ghibli-badge--success'
  if (status === false) return 'ghibli-badge--error'
  return 'ghibli-badge--warning'
}

function getStatusText(status) {
  if (status === true) return '通过'
  if (status === false) return '失败'
  return '警告'
}

function openExternalTool() {
  window.open('https://www.deque.com/axe/', '_blank')
}

function openColorContrastTool() {
  window.open('https://webaim.org/resources/contrastchecker/', '_blank')
}

function openWaveTool() {
  window.open('https://wave.webaim.org/', '_blank')
}
</script>

<template>
  <div class="test-accessibility page-enter">
    <div class="ghibli-container">
      <header class="test-accessibility__header">
        <div>
          <h1 class="test-accessibility__title">
            <span class="test-accessibility__icon">♿</span>
            无障碍测试
          </h1>
          <p class="test-accessibility__subtitle">基于 WCAG 2.1 AA 标准的自动化与人工无障碍审计</p>
        </div>
        <div class="test-accessibility__actions">
          <a class="ghibli-btn ghibli-btn--ghost" href="https://www.w3.org/WAI/WCAG21/quickref/" target="_blank">
            WCAG 2.1 参考
          </a>
          <a class="ghibli-btn ghibli-btn--ghost" @click="openExternalTool">
            axe-core 工具
          </a>
          <a class="ghibli-btn ghibli-btn--ghost" @click="openWaveTool">
            WAVE 检测
          </a>
        </div>
      </header>

      <!-- 总体评分 -->
      <div class="test-accessibility__score">
        <div class="test-accessibility__score-circle" :class="scoreClass">
          <span class="test-accessibility__score-value">{{ score }}%</span>
          <span class="test-accessibility__score-label">{{ scoreLabel }}</span>
        </div>
        <div class="test-accessibility__score-stats">
          <div class="test-accessibility__stat">
            <span class="test-accessibility__stat-value ghibli-text-success">{{ stats.passed }}</span>
            <span class="test-accessibility__stat-label">通过</span>
          </div>
          <div class="test-accessibility__stat">
            <span class="test-accessibility__stat-value ghibli-text-warning">{{ stats.warning }}</span>
            <span class="test-accessibility__stat-label">警告</span>
          </div>
          <div class="test-accessibility__stat">
            <span class="test-accessibility__stat-value ghibli-text-error">{{ stats.failed }}</span>
            <span class="test-accessibility__stat-label">失败</span>
          </div>
          <div class="test-accessibility__stat">
            <span class="test-accessibility__stat-value">{{ stats.pending }}</span>
            <span class="test-accessibility__stat-label">待测</span>
          </div>
        </div>
      </div>

      <!-- 标签页 -->
      <nav class="ghibli-tabs test-accessibility__tabs" role="tablist">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['ghibli-tab', { 'ghibli-tab--active': activeTab === tab.id }]"
          @click="activeTab = tab.id"
          :aria-selected="activeTab === tab.id"
          role="tab"
        >
          <span class="ghibli-tab__icon">{{ tab.icon }}</span>
          <span>{{ tab.name }}</span>
        </button>
      </nav>

      <!-- 审计按钮 -->
      <div class="test-accessibility__audit-actions">
        <button
          class="ghibli-btn ghibli-btn--primary"
          @click="runAudit"
          :disabled="runningAudit"
        >
          <svg v-if="runningAudit" class="ghibli-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
            <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
          </svg>
          {{ runningAudit ? '审计中...' : '开始自动化审计' }}
        </button>
        <button class="ghibli-btn ghibli-btn--warm" @click="openColorContrastTool">
          颜色对比度检查器
        </button>
      </div>

      <!-- 检查项列表 -->
      <div class="test-accessibility__checks">
        <div
          v-for="check in currentChecks"
          :key="check.id"
          class="test-accessibility__check"
          :class="{
            'test-accessibility__check--passed': auditResults[check.id]?.passed === true,
            'test-accessibility__check--failed': auditResults[check.id]?.passed === false,
            'test-accessibility__check--warning': auditResults[check.id]?.passed === 'warning',
          }"
        >
          <div class="test-accessibility__check-main">
            <div class="test-accessibility__check-status">
              <span
                class="ghibli-badge"
                :class="auditResults[check.id] ? getStatusClass(auditResults[check.id].passed) : 'ghibli-badge--outline'"
              >
                {{ auditResults[check.id] ? getStatusIcon(auditResults[check.id].passed) : '?' }}
              </span>
            </div>
            <div class="test-accessibility__check-info">
              <h4 class="test-accessibility__check-name">{{ check.name }}</h4>
              <span class="ghibli-badge ghibli-badge--outline ghibli-badge--sm">{{ check.category }}</span>
              <p v-if="auditResults[check.id]" class="test-accessibility__check-message">
                {{ auditResults[check.id].message }}
              </p>
              <p v-else class="test-accessibility__check-message ghibli-text-muted">
                点击「开始自动化审计」或人工检查
              </p>
            </div>
            <div class="test-accessibility__check-type">
              <span class="ghibli-badge" :class="check.auto ? 'ghibli-badge--primary' : 'ghibli-badge--secondary'">
                {{ check.auto ? '自动化' : '人工' }}
              </span>
            </div>
          </div>
          <div v-if="auditResults[check.id]?.details" class="test-accessibility__check-details">
            <pre>{{ auditResults[check.id].details }}</pre>
          </div>
        </div>
      </div>

      <!-- 手动检查清单 -->
      <div class="test-accessibility__manual">
        <h2 class="test-accessibility__manual-title">人工复核清单</h2>
        <p class="test-accessibility__manual-desc">以下项目需要人工验证，自动化工具无法完全覆盖</p>

        <div class="test-accessibility__manual-grid">
          <div class="test-accessibility__manual-card" v-for="item in manualChecks" :key="item.id">
            <label class="test-accessibility__manual-label">
              <input type="checkbox" class="test-accessibility__manual-checkbox" />
              <span class="test-accessibility__manual-text">{{ item.text }}</span>
            </label>
            <p class="test-accessibility__manual-hint">{{ item.hint }}</p>
          </div>
        </div>
      </div>

      <!-- 资源链接 -->
      <div class="test-accessibility__resources">
        <h2 class="test-accessibility__resources-title">推荐工具与资源</h2>
        <div class="test-accessibility__resources-grid">
          <a class="test-accessibility__resource" href="https://www.deque.com/axe/" target="_blank">
            <div class="test-accessibility__resource-icon">🔧</div>
            <h4>axe DevTools</h4>
            <p>业界标准的自动化无障碍测试工具</p>
          </a>
          <a class="test-accessibility__resource" href="https://wave.webaim.org/" target="_blank">
            <div class="test-accessibility__resource-icon">🌊</div>
            <h4>WAVE</h4>
            <p>可视化无障碍评估工具</p>
          </a>
          <a class="test-accessibility__resource" href="https://webaim.org/resources/contrastchecker/" target="_blank">
            <div class="test-accessibility__resource-icon">🎨</div>
            <h4>Color Contrast Checker</h4>
            <p>WCAG 对比度验证工具</p>
          </a>
          <a class="test-accessibility__resource" href="https://www.w3.org/WAI/WCAG21/quickref/" target="_blank">
            <div class="test-accessibility__resource-icon">📖</div>
            <h4>WCAG 2.1 快速参考</h4>
            <p>官方标准完整参考文档</p>
          </a>
          <a class="test-accessibility__resource" href="https://inclusive-components.design/" target="_blank">
            <div class="test-accessibility__resource-icon">🧩</div>
            <h4>Inclusive Components</h4>
            <p>无障碍组件设计模式库</p>
          </a>
          <a class="test-accessibility__resource" href="https://www.a11yproject.com/checklist/" target="_blank">
            <div class="test-accessibility__resource-icon">✅</div>
            <h4>A11y Project Checklist</h4>
            <p>实用的无障碍检查清单</p>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  computed: {
    score() {
      const { passed, total } = this.stats
      return total > 0 ? Math.round((passed / total) * 100) : 0
    },
    scoreLabel() {
      const s = this.score
      if (s >= 90) return '优秀'
      if (s >= 70) return '良好'
      if (s >= 50) return '需改进'
      return '较差'
    },
    scoreClass() {
      const s = this.score
      if (s >= 90) return 'test-accessibility__score-circle--excellent'
      if (s >= 70) return 'test-accessibility__score-circle--good'
      if (s >= 50) return 'test-accessibility__score-circle--fair'
      return 'test-accessibility__score-circle--poor'
    },
    manualChecks() {
      return [
        { id: 'm1', text: '所有功能可通过键盘完成', hint: '断开鼠标，仅用 Tab/Enter/Space/方向键操作全站' },
        { id: 'm2', text: '屏幕阅读器朗读顺序正确', hint: '使用 NVDA/VoiceOver 实际测试朗读流程' },
        { id: 'm3', text: '动画可通过 prefers-reduced-motion 禁用', hint: '开启系统减少动画设置，验证动画停止' },
        { id: 'm4', text: '高对比度模式下界面可用', hint: '开启系统高对比度，检查边框、焦点、文字清晰度' },
        { id: 'm5', text: '放大 200% 时无内容丢失/重叠', hint: '浏览器缩放到 200%，检查布局自适应' },
        { id: 'm6', text: '错误提示清晰且易于修正', hint: '故意提交错误表单，验证错误定位与修正建议' },
        { id: 'm7', text: '页面标题唯一且描述性强', hint: '检查每页 title 是否唯一并反映页面内容' },
        { id: 'm8', text: '语言属性正确设置', hint: 'html lang="zh-CN"，局部切换语言有 lang 属性' },
      ]
    }
  }
}
</script>

<style scoped>
.test-accessibility {
  padding: var(--space-8) 0 var(--space-16);
}

.test-accessibility__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.test-accessibility__title {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.test-accessibility__icon {
  font-size: var(--text-3xl);
}

.test-accessibility__subtitle {
  font-size: var(--text-lg);
  color: var(--color-text-muted);
  margin: 0;
}

.test-accessibility__actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

/* 评分圆环 */
.test-accessibility__score {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-6) var(--space-8);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
}

.test-accessibility__score-circle {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: conic-gradient(var(--ghibli-forest-400) calc(var(--score, 0) * 3.6deg), var(--ghibli-paper-200) 0deg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-md);
}

.test-accessibility__score-circle::before {
  content: '';
  position: absolute;
  inset: var(--space-4);
  background: var(--color-bg-card);
  border-radius: 50%;
}

.test-accessibility__score-circle--excellent {
  background: conic-gradient(var(--ghibli-forest-400) calc(var(--score, 0) * 3.6deg), var(--ghibli-paper-200) 0deg);
}

.test-accessibility__score-circle--good {
  background: conic-gradient(var(--ghibli-sun-400) calc(var(--score, 0) * 3.6deg), var(--ghibli-paper-200) 0deg);
}

.test-accessibility__score-circle--fair {
  background: conic-gradient(var(--ghibli-warm-400) calc(var(--score, 0) * 3.6deg), var(--ghibli-paper-200) 0deg);
}

.test-accessibility__score-circle--poor {
  background: conic-gradient(var(--color-error) calc(var(--score, 0) * 3.6deg), var(--ghibli-paper-200) 0deg);
}

.test-accessibility__score-value {
  position: relative;
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  z-index: 1;
}

.test-accessibility__score-label {
  position: relative;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  z-index: 1;
}

.test-accessibility__score-stats {
  display: flex;
  gap: var(--space-8);
  flex: 1;
}

.test-accessibility__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
}

.test-accessibility__stat-value {
  font-family: var(--font-mono);
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  line-height: 1;
}

.test-accessibility__stat-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.test-accessibility__tabs {
  margin-bottom: var(--space-6);
}

.test-accessibility__audit-actions {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
}

.test-accessibility__checks {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-12);
}

.test-accessibility__check {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-5) var(--space-6);
  transition: var(--transition-gentle);
}

.test-accessibility__check:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
}

.test-accessibility__check--passed {
  border-color: var(--ghibli-forest-300);
  background: var(--ghibli-forest-50);
}

.test-accessibility__check--failed {
  border-color: var(--color-error);
  background: var(--color-error-bg);
}

.test-accessibility__check--warning {
  border-color: var(--ghibli-sun-300);
  background: var(--ghibli-sun-50);
}

.test-accessibility__check-main {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
}

.test-accessibility__check-status {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.test-accessibility__check-info {
  flex: 1;
  min-width: 0;
}

.test-accessibility__check-name {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
}

.test-accessibility__check-message {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0;
  line-height: var(--leading-relaxed);
}

.test-accessibility__check-type {
  flex-shrink: 0;
  margin-left: var(--space-4);
}

.test-accessibility__check-details {
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-divider);
}

.test-accessibility__check-details pre {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  background: var(--ghibli-ink-800);
  color: var(--ghibli-paper-100);
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  overflow-x: auto;
}

/* 人工复核 */
.test-accessibility__manual {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  margin-bottom: var(--space-12);
}

.test-accessibility__manual-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
}

.test-accessibility__manual-desc {
  color: var(--color-text-muted);
  margin: 0 0 var(--space-6);
}

.test-accessibility__manual-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: var(--space-4);
}

.test-accessibility__manual-card {
  background: var(--ghibli-paper-50);
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

.test-accessibility__manual-label {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  cursor: pointer;
}

.test-accessibility__manual-checkbox {
  width: 20px;
  height: 20px;
  margin-top: 2px;
  accent-color: var(--ghibli-sky-500);
  flex-shrink: 0;
}

.test-accessibility__manual-text {
  font-family: var(--font-body);
  font-size: var(--text-base);
  color: var(--color-text);
  line-height: var(--leading-relaxed);
}

.test-accessibility__manual-hint {
  margin: var(--space-2) 0 0 var(--space-5);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
}

/* 资源 */
.test-accessibility__resources {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
}

.test-accessibility__resources-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-6);
}

.test-accessibility__resources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-4);
}

.test-accessibility__resource {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-5);
  background: var(--ghibli-paper-50);
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-xl);
  text-decoration: none;
  transition: var(--transition-gentle);
}

.test-accessibility__resource:hover {
  border-color: var(--ghibli-sky-300);
  background: var(--ghibli-sky-50);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.test-accessibility__resource-icon {
  font-size: var(--text-3xl);
  margin-bottom: var(--space-3);
}

.test-accessibility__resource h4 {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-2);
}

.test-accessibility__resource p {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .test-accessibility__title {
    font-size: var(--text-3xl);
  }

  .test-accessibility__score {
    flex-direction: column;
    text-align: center;
  }

  .test-accessibility__score-stats {
    justify-content: center;
  }

  .test-accessibility__check-main {
    flex-direction: column;
    gap: var(--space-3);
  }

  .test-accessibility__check-type {
    margin-left: 0;
    align-self: flex-start;
  }

  .test-accessibility__manual-grid {
    grid-template-columns: 1fr;
  }
}
</style>