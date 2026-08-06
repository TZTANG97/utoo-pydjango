import { defineStore } from 'pinia'

import {

  adminLogin,

  fetchAdminMain,

  fetchAdminUserCenter,

  fetchAdminWelcome,

} from '@/api/auth'

import type { AdminMenuItem, LoginResult, WelcomeData } from '@/types/admin'

import { getToken, removeToken, setToken } from '@/utils/auth'

import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'
import { indexPendingMenus } from '@/utils/menu-route'



function normalizeJavaChildMenu(item: Record<string, unknown>): AdminMenuItem {

  const children = Array.isArray(item.childrenMenus)

    ? item.childrenMenus.map((child) =>

        normalizeJavaChildMenu(child as Record<string, unknown>)

      )

    : []

  return {

    id: item.id as string | number | undefined,

    menu_name: String(item.name || item.menu_name || ''),

    menu_url: String(item.url || item.menu_url || ''),

    menu_icon: String(item.icon || item.menu_icon || ''),

    children,

  }

}



function normalizeJavaTopMenu(item: Record<string, unknown>): AdminMenuItem {

  const children = Array.isArray(item.childMenu)

    ? item.childMenu.map((child) =>

        normalizeJavaChildMenu(child as Record<string, unknown>)

      )

    : []

  return {

    id: item.id as string | number | undefined,

    menu_name: String(item.menuName || item.menu_name || ''),

    menu_url: String(item.url || item.menu_url || ''),

    menu_icon: String(item.menuIcon || item.menu_icon || ''),

    children,

  }

}



function buildMenuTree(items: AdminMenuItem[]): AdminMenuItem[] {

  const map = new Map<string, AdminMenuItem>()

  const roots: AdminMenuItem[] = []



  items.forEach((item) => {

    map.set(String(item.id), { ...item, children: [] })

  })



  map.forEach((item) => {

    const parentId = item.parent_id

    if (parentId && map.has(String(parentId))) {

      map.get(String(parentId))!.children!.push(item)

    } else {

      roots.push(item)

    }

  })



  const sortNodes = (nodes: AdminMenuItem[]) => {

    nodes.sort((a, b) => Number(a.menu_order || 0) - Number(b.menu_order || 0))

    nodes.forEach((node) => {

      if (node.children?.length) sortNodes(node.children)

    })

  }

  sortNodes(roots)

  return roots

}



function normalizeMenus(raw: unknown): AdminMenuItem[] {

  if (!Array.isArray(raw) || !raw.length) return []

  const first = raw[0] as Record<string, unknown>

  if ('childMenu' in first || 'menuName' in first) {

    return raw.map((item) => normalizeJavaTopMenu(item as Record<string, unknown>))

  }

  return buildMenuTree(raw as AdminMenuItem[])

}



export const useUserStore = defineStore('admin-user', {

  state: () => ({

    token: getToken() || '',

    userName: '',

    loginName: '',

    userType: 0,

    roleName: '',

    menus: [] as AdminMenuItem[],

    pendingMenus: {} as Record<string, { title: string; url: string }>,

    profile: null as Record<string, unknown> | null,

    welcome: null as WelcomeData | null,

    loaded: false,

  }),

  actions: {

    async login(loginName: string, password: string) {

      const res = await adminLogin({ loginName, password })

      if (!isAjaxOk(res)) {

        throw new Error(ajaxErrorMessage(res, '登录失败'))

      }

      const data = (res.obj || {}) as LoginResult

      if (!data.token) {

        throw new Error('登录成功但未返回 token')

      }

      this.token = data.token

      setToken(data.token)

      this.userName = data.userName || loginName

      this.loginName = data.loginName || loginName

      this.userType = Number(data.userType || 0)

      this.roleName = data.uRoleName || ''

      await this.loadShell()

    },

    async loadShell() {

      const mainRes = await fetchAdminMain()

      if (!isAjaxOk(mainRes)) {

        throw new Error(ajaxErrorMessage(mainRes, '加载菜单失败'))

      }

      const mainObj = (mainRes.obj || {}) as {

        menus?: unknown

        userName?: string

      }

      this.menus = normalizeMenus(mainObj.menus)
      this.pendingMenus = indexPendingMenus(this.menus)

      if (mainObj.userName) {

        this.userName = mainObj.userName

      }



      const centerRes = await fetchAdminUserCenter({ silentError: true })

      if (isAjaxOk(centerRes)) {

        this.profile = (centerRes.obj || null) as Record<string, unknown> | null

        const profile = this.profile || {}

        if (profile.trueName || profile.userName) {

          this.userName = String(profile.trueName || profile.userName)

        }

        if (profile.type || profile.utooType) {

          this.roleName = String(profile.type || profile.utooType)

        }

      }



      const welcomeRes = await fetchAdminWelcome({ silentError: true })

      if (isAjaxOk(welcomeRes)) {

        this.welcome = (welcomeRes.obj || null) as WelcomeData | null

        if (this.welcome?.userName) {

          this.userName = this.welcome.userName

        }

        if (this.welcome?.loginName) {

          this.loginName = this.welcome.loginName

        }

        if (this.welcome?.roleName) {

          this.roleName = this.welcome.roleName

        }

        if (this.welcome?.userType != null) {

          this.userType = Number(this.welcome.userType) || 0

        }

      }

      this.loaded = true

    },

    async ensureProfile() {

      if (this.loaded && this.token) return

      if (!this.token) {

        throw new Error('未登录')

      }

      await this.loadShell()

    },

    logout() {

      this.token = ''

      this.userName = ''

      this.loginName = ''

      this.userType = 0

      this.roleName = ''

      this.menus = []

      this.pendingMenus = {}

      this.profile = null

      this.welcome = null

      this.loaded = false

      removeToken()

    },

  },

})

