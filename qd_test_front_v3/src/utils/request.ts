import axios, { type AxiosRequestConfig } from 'axios'
import { ElNotification } from 'element-plus'
import { getToken } from '@/utils/auth'
import { resolveHttpErrorMessage } from '@/utils/error-message'

type RequestConfig = AxiosRequestConfig & { silentError?: boolean }

const service = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/api',
  timeout: 15000,
  headers: {
    Accept: 'application/json, */*',
  },
})

service.interceptors.request.use(
  (config) => {
    // 中台渠道标识：审计/差异配置用，不据此拆服务（见 docs/中台身份与菜单约定.md）
    config.headers['X-Channel'] = 'pc'
    const token = getToken()
    if (token) {
      config.headers.token = token
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

function normalizeBody(body: unknown) {
  if (!body || typeof body !== 'object') return body
  const b = body as Record<string, unknown>
  if (typeof b.code === 'number' && 'data' in b) {
    const message =
      (typeof b.message === 'string' && b.message.trim()) ||
      (b.code === 0 ? 'ok' : '操作失败，请重试')
    const payload = b.data ?? b.obj
    const normalized = { ...b, res: b.code === 0, resMsg: message, obj: payload, data: payload }
    if (b.code === 401 && typeof window !== 'undefined') {
      const path = window.location.hash || window.location.pathname || ''
      if (!path.includes('/login')) {
        console.warn('[api] 登录已失效，请重新登录')
      }
    }
    return normalized
  }
  if (typeof b.res === 'boolean') {
    const message =
      (typeof b.resMsg === 'string' && b.resMsg.trim()) ||
      (typeof b.message === 'string' && b.message.trim()) ||
      (b.res ? 'ok' : '操作失败，请重试')
    const payload = b.obj ?? b.data
    return { ...b, code: b.res ? 0 : 1, message, resMsg: message, data: payload, obj: payload }
  }
  return body
}

service.interceptors.response.use(
  (response) => normalizeBody(response.data),
  (error) => {
    const config = error.config as RequestConfig | undefined
    if (!config?.silentError) {
      const message = resolveHttpErrorMessage(error)
      ElNotification({
        title: '提示',
        type: 'error',
        message,
        duration: 5000,
      })
    }
    return Promise.reject(error)
  }
)

export default service
