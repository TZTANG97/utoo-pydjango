/** 从 HTTP 错误中提取可读文案 */
export function resolveHttpErrorMessage(error: unknown): string {
  const err = error as {
    response?: { status?: number; data?: unknown }
    code?: string
    message?: string
  }

  const status = err.response?.status
  const data = err.response?.data

  if (data && typeof data === 'object') {
    const body = data as Record<string, unknown>
    const detail = body.detail
    const msg = body.message ?? body.resMsg ?? body.msg
    if (typeof msg === 'string' && msg.trim()) return msg.trim()
    if (typeof detail === 'string' && detail.trim()) return detail.trim()
    if (Array.isArray(detail)) {
      const text = detail
        .map((item) => {
          if (typeof item === 'string') return item
          if (item && typeof item === 'object' && 'msg' in item) {
            return String((item as { msg?: string }).msg || '')
          }
          return ''
        })
        .filter(Boolean)
        .join('；')
      if (text) return text
    }
  }

  const statusMap: Record<number, string> = {
    400: '请求参数错误',
    401: '登录已过期，请重新登录',
    403: '没有权限访问',
    404: '请求的资源不存在',
    405: '请求方法错误',
    408: '请求超时',
    500: '服务器错误，请稍后重试',
    502: '网关错误，后端可能未启动',
    503: '服务暂不可用，请稍后重试',
  }

  if (status && statusMap[status]) return statusMap[status]
  if (err.code === 'ECONNABORTED') return '请求超时，请检查网络或稍后重试'
  if (err.message === 'Network Error') {
    return '无法连接服务器，请确认后端已启动（Python :18083 或 Java UAT）'
  }
  if (err.message?.trim()) return err.message.trim()
  return '请求失败，请重试'
}

/** 业务响应 res/resMsg 为空时的兜底 */
export function resolveBizMessage(
  res: { resMsg?: string; message?: string; code?: number } | null | undefined,
  fallback = '操作失败，请重试'
): string {
  const msg = res?.resMsg ?? res?.message
  if (typeof msg === 'string' && msg.trim()) return msg.trim()
  return fallback
}

/** 统一 notify 参数，避免 title 有内容、message 为空 */
export function normalizeNotifyOptions(options: unknown): Record<string, unknown> {
  if (typeof options === 'string') {
    const text = options.trim() || '操作失败，请重试'
    return { message: text }
  }
  if (!options || typeof options !== 'object') {
    return { message: '操作失败，请重试' }
  }
  const opts = { ...(options as Record<string, unknown>) }
  const message = opts.message ?? opts.msg
  if (typeof message === 'string' && message.trim()) {
    opts.message = message.trim()
    return opts
  }
  if (typeof opts.title === 'string' && opts.title.trim() && opts.title !== '提示') {
    opts.message = opts.title.trim()
    return opts
  }
  opts.message = '操作失败，请重试'
  return opts
}
