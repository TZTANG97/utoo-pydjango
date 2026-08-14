import request, {
  type AjaxBody,
  type RequestConfig,
  ajaxErrorMessage,
  isAjaxOk,
} from '@admin/utils/request'

export type { AjaxBody }
export { isAjaxOk, ajaxErrorMessage }

export interface DataTableResult<T = Record<string, unknown>> {
  draw?: number
  recordsTotal?: number
  recordsFiltered?: number
  data?: T[]
}

async function postAjax(url: string, data?: Record<string, unknown>, config?: RequestConfig) {
  return (await request.post(url, data, {
    ...config,
    headers: {
      'Content-Type': 'application/json',
      ...(config?.headers || {}),
    },
  })) as unknown as AjaxBody
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
export const fetchManagePtTypes = () => postAjax(`${BASE}/manage/queryPtTypeAll.ajax`, {})

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
export const fetchExpWelcomeOrderList = (p: Record<string, unknown>) =>
  fetchDatatable(`${BASE}/order/listWelcome.ajax`, p)
export const getExpOrderDetail = (id: string | number) =>
  postAjax(`${BASE}/order/detail.ajax`, { id })
export const auditExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/audit.ajax`, data)
export const cancelExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/cancel.ajax`, data)
export const submitExpOrderAudit = (id: string | number) =>
  postAjax(`${BASE}/order/submitAudit.ajax`, { id })
export const withdrawExpOrderAudit = (id: string | number) =>
  postAjax(`${BASE}/order/withdrawAudit.ajax`, { id })
export const costSettleExpOrder = (id: string | number) =>
  postAjax(`${BASE}/order/costSettle.ajax`, { id })
export const saveExpOrderReceiveBill = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/saveReceiveBill.ajax`, data)
export const amountPayExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/amountPay.ajax`, data)
export const updateExpOrderShareRatio = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/shareRatio.ajax`, data)
export const addExpOrderRelated = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/addRelated.ajax`, data)
export const delExpOrderRelated = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/delRelated.ajax`, data)
export const saveExpOrderFinish = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/saveFinish.ajax`, data)
export const saveExpChildReferencePrice = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/saveReferencePrice.ajax`, data)
export const updateExpChildTimeType = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/updateTimeType.ajax`, data)
export const fetchExpOrderMoreInfo = (id: string | number) =>
  postAjax(`${BASE}/order/moreInfo.ajax`, { id })
export const fetchExpOrderStatusOptions = (p: Record<string, unknown> = {}) =>
  postAjax(`${BASE}/order/statusOptions.ajax`, p)
export const exportExpOrders = (p: Record<string, unknown>) =>
  postAjax(`${BASE}/order/export.ajax`, p)

// type=10 样品/测试流转
export const sampleArriveExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/sampleArrive.ajax`, data)
export const samplePickExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/samplePick.ajax`, data)
export const testStartExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/testStart.ajax`, data)
export const testEndExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/testEnd.ajax`, data)
export const sampleReturnExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/sampleReturn.ajax`, data)
export const sampleShipExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/sampleShip.ajax`, data)
export const sampleRetainExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/sampleRetain.ajax`, data)
export const addVideoExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/addVideo.ajax`, data)
export const confirmDoneExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/confirmDone.ajax`, data)
export const retestExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/retest.ajax`, data)

// type=6/8 开票收款确认
export const saveExpOrderInvoiceBill = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/saveInvoiceBill.ajax`, data)
export const confirmExpOrderCustomer = (id: string | number) =>
  postAjax(`${BASE}/order/confirmCustomer.ajax`, { id })
export const confirmExpOrderPay = (id: string | number) =>
  postAjax(`${BASE}/order/confirmPay.ajax`, { id })
export const generateExpOrderAppointment = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/generateAppointment.ajax`, data)
export const updateExpOrderBasic = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/updateBasic.ajax`, data)
/** 对齐 Java submitExpOrder：body 为 [主单, ...明细行] */
export const submitExpOrder = (list: Record<string, unknown>[]) =>
  request.post(`${BASE}/order/submitExpOrder.ajax`, list, {
    headers: { 'Content-Type': 'application/json' },
  }) as unknown as Promise<AjaxBody>
export const createExpSubOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/createSubOrder.ajax`, data)

