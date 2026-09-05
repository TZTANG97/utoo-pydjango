import router from './router'
import { setupAdminPermission } from '@admin/permission'
import { setupClientPermission } from '@client/permission'

setupAdminPermission(router)
setupClientPermission(router)
