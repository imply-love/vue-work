<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { animeApi, animeRecommendationApi, animeRequestApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const PAGE_SIZE = 10

// ===== 板块切换：番剧库 / 番剧推荐 / 求番 =====
const TABS = [
  { key: 'library', label: '番剧库' },
  { key: 'recommend', label: '番剧推荐' },
  { key: 'request', label: '求番' },
]

const tab = ref('library')

const switchTab = (key) => {
  if (tab.value === key) return
  tab.value = key
  if (key === 'library') loadLibrary(1)
  if (key === 'recommend') loadRecommendations(1)
  if (key === 'request') loadRequests(1)
}

// ===== 番剧库列表（管理员在管理后台录入）=====
const library = ref([])
const libraryTotal = ref(0)
const libraryPage = ref(1)
const libraryLoading = ref(false)
const libraryError = ref('')

const loadLibrary = async (page = libraryPage.value) => {
  libraryLoading.value = true
  libraryError.value = ''
  try {
    const res = await animeApi.getList({ page, page_size: PAGE_SIZE })
    if (res.code === 0) {
      library.value = res.data.list || []
      libraryTotal.value = res.data.total || 0
      libraryPage.value = res.data.page || page
    } else {
      libraryError.value = res.message || '获取番剧库失败'
    }
  } catch (err) {
    libraryError.value = err.message || '获取番剧库失败'
  } finally {
    libraryLoading.value = false
  }
}

// ===== 番剧推荐列表 =====
const recommendations = ref([])
const recommendTotal = ref(0)
const recommendPage = ref(1)
const recommendLoading = ref(false)
const recommendError = ref('')

const REVIEW_META = {
  0: { label: '待评审', type: 'warm' },
  1: { label: '已推荐', type: 'normal' },
  2: { label: '已打回', type: 'danger' },
}
const reviewMeta = (status) => REVIEW_META[status] || REVIEW_META[0]

const loadRecommendations = async (page = recommendPage.value) => {
  recommendLoading.value = true
  recommendError.value = ''
  try {
    const res = await animeRecommendationApi.getList({ page, page_size: PAGE_SIZE })
    if (res.code === 0) {
      recommendations.value = res.data.list || []
      recommendTotal.value = res.data.total || 0
      recommendPage.value = res.data.page || page
    } else {
      recommendError.value = res.message || '获取推荐列表失败'
    }
  } catch (err) {
    recommendError.value = err.message || '获取推荐列表失败'
  } finally {
    recommendLoading.value = false
  }
}

// ===== 求番列表 =====
const requests = ref([])
const requestTotal = ref(0)
const requestPage = ref(1)
const requestLoading = ref(false)
const requestError = ref('')

const loadRequests = async (page = requestPage.value) => {
  requestLoading.value = true
  requestError.value = ''
  try {
    const res = await animeRequestApi.getList({ page, page_size: PAGE_SIZE })
    if (res.code === 0) {
      requests.value = res.data.list || []
      requestTotal.value = res.data.total || 0
      requestPage.value = res.data.page || page
    } else {
      requestError.value = res.message || '获取求番列表失败'
    }
  } catch (err) {
    requestError.value = err.message || '获取求番列表失败'
  } finally {
    requestLoading.value = false
  }
}

// ===== 推荐表单：番名、链接、推荐理由均为必填 =====
const recommendOpen = ref(false)
const recommendForm = ref({ anime_name: '', link: '', reason: '' })
const recommendSubmitting = ref(false)
const recommendFormError = ref('')

const openRecommend = () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  recommendFormError.value = ''
  recommendOpen.value = true
  requestOpen.value = false
}

const submitRecommend = async () => {
  if (recommendSubmitting.value) return
  recommendFormError.value = ''
  const animeName = recommendForm.value.anime_name.trim()
  const link = recommendForm.value.link.trim()
  const reason = recommendForm.value.reason.trim()
  if (!animeName) {
    recommendFormError.value = '请填写推荐番名'
    return
  }
  if (!link) {
    recommendFormError.value = '请填写推荐番剧链接'
    return
  }
  if (!/^https?:\/\/\S+$/i.test(link)) {
    recommendFormError.value = '链接需以 http:// 或 https:// 开头'
    return
  }
  if (!reason) {
    recommendFormError.value = '请填写推荐理由'
    return
  }

  recommendSubmitting.value = true
  try {
    const res = await animeRecommendationApi.create({ anime_name: animeName, link, reason })
    if (res.code === 0) {
      recommendForm.value = { anime_name: '', link: '', reason: '' }
      window.$ghibli?.showToast({ type: 'success', title: '推荐成功', message: '等待管理员评审' })
      if (recommendPage.value !== 1) recommendPage.value = 1
      await loadRecommendations(1)
    } else {
      recommendFormError.value = res.message
    }
  } catch (err) {
    recommendFormError.value = err.message || '推荐失败，请稍后重试'
  } finally {
    recommendSubmitting.value = false
  }
}