// type=9 确认已下单 / 付款申请 / 上传付款发票
export const confirmExpOrdered = (id: string | number) =>
  postAjax(`${BASE}/order/confirmOrdered.ajax`, { id })
export const subPayExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/subPay.ajax`, data)
export const uploadSubPayExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/uploadSubPay.ajax`, data)
export const uploadSubInvoiceExpOrder = (data: Record<string, unknown>) =>
  postAjax(`${BASE}/order/uploadSubInvoice.ajax`, data)

export const uploadExpOrderFile = (formData: FormData) =>
  // 勿手动设 Content-Type，否则缺少 boundary，Django 解析不到 FILES
  // 对齐 Java experimentOrder/uploadData.ajax（同时保留 adminExperiment 路径）
  request.post(`/experimentOrder/uploadData.ajax`, formData, {
    timeout: 120000,
    headers: { 'Content-Type': undefined as unknown as string },
  }) as unknown as Promise<AjaxBody>

/** 对齐 Java bill/uploadBill.ajax：收款/开票弹窗凭据 */
export const uploadExpBillFile = (formData: FormData) =>
  request.post(`/bill/uploadBill.ajax`, formData, {
    timeout: 120000,
    headers: { 'Content-Type': undefined as unknown as string },
  }) as unknown as Promise<AjaxBody>

export const deleteExpOrderFile = (id: string | number) =>
  postAjax(`${BASE}/order/deleteFile.ajax`, { id })

/** 对齐 Java downloadFile.ajax：blob 强制下载，避免 window.open 预览 */
export async function downloadExpOrderFile(
  id: string | number,
  displayName?: string
): Promise<{ ok: boolean; message?: string }> {
  const result = await fetchExpOrderFileBlob(id, displayName)
  if (!result.ok || !result.blob) {
    return { ok: false, message: result.message || '下载失败' }
  }
  const objUrl = URL.createObjectURL(result.blob)
  const a = document.createElement('a')
  a.href = objUrl
  a.download = result.filename || displayName || `file-${id}`
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(objUrl)
  return { ok: true }
}

/** 拉取附件字节（本地盘 / OSS），供下载与预览共用 */
export async function fetchExpOrderFileBlob(
  id: string | number,
  displayName?: string
): Promise<{ ok: boolean; blob?: Blob; filename?: string; message?: string }> {
  const { getToken } = await import('@admin/utils/auth')
  const token = getToken() || ''
  const base = (import.meta.env.VITE_APP_BASE_API as string) || '/api'
  const qs = new URLSearchParams({
    id: String(id),
    ...(displayName ? { name: displayName } : {}),
  })
  // 优先订单服务正式路由；pc 为网关本地兜底（勿再误转发 404）
  const urls = [
    `${base}/experimentOrder/downloadFile.ajax?${qs}`,
    `${base}/adminExperiment/order/downloadFile.ajax?${qs}`,
    `${base}/pc/downloadFile.ajax?${qs}`,
  ]
  let lastErr = '下载失败'
  let businessErr = ''
  for (const url of urls) {
    try {
      const res = await fetch(url, {
        method: 'GET',
        headers: {
          Accept: 'application/octet-stream,*/*',
          'X-Channel': 'admin',
          ...(token
            ? { token, Authorization: `Bearer ${token}` }
            : {}),
        },
      })
      const ct = (res.headers.get('content-type') || '').toLowerCase()
      if (!res.ok) {
        let msg = `下载失败(${res.status})`
        if (ct.includes('json')) {
          try {
            const body = (await res.json()) as AjaxBody
            msg = body.resMsg || body.message || msg
          } catch {
            /* keep msg */
          }
        }
        // 网关转发 404/非 JSON 属于路由问题，保留更早的业务错误
        const isProxyNoise =
          /返回非 JSON|不可用（HTTP|Not Found/i.test(msg) || res.status === 404
        if (!isProxyNoise || !businessErr) {
          lastErr = msg
          if (!isProxyNoise) businessErr = msg
        }
        continue
      }
      const blob = await res.blob()
      if (ct.includes('json') || blob.type.includes('json')) {
        const text = await blob.text()
        try {
          const body = JSON.parse(text) as AjaxBody
          const msg = body.resMsg || body.message || lastErr
          lastErr = msg
          businessErr = msg
        } catch {
          lastErr = text || lastErr
        }
        continue
      }
      const cd = res.headers.get('content-disposition') || ''
      let filename = displayName || `file-${id}`
      const m = /filename\*=UTF-8''([^;]+)|filename=\"?([^\";]+)\"?/i.exec(cd)
      if (m) {
        filename = decodeURIComponent((m[1] || m[2] || filename).trim())
      }
      // filename= 可能是 ASCII 占位，优先用展示名（含中文预约单）
      if (displayName && /\.pdf$/i.test(displayName)) {
        filename = displayName
      }
      const lower = filename.toLowerCase()
      let mime = blob.type || 'application/octet-stream'
      if (lower.endsWith('.pdf')) mime = 'application/pdf'
      else if (lower.endsWith('.png')) mime = 'image/png'
      else if (lower.endsWith('.jpg') || lower.endsWith('.jpeg')) mime = 'image/jpeg'
      const typed =
        mime && mime !== blob.type
          ? new Blob([blob], { type: mime })
          : blob
      return { ok: true, blob: typed, filename }
    } catch (e) {
      lastErr = e instanceof Error ? e.message : lastErr
    }
  }
  return { ok: false, message: businessErr || lastErr }
}

