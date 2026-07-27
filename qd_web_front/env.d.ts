/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_BASE_API: string
  readonly VITE_API_TARGET: string
  readonly VITE_API_MODE?: string
  readonly VITE_OSS_PUBLIC_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

declare module 'virtual:svg-icons-register'

import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    hidden?: boolean
    affix?: boolean
    noTagsView?: boolean
    roles?: string[]
  }
}
