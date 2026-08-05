import request, {
  type AjaxBody,
  type RequestConfig,
  ajaxErrorMessage,
  isAjaxOk,
} from '@/utils/request'

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
  // ?????????????????????????????????  if (typeof res.res === 'boolean' || typeof res.res === 'number') {
    if (!isAjaxOk(res)) {
      throw new Error(ajaxErrorMessage(res, '????'))
    }
    const wrapped = (res.obj as DataTableResult<T> | undefined) || {}
    return {
      draw: wrapped.draw || 1,
      recordsTotal: Number(wrapped.recordsTotal || 0),
      recordsFiltered: Number(wrapped.recordsFiltered || wrapped.recordsTotal || 0),
      data: Array.isArray(wrapped.data) ? wrapped.data : [],
    }
  }
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

// ????
export const fetchStorehouseList = (p: Record<string, unknown>) =>
  fetchDatatable('/storeHouse/list.ajax', p)
export const getStorehouse = (id: string | number) => postAjax('/storeHouse/get.ajax', { id })
export const saveStorehouse = (data: Record<string, unknown>) =>
  postAjax(data.id ? '/storeHouse/updateStoreHouse.ajax' : '/storeHouse/submitStoreHouse.ajax', data)
export const updateStorehouseStatus = (id: string | number, status: number) =>
  postAjax('/storeHouse/updateStatus.ajax', { id, shstatus: status })
export const deleteStorehouse = (id: string | number) => postAjax('/storeHouse/del.ajax', { id })

// ???? / ????
function samplePrefix(retain: boolean) {
  return retain ? '/sampleremainstoreHouse' : '/samplestoreHouse'
}
export const fetchSampleStorehouseList = (retain: boolean, p: Record<string, unknown>) =>
  fetchDatatable(`${samplePrefix(retain)}/list.ajax`, p)
export const getSampleStorehouse = (retain: boolean, id: string | number) =>
  postAjax(`${samplePrefix(retain)}/get.ajax`, { id })
export const saveSampleStorehouse = (retain: boolean, data: Record<string, unknown>) =>
  postAjax(
    `${samplePrefix(retain)}/${data.id ? 'updateStoreHouse' : 'submitStoreHouse'}.ajax`,
    data
  )
export const updateSampleStorehouseStatus = (
  retain: boolean,
  id: string | number,
  status: number
) => postAjax(`${samplePrefix(retain)}/updateStatus.ajax`, { id, shstatus: status })
export const deleteSampleStorehouse = (retain: boolean, id: string | number) =>
  postAjax(`${samplePrefix(retain)}/del.ajax`, { id })

/** ???? API ???goods / sample / retain */
function storeConfigPrefix(mode: 'goods' | 'sample' | 'retain') {
  if (mode === 'goods') return '/storeHouse'
  if (mode === 'retain') return '/sampleremainstoreHouse'
  return '/samplestoreHouse'
}
export const fetchStoreBlockList = (
  mode: 'goods' | 'sample' | 'retain',
  p: Record<string, unknown>
) => fetchDatatable(`${storeConfigPrefix(mode)}/storeBlockList.ajax`, p)
export const fetchStoreBlockOptions = (mode: 'goods' | 'sample' | 'retain', storeId: string | number) =>
  postAjax(`${storeConfigPrefix(mode)}/queryStoreBlock.ajax`, { store_id: storeId })
export const addStoreBlock = (
  mode: 'goods' | 'sample' | 'retain',
  data: Record<string, unknown>
) => postAjax(`${storeConfigPrefix(mode)}/addStoreBlock.ajax`, data)
export const fetchStorePositionList = (
  mode: 'goods' | 'sample' | 'retain',
  p: Record<string, unknown>
) => fetchDatatable(`${storeConfigPrefix(mode)}/storePositionList.ajax`, p)
export const addStorePosition = (
  mode: 'goods' | 'sample' | 'retain',
  data: Record<string, unknown>
) => postAjax(`${storeConfigPrefix(mode)}/addStorePos.ajax`, data)
export const deleteStorePosition = (mode: 'goods' | 'sample' | 'retain', id: string | number) =>
  postAjax(`${storeConfigPrefix(mode)}/delStorePos.ajax`, { id })
export const clearSampleStoreGoods = (mode: 'sample' | 'retain', id: string | number) =>
  postAjax(`${storeConfigPrefix(mode)}/delSamplegoods.ajax`, { id })
