import axios, { type AxiosInstance } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@client/stores/auth'

const BASE_URL = String(import.meta.env.VITE_API_BASE || import.meta.env.VITE_APP_BASE_API || '/api').trim() || '/api'

export const request: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

request.interceptors.request.use((config) => {
  if (typeof config.baseURL === 'string') {
    config.baseURL = config.baseURL.trim() || '/api'
  }
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

request.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout()
      const base = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')
      window.location.href = `${base}/login`
    } else {
      const detail = err.response?.data?.detail
      const msg = err.response?.data?.message
      ElMessage.error(detail || msg || err.message || '请求失败')
    }
    return Promise.reject(err)
  }
)
