import request, { type AjaxBody, type RequestConfig, isAjaxOk } from '@admin/utils/request'

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

/** 可用余额：对齐 /funds/account_userId.htm，失败则回退 userAccountDetail */
export async function fetchUserAvailableBalance(
  userId: string | number,
  accountType: number
): Promise<number> {
  try {
    const body = await postAjax(
      '/funds/account_userId.htm',
      { userId, type: accountType, accountType },
      { silentError: true }
    )
    if (typeof body.obj === 'number') return body.obj
    if (body.obj != null && !Number.isNaN(Number(body.obj))) return Number(body.obj)
  } catch {
    /* fallback below */
  }
  const detail = await fetchUserAccountDetail(userId)
  if (!isAjaxOk(detail)) return 0
  const obj = (detail.obj || {}) as { accounts?: Record<string, unknown>[] }
  const list = Array.isArray(obj.accounts) ? obj.accounts : []
  const hit = list.find(
    (a) => Number(a.accountType ?? a.account_type ?? a.type) === Number(accountType)
  )
  return Number(hit?.availableBalance ?? hit?.available_balance ?? 0)
}

/** 当前用户某币种可用余额（优先走账户详情，兼容 ajax 包装） */
export async function fetchAvailableBalance(userId: string | number, accountType: number) {
  const res = await fetchUserAccountDetail(userId)
  const accounts = ((res.obj as { accounts?: Record<string, unknown>[] } | undefined)?.accounts ||
    []) as Record<string, unknown>[]
  const hit = accounts.find((a) => Number(a.accountType) === Number(accountType))
  return Number(hit?.availableBalance ?? 0)
}

/** 转账可选转入用户（有对应币种账户） */
export const fetchTransferUsers = (accountType: number) =>
  fetchDatatable<{ userId?: string | number; userName?: string; trueName?: string }>(
    '/account_User.ajax',
    { accountType, start: 0, length: 999, draw: 1 }
  )

export const fetchAssetOverview = (p: Record<string, unknown> = {}) =>
  postAjax('/funds/assetAcc.ajax', p)
/** 资金账户页顶部统计（totala/totalf/rmbi/usi + 利率） */
export const fetchAssetAccountSummary = (p: Record<string, unknown> = {}) =>
  postAjax('/funds/assetAccountxcx.ajax', p)
/** 昨日收益 rmbzrsy / uszrsy */
export const fetchYesterdayIncome = (p: Record<string, unknown> = {}) =>
  postAjax('/yesterdayIncome.ajax', p)
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
export const chargeBackCompanyPay = (p: Record<string, unknown>) =>
  postAjax('/companyPay/chargeBack.ajax', p)
export const updateCompanyPayStatus = (p: Record<string, unknown>) =>
  postAjax('/companyPay/companyPayUpdate.ajax', p)

export const fetchUserPayList = (p: Record<string, unknown>) =>
  postAjax('/userPay/selDetailList.ajax', p)
export const saveUserPay = (list: Record<string, unknown>[]) =>
  postAjax('/userPay/submitUserPay.ajax', { list })
export const chargeBackUserPay = (p: Record<string, unknown>) =>
  postAjax('/userPay/chargeBack.ajax', p)
export const updateUserPayStatus = (p: Record<string, unknown>) =>
  postAjax('/userPay/companyPayUpdate.ajax', p)

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

/** 公司列表实验金额（对齐 Java/MP selCompanySaleByYear） */
export const fetchCompanySaleByYear = (p: Record<string, unknown> = {}) =>
  postAjax('/digitalManage/selCompanySaleByYear.ajax', p)

/** 实验/分包月度金额柱图（对齐 Java/MP selExpSaleByYear） */
export const fetchExpSaleByYear = (p: Record<string, unknown> = {}) =>
  postAjax('/digitalManage/selExpSaleByYear.ajax', p)

/** 实验/分包已收+应收双饼图（对齐 Java SSR companyOverdueReceive） */
export const fetchExpReceivePie = (p: Record<string, unknown> = {}) =>
  postAjax('/digitalManage/selExpReceivePie.ajax', p)

/** 个人实验总额（公司基金等非管理员看板） */
export const fetchUserAmountByYearSygr = (p: Record<string, unknown> = {}) =>
  postAjax('/digitalManage/selUserAmountByYearsygr.ajax', p)

/** 个人实验分包总额 */
export const fetchUserAmountByYearSyfbgr = (p: Record<string, unknown> = {}) =>
  postAjax('/digitalManage/selUserAmountByYearsyfbgr.ajax', p)

/** 个人应收/应付饼图（公司基金等非管理员看板） */
export const fetchUserOverduePie = (p: Record<string, unknown> = {}) =>
  postAjax('/digitalManage/selUserOverduePie.ajax', p)
