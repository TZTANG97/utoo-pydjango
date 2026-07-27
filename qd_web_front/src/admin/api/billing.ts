import request, { type RequestConfig } from '@admin/utils/request'
import { isAjaxOk } from '@admin/utils/request'

export interface DatatableResult<T> {
  draw: number
  recordsTotal: number
  recordsFiltered: number
  data: T[]
}

export interface ListQuery {
  start?: number
  length?: number
  draw?: number
  order_startime?: string
  order_endtime?: string
  status?: string
  order_num?: string
  user_id?: string
  pay_type?: string
  pay_way?: string
}

async function fetchDatatable<T>(
  url: string,
  params: ListQuery,
  config?: RequestConfig
): Promise<DatatableResult<T>> {
  const res = await request.post(url, params, config)
  if (!isAjaxOk(res)) {
    const body = res as { resMsg?: string; message?: string }
    throw new Error(body.resMsg || body.message || '加载失败')
  }
  const payload = (res.obj || res) as DatatableResult<T>
  return {
    draw: payload.draw || 1,
    recordsTotal: payload.recordsTotal || 0,
    recordsFiltered: payload.recordsFiltered || 0,
    data: Array.isArray(payload.data) ? payload.data : [],
  }
}

export function fetchInvoiceList(params: ListQuery, config?: RequestConfig) {
  return fetchDatatable<Record<string, unknown>>('/vue/invoice/listPage.ajax', params, config)
}

export function fetchInvoiceDetail(id: string | number, config?: RequestConfig) {
  return request.get('/vue/invoice/invoiceDetail.ajax', { params: { id }, ...config })
}

export function rejectInvoice(id: string | number, config?: RequestConfig) {
  return request.post('/vue/invoice/bohuiInvoice.ajax', { id }, config)
}

export function fetchPayLogList(params: ListQuery, config?: RequestConfig) {
  return fetchDatatable<Record<string, unknown>>('/vue/payLog/payList.ajax', params, config)
}

export function fetchPaymentApplyList(params: ListQuery, config?: RequestConfig) {
  return fetchDatatable<Record<string, unknown>>('/vue/paymentapply/applylist.ajax', params, config)
}

export function fetchPaymentApplyDetail(id: string | number, config?: RequestConfig) {
  return request.get('/vue/paymentapply/applyDetail.ajax', { params: { id }, ...config })
}

export function agreePaymentApply(id: string | number, config?: RequestConfig) {
  return request.post('/vue/bill/agreepayment.ajax', { id }, config)
}

export function refusePaymentApply(id: string | number, mark: string, config?: RequestConfig) {
  return request.post('/vue/bill/refusepayment.ajax', { id, mark }, config)
}

export function fetchRetestList(params: ListQuery, config?: RequestConfig) {
  return fetchDatatable<Record<string, unknown>>('/vue/retestapplication/list.ajax', params, config)
}

export function fetchRetestDetail(id: string | number, config?: RequestConfig) {
  return request.get('/vue/retestapplication/retestDetail.ajax', { params: { id }, ...config })
}

export function agreeRetest(id: string | number, mark: string, config?: RequestConfig) {
  return request.post('/vue/retestapplication/agreeretestapplication.ajax', { id, mark }, config)
}

export function refuseRetest(id: string | number, mark: string, config?: RequestConfig) {
  return request.post('/vue/retestapplication/refusetestapplication.ajax', { id, mark }, config)
}