// ===== 求番表单 =====
const requestOpen = ref(false)
const requestForm = ref({ anime_name: '', reason: '' })
const requestSubmitting = ref(false)
const requestFormError = ref('')

const openRequest = () => {
  if (!authStore.isLoggedIn) {
    goLogin()
    return
  }
  requestFormError.value = ''
  requestOpen.value = true
  recommendOpen.value = false
}

const submitRequest = async () => {
  if (requestSubmitting.value) return
  requestFormError.value = ''
  const animeName = requestForm.value.anime_name.trim()
  if (!animeName) {
    requestFormError.value = '请填写想求的番剧名称'
    return
  }

  requestSubmitting.value = true
  try {
    const res = await animeRequestApi.create({
      anime_name: animeName,
      reason: requestForm.value.reason.trim(),
    })
    if (res.code === 0) {
      requestForm.value = { anime_name: '', reason: '' }
      window.$ghibli?.showToast({
        type: 'success',
        title: '求番成功',
        message: '已通知管理员，会尽快收录',
      })
      if (requestPage.value !== 1) requestPage.value = 1
      await loadRequests(1)
    } else {
      requestFormError.value = res.message
    }
  } catch (err) {
    requestFormError.value = err.message || '求番失败，请稍后重试'
  } finally {
    requestSubmitting.value = false
  }
}

// ===== 分页与链接 =====
const changePage = (payload, currentRef, loader) => {
  const current = typeof payload === 'number' ? payload : payload?.current
  if (!current) return
  loader(current)
  currentRef.value = current
}

const openLink = (link) => {
  if (!link) return
  window.open(link, '_blank', 'noopener,noreferrer')
}

const goLogin = () => router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
const avatarText = (name) => (name || '同好').slice(0, 1)

const currentTotal = computed(() => {
  if (tab.value === 'library') return libraryTotal.value
  if (tab.value === 'recommend') return recommendTotal.value
  return requestTotal.value
})