/** 预览附件：经后端取流后新开页，避免直链 OSS NoSuchKey */
export async function previewExpOrderFile(
  id: string | number,
  displayName?: string
): Promise<{ ok: boolean; message?: string }> {
  const result = await fetchExpOrderFileBlob(id, displayName)
  if (!result.ok || !result.blob) {
    return { ok: false, message: result.message || '预览失败' }
  }
  const objUrl = URL.createObjectURL(result.blob)
  const win = window.open(objUrl, '_blank')
  if (!win) {
    URL.revokeObjectURL(objUrl)
    return { ok: false, message: '浏览器拦截了预览窗口，请允许弹窗后重试' }
  }
  window.setTimeout(() => URL.revokeObjectURL(objUrl), 60_000)
  return { ok: true }
}


export const updateExpOrderMsg = (id: string | number, msg: string) =>
  postAjax(`${BASE}/order/updateMsg.ajax`, { id, msg })

export const fetchGrabOrderList = (p: Record<string, unknown>) =>
  fetchDatatable(`${BASE}/grab/list.ajax`, p)
/** 对齐 Java competitionOrder：参数为子单 id */
export const grabExpOrder = (childId: string | number) =>
  postAjax(`${BASE}/grab/competition.ajax`, { ofId: childId, id: childId })

// IOT 设备绑定（baseURL 已含 /api，路径勿再加 /api）
export const iotAuthLogin = (data: Record<string, unknown>) =>
  postAjax(`/iot/auth/login`, data)
export const iotAuthStatus = (data?: Record<string, unknown>) =>
  postAjax(`/iot/auth/status`, data || {})
export const iotAuthLogout = (data?: Record<string, unknown>) =>
  postAjax(`/iot/auth/logout`, data || {})
export const iotListDevices = (data?: Record<string, unknown>) =>
  postAjax(`/iot/device/list`, data || {})
export const iotBindDevice = (data: Record<string, unknown>) =>
  postAjax(`/iot/device/bind`, data)
/** 创建 IOT 试验任务（不选设备）；可传 childId 单行，或 childIds / all=1 批量 */
export const iotCreateTask = (data: Record<string, unknown>) =>
  postAjax(`/iot/task/create`, data)
export const iotCreateTasksBatch = (data: Record<string, unknown>) =>
  postAjax(`/iot/task/create-batch`, data)
/** 一单多行任务总览 */
export const iotTaskOverview = (data: Record<string, unknown>) =>
  postAjax(`/iot/task/overview`, data)
/** 免登跳转 IOT（授权缓存换 ticket） */
export const iotSsoJump = (data?: Record<string, unknown>) =>
  postAjax(`/iot/sso/jump`, data || {})
export const iotUnbindDevice = (data: Record<string, unknown>) =>
  postAjax(`/iot/device/unbind`, data)
export const iotGetBinding = (data: Record<string, unknown>) =>
  postAjax(`/iot/device/binding`, data)
export const iotResyncDevice = (data: Record<string, unknown>) =>
  postAjax(`/iot/device/resync`, data)
export const iotResyncTasksBatch = (data: Record<string, unknown>) =>
  postAjax(`/iot/device/resync-batch`, data)
