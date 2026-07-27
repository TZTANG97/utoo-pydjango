import type { Router } from 'vue-router'
import { useUserStore } from '@admin/stores/user'
import { getToken } from '@admin/utils/auth'
import { handleUnauthorized } from '@admin/utils/request'
import NProgress from 'nprogress'

NProgress.configure({ showSpinner: false })

const whiteList = ['/admin/login']

/** 仅处理 /admin/* 路由；由根 permission 按 path 分发调用 */
export function setupAdminPermission(router: Router) {
  router.beforeEach(async (to, _from, next) => {
    if (!to.path.startsWith('/admin')) {
      next()
      return
    }

    NProgress.start()
    document.title = to.meta.title
      ? `${to.meta.title} - 愉兔检测管理平台`
      : '愉兔检测管理平台'

    const token = getToken()
    const userStore = useUserStore()

    if (token) {
      if (to.path === '/admin/login') {
        next({ path: '/admin/dashboard' })
        NProgress.done()
        return
      }
      try {
        if (!userStore.loaded) {
          await userStore.ensureProfile()
        }
        next()
      } catch {
        userStore.logout()
        handleUnauthorized()
        next(`/admin/login?redirect=${encodeURIComponent(to.fullPath)}`)
        NProgress.done()
      }
      return
    }

    if (whiteList.includes(to.path)) {
      next()
      return
    }

    next(`/admin/login?redirect=${encodeURIComponent(to.fullPath)}`)
    NProgress.done()
  })

  router.afterEach((to) => {
    if (to.path.startsWith('/admin')) {
      NProgress.done()
    }
  })
}