export const fetchStorePositionQr = (mode: 'goods' | 'sample' | 'retain', id: string | number) =>
  postAjax(`${storeConfigPrefix(mode)}/genQrcode.ajax`, { id })

// ??
export const fetchInventoryList = (p: Record<string, unknown>) =>
  fetchDatatable('/inventory/list.ajax', p)
export const fetchInventoryChildren = (p: Record<string, unknown>) =>
  postAjax('/inventory/children.ajax', p)
export const fetchInventorySummary = () => postAjax('/inventory/summary.ajax')
export const getInventory = (id: string | number) => postAjax('/inventory/get.ajax', { id })
export const updateInventory = (data: Record<string, unknown>) =>
  postAjax('/inventory/update.ajax', data)

// ????export const fetchLabList = (p: Record<string, unknown>) => fetchDatatable('/lab/list.ajax', p)
export const fetchLabOptions = () => postAjax('/lab/options.ajax')
export const getLab = (id: string | number) => postAjax('/lab/get.ajax', { id })
export const saveLab = (data: Record<string, unknown>) => postAjax('/lab/save.ajax', data)
export const updateLabStatus = (id: string | number, status: number) =>
  postAjax('/lab/updateStatus.ajax', { id, status, shstatus: status })
export const deleteLab = (id: string | number) => postAjax('/lab/del.ajax', { id })

// 实验线（实验室查看页）
export const fetchLabLineList = (p: Record<string, unknown>) =>
  fetchDatatable('/lab/lineList.ajax', p)
/** 对齐 Java /lab/selLineList.ajax：选择实验平台（不要求 lab_id） */
export const fetchSelLineList = (p: Record<string, unknown> = {}) =>
  fetchDatatable('/lab/selLineList.ajax', p)
export const fetchLabLineClassOptions = () => postAjax('/lab/lineClassOptions.ajax')
export const getLabLine = (id: string | number) => postAjax('/lab/getLine.ajax', { id })
export const submitLabLine = (data: Record<string, unknown>) =>
  postAjax('/lab/submitLine.ajax', data)
export const updateLabLine = (data: Record<string, unknown>) =>
  postAjax('/lab/updateLine.ajax', data)
export const updateLabLineStatus = (id: string | number, status: number) =>
  postAjax('/lab/updateLineStatus.ajax', { id, status, shstatus: status })

// ??????export const fetchSampleOrderList = (p: Record<string, unknown>) =>
  fetchDatatable('/inTreasury/list.ajax', p)
export const fetchSampleOrderOptions = () => postAjax('/inTreasury/options.ajax')
export const fetchSampleStorePositions = (storeId: string | number, type: 0 | 1 = 0) =>
  postAjax('/samplestoreHouse/queryListByStoreId.ajax', { store_id: storeId, type })
export const getSampleOrderDetail = (id: string | number) =>
  postAjax('/inTreasury/detail.ajax', { id })
export const exportSampleOrders = (p: Record<string, unknown>) =>
  postAjax('/inTreasury/export.ajax', p)

// ????
export const fetchDeviceBookingList = (p: Record<string, unknown>) =>
  fetchDatatable('/expLog/list.ajax', p)
export const getDeviceBookingDetail = (id: string | number, p: Record<string, unknown> = {}) =>
  postAjax('/expLog/logDetail.ajax', { id, ...p })
export const fetchDeviceBookingOptions = () => postAjax('/expLog/options.ajax')

// ????
export const fetchIncomeOverview = () => postAjax('/inIncome/overview.ajax')
export const fetchIncomeList = (p: Record<string, unknown>) =>
  fetchDatatable('/inIncome/costList.ajax', p)
export const fetchIncomeRatio = () => postAjax('/inIncome/queryTzblmx.ajax')
export const fetchIncomeInvestUsers = (accountType: number | string = 1) =>
  postAjax('/inIncome/queryCzUsers.ajax', { accountType })
export const fetchIncomeUsers = (keyword = '') =>
  postAjax('/inIncome/queryUsers.ajax', { keyword })
export const submitIncomeInvest = (p: Record<string, unknown>) =>
  postAjax('/inIncome/submitInvestFreez.ajax', p)
export const submitIncomeDisinvest = (p: Record<string, unknown>) =>
  postAjax('/inIncome/submitDisInvest.ajax', p)
export const submitIncomeTax = (p: Record<string, unknown>) =>
  postAjax('/inIncome/submitOtherPay.ajax', p)
