import store from './store'
import { ElMessage as Message } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { getToken } from '@client/utils/auth'
import getPageTitle from '@client/utils/get-page-title'

NProgress.configure({ showSpinner: false })

const whiteList = ['/login', '/', '/home', '/cate', '/cateDetail', '/companyInt', '/discussion', '/discussionNotes']

function isWhiteRoute(path) {
  return (
    whiteList.indexOf(path) !== -1 ||
    path.startsWith('/test_detail') ||
    path.startsWith('/discussion/')
  )
}

function isPersonalCenterRoute(path) {
  return path === '/b' || path.startsWith('/b/')
}

function withTimeout(promise, ms, label) {
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      setTimeout(() => reject(new Error(`${label} timeout after ${ms}ms`)), ms)
    }),
  ])
}

/** 仅处理非 /admin 路由 */
export function setupClientPermission(router) {
  router.beforeEach(async (to, from, next) => {
    if (to.path.startsWith('/admin')) {
      next()
      return
    }

    NProgress.start()
    document.title = getPageTitle(to.meta.title)

    const hasToken = getToken()
    const onWhiteList = isWhiteRoute(to.path)

    if (!store.state.cate.cateList.length) {
      store.dispatch('cate/getCateList').catch((e) => {
        console.warn('[permission] 加载实验分类失败，页面仍可访问', e)
      })
    }

    if (hasToken) {
      if (to.path === '/login') {
        next({ path: '/b/order' })
        NProgress.done()
        return
      }

      const hasGetUserInfo = store.getters.name
      if (hasGetUserInfo) {
        next()
        return
      }

      const loadProfile = () =>
        withTimeout(store.dispatch('user/getInfo'), 8000, 'getInfo').catch((error) => {
          console.warn('[permission] getInfo failed', error)
          return null
        })

      if (isPersonalCenterRoute(to.path)) {
        loadProfile()
        next()
        return
      }

      if (onWhiteList) {
        loadProfile().then(async (res) => {
          // 业务失败，或 401 已被拦截器清掉 cookie：同步清掉本地登录态
          const authGone = !res && !getToken()
          if ((res && res.res === false) || authGone) {
            if (res && !res.res) {
              console.warn('[permission] getInfo business error', res.resMsg)
            }
            await store.dispatch('user/resetToken').catch(() => {})
          }
        })
        next()
        return
      }

      try {
        const res = await loadProfile()
        if (res && res.res === false) {
          throw new Error(res.resMsg || 'getInfo failed')
        }
        next()
      } catch (error) {
        await store.dispatch('user/resetToken')
        console.warn('[permission] getInfo failed', error)
        Message.error('登录已失效，请重新登录')
        next(`/login?redirect=${to.path}`)
        NProgress.done()
      }
      return
    }

    if (onWhiteList) {
      next()
    } else {
      next(`/login?redirect=${to.path}`)
      NProgress.done()
    }
  })

  router.afterEach((to) => {
    if (!to.path.startsWith('/admin')) {
      NProgress.done()
    }
  })
}
