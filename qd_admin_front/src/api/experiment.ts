import request, {
  type AjaxBody,
  type RequestConfig,
  ajaxErrorMessage,
  isAjaxOk,
} from '@/utils/request'

export type { AjaxBody }
export { isAjaxOk, ajaxErrorMessage }

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
  if (typeof res.res === 'boolean' || typeof res.res === 'number') {
    if (!isAjaxOk(res)) {
      throw new Error(ajaxErrorMessage(res, '加载失败'))
    }
    const wrapped = (res.obj as DataTableResult<T> | undefined) || {}
    if (Array.isArray(wrapped.data) || typeof wrapped.recordsTotal === 'number') {
      return {
        draw: wrapped.draw || 1,
        recordsTotal: Number(wrapped.recordsTotal || 0),
        recordsFiltered: Number(wrapped.recordsFiltered || wrapped.recordsTotal || 0),
        data: Array.isArray(wrapped.data) ? wrapped.data : [],
      }
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

const BASE = '/adminExperiment'

// 类目
export const fetchManageList = (p: Record<string, unknown>) =>
  fetchDatatable(`${BASE}/manage/list.ajax`, p)
export const getManage = (id: string | number) => postAjax(`${BASE}/manage/get.ajax`, { id })
export const saveManage = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/manage/save.ajax`, data)
export const updateManageStatus = (id: string | number, status: number) =>
  postAjax(`${BASE}/manage/updateStatus.ajax`, { id, status })
export const deleteManage = (id: string | number) => postAjax(`${BASE}/manage/del.ajax`, { id })
export const fetchManageOptions = (type: number, parentId?: string | number) =>
  postAjax(`${BASE}/manage/options.ajax`, { type, parentId: parentId || '' })

// 测试项目
export const fetchProjectList = (p: Record<string, unknown>) =>
  fetchDatatable(`${BASE}/project/list.ajax`, p)
export const getProject = (id: string | number) => postAjax(`${BASE}/project/get.ajax`, { id })
export const saveProject = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/project/save.ajax`, data)
export const deleteProject = (id: string | number) => postAjax(`${BASE}/project/del.ajax`, { id })

// 实验产品
export const fetchExpGoodsList = (p: Record<string, unknown>) =>
  fetchDatatable(`${BASE}/goods/list.ajax`, p)
export const getExpGoods = (id: string | number) => postAjax(`${BASE}/goods/get.ajax`, { id })
export const saveExpGoods = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/goods/save.ajax`, data)
export const deleteExpGoods = (id: string | number) => postAjax(`${BASE}/goods/del.ajax`, { id })

// 实验品牌
export const fetchExpBrandList = (p: Record<string, unknown>) =>
  fetchDatatable(`${BASE}/brand/list.ajax`, p)
export const getExpBrand = (id: string | number) => postAjax(`${BASE}/brand/get.ajax`, { id })
export const saveExpBrand = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/brand/save.ajax`, data)
export const deleteExpBrand = (id: string | number) => postAjax(`${BASE}/brand/del.ajax`, { id })
export const fetchExpBrandOptions = () => postAjax(`${BASE}/brand/options.ajax`)

// 样品属性
export const fetchSampleAttrList = (p: Record<string, unknown>) =>
  fetchDatatable(`${BASE}/sampleAttr/list.ajax`, p)
export const getSampleAttr = (id: string | number) =>
  postAjax(`${BASE}/sampleAttr/get.ajax`, { id })
export const saveSampleAttr = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/sampleAttr/save.ajax`, data)
export const updateSampleAttrStatus = (id: string | number, status: number) =>
  postAjax(`${BASE}/sampleAttr/updateStatus.ajax`, { id, status })
export const deleteSampleAttr = (id: string | number) =>
  postAjax(`${BASE}/sampleAttr/del.ajax`, { id })
export const fetchSampleAttrOptions = (type: number, parentId?: string | number) =>
  postAjax(`${BASE}/sampleAttr/options.ajax`, { type, parentId: parentId || '' })

// 订单
export const fetchExpOrderList = (p: Record<string, unknown>) =>
  fetchDatatable(`${BASE}/order/list.ajax`, p)
export const getExpOrderDetail = (id: string | number) =>
  postAjax(`${BASE}/order/detail.ajax`, { id })
export const auditExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/audit.ajax`, data)
export const fetchExpOrderStatusOptions = (p: Record<string, unknown> = {}) =>
  postAjax(`${BASE}/order/statusOptions.ajax`, p)
export const exportExpOrders = (p: Record<string, unknown>) =>
  postAjax(`${BASE}/order/export.ajax`, p)

export const fetchGrabOrderList = (p: Record<string, unknown>) =>
  fetchDatatable(`${BASE}/grab/list.ajax`, p)
export const grabExpOrder = (id: string | number) =>
  postAjax(`${BASE}/grab/competition.ajax`, { id })
