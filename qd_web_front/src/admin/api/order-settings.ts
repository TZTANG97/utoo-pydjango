import request, { type AjaxBody, type RequestConfig } from '@admin/utils/request'
import { isAjaxOk } from '@admin/utils/request'

export interface DataTableResult<T = Record<string, unknown>> {
  draw?: number
  recordsTotal?: number
  recordsFiltered?: number
  data?: T[]
}

async function postAjax(
  url: string,
  data?: Record<string, unknown>,
  config?: RequestConfig
) {
  return (await request.post(url, data, config)) as unknown as AjaxBody
}

async function getAjax(url: string, config?: RequestConfig) {
  return (await request.get(url, config)) as unknown as AjaxBody
}

async function fetchDatatable<T>(
  url: string,
  params: Record<string, unknown>
): Promise<DataTableResult<T>> {
  const res = await postAjax(url, params)
  const payload = (res.data ? res : (res.obj as DataTableResult<T> | undefined) || res) as DataTableResult<T>
  return {
    draw: payload.draw || 1,
    recordsTotal: payload.recordsTotal || 0,
    recordsFiltered: payload.recordsFiltered || 0,
    data: Array.isArray(payload.data) ? payload.data : [],
  }
}

export function fetchTaxList(params: Record<string, unknown>) {
  return fetchDatatable('/taxesConfig/getTaxesList.ajax', params)
}

export async function submitTax(data: { name: string; taxValue: string | number }) {
  const res = await postAjax('/taxesConfig/submitTases.ajax', data)
  return isAjaxOk(res)
}

export function updateTax(data: { id: number | string; name: string; taxValue: string | number }) {
  return postAjax('/taxesConfig/updateTases.ajax', data)
}

export async function updateTaxStatus(id: number | string, status: '1' | '2') {
  const res = await postAjax('/taxesConfig/updateStatus.ajax', { id, status })
  return isAjaxOk(res)
}

export function fetchPaytypeList(params: Record<string, unknown>) {
  return fetchDatatable('/consumePaytype/getPaymentList.ajax', params)
}

export async function submitPaytype(data: Record<string, unknown>) {
  const res = await postAjax('/consumePaytype/submitPayment.ajax', data)
  return isAjaxOk(res)
}

export function updatePaytypeStatus(id: number | string, status: '0' | '1') {
  return postAjax('/consumePaytype/updateDelStatus.ajax', { id, status })
}

export function fetchBillTypeList(params: Record<string, unknown>) {
  return fetchDatatable('/billtype/getBillByType.ajax', params)
}

export async function submitBillType(data: { name: string; type: number }) {
  const res = await postAjax('/billtype/submitBillType.ajax', data)
  return isAjaxOk(res)
}

export function updateBillType(data: { id: number | string; name: string }) {
  return postAjax('/billtype/updateBillType.ajax', data)
}

export async function updateBillTypeStatus(id: number | string, status: '1' | '2') {
  const res = await postAjax('/billtype/updateStatus.ajax', { id, status })
  return isAjaxOk(res)
}

export function fetchOrderTypeList(params: Record<string, unknown>) {
  return fetchDatatable('/orderType/list.ajax', params)
}

export function submitOrderType(data: Record<string, unknown>) {
  return postAjax('/orderType/submitOrderType.ajax', data)
}

export function updateOrderType(data: Record<string, unknown>) {
  return postAjax('/orderType/updateOrderType.ajax', data)
}

export function deleteOrderType(id: number | string) {
  return postAjax('/orderType/del.ajax', { id })
}

export function fetchOrderTypeTables() {
  return getAjax('/orderType/queryAllOrderType.ajax')
}

export function fetchEvaluateSetting() {
  return getAjax('/edit/evaluateSetting.ajax')
}

export function saveEvaluateSetting(data: {
  evaluate_time: number
  evaluate_time_type: number
}) {
  return postAjax('/edit/evaluateSave.ajax', data)
}

export function normalizeTaxInput(value: string | number) {
  const raw = String(value).trim()
  if (!raw) return ''
  const cleaned = raw.endsWith('%') ? raw.slice(0, -1) : raw
  const num = Number(cleaned)
  if (Number.isNaN(num)) return raw
  return num > 1 ? (num / 100).toFixed(4) : String(num)
}

export function fetchTaxAll() {
  return getAjax('/taxesConfig/getAllConfigs.ajax')
}

export function fetchPaytypeAll() {
  return fetchPaytypeList({ start: 0, length: 500, draw: 1 })
}

export function fetchBillTypeAll(billType: number) {
  return fetchBillTypeList({ type: billType, start: 0, length: 500, draw: 1 })
}

export function formatTaxDisplay(value?: number | null) {
  if (value == null) return '-'
  return `${(value * 100).toFixed(2)}%`
}
