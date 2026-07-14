import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { DataTableResult } from '@/api/order-settings'

export function useDataTable<T extends Record<string, unknown>>(
  loader: (params: Record<string, unknown>) => Promise<DataTableResult<T> | unknown>
) {
  const loading = ref(false)
  const rows = ref<T[]>([])
  const total = ref(0)
  const pagination = reactive({
    page: 1,
    pageSize: 10,
  })

  async function load(extra: Record<string, unknown> = {}) {
    loading.value = true
    try {
      const start = (pagination.page - 1) * pagination.pageSize
      const res = (await loader({
        draw: pagination.page,
        start,
        length: pagination.pageSize,
        ...extra,
      })) as DataTableResult<T>
      rows.value = Array.isArray(res?.data) ? res.data : []
      total.value = Number(res?.recordsTotal || 0)
    } catch (err) {
      rows.value = []
      total.value = 0
      // 网络错误已由 axios 拦截器提示；业务失败（如未登录）在此提示
      const axiosErr = err as { isAxiosError?: boolean; message?: string }
      if (!axiosErr?.isAxiosError) {
        ElMessage.error(err instanceof Error ? err.message : '加载失败')
      }
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    rows,
    total,
    pagination,
    load,
  }
}
