<template>
  <div class="page-wrap">
    <section class="filter-panel">
      <div class="action-bar">
        <el-button type="primary" @click="onCreate">创建实验订单</el-button>
        <el-button type="warning" :loading="exporting" @click="handleExport">导出EXCEL</el-button>
      </div>

      <el-form
        :inline="true"
        class="filter-form"
        @submit.prevent="reload"
        @keydown.enter="onFilterEnter"
      >
        <el-form-item>
          <el-input
            v-model="filters.customerName"
            clearable
            placeholder="客户企业名称"
            style="width: 150px"
            @keyup.enter="reload"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="filters.orderId"
            clearable
            placeholder="订单编号"
            style="width: 150px"
            @keyup.enter="reload"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="filters.goodsName"
            clearable
            placeholder="型号/产品名称"
            style="width: 150px"
            @keyup.enter="reload"
          />
        </el-form-item>
        <el-form-item>
          <div class="date-range" @keydown.enter.capture="onDateEnter">
            <el-date-picker
              v-model="filters.orderStart"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="下单开始"
              clearable
              style="width: 140px"
            />
            <span class="range-sep">至</span>
            <el-date-picker
              v-model="filters.orderEnd"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="下单结束"
              clearable
              style="width: 140px"
            />
          </div>
        </el-form-item>
        <el-form-item>
          <el-select
            v-model="filters.supplierName"
            clearable
            filterable
            placeholder="全部所属公司"
            style="width: 160px"
            @keyup.enter="reload"
          >
            <el-option
              v-for="o in supplierOpts"
              :key="String(o.value)"
              :label="String(o.label)"
              :value="String(o.value)"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select
            v-model="filters.saleManager"
            clearable
            filterable
            placeholder="全部销售主管"
            style="width: 140px"
            @keyup.enter="reload"
          >
            <el-option
              v-for="o in managerOpts"
              :key="String(o.value)"
              :label="String(o.label)"
              :value="String(o.value)"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select
            v-model="filters.saleUser"
            clearable
            filterable
            placeholder="全部销售人员"
            style="width: 140px"
            @keyup.enter="reload"
          >
            <el-option
              v-for="o in saleUserOpts"
              :key="String(o.value)"
              :label="String(o.label)"
              :value="String(o.value)"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select
            v-model="filters.orderStatus"
            clearable
            placeholder="全部订单状态"
            style="width: 150px"
            @keyup.enter="reload"
          >
            <el-option
              v-for="o in statusOpts"
              :key="String(o.value)"
              :label="String(o.label)"
              :value="String(o.value)"
            >
              <span class="status-option">
                <el-tag
                  :type="statusTagType(String(o.label))"
                  size="small"
                  effect="light"
                  round
                >
                  {{ o.label }}
                </el-tag>
              </span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item class="filter-actions">
          <el-button type="primary" native-type="submit">查询</el-button>
          <el-button type="danger" class="btn-reset" native-type="button" @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="table-panel">
      <div class="table-toolbar">
        <div class="toolbar-title">
          <span class="title-text">实验订单</span>
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
        <el-table-column prop="orderId" label="订单编号" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button link type="primary" class="order-link" @click="openDetail(row)">
              {{ row.orderId }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="customerName" label="客户企业名称" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-strong">{{ row.customerName || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplierName" label="所属公司名称" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-muted">{{ row.supplierName || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="saleManager" label="销售主管" width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-muted">{{ row.saleManager || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="saleUser" label="销售人员" width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-muted">{{ row.saleUser || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="totalPrice" label="订单总价" width="110" align="right">
          <template #default="{ row }">
            <span class="money">¥ {{ formatMoney(row.totalPrice) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="invoiceLabel" label="是否开票" width="96" align="center">
          <template #default="{ row }">
            <el-tag
              :type="invoiceTagType(row.invoiceLabel)"
              size="small"
              effect="light"
              round
            >
              {{ row.invoiceLabel || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="orderTime" label="下单时间" width="118">
          <template #default="{ row }">
            <span class="cell-muted">{{ row.orderTime || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="orderStatusLabel" label="订单状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag
              :type="statusTagType(row.orderStatusLabel)"
              size="small"
              effect="light"
              round
              class="status-tag"
            >
              {{ row.orderStatusLabel || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="invoiceAmount" label="已开票金额" width="118" align="right">
          <template #default="{ row }">
            <span class="money soft">¥ {{ formatMoney(row.invoiceAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="receiveAmount" label="已收款金额" width="118" align="right">
          <template #default="{ row }">
            <span class="money soft">¥ {{ formatMoney(row.receiveAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right" align="center">
          <template #default="{ row }">
            <div class="op-group">
              <el-button link type="primary" @click="openDetail(row)">查看</el-button>
              <el-button
                v-if="String(row.orderStatus) !== '0'"
                link
                type="primary"
                @click="onCopy(row)"
              >
                复制
              </el-button>
            </div>
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
} from '@admin/api/experiment'
import { fetchSupplierAll, fetchUserList } from '@admin/api/system'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

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
  orderId: '',
  goodsName: '',
  orderStart: '',
  orderEnd: '',
  supplierName: '',
  saleManager: '',
  saleUser: '',
  orderStatus: '',
})

const statusOpts = ref<Record<string, unknown>[]>([])
const supplierOpts = ref<Record<string, unknown>[]>([])
const managerOpts = ref<Record<string, unknown>[]>([])
const saleUserOpts = ref<Record<string, unknown>[]>([])
const exporting = ref(false)

function formatMoney(value: unknown) {
  const num = Number(value ?? 0)
  return Number.isFinite(num) ? num.toFixed(2) : '0.00'
}

function statusTagType(label: unknown): 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  const text = String(label || '')
  if (/待审核|待确认|待处理|审核中/.test(text)) return 'warning'
  if (/已付款|已完成|已结清|完成|通过/.test(text)) return 'success'
  if (/拒绝|驳回|取消|关闭|作废/.test(text)) return 'danger'
  if (/未发起|草稿|新建/.test(text)) return 'info'
  if (/进行中|测试|实验|发货|收款/.test(text)) return 'primary'
  return 'info'
}

function invoiceTagType(label: unknown): 'success' | 'info' {
  const text = String(label || '')
  return /是|已开|开票/.test(text) && !/未/.test(text) ? 'success' : 'info'
}

function rowClassName({ row }: { row: Record<string, unknown> }) {
  const label = String(row.orderStatusLabel || '')
  return /待审核|待确认|待处理/.test(label) ? 'row-pending' : ''
}

function listParams() {
  const p: Record<string, unknown> = { orderType: '6' }
  if (filters.customerName) p.customer_name = filters.customerName.trim()
  if (filters.orderId) p.orderId = filters.orderId.trim()
  if (filters.goodsName) p.goodsName = filters.goodsName.trim()
  if (filters.orderStart) p.orderStart = filters.orderStart
  if (filters.orderEnd) p.orderEnd = filters.orderEnd
  if (filters.supplierName) p.supplierName = filters.supplierName
  if (filters.saleManager) p.saleManager = filters.saleManager
  if (filters.saleUser) p.saleUser = filters.saleUser
  if (filters.orderStatus) p.orderStatus = filters.orderStatus
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchExpOrderList({ ...p, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

/** 下拉选完后回车查询；下拉面板打开时不拦截（留给选中项） */
function onFilterEnter(e: KeyboardEvent) {
  if (e.key !== 'Enter' || e.isComposing) return
  const target = e.target as HTMLElement | null
  // 日期框由 onDateEnter 单独处理
  if (target?.closest('.el-date-editor')) return
  const openSelect = document.querySelector('.el-select__popper:not([aria-hidden="true"])')
  if (openSelect) return
  e.preventDefault()
  reload()
}

/** 日期输入框回车：capture 阶段拦截，避免被 DatePicker 吞掉 */
function onDateEnter(e: KeyboardEvent) {
  if (e.key !== 'Enter' || e.isComposing) return
  e.preventDefault()
  e.stopPropagation()
  // 若日期面板仍打开，先关掉再查
  const openPicker = document.querySelector('.el-picker__popper:not([aria-hidden="true"])')
  if (openPicker) {
    ;(e.target as HTMLElement | null)?.blur?.()
  }
  reload()
}

function resetFilters() {
  Object.assign(filters, {
    customerName: '',
    orderId: '',
    goodsName: '',
    orderStart: '',
    orderEnd: '',
    supplierName: '',
    saleManager: '',
    saleUser: '',
    orderStatus: '',
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
  const statusRes = await fetchExpOrderStatusOptions()
  if (isAjaxOk(statusRes) && Array.isArray(statusRes.obj)) {
    statusOpts.value = statusRes.obj as Record<string, unknown>[]
  }

  const silent = { silentError: true }
  try {
    const supRes = await fetchSupplierAll(silent)
    if (isAjaxOk(supRes)) {
      const raw = (supRes.obj || supRes.data) as unknown
      const list = Array.isArray(raw)
        ? raw
        : Array.isArray((raw as Record<string, unknown>)?.list)
          ? ((raw as Record<string, unknown>).list as unknown[])
          : []
      supplierOpts.value = (list as Record<string, unknown>[])
        .map((s) => ({
          value: String(s.id ?? ''),
          label: String(s.companyName || s.company_name || s.name || s.id || ''),
        }))
        .filter((o) => o.value)
    }
  } catch {
    /* ignore */
  }

  try {
    const mgr = await fetchUserList({ start: 0, length: 500, type: 1, draw: 1 }, silent)
    managerOpts.value = mapUserRows(Array.isArray(mgr.data) ? mgr.data : [])
  } catch {
    /* ignore */
  }
  try {
    const sale = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 }, silent)
    saleUserOpts.value = mapUserRows(Array.isArray(sale.data) ? sale.data : [])
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
      from: 'orders',
      ...(orderNo ? { orderNo } : {}),
    },
  })
}

function onCreate() {
  router.push({ name: 'ExperimentOrderCreate' })
}

function onCopy(row: Record<string, unknown>) {
  router.push({
    name: 'ExperimentOrderCreate',
    query: { copyFrom: String(row.id) },
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
    ['customerName', '客户企业名称'],
    ['supplierName', '所属公司名称'],
    ['saleManager', '销售主管'],
    ['saleUser', '销售人员'],
    ['totalPrice', '订单总价'],
    ['invoiceLabel', '是否开票'],
    ['orderTime', '下单时间'],
    ['orderStatusLabel', '订单状态'],
    ['invoiceAmount', '已开票金额'],
    ['receiveAmount', '已收款金额'],
  ] as const
  const escape = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [
    headers.map((h) => escape(h[1])).join(','),
    ...dataRows.map((r) => headers.map((h) => escape(r[h[0]])).join(',')),
  ]
  const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function handleExport() {
  exporting.value = true
  try {
    const res = await exportExpOrders({ orderType: '6', ...listParams() })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '导出失败'))
      return
    }
    const obj = res.obj as Record<string, unknown> | unknown[] | null
    // 对齐 Java：实验订单导出 xlsx（base64）
    if (
      obj &&
      !Array.isArray(obj) &&
      typeof obj === 'object' &&
      typeof obj.base64 === 'string' &&
      obj.base64
    ) {
      downloadBase64File(
        String(obj.fileName || '实验订单.xlsx'),
        String(obj.base64),
        String(obj.contentType || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
      )
      ElMessage.success(`已导出 ${Number(obj.rowCount) || 0} 条`)
      return
    }
    const dataRows = Array.isArray(obj) ? (obj as Record<string, unknown>[]) : []
    downloadCsv('experiment_orders.csv', dataRows)
    ElMessage.success(`已导出 ${dataRows.length} 条`)
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

function applyRouteQuery() {
  const q = route.query
  const orderId = String(q.orderId || q.order_id || '').trim()
  if (orderId) filters.orderId = orderId
  const year = String(q.year || q.statistics_time || '').trim()
  if (year && /^\d{4}$/.test(year)) {
    filters.orderStart = `${year}-01-01`
    filters.orderEnd = `${year}-12-31`
  }
  if (q.orderStart) filters.orderStart = String(q.orderStart)
  if (q.orderEnd) filters.orderEnd = String(q.orderEnd)
  if (q.saleUser) filters.saleUser = String(q.saleUser)
  if (q.saleManager) filters.saleManager = String(q.saleManager)
  if (q.orderStatus) filters.orderStatus = String(q.orderStatus)
}

onMounted(async () => {
  applyRouteQuery()
  await loadOptions()
  reload()
})
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

.status-option {
  display: inline-flex;
  align-items: center;
}

.filter-actions {
  :deep(.el-form-item__content) {
    gap: 8px;
  }
}

.btn-reset {
  --el-button-bg-color: #f56c6c;
  --el-button-border-color: #f56c6c;
  --el-button-text-color: #fff;
  --el-button-hover-bg-color: #f78989;
  --el-button-hover-border-color: #f78989;
  --el-button-hover-text-color: #fff;
  --el-button-active-bg-color: #dd6161;
  --el-button-active-border-color: #dd6161;
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

  &.soft {
    font-weight: 550;
    color: #d4a24a;
  }
}

.status-tag {
  min-width: 72px;
  justify-content: center;
}

.op-group {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
