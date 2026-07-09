import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { normalizeNotifyOptions } from '@/utils/error-message'
import 'normalize.css/normalize.css'
import 'element-plus/dist/index.css'
import '@/common.scss'
import '@/styles/index.scss'
import 'nprogress/nprogress.css'
import 'virtual:svg-icons-register'

import App from './App.vue'
import store from './store'
import router from './router'
import '@/permission'

import SvgIcon from '@/components/SvgIcon/index.vue'
import edit from '@/components/edit/index.vue'

const app = createApp(App)

app.component('svg-icon', SvgIcon)
app.component('editor', edit)

app.use(store)
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

if (!window.location.hash || window.location.hash === '#/' || window.location.hash === '#') {
  router.replace('/home')
}
