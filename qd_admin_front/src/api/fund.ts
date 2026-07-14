import request, { type AjaxBody, type RequestConfig, isAjaxOk } from '@/utils/request'

export type { AjaxBody }
export { isAjaxOk }

export interface DataTableResult<T = Record<string, unknown>> {
  draw?: number
  recordsTotal?: number
  recordsFiltered?: number
  data?: T[]
}

async function postAjax(url: string, data?: Record<string, unknown> | unknown[], config?: RequestConfig) {
  return (await request.post(url, data, config)) as unknown as AjaxBody
}

async function fetchDatatable<T>(
  url: string,
  params: Record<string, unknown>
): Promise<DataTableResult<T>> {
  const res = await postAjax(url, params)
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

export const fetchFundSetting = () => postAjax('/funds/accountGet.ajax')
export const saveFundRates = (data: Record<string, unknown>) =>
  postAjax('/funds/account_save.ajax', data)
export const saveExchangeRate = (data: Record<string, unknown>) =>
  postAjax('/funds/saveUSExchangeRate.ajax', data)

export const fetchAccountOverviewList = (p: Record<string, unknown>) =>
  fetchDatatable('/funds/fundAccountList.ajax', p)
export const fetchUserAccountDetail = (id: string | number) =>
  postAjax('/funds/userAccountDetail.ajax', { id })

export const fetchAssetOverview = (p: Record<string, unknown> = {}) =>
  postAjax('/funds/assetAcc.ajax', p)
export const fetchAccountLogList = (p: Record<string, unknown>) =>
  fetchDatatable('/getAccountLog.ajax', p)
export const fetchExpSumByYear = (p: Record<string, unknown> = {}) =>
  postAjax('/selExpSumByYear.ajax', p)
export const fetchFundYears = () => postAjax('/funds/fundYears.ajax')
export const submitAccountApply = (p: Record<string, unknown>) =>
  postAjax('/funds/accountLog_add.ajax', p)
export const submitTransferApply = (p: Record<string, unknown>) =>
  postAjax('/funds/account_transfer_add.ajax', p)
export const submitLoanApply = (p: Record<string, unknown>) =>
  postAjax('/funds/account_loan_add.ajax', p)
export const submitChargeback = (p: Record<string, unknown>) =>
  postAjax('/funds/submit_chargeback.ajax', p)
export const submitLoanClear = (p: Record<string, unknown>) =>
  postAjax('/funds/account_loan_clear_add.ajax', p)
export const fetchFundUsers = (keyword = '') =>
  postAjax('/funds/fundUsers.ajax', { keyword })
export const cancelAccountApply = (id: string | number) => postAjax('/pass.ajax', { id, status: -2 })
export const passAccountLog = (id: string | number, status: string | number) =>
  postAjax('/pass.ajax', { id, status })

export const fetchCompanyOptions = () => postAjax('/companyPay/queryCompanies.ajax')
export const fetchUserPayOptions = () => postAjax('/userPay/queryAllUserPay.ajax')
export const fetchLabOptions = () => postAjax('/projectPay/queryLabs.ajax')

export const fetchCompanyPayList = (p: Record<string, unknown>) =>
  postAjax('/companyPay/selDetailList.ajax', p)
export const saveCompanyPay = (list: Record<string, unknown>[]) =>
  postAjax('/companyPay/submitCompanyPay.ajax', { list })

export const fetchUserPayList = (p: Record<string, unknown>) =>
  postAjax('/userPay/selDetailList.ajax', p)
export const saveUserPay = (list: Record<string, unknown>[]) =>
  postAjax('/userPay/submitUserPay.ajax', { list })

export const fetchCompanyLoanList = (p: Record<string, unknown>) =>
  postAjax('/companyLoanPay/selDetailList.ajax', p)
export const saveCompanyLoan = (list: Record<string, unknown>[]) =>
  postAjax('/companyLoanPay/submitCompanyPay.ajax', { list })

export const fetchProjectPayList = (p: Record<string, unknown>) =>
  postAjax('/projectPay/selDetailList.ajax', p)
export const saveProjectPay = (list: Record<string, unknown>[]) =>
  postAjax('/projectPay/submitUserPay.ajax', { list })

export const fetchDigitalManageOverview = (p: Record<string, unknown> = {}) =>
  postAjax('/digitalManage/overview.ajax', p)
