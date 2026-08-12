/** 按需加载浏览器脚本，同一 URL 只请求一次 */

const pending = new Map()

export function loadScript(src, { attrs = {} } = {}) {
  if (typeof document === 'undefined') {
    return Promise.reject(new Error('document unavailable'))
  }
  const existing = document.querySelector(`script[data-load-src="${src}"]`)
  if (existing) {
    if (existing.dataset.loaded === '1') return Promise.resolve()
    return (
      pending.get(src) ||
      new Promise((resolve, reject) => {
        existing.addEventListener('load', () => resolve(), { once: true })
        existing.addEventListener('error', () => reject(new Error(`load failed: ${src}`)), {
          once: true,
        })
      })
    )
  }
  if (pending.has(src)) return pending.get(src)

  const p = new Promise((resolve, reject) => {
    const s = document.createElement('script')
    s.src = src
    s.async = true
    s.dataset.loadSrc = src
    Object.keys(attrs).forEach((k) => {
      s.setAttribute(k, attrs[k])
    })
    s.onload = () => {
      s.dataset.loaded = '1'
      pending.delete(src)
      resolve()
    }
    s.onerror = () => {
      pending.delete(src)
      s.remove()
      reject(new Error(`load failed: ${src}`))
    }
    document.head.appendChild(s)
  })
  pending.set(src, p)
  return p
}

const AMAP_KEY = '44f700f92d42c3cc186e816bd2ec5df8'
const AMAP_SRC = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}`

export function loadAMap() {
  if (typeof window !== 'undefined' && window.AMap) {
    return Promise.resolve(window.AMap)
  }
  return loadScript(AMAP_SRC).then(() => window.AMap)
}

export function loadMammoth() {
  if (typeof window !== 'undefined' && window.mammoth) {
    return Promise.resolve(window.mammoth)
  }
  return loadScript('/mammoth.browser.min.js').then(() => window.mammoth)
}

export function loadXlsx() {
  if (typeof window !== 'undefined' && window.XLSX) {
    return Promise.resolve(window.XLSX)
  }
  return loadScript('/xlsx.full.min.js').then(() => window.XLSX)
}
