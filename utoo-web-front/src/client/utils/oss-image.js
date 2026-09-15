/**
 * 讨论区 / 实验卡片图片 URL — 对齐 Java / 阿里云 OSS 桶 qgongye
 * 可通过 .env.development 覆盖：VITE_OSS_PUBLIC_BASE
 */
const OSS_BASE =
  (import.meta.env.VITE_OSS_PUBLIC_BASE || '').replace(/\/$/, '') ||
  'https://qgongye.oss-cn-shanghai.aliyuncs.com'

const DEFAULT_AVATAR = `${OSS_BASE}/goods/531da299-7156-4ad0-95a4-c94e978c924d.jpg`

/** 分类/实验卡片缺省图（本地静态资源，避免外链失败） */
export const CATALOG_PLACEHOLDER =
  new URL('../static/hp1.webp', import.meta.url).href

const NON_IMAGE_EXT = /\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|7z|mp4|mov|avi)(\?|$)/i

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

/** 是否像可渲染的图片地址（排除 pdf 等） */
export function isLikelyImageUrl(url) {
  const s = String(url || '').trim()
  if (!s) return false
  return !NON_IMAGE_EXT.test(s)
}

/**
 * 实验/分类卡片封面：修正空链、pdf、相对路径；失败时用占位图
 * @param {string} [url]
 */
export function resolveCatalogImage(url) {
  const s = String(url || '').trim()
  if (!s || !isLikelyImageUrl(s)) {
    return CATALOG_PLACEHOLDER
  }
  if (s.startsWith('http://') || s.startsWith('https://') || s.startsWith('data:') || s.startsWith('blob:')) {
    return s
  }
  if (s.startsWith('//')) {
    return `https:${s}`
  }
  return `${OSS_BASE}/${s.replace(/^\//, '')}`
}

/** img @error 回退占位，避免破图死循环 */
export function onCatalogImgError(event) {
  const el = event && event.target
  if (!el || el.dataset.fallback === '1') return
  el.dataset.fallback = '1'
  el.src = CATALOG_PLACEHOLDER
}

export { OSS_BASE, DEFAULT_AVATAR }
