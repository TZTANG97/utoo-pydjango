/** 讨论区时间展示：相对时间 + 完整时间（悬停 title） */

function pad(n) {
  return String(n).padStart(2, '0')
}

export function parseDate(value) {
  if (value == null || value === '') return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

/** 列表用：刚刚 / 3分钟前 / 昨天 14:30 / 03-15 09:20 */
export function formatRelativeTime(value) {
  const date = parseDate(value)
  if (!date) return ''
  const now = Date.now()
  const diff = now - date.getTime()
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const hm = `${pad(date.getHours())}:${pad(date.getMinutes())}`

  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / minute)} 分钟前`
  if (diff < day) return `${Math.floor(diff / hour)} 小时前`
  if (diff < 2 * day) return `昨天 ${hm}`

  const y = date.getFullYear()
  const thisY = new Date().getFullYear()
  const md = `${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  if (y === thisY) return `${md} ${hm}`
  return `${y}-${md} ${hm}`
}

/** 详情/悬停：2024-03-15 09:20:30 */
export function formatFullTime(value) {
  const date = parseDate(value)
  if (!date) return ''
  return date.toLocaleString('zh-CN', { hour12: false })
}
