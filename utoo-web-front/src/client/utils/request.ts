import axios, { type AxiosRequestConfig } from 'axios'
import { ElNotification } from 'element-plus'
import { getToken, removeToken } from '@client/utils/auth'
import { resolveHttpErrorMessage } from '@client/utils/error-message'

type RequestConfig = AxiosRequestConfig & { silentError?: boolean }

/** 并发认证失败只提示一次 */
let authErrorNotifiedAt = 0
const AUTH_NOTIFY_COOLDOWN_MS = 3000

function isLoginPage(): boolean {
  if (typeof window === 'undefined') return false
  const path = window.location.hash || window.location.pathname || ''
  return path.includes('/login')
}

function isAuthFailureMessage(message: string): boolean {
  return (
    message.includes('认证令牌') ||
    message.includes('登录已过期') ||
    message.includes('登录已失效') ||
    message.includes('未登录')
  )
}

const service = axios.create({
  // 去掉首尾空白，避免启动脚本/环境变量把 `/api` 写成 `/api ` 导致全部请求变成 `/api%20/...` 而 404
  baseURL: String(import.meta.env.VITE_APP_BASE_API || '/api').trim() || '/api',
  timeout: 15000,
  headers: {
    Accept: 'application/json, */*',
  },
})

service.interceptors.request.use(
  (config) => {
    // 中台渠道标识：审计/差异配置用，不据此拆服务（见 docs/中台身份与菜单约定.md）
    config.headers['X-Channel'] = 'pc'
    if (typeof config.baseURL === 'string') {
      config.baseURL = config.baseURL.trim() || '/api'
    }
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
      if (!isLoginPage()) {
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
    const status = error.response?.status
    const message = resolveHttpErrorMessage(error)
    const authByMessage = typeof message === 'string' && isAuthFailureMessage(message)
    // 401，或 403 且文案为令牌/登录失效（勿把业务无权限 403 当成掉登录）
    const isAuthError = status === 401 || (status === 403 && authByMessage) || authByMessage

    if (isAuthError) {
      try {
        removeToken()
      } catch {
        /* ignore */
      }
    }

    // 登录页或调用方声明 silentError：不弹窗（路由守卫自行处理）
    if (config?.silentError || (isAuthError && isLoginPage())) {
      return Promise.reject(error)
    }

    const now = Date.now()
    if (isAuthError) {
      if (now - authErrorNotifiedAt < AUTH_NOTIFY_COOLDOWN_MS) {
        return Promise.reject(error)
      }
      authErrorNotifiedAt = now
    }
    ElNotification({
      title: '提示',
      type: 'error',
      message,
      duration: 5000,
    })
    return Promise.reject(error)
  }
)

export default service
