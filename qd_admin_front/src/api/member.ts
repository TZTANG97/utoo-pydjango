import request, { type AjaxBody, type RequestConfig, isAjaxOk } from '@/utils/request'

export type { AjaxBody }
export { isAjaxOk }

export interface DataTableResult<T = Record<string, unknown>> {
  draw?: number
  recordsTotal?: number
  recordsFiltered?: number
  data?: T[]
}

export interface DistrictOption {
  id?: string | number
  superId?: string | number
  disName?: string
  disSort?: number | string
  type?: string | number
}

async function postAjax(
  url: string,
  data?: Record<string, unknown>,
  config?: RequestConfig
) {
  return (await request.post(url, data, config)) as unknown as AjaxBody
}

async function getAjax(url: string, params?: Record<string, unknown>, config?: RequestConfig) {
  return (await request.get(url, { params, ...config })) as unknown as AjaxBody
}

async function fetchDatatable<T>(
  url: string,
  params: Record<string, unknown>
): Promise<DataTableResult<T>> {
  const res = await postAjax(url, params)
  // DataTable 直出（无 res 包装）
  if (
    Array.isArray((res as DataTableResult<T>).data) ||
    typeof (res as DataTableResult<T>).recordsTotal === 'number'
  ) {
    const direct = res as DataTableResult<T>
    return {
      draw: direct.draw || 1,
      recordsTotal: direct.recordsTotal || 0,
      recordsFiltered: direct.recordsFiltered || 0,
      data: Array.isArray(direct.data) ? direct.data : [],
    }
  }
  const payload = ((res.obj as DataTableResult<T> | undefined) || res) as DataTableResult<T>
  return {
    draw: payload.draw || 1,
    recordsTotal: payload.recordsTotal || 0,
    recordsFiltered: payload.recordsFiltered || 0,
    data: Array.isArray(payload.data) ? payload.data : [],
  }
}

// 企业会员
export function fetchEnterpriseList(params: Record<string, unknown>) {
  return fetchDatatable('/userCompany/getUserCompanyList.ajax', { type: 3, ...params })
}

export function getEnterprise(id: string | number) {
  return postAjax('/userCompany/getById.ajax', { id })
}

export function getEnterpriseDetail(id: string | number) {
  return postAjax('/userCompany/getCompanyByComId.ajax', { id })
}

export function saveEnterprise(data: Record<string, unknown>) {
  return postAjax('/userCompany/saveUserCompany.ajax', data)
}

export function updateEnterprise(data: Record<string, unknown>) {
  return postAjax('/userCompany/updateUserCompany.ajax', data)
}

export function deleteEnterprise(id: string | number) {
  return postAjax('/userCompany/updateStatus.ajax', { id })
}

export async function fetchDistrictOptions(superId: string | number) {
  const res = await getAjax('/member/queryProCityCo.ajax', { superId })
  const list = (res.obj || res.data || []) as DistrictOption[]
  return Array.isArray(list) ? list : []
}

export function fetchCompanyContacts(params: Record<string, unknown>) {
  return fetchDatatable('/member/getUserListByComId.ajax', params)
}

export function addCompanyContact(data: Record<string, unknown>) {
  return postAjax('/member/addLinkUser.ajax', data)
}

export function editCompanyContact(data: Record<string, unknown>) {
  return postAjax('/member/editLinkUser.ajax', data)
}

export function unbindCompanyContact(id: string | number) {
  return postAjax('/member/updateStatus.ajax', { id, status: 0 })
}

export function getMember(id: string | number) {
  return postAjax('/member/getUserByUserId.ajax', { id })
}

export function fetchCompanyInvoices(params: Record<string, unknown>) {
  return fetchDatatable('/companyinvoicelog/invoiceList.ajax', params)
}

export function fetchCompanyPayLogs(params: Record<string, unknown>) {
  return fetchDatatable('/payLog/list0909.ajax', params)
}

export function fetchCompanyBalanceLogs(params: Record<string, unknown>) {
  return fetchDatatable('/payLog/list910.ajax', { pay_way: 4, ...params })
}

export function fetchCompanyArrears(params: Record<string, unknown>) {
  return fetchDatatable('/payLog/qklist0909.ajax', params)
}

// 个人会员
export function fetchMemberList(params: Record<string, unknown>) {
  return fetchDatatable('/member/memberList.ajax', params)
}

export function addMember(data: Record<string, unknown>) {
  return postAjax('/member/addMember.ajax', data)
}

export function editMember(data: Record<string, unknown>) {
  return postAjax('/member/editMember.ajax', data)
}

export function unbindMember(id: string | number) {
  return postAjax('/member/updateStatus.ajax', { id })
}

export function fetchUserInvoices(params: Record<string, unknown>) {
  return fetchDatatable('/userinvoicelog/invoiceList.ajax', params)
}

export function fetchUserPayLogs(params: Record<string, unknown>) {
  return fetchDatatable('/payLog/list828.ajax', params)
}

export function fetchUserBalanceLogs(params: Record<string, unknown>) {
  return fetchDatatable('/payLog/list.ajax', { pay_way: 4, ...params })
}

export function fetchUserArrears(params: Record<string, unknown>) {
  return fetchDatatable('/payLog/qklist.ajax', params)
}

// 会员申请
export function fetchApplyVipList(params: Record<string, unknown>) {
  return fetchDatatable('/applyVip/list.ajax', params)
}

export function getApplyVip(id: string | number) {
  return postAjax('/applyVip/detail.ajax', { id })
}

export function updateApplyVip(data: Record<string, unknown>) {
  return postAjax('/applyVip/update.ajax', data)
}

// 积分设置
export function getIntegralSetting() {
  return postAjax('/integral/setting_get.ajax')
}

export function saveIntegralExpire(expireDate: number) {
  return postAjax('/integral/setting_save.ajax', { expireDate })
}

export function saveIntegralRatio(integral_convert_ratio: number) {
  return postAjax('/integral/integral_convert_ratio_save.ajax', { integral_convert_ratio })
}

// 线下充值
export function fetchOfflineRechargeList(params: Record<string, unknown>) {
  return fetchDatatable('/offlineRecharge/offRechargeList.ajax', params)
}

export function getOfflineRecharge(id: string | number) {
  return postAjax('/offlineRecharge/rechargeDetail.ajax', { id })
}

export function fetchRechargeUserPicker(params: Record<string, unknown>) {
  return fetchDatatable('/offlineRecharge/userList.ajax', params)
}

export function addOfflineRecharge(data: Record<string, unknown>) {
  return postAjax('/offlineRecharge/recharge_add.ajax', data)
}
