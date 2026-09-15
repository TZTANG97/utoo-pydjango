import request, { type AjaxBody, type RequestConfig, isAjaxOk } from '@admin/utils/request'

export type { AjaxBody }
export { isAjaxOk }

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

/** 旧站 jQuery $.post 同款 form 提交，避免 JSON 经网关转发后上游取不到字段 */
async function postFormAjax(url: string, data: Record<string, unknown>) {
  const body = new URLSearchParams()
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined || value === null) continue
    body.set(key, String(value))
  }
  return (await request.post(url, body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
  })) as unknown as AjaxBody
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

// --- service apply (caliOrder) ---
export function fetchServiceApplyList(params: Record<string, unknown>) {
  return fetchDatatable('/caliOrder/list.ajax', params)
}

export function updateServiceApply(data: Record<string, unknown>) {
  return postAjax('/caliOrder/update.ajax', data)
}

// --- buyback ---
export function fetchBuybackApplyList(params: Record<string, unknown>) {
  return fetchDatatable('/apply/list.ajax', params)
}

export function updateBuybackApply(data: Record<string, unknown>) {
  return postAjax('/apply/update.ajax', data)
}

// --- consult ---
export function fetchConsultList(params: Record<string, unknown>) {
  return fetchDatatable('/consult/list.ajax', params)
}

export function getConsultDetail(id: string | number) {
  return postAjax('/consult/consultDetail.ajax', { id })
}

export function getConsultDetailXq(id: string | number) {
  return postAjax('/consult/consultDetailxq.ajax', { id })
}

export function cancelConsult(id: string | number) {
  return postAjax('/consult/cancelConsult.ajax', { id })
}

export function updateConsult(list: unknown[]) {
  return request.post('/consult/updateConsult.ajax', list, {
    headers: { 'Content-Type': 'application/json' },
  }) as unknown as Promise<AjaxBody>
}

export function saveConsultOrder(list: unknown[]) {
  return request.post('/consult/saveOrder.ajax', list, {
    headers: { 'Content-Type': 'application/json' },
  }) as unknown as Promise<AjaxBody>
}

export function fetchConsultSampleList(consultId: string | number) {
  return postAjax('/consult/querySampleList.ajax', { consultId })
}

// --- consult settings ---
export function getConsultSetting() {
  return postAjax('/consult/settingGet.ajax')
}

export function saveConsultSetting(data: Record<string, unknown>) {
  return postAjax('/consult/settingSave.ajax', data)
}

export function getIshowSetting() {
  return postAjax('/consult/isshowGet.ajax')
}

export function saveIshowSetting(data: Record<string, unknown>) {
  return postAjax('/consult/isshowSave.ajax', data)
}

// --- faq ---
export function fetchFaqList(params: Record<string, unknown>) {
  return fetchDatatable('/records/problemlistPage.ajax', params)
}

export function submitFaq(data: Record<string, unknown>) {
  return postFormAjax('/records/submitproblem.ajax', data)
}

export function editFaq(data: Record<string, unknown>) {
  return postFormAjax('/records/editproblem.ajax', data)
}

export function deleteFaq(id: string | number) {
  return postFormAjax('/records/deleteproblem.ajax', { id })
}

// --- records ---
export function fetchRecordsList(params: Record<string, unknown>) {
  return fetchDatatable('/records/recordslistPage.ajax', params)
}

export function getRecordsDetail(id: string | number) {
  return postAjax('/records/recordsDetail.ajax', { id })
}

export function deleteRecords(id: string | number) {
  return postAjax('/records/deleterecords.ajax', { id })
}

// --- evaluated orders ---
export function fetchEvaluatedOrderList(params: Record<string, unknown>) {
  return fetchDatatable('/experimentOrder/evaluate_list_dpt.ajax', params)
}

export function fetchEvaluatedSubOrderList(params: Record<string, unknown>) {
  return fetchDatatable('/experimentSubOrder/sublist_dpt.ajax', params)
}

// --- proposals ---
export function fetchProposalList(params: Record<string, unknown>) {
  return fetchDatatable('/productOrder/prove_list.ajax', params)
}

export function getProposalDetail(id: string | number) {
  return postAjax('/productOrder/proveDetail.ajax', { id })
}

export function updateProposalImprove(data: Record<string, unknown>) {
  return postAjax('/productOrder/updateProposalImprove.ajax', data)
}

// --- openid ---
export function fetchOpenidList(params: Record<string, unknown>) {
  return fetchDatatable('/expOpenid/openidList.ajax', params)
}

export function submitOpenid(data: Record<string, unknown>) {
  return postFormAjax('/expOpenid/submitOpenid.ajax', data)
}

export function deleteOpenid(id: string | number) {
  return postFormAjax('/expOpenid/del.ajax', { id })
}
