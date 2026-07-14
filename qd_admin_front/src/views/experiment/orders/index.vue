<template>
  <admin-page-card title="实验订单">
    <template #actions>
      <el-button type="primary" @click="onCreate">创建实验订单</el-button>
      <el-button type="warning" :loading="exporting" @click="handleExport">导出EXCEL</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item>
        <el-input v-model="filters.customerName" clearable placeholder="客户企业名称" style="width: 150px" />
      </el-form-item>
      <el-form-item>
        <el-input v-model="filters.orderId" clearable placeholder="订单编号" style="width: 150px" />
      </el-form-item>
      <el-form-item>
        <el-input v-model="filters.goodsName" clearable placeholder="型号/产品名称" style="width: 150px" />
      </el-form-item>
      <el-form-item>
        <el-date-picker
          v-model="filters.orderStart"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="下单开始时间"
          clearable
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-date-picker
          v-model="filters.orderEnd"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="下单结束时间"
          clearable
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-select v-model="filters.supplierName" clearable filterable placeholder="全部所属公司" style="width: 160px">
          <el-option
            v-for="o in supplierOpts"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="filters.saleManager" clearable filterable placeholder="全部销售主管" style="width: 140px">
          <el-option
            v-for="o in managerOpts"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="filters.saleUser" clearable filterable placeholder="全部销售人员" style="width: 140px">
          <el-option
            v-for="o in saleUserOpts"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="filters.orderStatus" clearable placeholder="全部订单状态" style="width: 150px">
          <el-option
            v-for="o in statusOpts"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="50" label="#" align="center" />
      <el-table-column prop="orderId" label="订单编号" min-width="170" show-overflow-tooltip />
      <el-table-column prop="customerName" label="客户企业名称" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.customerName || '' }}</template>
      </el-table-column>
      <el-table-column prop="supplierName" label="所属公司名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="saleManager" label="销售主管" width="100" show-overflow-tooltip />
      <el-table-column prop="saleUser" label="销售人员" width="100" show-overflow-tooltip />
      <el-table-column prop="totalPrice" label="订单总价" width="100" align="right" />
      <el-table-column prop="invoiceLabel" label="是否开票" width="90" align="center" />
      <el-table-column prop="orderTime" label="下单时间" width="110" />
      <el-table-column prop="orderStatusLabel" label="订单状态" width="120" show-overflow-tooltip />
      <el-table-column prop="invoiceAmount" label="已开票金额" width="110" align="right" />
      <el-table-column prop="receiveAmount" label="已收款金额" width="110" align="right" />
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button
            v-if="String(row.orderStatus) !== '66'"
            link
            type="primary"
            @click="onCopy(row)"
          >
            复制
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50]"
        layout="sizes, total, prev, pager, next"
        :total="total"
        @size-change="reload"
        @current-change="() => load(listParams())"
      />
    </div>

    <el-drawer v-model="drawerVisible" title="订单详情" size="760px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单编号">{{ detail.orderId }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">{{ detail.orderStatusLabel }}</el-descriptions-item>
          <el-descriptions-item label="客户企业">{{ detail.companyName || detail.customerName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="订单总价">{{ detail.totalPrice ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="销售主管">{{ detail.saleManager }}</el-descriptions-item>
          <el-descriptions-item label="销售人员">{{ detail.saleUser }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ detail.orderTime || detail.addTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detail.addTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.mark || '-' }}</el-descriptions-item>
        </el-descriptions>
        <h4 class="section-title">子单明细</h4>
        <el-table :data="(detail.children as Record<string, unknown>[]) || []" border size="small">
          <el-table-column prop="childOrderId" label="子单号" min-width="130" show-overflow-tooltip />
          <el-table-column prop="goodsName" label="产品" min-width="120" show-overflow-tooltip />
          <el-table-column prop="goodsSpec" label="型号" min-width="100" />
          <el-table-column prop="projectName" label="测试项目" min-width="120" show-overflow-tooltip />
          <el-table-column prop="testUserName" label="测试员" width="100" />
          <el-table-column prop="orderStatusLabel" label="状态" width="90" />
        </el-table>
      </template>
    </el-drawer>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  exportExpOrders,
  fetchExpOrderList,
  fetchExpOrderStatusOptions,
  getExpOrderDetail,
} from '@/api/experiment'
import { fetchSupplierAll, fetchUserList } from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

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
const drawerVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const exporting = ref(false)

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

function mapUserRows(data: Record<string, unknown>[]) {
  return data.map((u) => ({
    value: String(u.id ?? u.userId ?? ''),
    label: String(u.userName || u.trueName || u.user_name || u.true_name || u.id || ''),
  })).filter((o) => o.value)
}

async function loadOptions() {
  const statusRes = await fetchExpOrderStatusOptions()
  if (isAjaxOk(statusRes) && Array.isArray(statusRes.obj)) {
    statusOpts.value = statusRes.obj as Record<string, unknown>[]
  }

  try {
    const supRes = await fetchSupplierAll()
    if (isAjaxOk(supRes)) {
      const raw = (supRes.obj || supRes.data) as unknown
      const list = Array.isArray(raw)
        ? raw
        : Array.isArray((raw as Record<string, unknown>)?.list)
          ? ((raw as Record<string, unknown>).list as unknown[])
          : []
      supplierOpts.value = (list as Record<string, unknown>[]).map((s) => ({
        value: String(s.id ?? ''),
        label: String(s.companyName || s.company_name || s.name || s.id || ''),
      })).filter((o) => o.value)
    }
  } catch {
    /* ignore */
  }

  try {
    const mgr = await fetchUserList({ start: 0, length: 500, type: 1, draw: 1 })
    managerOpts.value = mapUserRows(Array.isArray(mgr.data) ? mgr.data : [])
  } catch {
    /* ignore */
  }
  try {
    const sale = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 })
    saleUserOpts.value = mapUserRows(Array.isArray(sale.data) ? sale.data : [])
  } catch {
    /* ignore */
  }
}

async function openDetail(row: Record<string, unknown>) {
  const res = await getExpOrderDetail(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  detail.value = (res.obj as Record<string, unknown>) || null
  drawerVisible.value = true
}

function onCreate() {
  ElMessage.info('创建实验订单功能将在后续批次完善')
}

function onCopy(_row: Record<string, unknown>) {
  ElMessage.info('复制订单功能将在后续批次完善')
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
    const dataRows = Array.isArray(res.obj) ? (res.obj as Record<string, unknown>[]) : []
    downloadCsv('experiment_orders.csv', dataRows)
    ElMessage.success(`已导出 ${dataRows.length} 条`)
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  await loadOptions()
  reload()
})
</script>

<style scoped lang="scss">
.filter-form { margin-bottom: 12px; }
.pager { display: flex; justify-content: flex-end; margin-top: 16px; }
.section-title { margin: 20px 0 10px; font-size: 14px; font-weight: 600; }
</style>