onMounted(() => {
  loadLibrary(1)
  loadRecommendations(1)
  loadRequests(1)
})
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero heroes-hero">
      <div class="heroes-hero__text">
        <h1 class="page-title">番剧库</h1>
        <p class="page-sub">管理员收录的番剧、同好推荐的宝藏番，以及求番许愿池</p>
      </div>
      <div class="heroes-actions">
        <lay-button type="primary" size="lg" @click="openRecommend">推荐一部番</lay-button>
        <lay-button type="normal" size="lg" @click="openRequest">求一部番</lay-button>
      </div>
    </section>

    <!-- 推荐表单 -->
    <lay-card v-if="recommendOpen" class="composer-card">
      <div class="composer-head">
        <h2 class="composer-title">推荐一部番</h2>
        <lay-button size="sm" @click="recommendOpen = false">收起</lay-button>
      </div>

      <lay-form class="composer-form" label-position="top" @submit="submitRecommend">
        <div v-if="recommendFormError" class="form-error" role="alert">{{ recommendFormError }}</div>

        <lay-form-item label="番名" required>
          <lay-input
            v-model="recommendForm.anime_name"
            placeholder="例如：千与千寻"
            :maxlength="100"
            allow-clear
          />
        </lay-form-item>

        <lay-form-item label="番剧链接" required>
          <lay-input
            v-model="recommendForm.link"
            type="url"
            placeholder="以 http:// 或 https:// 开头的有效地址"
            :maxlength="500"
            allow-clear
          />
        </lay-form-item>

        <lay-form-item label="推荐理由" required>
          <lay-textarea
            v-model="recommendForm.reason"
            :rows="4"
            :maxlength="5000"
            show-count
            placeholder="为什么推荐这部番？剧情、画面、音乐都可以写"
          />
        </lay-form-item>

        <div class="form-actions">
          <lay-button type="primary" native-type="submit" :loading="recommendSubmitting">
            {{ recommendSubmitting ? '提交中...' : '提交推荐' }}
          </lay-button>
          <lay-button native-type="button" @click="recommendOpen = false">取消</lay-button>
        </div>
      </lay-form>
    </lay-card>

    <!-- 求番表单 -->
    <lay-card v-if="requestOpen" class="composer-card">
      <div class="composer-head">
        <h2 class="composer-title">发起求番</h2>
        <lay-button size="sm" @click="requestOpen = false">收起</lay-button>
      </div>

      <lay-form class="composer-form" label-position="top" @submit="submitRequest">
        <div v-if="requestFormError" class="form-error" role="alert">{{ requestFormError }}</div>

        <lay-form-item label="番剧名" required>
          <lay-input
            v-model="requestForm.anime_name"
            placeholder="想看的番叫什么？例如：你想求《千与千寻》收录"
            :maxlength="100"
            allow-clear
          />
        </lay-form-item>

        <lay-form-item label="理由（选填）">
          <lay-textarea
            v-model="requestForm.reason"
            :rows="4"
            :maxlength="5000"
            show-count
            placeholder="为什么想看这部番？有推荐人也可以写上，方便管理员优先收录"
          />
        </lay-form-item>

        <div class="form-actions">
          <lay-button type="primary" native-type="submit" :loading="requestSubmitting">
            {{ requestSubmitting ? '提交中...' : '提交求番' }}
          </lay-button>
          <lay-button native-type="button" @click="requestOpen = false">取消</lay-button>
        </div>
      </lay-form>
    </lay-card>

    <div class="page-toolbar heroes-toolbar">
      <div class="tab-row">
        <lay-button
          v-for="item in TABS"
          :key="item.key"
          :type="tab === item.key ? 'primary' : undefined"
          @click="switchTab(item.key)"
        >
          {{ item.label }}
        </lay-button>
      </div>
      <span class="page-toolbar__spacer"></span>
      <span class="muted heroes-count">共 {{ currentTotal }} 条</span>
    </div>

    <!-- ===== 番剧库 ===== -->
    <template v-if="tab === 'library'">
      <lay-card v-if="libraryLoading && !library.length">
        <div class="empty-box">正在把番剧库搬过来……</div>
      </lay-card>
      <lay-card v-else-if="libraryError">
        <div class="empty-box">
          <p class="danger-text">{{ libraryError }}</p>
          <lay-button type="primary" @click="loadLibrary(libraryPage)">重试</lay-button>
        </div>
      </lay-card>
      <lay-card v-else-if="!library.length">
        <div class="empty-box">
          <h3 class="empty-box__title">番剧库还是空的</h3>
          <p class="muted">管理员还没有录入番剧，先去求一部番吧</p>
          <lay-button type="primary" @click="openRequest">求一部番</lay-button>
        </div>
      </lay-card>
      <lay-card v-else class="list-card">
        <ul class="entry-list">
          <li v-for="item in library" :key="item.id" class="list-row">
            <div class="list-row__main">
              <div class="request-head">
                <h3 class="list-row__title">{{ item.title }}</h3>
                <lay-tag v-if="item.category" type="normal" variant="light" shape="round" size="sm">
                  {{ item.category }}
                </lay-tag>
              </div>
              <p v-if="item.description" class="entry-desc">{{ item.description }}</p>
              <div class="meta">
                <span>管理员收录</span>
                <time :datetime="item.create_time">{{ item.create_time }}</time>
              </div>
            </div>
            <lay-button v-if="item.link" size="sm" type="primary" @click="openLink(item.link)">
              打开
            </lay-button>
          </li>
        </ul>
        <div v-if="libraryTotal > PAGE_SIZE" class="pagination-wrap">
          <lay-page
            v-model="libraryPage"
            :total="libraryTotal"
            :limit="PAGE_SIZE"
            :layout="['prev', 'page', 'next', 'count']"
            @change="(payload) => changePage(payload, libraryPage, loadLibrary)"
          />
        </div>
      </lay-card>
    </template>

    <!-- ===== 番剧推荐 ===== -->
    <template v-else-if="tab === 'recommend'">
      <lay-card v-if="recommendLoading && !recommendations.length">
        <div class="empty-box">正在加载推荐……</div>
      </lay-card>
      <lay-card v-else-if="recommendError">
        <div class="empty-box">
          <p class="danger-text">{{ recommendError }}</p>
          <lay-button type="primary" @click="loadRecommendations(recommendPage)">重试</lay-button>
        </div>
      </lay-card>
      <lay-card v-else-if="!recommendations.length">
        <div class="empty-box">
          <h3 class="empty-box__title">还没有番剧推荐</h3>
          <p class="muted">有想安利的宝藏番？点击右上角「推荐一部番」</p>
          <lay-button type="primary" @click="openRecommend">推荐一部番</lay-button>
        </div>
      </lay-card>
      <lay-card v-else class="list-card">
        <ul class="entry-list">
          <li v-for="item in recommendations" :key="item.id" class="list-row">
            <span class="avatar-circle" aria-hidden="true">{{ avatarText(item.author_nickname) }}</span>
            <div class="list-row__main">
              <div class="request-head">
                <h3 class="list-row__title">{{ item.anime_name }}</h3>
                <lay-tag
                  :type="reviewMeta(item.review_status).type"
                  variant="light"
                  shape="round"
                  size="sm"
                >
                  {{ reviewMeta(item.review_status).label }}
                </lay-tag>
              </div>
              <p v-if="item.reason" class="entry-desc">推荐理由：{{ item.reason }}</p>
              <div class="meta">
                <span>{{ item.author_nickname || '热心同好' }}</span>
                <time :datetime="item.create_time">{{ item.create_time }}</time>
              </div>
            </div>
            <lay-button v-if="item.link" size="sm" type="primary" @click="openLink(item.link)">
              查看番剧
            </lay-button>
          </li>
        </ul>
        <div v-if="recommendTotal > PAGE_SIZE" class="pagination-wrap">
          <lay-page
            v-model="recommendPage"
            :total="recommendTotal"
            :limit="PAGE_SIZE"
            :layout="['prev', 'page', 'next', 'count']"
            @change="(payload) => changePage(payload, recommendPage, loadRecommendations)"
          />
        </div>
      </lay-card>
    </template>

    <!-- ===== 求番 ===== -->
    <template v-else>
      <lay-card v-if="requestLoading && !requests.length">
        <div class="empty-box">正在把求番名单搬过来……</div>
      </lay-card>
      <lay-card v-else-if="requestError">
        <div class="empty-box">
          <p class="danger-text">{{ requestError }}</p>
          <lay-button type="primary" @click="loadRequests(requestPage)">重试</lay-button>
        </div>
      </lay-card>
      <lay-card v-else-if="!requests.length">
        <div class="empty-box">
          <h3 class="empty-box__title">还没有人求番</h3>
          <p class="muted">想看的番不在库里？点右上角「求一部番」，让管理员安排上</p>
          <lay-button type="primary" @click="openRequest">求一部番</lay-button>
        </div>
      </lay-card>
      <lay-card v-else class="list-card">
        <ul class="entry-list">
          <li v-for="item in requests" :key="item.id" class="list-row">
            <span class="avatar-circle" aria-hidden="true">{{ avatarText(item.author_nickname) }}</span>
            <div class="list-row__main">
              <div class="request-head">
                <h3 class="list-row__title">{{ item.anime_name }}</h3>
                <lay-tag
                  :type="item.status === 1 ? 'normal' : 'warm'"
                  variant="light"
                  shape="round"
                  size="sm"
                >
                  {{ item.status === 1 ? '已收录' : '待收录' }}
                </lay-tag>
              </div>
              <p v-if="item.reason" class="entry-desc">{{ item.reason }}</p>
              <div class="meta">
                <span>{{ item.author_nickname || '热心同好' }}</span>
                <time :datetime="item.create_time">{{ item.create_time }}</time>
              </div>
            </div>
          </li>
        </ul>
        <div v-if="requestTotal > PAGE_SIZE" class="pagination-wrap">
          <lay-page
            v-model="requestPage"
            :total="requestTotal"
            :limit="PAGE_SIZE"
            :layout="['prev', 'page', 'next', 'count']"
            @change="(payload) => changePage(payload, requestPage, loadRequests)"
          />
        </div>
      </lay-card>
    </template>
  </div>
