<template>
  <div class="page-wrap">
    <section class="filter-panel">
      <div class="action-bar">
        <el-button type="warning" :loading="exportingFinished" @click="handleExportFinished">
          导出测试完成项目EXCEL
        </el-button>
        <el-button type="warning" :loading="exporting" @click="handleExport">导出EXCEL</el-button>
      </div>

      <el-form :inline="true" class="filter-form" @submit.prevent>
        <el-form-item>
          <el-input v-model="filters.customerName" clearable placeholder="客户名称" style="width: 150px" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="filters.parentOrderId" clearable placeholder="来源订单" style="width: 150px" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="filters.orderId" clearable placeholder="订单编号" style="width: 150px" />
        </el-form-item>
        <el-form-item>
          <div class="date-range">
            <el-date-picker
              v-model="filters.finishStart"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="完成开始"
              clearable
              style="width: 140px"
            />
            <span class="range-sep">至</span>
            <el-date-picker
              v-model="filters.finishEnd"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="完成结束"
              clearable
              style="width: 140px"
            />
          </div>
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.saleManager" clearable filterable placeholder="全部销售主管" style="width: 140px">
            <el-option v-for="o in managerOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.saleUser" clearable filterable placeholder="全部采购人员" style="width: 140px">
            <el-option v-for="o in purchaseOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.orderStatus" clearable placeholder="全部订单状态" style="width: 150px">
            <el-option v-for="o in statusOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)">
              <el-tag :type="statusTagType(String(o.label))" size="small" effect="light" round>{{ o.label }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.payStatus" clearable placeholder="全部付款状态" style="width: 140px">
            <el-option v-for="o in payStatusOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)">
              <el-tag :type="payTagType(String(o.label))" size="small" effect="light" round>{{ o.label }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.testUserId" clearable filterable placeholder="全部测试人员" style="width: 140px">
            <el-option v-for="o in testUserOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-actions">
          <el-button type="primary" @click="reload">查询</el-button>
          <el-button type="danger" class="btn-reset" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="table-panel">
      <div class="table-toolbar">
        <div class="toolbar-title">
          <span class="title-text">实验分包子订单</span>
          <span class="title-meta">共 {{ total }} 条</span>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="rows"
        class="data-table"
        stripe
        :header-cell-style="headerCellStyle"
        :row-class-name="rowClassName"
      >
        <el-table-column type="index" width="52" label="#" align="center" />
        <el-table-column prop="orderId" label="订单编号" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button link type="primary" class="order-link" @click="openDetail(row)">{{ row.orderId }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="parentOrderId" label="来源订单" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-code">{{ row.parentOrderId || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="companyName" label="进货公司名称" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-strong">
              {{ row.stockCompanyName || row.companyName || row.customerName || '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="saleManager" label="销售主管" width="100" show-overflow-tooltip>
          <template #default="{ row }"><span class="cell-muted">{{ row.saleManager || '-' }}</span></template>
        </el-table-column>
        <el-table-column prop="saleUser" label="采购人员" width="100" show-overflow-tooltip>
          <template #default="{ row }"><span class="cell-muted">{{ row.saleUser || '-' }}</span></template>
        </el-table-column>
        <el-table-column prop="testName" label="测试人员" width="100" show-overflow-tooltip>
          <template #default="{ row }"><span class="cell-muted">{{ row.testName || '-' }}</span></template>
        </el-table-column>
        <el-table-column prop="totalPrice" label="订单总价" width="110" align="right">
          <template #default="{ row }">
            <span class="money">¥ {{ formatMoney(row.totalPrice) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="orderTime" label="下单时间" width="110">
          <template #default="{ row }"><span class="cell-muted">{{ row.orderTime || '-' }}</span></template>
        </el-table-column>
        <el-table-column prop="orderStatusLabel" label="订单状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.orderStatusLabel)" size="small" effect="light" round class="status-tag">
              {{ row.orderStatusLabel || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payStatusLabel" label="付款状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="payTagType(row.payStatusLabel)" size="small" effect="plain" round>
              {{ row.payStatusLabel || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          background
          layout="sizes, total, prev, pager, next"
          :total="total"
          @size-change="reload"
          @current-change="() => load(listParams())"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  exportExpOrders,
  fetchExpOrderList,
  fetchExpOrderStatusOptions,
} from '@/api/experiment'
import { fetchUserList } from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const router = useRouter()
const route = useRoute()

const headerCellStyle = {
  background: '#f3f6fb',
  color: '#3a4660',
  fontWeight: 600,
  borderBottom: '1px solid #e4ebf5',
}

const filters = reactive({
  customerName: '',
  parentOrderId: '',
  orderId: '',
  finishStart: '',
  finishEnd: '',
  saleManager: '',
  saleUser: '',
  orderStatus: '',
  payStatus: '',
  testUserId: '',
})

const statusOpts = ref<Record<string, unknown>[]>([])
const payStatusOpts = ref<Record<string, unknown>[]>([])
const managerOpts = ref<Record<string, unknown>[]>([])
const purchaseOpts = ref<Record<string, unknown>[]>([])
const testUserOpts = ref<Record<string, unknown>[]>([])
const exporting = ref(false)
const exportingFinished = ref(false)

function formatMoney(value: unknown) {
  const num = Number(value ?? 0)
  return Number.isFinite(num) ? num.toFixed(2) : '0.00'
}

function statusTagType(label: unknown): 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  const text = String(label || '')
  if (/待审核|待确认|待处理|审核中/.test(text)) return 'warning'
  if (/已付款|已完成|已结清|完成|通过/.test(text)) return 'success'
  if (/拒绝|驳回|取消|关闭|作废/.test(text)) return 'danger'
  if (/未发起|草稿|新建|未申请/.test(text)) return 'info'
  if (/进行中|测试|实验|发货|收款/.test(text)) return 'primary'
  return 'info'
}

function payTagType(label: unknown): 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  const text = String(label || '')
  if (/待审核/.test(text)) return 'warning'
  if (/已审核|已付款|已完成/.test(text)) return 'success'
  if (/已驳回|拒绝/.test(text)) return 'danger'
  if (/未申请/.test(text)) return 'info'
  return 'primary'
}

function rowClassName({ row }: { row: Record<string, unknown> }) {
  return /待审核|待确认|待处理/.test(String(row.orderStatusLabel || row.payStatusLabel || ''))
    ? 'row-pending'
    : ''
}

function listParams() {
  const p: Record<string, unknown> = { orderType: '9' }
  if (filters.customerName) p.stockCompanyName = filters.customerName.trim()
  if (filters.parentOrderId) p.parentOrderId = filters.parentOrderId.trim()
  if (filters.orderId) p.orderId = filters.orderId.trim()
  if (filters.finishStart) p.finishStart = filters.finishStart
  if (filters.finishEnd) p.finishEnd = filters.finishEnd
  if (filters.saleManager) p.saleManager = filters.saleManager
  if (filters.saleUser) p.saleUser = filters.saleUser
  if (filters.orderStatus) p.orderStatus = filters.orderStatus
  if (filters.payStatus !== '') p.payStatus = filters.payStatus
  if (filters.testUserId) p.testUserId = filters.testUserId
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchExpOrderList({ ...p, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

function resetFilters() {
  Object.assign(filters, {
    customerName: '',
    parentOrderId: '',
    orderId: '',
    finishStart: '',
    finishEnd: '',
    saleManager: '',
    saleUser: '',
    orderStatus: '',
    payStatus: '',
    testUserId: '',
  })
  reload()
}

function mapUserRows(data: Record<string, unknown>[]) {
  return data
    .map((u) => ({
      value: String(u.id ?? u.userId ?? ''),
      label: String(u.userName || u.trueName || u.user_name || u.true_name || u.id || ''),
    }))
    .filter((o) => o.value)
}

async function loadOptions() {
  const statusRes = await fetchExpOrderStatusOptions({ kind: '9' })
  if (isAjaxOk(statusRes) && Array.isArray(statusRes.obj)) {
    statusOpts.value = statusRes.obj as Record<string, unknown>[]
  }
  const payRes = await fetchExpOrderStatusOptions({ kind: 'pay' })
  if (isAjaxOk(payRes) && Array.isArray(payRes.obj)) {
    payStatusOpts.value = payRes.obj as Record<string, unknown>[]
  } else {
    payStatusOpts.value = [
      { value: '0', label: '未申请' },
      { value: '33', label: '已驳回' },
      { value: '32', label: '待审核' },
      { value: '34', label: '已审核' },
      { value: '36', label: '已付款' },
      { value: '38', label: '已完成' },
    ]
  }

  const silent = { silentError: true }
  try {
    const mgr = await fetchUserList({ start: 0, length: 500, type: 1, draw: 1 }, silent)
    managerOpts.value = mapUserRows(Array.isArray(mgr.data) ? mgr.data : [])
  } catch {
    /* ignore */
  }
  try {
    const purchase = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 }, silent)
    purchaseOpts.value = mapUserRows(Array.isArray(purchase.data) ? purchase.data : [])
  } catch {
    /* ignore */
  }
  try {
    const tester = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 }, silent)
    testUserOpts.value = mapUserRows(Array.isArray(tester.data) ? tester.data : [])
  } catch {
    /* ignore */
  }
}

function openDetail(row: Record<string, unknown>) {
  const orderNo = String(row.orderId || '').trim()
  router.push({
    name: 'ExperimentOrderDetail',
    params: { id: String(row.id) },
    query: {
      from: 'subcontract-sub-orders',
      ...(orderNo ? { orderNo } : {}),
    },
  })
}

function downloadBase64File(fileName: string, base64: string, contentType: string) {
  const bin = atob(base64)
  const bytes = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  const blob = new Blob([bytes], { type: contentType || 'application/octet-stream' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  a.click()
  URL.revokeObjectURL(url)
}

function downloadCsv(filename: string, dataRows: Record<string, unknown>[]) {
  const headers = [
    ['orderId', '订单编号'],
    ['parentOrderId', '来源订单'],
    ['companyName', '进货公司名称'],
    ['saleManager', '销售主管'],
    ['saleUser', '采购人员'],
    ['testName', '测试人员'],
    ['totalPrice', '订单总价'],
    ['orderTime', '下单时间'],
    ['orderStatusLabel', '订单状态'],
    ['payStatusLabel', '付款状态'],
  ] as const
  const escape = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [
    headers.map((h) => escape(h[1])).join(','),
    ...dataRows.map((r) =>
      headers
        .map((h) =>
          escape(
            h[0] === 'companyName'
              ? r.stockCompanyName || r.companyName || r.customerName || ''
              : r[h[0]]
          )
        )
        .join(',')
    ),
  ]
  const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function doExport(extra: Record<string, unknown> = {}) {
  const res = await exportExpOrders({ ...listParams(), ...extra })
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '导出失败'))
    return
  }
  const obj = res.obj as Record<string, unknown> | unknown[] | null
  if (
    obj &&
    !Array.isArray(obj) &&
    typeof obj === 'object' &&
    typeof obj.base64 === 'string' &&
    obj.base64
  ) {
    downloadBase64File(
      String(obj.fileName || '实验分包子订单.xlsx'),
      String(obj.base64),
      String(obj.contentType || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    )
    ElMessage.success(`已导出 ${Number(obj.rowCount) || 0} 条`)
    return
  }
  const dataRows = Array.isArray(obj) ? (obj as Record<string, unknown>[]) : []
  downloadCsv('experiment_subcontract_sub_orders.csv', dataRows)
  ElMessage.success(`已导出 ${dataRows.length} 条`)
}

async function handleExport() {
  exporting.value = true
  try {
    await doExport()
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

async function handleExportFinished() {
  exportingFinished.value = true
  try {
    await doExport({ exportMode: 'finished' })
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exportingFinished.value = false
  }
}

onMounted(async () => {
  applyRouteQuery()
  await loadOptions()
  reload()
})

function applyRouteQuery() {
  const q = route.query
  if (q.orderId) filters.orderId = String(q.orderId)
  if (q.parentOrderId) filters.parentOrderId = String(q.parentOrderId)
  if (q.saleManager) filters.saleManager = String(q.saleManager)
  if (q.saleUser) filters.saleUser = String(q.saleUser)
  if (q.orderStatus) filters.orderStatus = String(q.orderStatus)
  if (q.payStatus != null && String(q.payStatus) !== '') {
    filters.payStatus = String(q.payStatus)
  }
  if (q.testUserId) filters.testUserId = String(q.testUserId)
}
</script>

<style scoped lang="scss">
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.filter-panel,
.table-panel {
  background: #fff;
  border: 1px solid #e8eef6;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(31, 45, 61, 0.04);
}

.filter-panel {
  padding: 14px 18px 2px;
  background: linear-gradient(180deg, #fbfcfe 0%, #ffffff 55%);
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eef2f8;
  flex-wrap: wrap;
}

.filter-form {
  :deep(.el-form-item) {
    margin-right: 12px;
    margin-bottom: 14px;
  }
}

.date-range {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.range-sep {
  color: #94a0b4;
  font-size: 13px;
}

.filter-actions {
  :deep(.el-form-item__content) {
    gap: 8px;
  }
}

.btn-reset {
  color: #fff !important;
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
}

.table-panel {
  padding: 14px 16px 16px;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eef2f8;
}

.toolbar-title {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.title-text {
  font-size: 15px;
  font-weight: 600;
  color: #24324a;
}

.title-meta {
  font-size: 12px;
  color: #8a95a8;
}

.data-table {
  --el-table-border-color: #eef2f8;
  --el-table-row-hover-bg-color: #f5f9ff;

  :deep(.el-table__inner-wrapper::before) {
    display: none;
  }

  :deep(.el-table__row.row-pending > td.el-table__cell) {
    background: #fffaf2;
  }

  :deep(.el-table__row.row-pending:hover > td.el-table__cell) {
    background: #fff4e5 !important;
  }
}

.order-link {
  font-weight: 600;
}

.cell-code {
  color: #2f6fed;
  font-weight: 550;
}

.cell-strong {
  color: #24324a;
  font-weight: 550;
}

.cell-muted {
  color: #6b768a;
  font-size: 13px;
}

.money {
  color: #e6a23c;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}

.status-tag {
  min-width: 72px;
  justify-content: center;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
