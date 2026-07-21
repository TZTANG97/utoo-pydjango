import axios, { type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from '@/utils/auth'

export type AjaxBody = {
  res?: boolean | number
  resMsg?: string
  obj?: unknown
  code?: number
  message?: string
  data?: unknown
  draw?: number
  recordsTotal?: number
  recordsFiltered?: number
}

export type RequestConfig = AxiosRequestConfig & { silentError?: boolean }

const service = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/api',
  timeout: 15000,
  headers: {
    Accept: 'application/json, */*',
  },
})

service.interceptors.request.use((config) => {
  // 中台渠道标识：审计/差异配置用，不据此拆服务（见 docs/中台身份与菜单约定.md）
  config.headers['X-Channel'] = 'admin'
  const token = getToken()
  if (token) {
    config.headers.token = token
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function normalizeBody(body: unknown): AjaxBody {
  if (typeof body === 'boolean') {
    return { res: body, code: body ? 0 : 1 }
  }
  if (!body || typeof body !== 'object') return {}
  const b = body as AjaxBody
  if (typeof b.code === 'number' && 'data' in b) {
    return {
      ...b,
      res: b.code === 0,
      resMsg: b.message,
      obj: b.data,
    }
  }
  if (typeof b.res === 'boolean' || typeof b.res === 'number') {
    const ok = b.res === true || b.res === 1
    return {
      ...b,
      res: ok,
      code: ok ? 0 : 1,
      message: b.resMsg,
      data: b.obj,
    }
  }
  return b
}

service.interceptors.response.use(
  (response) => normalizeBody(response.data) as typeof response.data,
  (error) => {
    const config = error.config as RequestConfig | undefined
    if (!config?.silentError) {
      const msg =
        error.response?.data?.resMsg ||
        error.response?.data?.message ||
        error.message ||
        '网络异常，请稍后重试'
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export function isAjaxOk(body: AjaxBody | undefined): body is AjaxBody & { res: true } {
  return !!body && (body.res === true || body.res === 1)
}

export function ajaxErrorMessage(body: AjaxBody | undefined, fallback = '操作失败') {
  return body?.resMsg || body?.message || fallback
}

export function handleUnauthorized() {
  removeToken()
  const hash = window.location.hash || ''
  if (!hash.includes('/login')) {
    window.location.hash = '#/login'
  }
}

export default service
