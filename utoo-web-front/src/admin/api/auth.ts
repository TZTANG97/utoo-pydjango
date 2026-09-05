import request, { type AjaxBody, type RequestConfig, isAjaxOk } from '@admin/utils/request'

export interface LoginPayload {
  loginName: string
  password: string
}

export interface DataTableResult<T = Record<string, unknown>> {
  draw?: number
  recordsTotal?: number
  recordsFiltered?: number
  data?: T[]
}

export function adminLogin(data: LoginPayload, config?: RequestConfig) {
  return request.post('/vue/userLogin.ajax', data, config)
}

export function fetchAdminMain(config?: RequestConfig) {
  return request.get('/vue/main.ajax', config)
}

export function fetchAdminUserCenter(config?: RequestConfig) {
  return request.get('/vue/usercenter.ajax', config)
}

export function fetchAdminWelcome(
  config?: RequestConfig & { params?: Record<string, unknown> },
) {
  return request.get('/vue/welcome.ajax', config)
}

export async function fetchSysLogs(
  params: Record<string, unknown>,
  config?: RequestConfig
): Promise<DataTableResult> {
  const res = (await request.post('/vue/sysLogs.ajax', params, config)) as unknown as AjaxBody
  const payload = (res.obj || res) as DataTableResult
  return {
    draw: payload.draw || 1,
    recordsTotal: payload.recordsTotal || 0,
    recordsFiltered: payload.recordsFiltered || 0,
    data: Array.isArray(payload.data) ? payload.data : [],
  }
}

export { isAjaxOk }
