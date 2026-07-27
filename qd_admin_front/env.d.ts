/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_BASE_API: string
  readonly VITE_API_TARGET: string
  /** 同域子路径部署，如 /admin/；本地开发可省略 */
  readonly VITE_BASE_PATH?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    hidden?: boolean
    affix?: boolean
    /** 不进入顶部 TagsView（登录/404 等） */
    noTagsView?: boolean
  }
}
