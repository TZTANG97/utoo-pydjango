/**
 * 讨论区图片 URL — 对齐 Java / 阿里云 OSS 桶 qgongye
 * 可通过 .env.development 覆盖：VITE_OSS_PUBLIC_BASE
 */
const OSS_BASE =
  (import.meta.env.VITE_OSS_PUBLIC_BASE || '').replace(/\/$/, '') ||
  'https://qgongye.oss-cn-shanghai.aliyuncs.com'

const DEFAULT_AVATAR = `${OSS_BASE}/goods/531da299-7156-4ad0-95a4-c94e978c924d.jpg`

/**
 * @param {string} [path]
 * @param {string} [name]
 * @param {string} [imageUrl] 后端可选完整地址
 */
export function buildOssImageUrl(path, name, imageUrl) {
  if (imageUrl && String(imageUrl).startsWith('http')) {
    return imageUrl
  }
  const p = (path || '').trim()
  const n = (name || '').trim()
  if (p.startsWith('http://') || p.startsWith('https://')) {
    return n ? `${p.replace(/\/$/, '')}/${n}` : p
  }
  if (!p && !n) {
    return DEFAULT_AVATAR
  }
  if (p && !n) {
    return `${OSS_BASE}/${p.replace(/^\//, '')}`
  }
  return `${OSS_BASE}/${p.replace(/^\//, '')}/${n.replace(/^\//, '')}`
}

export function defaultAvatarUrl() {
  return DEFAULT_AVATAR
}

export { OSS_BASE }
