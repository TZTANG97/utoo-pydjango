import router from '@/router'
import { useUserStore } from '@/stores/user'
import { getToken } from '@/utils/auth'
import { handleUnauthorized } from '@/utils/request'
import NProgress from 'nprogress'

NProgress.configure({ showSpinner: false })

const whiteList = ['/login']

router.beforeEach(async (to, _from, next) => {
  NProgress.start()
  document.title = to.meta.title
    ? `${to.meta.title} - 愉兔检测管理平台`
    : '愉兔检测管理平台'

  const token = getToken()
  const userStore = useUserStore()

  if (token) {
    if (to.path === '/login') {
      next({ path: '/dashboard' })
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
      next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
      NProgress.done()
    }
    return
  }

  if (whiteList.includes(to.path)) {
    next()
    return
  }

  next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
  NProgress.done()
})

router.afterEach(() => {
  NProgress.done()
})
