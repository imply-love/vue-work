<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { postApi } from '@/api'

const CATEGORIES = ['新番讨论', '老番怀旧', '安利分享', '求推荐', '同人创作', '其他']

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)

const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const fieldError = ref('')
// 编辑时帖子的状态：1-已发布 0-草稿；新建时为 null
const postStatus = ref(null)

const emptyForm = () => ({
  title: '',
  category: '',
  tags: '',
  summary: '',
  content: '',
  visibility: 0,
})

const form = ref(emptyForm())

const toast = (type, title, message) => {
  window.$ghibli?.showToast({ type, title, message })
}

const loadDetail = async () => {
  loadError.value = ''
  fieldError.value = ''

  // 新建：直接使用空表单
  if (!isEdit.value) {
    form.value = emptyForm()
    postStatus.value = null
    loading.value = false
    return
  }

  loading.value = true
  try {
    const res = await postApi.getDetail(route.params.id)
    if (res.code !== 0) {
      loadError.value = res.message || '加载帖子失败'
      return
    }
    // 只能编辑自己的帖子
    if (!res.data.is_self) {
      toast('error', '无权编辑', '只能编辑自己发布的帖子')
      router.replace('/content/posts')
      return
    }
    const item = res.data
    form.value = {
      title: item.title || '',
      category: item.category || '',
      tags: item.tags || '',
      summary: item.summary || '',
      content: item.content || '',
      visibility: Number.isInteger(item.visibility) ? item.visibility : 0,
    }
    postStatus.value = item.status
  } catch (err) {
    loadError.value = err.message || '加载帖子失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 顶部提示：新建 / 编辑草稿 / 编辑已发布帖子
const notice = computed(() => {
  if (loading.value || loadError.value) return ''
  if (!isEdit.value) return '发布后会立即出现在讨论区；没写完也可以先存进草稿箱。'
  if (postStatus.value === 0) return '这是一篇草稿，草稿发布后才会出现在讨论区。'
  return '修改已发布帖子会把发布时间更新为本次修改时间，并标记为「二编/三编…」，已有评论不受影响。'
})

const validate = (asDraft) => {
  const title = form.value.title.trim()
  const content = form.value.content.trim()
  const summary = form.value.summary.trim()
  const tags = form.value.tags.trim()

  if (title.length > 200) return '标题不能超过 200 个字'
  if (summary.length > 255) return '摘要不能超过 255 个字'
  if (tags.length > 255) return '标签不能超过 255 个字'
  if (content.length > 20000) return '正文不能超过 20000 个字'

  if (asDraft) {
    // 草稿只要求三者之一
    if (!title && !summary && !content) return '草稿至少需要填写标题、摘要或正文之一'
  } else {
    if (!title) return '请填写标题'
    if (!content) return '请填写正文'
  }
  return ''
}

const normalizeVisibility = (value) => {
  const num = Number(value)
  return [0, 1, 2].includes(num) ? num : 0
}

const submit = async (asDraft) => {
  if (submitting.value) return

  fieldError.value = ''
  const message = validate(asDraft)
  if (message) {
    fieldError.value = message
    return
  }

  const payload = {
    title: form.value.title.trim(),
    category: form.value.category || '',
    tags: form.value.tags.trim(),
    summary: form.value.summary.trim(),
    content: form.value.content.trim(),
    visibility: normalizeVisibility(form.value.visibility),
    draft: asDraft ? 1 : 0,
  }

  submitting.value = true
  try {
    const res = isEdit.value
      ? await postApi.update(route.params.id, payload)
      : await postApi.create(payload)

    if (res.code === 0) {
      const id = res.data?.id || route.params.id
      if (asDraft) {
        toast('success', '已保存到草稿箱', '可以在「内容管理 - 草稿箱」继续编辑')
        router.push('/content/drafts')
      } else if (isEdit.value) {
        toast('success', '更新成功', '帖子已保存')
        router.push(`/posts/${id}`)
      } else {
        toast('success', '已提交审核', '帖子审核通过后会在讨论区公开显示')
        router.push('/content/posts')
      }
    } else {
      fieldError.value = res.message || '操作失败，请稍后重试'
    }
  } catch (err) {
    // 1014：账号被封禁，发帖/编辑被拒绝
    if (err?.code === 1014) {
      toast('warning', '账号已被封禁', '暂时无法发帖或编辑，可前往申诉页面提交申诉')
      router.push('/appeal')
      return
    }
    fieldError.value = err?.message || '操作失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

const cancel = () => router.back()

onMounted(loadDetail)

// /posts/new 与 /posts/:id/edit 共用同一个组件，参数变化时重新初始化
watch(
  () => route.params.id,
  () => loadDetail()
)
</script>

<template>
  <div class="page-wrap">
    <section class="page-hero">
      <h1 class="page-title">{{ isEdit ? '编辑帖子' : '写新帖' }}</h1>
      <p class="page-sub">
        {{ isEdit ? '把想说的话再打磨一下，改完记得保存。' : '想到什么就写什么，讨论区等你开楼。' }}
      </p>
    </section>

    <p v-if="notice" class="editor-tip">{{ notice }}</p>

    <lay-card>
      <div v-if="loading" class="loading-box">正在加载帖子…</div>

      <div v-else-if="loadError" class="empty-box">
        <p class="danger-text">{{ loadError }}</p>
        <div class="form-actions center-actions">
          <lay-button type="primary" @click="loadDetail">重试</lay-button>
          <lay-button @click="cancel">返回</lay-button>
        </div>
      </div>

      <lay-form v-else :model="form" label-position="top">
        <lay-form-item label="标题" required>
          <lay-input
            v-model="form.title"
            :maxlength="200"
            placeholder="一句话说清你想聊什么，例如：有人看过《哈尔的移动城堡》吗？"
          />
        </lay-form-item>

        <div class="editor-grid">
          <lay-form-item label="分类">
            <lay-select v-model="form.category" placeholder="选择分类（可不选）">
              <lay-select-option v-for="cat in CATEGORIES" :key="cat" :label="cat" :value="cat" />
            </lay-select>
          </lay-form-item>

          <lay-form-item label="可见性">
            <lay-select v-model="form.visibility" placeholder="选择可见范围">
              <lay-select-option label="公开（所有人可见）" :value="0" />
              <lay-select-option label="私密（仅自己可见）" :value="1" />
              <lay-select-option label="仅好友可见" :value="2" />
            </lay-select>
          </lay-form-item>
        </div>

        <lay-form-item label="标签">
          <lay-input
            v-model="form.tags"
            :maxlength="255"
            placeholder="选填，多个标签用逗号分隔，例如：宫崎骏,治愈,经典"
          />
        </lay-form-item>

        <lay-form-item label="摘要">
          <lay-textarea
            v-model="form.summary"
            :maxlength="255"
            :rows="2"
            placeholder="选填，一句话概括帖子内容，让列表卡片更醒目"
          />
        </lay-form-item>

        <lay-form-item label="正文" required>
          <lay-textarea
            v-model="form.content"
            :maxlength="20000"
            :rows="14"
            placeholder="展开聊聊：剧情、角色、观后感，想到什么写什么"
          />
        </lay-form-item>

        <p v-if="fieldError" class="danger-text field-error" role="alert">{{ fieldError }}</p>

        <div class="form-actions">
          <lay-button type="primary" :loading="submitting" @click="submit(false)">
            {{ submitting ? '提交中…' : '发布' }}
          </lay-button>
          <lay-button :loading="submitting" @click="submit(true)">保存草稿</lay-button>
          <lay-button :disabled="submitting" @click="cancel">取消</lay-button>
        </div>
      </lay-form>
    </lay-card>
  </div>
</template>

<style scoped>
.editor-tip {
  margin: 0 0 var(--space-6);
  padding: var(--space-4) var(--space-6);
  background: var(--ghibli-sky-50);
  border: 1px solid var(--ghibli-sky-200);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--ghibli-sky-800);
}

.editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-6);
}

.loading-box {
  padding: var(--space-16) 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.field-error {
  margin: 0 0 var(--space-4);
  font-size: var(--text-sm);
}

.center-actions {
  justify-content: center;
  margin-top: var(--space-4);
}

@media (max-width: 768px) {
  .editor-grid {
    grid-template-columns: 1fr;
  }
}
</style>
