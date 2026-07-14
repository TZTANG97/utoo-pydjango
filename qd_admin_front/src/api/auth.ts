import request, { type RequestConfig } from '@/utils/request'

export interface LoginPayload {
  loginName: string
  password: string
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

export function fetchAdminWelcome(config?: RequestConfig) {
  return request.get('/vue/welcome.ajax', config)
}
