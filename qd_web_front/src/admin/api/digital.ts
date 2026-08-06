import request, { type AjaxBody, type RequestConfig, isAjaxOk } from '@admin/utils/request'

export type { AjaxBody }
export { isAjaxOk }

export interface DataTableResult<T = Record<string, unknown>> {
  draw?: number
  recordsTotal?: number
  recordsFiltered?: number
  data?: T[]
}

async function postAjax(url: string, data?: Record<string, unknown>, config?: RequestConfig) {
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

export function fetchDigitalDepts() {
  return postAjax('/digital/deptOptions.ajax')
}

/** 对齐 Java queryAllDept：仅有统计数据的部门 */
export function fetchStatsDepts() {
  return postAjax('/testUserStats/queryAllDept.ajax')
}

export function fetchStatsOverview(params: Record<string, unknown>) {
  return postAjax('/testUserStats/overview.ajax', params)
}

/** 对齐 Java selDateOverviewByYear.ajax */
export function fetchStatsDashboard(params: Record<string, unknown>) {
  return postAjax('/testUserStats/selDateOverviewByYear.ajax', params)
}

/** 对齐 Java board1.ajax：本月最佳 / 人数 */
export function fetchStatsBoard1(params: Record<string, unknown>) {
  return postAjax('/testUserStats/board1.ajax', params)
}

/** 对齐 Java selOrderManage.ajax */
export function fetchStatsOrderManage(params: Record<string, unknown>) {
  return postAjax('/testUserStats/selOrderManage.ajax', params)
}

/** 对齐 Java board.ajax：人员年度月度完成量 */
export function fetchStatsBoardAnnual(params: Record<string, unknown>) {
  return postAjax('/testUserStats/board.ajax', params)
}

export function fetchStatsUsersByDept(deptId: string | number = '') {
  return postAjax('/testUserStats/queryUsersByDeptId.ajax', { deptId: String(deptId || '') })
}

export function fetchTestPlanDepts() {
  return postAjax('/testUserPerformance/loadDpet.ajax')
}

export function fetchTestPlanUsers(params: Record<string, unknown>) {
  return fetchDatatable('/testUserPerformance/queryUsers.ajax', params)
}

export function getTestTarget(params: Record<string, unknown>) {
  return postAjax('/testUserPerformance/selAmountByYear.ajax', params)
}

export function saveTestTarget(data: Record<string, unknown>) {
  return postAjax('/testUserPerformance/setPerformance.ajax', data)
}

export function showTestTargets(test_user_id: string | number) {
  return postAjax('/testUserPerformance/showByUserId.ajax', { test_user_id })
}

export function fetchSalePlanDepts() {
  return postAjax('/saleUserPerformance/loadDpet.ajax')
}

export function fetchSalePlanUsers(params: Record<string, unknown>) {
  return fetchDatatable('/saleUserPerformance/queryUsers.ajax', params)
}

export function getSaleTarget(params: Record<string, unknown>) {
  return postAjax('/saleUserPerformance/selAmountByYear.ajax', params)
}

export function saveSaleTarget(data: Record<string, unknown>) {
  return postAjax('/saleUserPerformance/setPerformance.ajax', data)
}

export function showSaleTargets(sale_user_id: string | number) {
  return postAjax('/saleUserPerformance/showByUserId.ajax', {
    sale_user_id,
    test_user_id: sale_user_id,
  })
}

export function fetchLabTestPerf(year: string | number) {
  return postAjax('/labPerformance/selByYear.ajax', { year })
}

export function fetchLabSaleUsers() {
  return postAjax('/labPerformanceSaleuser/selUsersByDeptId.ajax')
}

export function fetchLabSalePerf(params: Record<string, unknown>) {
  return postAjax('/labPerformanceSaleuser/selByYear.ajax', params)
}

export function fetchLabSalePerfOrders(params: Record<string, unknown>) {
  // 走网关独占路径，避免被 SVC_ADMIN_ASSET 前缀代理打到未同步的 Asset
  return fetchDatatable('/adminLabSale/expOrderList.ajax', params)
}
