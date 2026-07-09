import router from './router'
import store from './store'
import { ElMessage as Message } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { getToken } from '@/utils/auth'
import getPageTitle from '@/utils/get-page-title'

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

/** 避免后端未启动时 axios 长时间挂起导致白屏 */
function withTimeout(promise, ms, label) {
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      setTimeout(() => reject(new Error(`${label} timeout after ${ms}ms`)), ms)
    }),
  ])
}

router.beforeEach(async (to, from, next) => {
  NProgress.start()
  document.title = getPageTitle(to.meta.title)

  const hasToken = getToken()
  const onWhiteList = isWhiteRoute(to.path)

  // 分类数据后台加载，绝不阻塞首屏
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

    // 个人中心：有 token 即放行，避免点击「个人中心」无反应
    if (isPersonalCenterRoute(to.path)) {
      loadProfile()
      next()
      return
    }

    // 首页等白名单：不阻塞导航，后台拉用户信息
    if (onWhiteList) {
      loadProfile().then(async (res) => {
        if (res && !res.res) {
          console.warn('[permission] getInfo business error', res.resMsg)
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

router.afterEach(() => {
  NProgress.done()
})
