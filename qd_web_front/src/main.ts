import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { normalizeNotifyOptions } from '@client/utils/error-message'
import 'normalize.css/normalize.css'
import 'element-plus/dist/index.css'
import 'nprogress/nprogress.css'
import '@wangeditor/editor/dist/css/style.css'
import 'virtual:svg-icons-register'

// C 端全局样式
import '@client/common.scss'
import '@client/styles/index.scss'
// 管理后台样式
import '@admin/assets/main.css'

import App from './App.vue'
import clientStore from '@client/store'
import { pinia } from '@admin/stores'
import router from './router'
import './permission'

import SvgIcon from '@client/components/SvgIcon/index.vue'
import edit from '@client/components/edit/index.vue'

const app = createApp(App)

app.component('svg-icon', SvgIcon)
app.component('editor', edit)

app.use(pinia)
app.use(clientStore)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.config.globalProperties.$message = ElMessage
app.config.globalProperties.$confirm = ElMessageBox.confirm
app.config.globalProperties.$alert = ElMessageBox.alert
app.config.globalProperties.$prompt = ElMessageBox.prompt

function createNotify(type?: 'success' | 'warning' | 'info' | 'error') {
  return (options: unknown) => {
    const opts = normalizeNotifyOptions(options)
    if (type) opts.type = type
    return ElNotification(opts as Parameters<typeof ElNotification>[0])
  }
}

const $notify = createNotify() as typeof ElNotification & {
  success: ReturnType<typeof createNotify>
  warning: ReturnType<typeof createNotify>
  info: ReturnType<typeof createNotify>
  error: ReturnType<typeof createNotify>
}
$notify.success = createNotify('success')
$notify.warning = createNotify('warning')
$notify.info = createNotify('info')
$notify.error = createNotify('error')
app.config.globalProperties.$notify = $notify

app.mount('#app')

const hash = window.location.hash || ''
if (!hash || hash === '#' || hash === '#/') {
  router.replace('/home')
}
