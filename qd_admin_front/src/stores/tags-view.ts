import { defineStore } from 'pinia'
import type { RouteLocationNormalized } from 'vue-router'

export type TagView = {
  path: string
  fullPath: string
  name?: string | symbol | null
  title: string
  affix?: boolean
}

function toTag(route: RouteLocationNormalized): TagView | null {
  if (route.meta?.hidden) return null
  if (route.path.startsWith('/redirect')) return null
  if (route.path === '/login') return null
  if (!route.name && !route.meta?.title) return null

  return {
    path: route.path,
    fullPath: route.fullPath,
    name: route.name,
    title: String(route.meta?.title || route.name || '未命名'),
    affix: Boolean(route.meta?.affix),
  }
}

export const useTagsViewStore = defineStore('tagsView', {
  state: () => ({
    visitedViews: [] as TagView[],
    refreshKeys: {} as Record<string, number>,
  }),
  actions: {
    addView(route: RouteLocationNormalized) {
      const tag = toTag(route)
      if (!tag) return
      const exists = this.visitedViews.find((item) => item.path === tag.path)
      if (exists) {
        exists.fullPath = tag.fullPath
        exists.title = tag.title
        return
      }
      this.visitedViews.push(tag)
    },
    delView(path: string) {
      this.visitedViews = this.visitedViews.filter((item) => item.path !== path || item.affix)
    },
    delOthers(path: string) {
      this.visitedViews = this.visitedViews.filter(
        (item) => item.affix || item.path === path
      )
    },
    delAll() {
      this.visitedViews = this.visitedViews.filter((item) => item.affix)
    },
    refreshView(path: string) {
      this.refreshKeys[path] = (this.refreshKeys[path] || 0) + 1
    },
    viewKey(route: { path: string; fullPath: string }) {
      return `${route.fullPath}__${this.refreshKeys[route.path] || 0}`
    },
    reset() {
      this.visitedViews = []
      this.refreshKeys = {}
    },
  },
})
