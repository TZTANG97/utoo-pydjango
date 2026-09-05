/** 浏览器端路径拼接（替代 Node path.resolve） */
export function resolvePath(basePath, routePath) {
  if (!routePath) return basePath || '/'
  if (routePath.startsWith('http://') || routePath.startsWith('https://')) {
    return routePath
  }
  const base = (basePath || '').replace(/\/$/, '')
  const segment = String(routePath).replace(/^\//, '')
  if (!base) return `/${segment}`
  return segment ? `${base}/${segment}` : base
}
