import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { postApi } from '@/api'

export const usePostStore = defineStore('posts', () => {
  // State
  const posts = ref([])
  const loading = ref(false)
  const error = ref('')
  const pagination = ref({
    page: 1,
    page_size: 10,
    total: 0,
    total_pages: 0,
  })
  const hasMore = computed(() => pagination.value.page < pagination.value.total_pages)

  // Actions
  async function fetchPosts(page = 1, append = false) {
    loading.value = true
    error.value = ''
    try {
      const response = await postApi.getList({ page, page_size: pagination.value.page_size })
      if (response.code === 0) {
        const { list, total, page: currentPage, page_size, total_pages } = response.data
        if (append) {
          posts.value = [...posts.value, ...list]
        } else {
          posts.value = list
        }
        pagination.value = { total, page: currentPage, page_size, total_pages }
        return { success: true, list }
      }
      error.value = response.message
      return { success: false, message: response.message }
    } catch (err) {
      error.value = err.message || '获取帖子列表失败'
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    if (loading.value || !hasMore.value) return { success: false, message: '没有更多内容' }
    return fetchPosts(pagination.value.page + 1, true)
  }

  function reset() {
    posts.value = []
    pagination.value = { page: 1, page_size: 10, total: 0, total_pages: 0 }
    error.value = ''
  }

  return {
    posts,
    loading,
    error,
    pagination,
    hasMore,
    fetchPosts,
    loadMore,
    reset,
  }
})