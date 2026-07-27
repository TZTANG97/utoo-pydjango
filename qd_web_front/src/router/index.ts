import { createRouter, createWebHashHistory } from 'vue-router'
import { adminRoutes } from '@admin/router'
import { clientRoutes } from '@client/router'

const router = createRouter({
  history: createWebHashHistory(),
  scrollBehavior: () => ({ top: 0 }),
  // admin 在前，避免被 C 端 catch-all 吞掉
  routes: [...adminRoutes, ...clientRoutes],
})

export default router
