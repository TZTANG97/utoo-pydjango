import { defineStore } from 'pinia'
import type { RouteLocationNormalized } from 'vue-router'

export type TagView = {
  path: string
  fullPath: string
  name?: string | symbol | null
  title: string
  affix?: boolean
}

/** 实验订单详情：按来源列表决定标签标题 */
const DETAIL_FROM_TITLE: Record<string, string> = {
  orders: '实验订单详情',
  'sub-orders': '实验子订单详情',
  'subcontract-orders': '实验分包订单详情',
  'subcontract-sub-orders': '实验分包子订单详情',
  'grab-orders': '抢单实验详情',
}

const DETAIL_TYPE_TITLE: Record<string, string> = {
  '6': '实验订单详情',
  '10': '实验子订单详情',
  '8': '实验分包订单详情',
  '9': '实验分包子订单详情',
}

/** 详情 from → 列表页标签（路径须带 /admin，与 router 一致；否则会插出 404 幽灵标签） */
const LIST_TAG_BY_FROM: Record<string, TagView> = {
  orders: {
    path: '/admin/experiment/orders',
    fullPath: '/admin/experiment/orders',
    name: 'ExperimentOrders',
    title: '实验订单',
  },
  'sub-orders': {
    path: '/admin/experiment/sub-orders',
    fullPath: '/admin/experiment/sub-orders',
    name: 'ExperimentSubOrders',
    title: '实验子订单',
  },
  'subcontract-orders': {
    path: '/admin/experiment/subcontract-orders',
    fullPath: '/admin/experiment/subcontract-orders',
    name: 'ExperimentSubcontractOrders',
    title: '实验分包订单',
  },
  'subcontract-sub-orders': {
    path: '/admin/experiment/subcontract-sub-orders',
    fullPath: '/admin/experiment/subcontract-sub-orders',
    name: 'ExperimentSubcontractSubOrders',
    title: '实验分包子订单',
  },
  'grab-orders': {
    path: '/admin/experiment/grab-orders',
    fullPath: '/admin/experiment/grab-orders',
    name: 'ExperimentGrabOrders',
    title: '抢单实验列表',
  },
}

const ORDER_DETAIL_PATH_PREFIX = '/admin/experiment/order-detail/'

function titleHasOrderNo(title: string) {
  // 「单号 + 空格 + …详情」
  return /^\S+\s.+详情$/.test(title)
}

export function resolveRouteTitle(route: RouteLocationNormalized): string {
  if (route.name === 'ExperimentOrderDetail') {
    const from = String(route.query.from || '')
    const orderNo = String(route.query.orderNo || '').trim()
    const base = DETAIL_FROM_TITLE[from] || String(route.meta?.title || '订单详情')
    return orderNo ? `${orderNo} ${base}` : base
  }
  if (route.name === 'FundDigitalOrders') {
    return String(route.query.title || route.meta?.title || '实验订单')
  }
  return String(route.meta?.title || route.name || '未命名')
}

export function detailTitleByOrderType(orderType: string | number, orderNo?: string): string {
  const base = DETAIL_TYPE_TITLE[String(orderType)] || '订单详情'
  const no = String(orderNo || '').trim()
  return no ? `${no} ${base}` : base
}

export function detailFromByOrderType(orderType: string | number): string {
  const map: Record<string, string> = {
    '6': 'orders',
    '10': 'sub-orders',
    '8': 'subcontract-orders',
    '9': 'subcontract-sub-orders',
  }
  return map[String(orderType)] || 'orders'
}

function toTag(route: RouteLocationNormalized): TagView | null {
  // hidden 仅表示不进侧栏菜单；标签页用 noTagsView 排除
  if (route.meta?.noTagsView) return null
  if (route.path.startsWith('/redirect')) return null
  if (route.path === '/admin/login') return null
  if (route.name === 'NotFound' || route.path === '/404') return null
  if (!route.name && !route.meta?.title) return null

  return {
    path: route.path,
    fullPath: route.fullPath,
    name: route.name,
    title: resolveRouteTitle(route),
    affix: Boolean(route.meta?.affix),
  }
}

export const useTagsViewStore = defineStore('tagsView', {
  state: () => ({
    visitedViews: [] as TagView[],
    refreshKeys: {} as Record<string, number>,
  }),
  actions: {
    ensureSourceListTag(from: string) {
      const meta = LIST_TAG_BY_FROM[from]
      if (!meta) return
      // 用 name 或 path 判断，避免 /admin 前缀不一致时重复插入幽灵标签
      const exists = this.visitedViews.find(
        (item) => item.name === meta.name || item.path === meta.path
      )
      if (exists) return
      const detailIdx = this.visitedViews.findIndex((item) =>
        item.path.startsWith(ORDER_DETAIL_PATH_PREFIX)
      )
      const tag = { ...meta }
      if (detailIdx >= 0) {
        this.visitedViews.splice(detailIdx, 0, tag)
      } else {
        this.visitedViews.push(tag)
      }
    },

    addView(route: RouteLocationNormalized) {
      const tag = toTag(route)
      if (!tag) return

      if (route.name === 'ExperimentOrderDetail') {
        const from = String(route.query.from || '')
        if (from) this.ensureSourceListTag(from)
      }

      const exists = this.visitedViews.find((item) => item.path === tag.path)
      if (exists) {
        exists.fullPath = tag.fullPath
        if (tag.title && tag.title !== '订单详情') {
          // 已有带单号标题时，禁止被短标题回写
          if (titleHasOrderNo(exists.title) && !titleHasOrderNo(tag.title)) {
            return
          }
          this.visitedViews = this.visitedViews.map((item) =>
            item.path === tag.path ? { ...item, fullPath: tag.fullPath, title: tag.title } : item
          )
        }
        return
      }
      this.visitedViews.push(tag)
    },

    updateViewTitle(path: string, title: string) {
      if (!title) return
      const idx = this.visitedViews.findIndex((item) => item.path === path)
      if (idx < 0) {
        // 标签尚未创建时先占位，避免丢单号
        this.visitedViews.push({
          path,
          fullPath: path,
          name: 'ExperimentOrderDetail',
          title,
        })
        return
      }
      // 替换对象，确保 TagsView 响应式刷新
      this.visitedViews.splice(idx, 1, { ...this.visitedViews[idx], title })
    },

    delView(path: string) {
      this.visitedViews = this.visitedViews.filter((item) => item.path !== path || item.affix)
    },

    delOthers(path: string) {
      this.visitedViews = this.visitedViews.filter((item) => item.affix || item.path === path)
    },

    delAll() {
      this.visitedViews = this.visitedViews.filter((item) => item.affix)
    },

    refreshView(path: string) {
      this.refreshKeys[path] = (this.refreshKeys[path] || 0) + 1
    },

    viewKey(route: { path: string; fullPath: string }) {
      const base = route.path.startsWith(ORDER_DETAIL_PATH_PREFIX)
        ? route.path
        : route.fullPath
      return `${base}__${this.refreshKeys[route.path] || 0}`
    },

    reset() {
      this.visitedViews = []
      this.refreshKeys = {}
    },
  },
})