</template>

<style scoped>
.heroes-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-6);
}

.heroes-hero__text {
  min-width: 0;
}

.heroes-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.composer-card {
  margin-bottom: var(--space-6);
  border-color: var(--ghibli-sakura-200);
}

.composer-card :deep(.layui-card-body) {
  padding: var(--space-6) var(--space-8);
}

.composer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.composer-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0;
}

.composer-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.composer-form :deep(.layui-form-item) {
  margin-bottom: 0;
}

.form-error {
  padding: var(--space-3) var(--space-4);
  background: var(--color-error-bg);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-lg);
  color: var(--color-error);
  font-size: var(--text-sm);
}

.heroes-toolbar {
  align-items: center;
}

.heroes-count {
  font-size: var(--text-sm);
}

.list-card :deep(.layui-card-body) {
  padding: var(--space-4) var(--space-8);
}

.entry-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.request-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.request-head .list-row__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-lg);
  white-space: normal;
}

.entry-desc {
  margin: var(--space-2) 0 0;
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
}

.meta {
  margin-top: var(--space-2);
}

@media (max-width: 768px) {
  .heroes-hero {
    padding: var(--space-8) var(--space-6);
  }

  .composer-card :deep(.layui-card-body),
  .list-card :deep(.layui-card-body) {
    padding: var(--space-4) var(--space-5);
  }
}
</style>
