<template>
  <admin-page-card title="实验分包子订单">
    <template #actions>
      <el-button type="warning" :loading="exportingFinished" @click="handleExportFinished">
        导出测试完成项目EXCEL
      </el-button>
      <el-button type="warning" :loading="exporting" @click="handleExport">导出EXCEL</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item>
        <el-input
          v-model="filters.customerName"
          clearable
          placeholder="客户名称"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-input
          v-model="filters.parentOrderId"
          clearable
          placeholder="来源订单"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-input v-model="filters.orderId" clearable placeholder="订单编号" style="width: 150px" />
      </el-form-item>
      <el-form-item>
        <el-date-picker
          v-model="filters.finishStart"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="测试完成开始时间"
          clearable
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item>
        <el-date-picker
          v-model="filters.finishEnd"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="测试完成结束时间"
          clearable
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="filters.saleManager"
          clearable
          filterable
          placeholder="全部销售主管"
          style="width: 140px"
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
          placeholder="全部采购人员"
          style="width: 140px"
        >
          <el-option
            v-for="o in purchaseOpts"
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
        >
          <el-option
            v-for="o in statusOpts"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="filters.payStatus"
          clearable
          placeholder="全部付款状态"
          style="width: 140px"
        >
          <el-option
            v-for="o in payStatusOpts"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="filters.testUserId"
          clearable
          filterable
          placeholder="全部测试人员"
          style="width: 140px"
        >
          <el-option
            v-for="o in testUserOpts"
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
      <el-table-column prop="orderId" label="订单编号" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">{{ row.orderId }}</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="parentOrderId" label="来源订单" min-width="160" show-overflow-tooltip />
      <el-table-column prop="companyName" label="进货公司名称" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.stockCompanyName || row.companyName || row.customerName || '' }}
        </template>
      </el-table-column>
      <el-table-column prop="saleManager" label="销售主管" width="100" show-overflow-tooltip />
      <el-table-column prop="saleUser" label="采购人员" width="100" show-overflow-tooltip />
      <el-table-column prop="testName" label="测试人员" width="100" show-overflow-tooltip />
      <el-table-column prop="totalPrice" label="订单总价" width="100" align="right" />
      <el-table-column prop="orderTime" label="下单时间" width="110" />
      <el-table-column
        prop="orderStatusLabel"
        label="订单状态"
        width="120"
        show-overflow-tooltip
      />
      <el-table-column prop="payStatusLabel" label="付款状态" width="100" show-overflow-tooltip />
      <el-table-column label="操作" width="90" fixed="right">
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
        layout="sizes, total, prev, pager, next"
        :total="total"
        @size-change="reload"
        @current-change="() => load(listParams())"
      />
    </div>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  exportExpOrders,
  fetchExpOrderList,
  fetchExpOrderStatusOptions,
} from '@/api/experiment'
import { fetchUserList } from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const router = useRouter()

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
    // 与 Java purchasePayStatus 一致的兜底
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
  router.push({
    name: 'ExperimentOrderDetail',
    params: { id: String(row.id) },
    query: { from: 'subcontract-sub-orders' },
  })
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

async function doExport(filename: string) {
  const res = await exportExpOrders({ ...listParams() })
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '导出失败'))
    return
  }
  const dataRows = Array.isArray(res.obj) ? (res.obj as Record<string, unknown>[]) : []
  downloadCsv(filename, dataRows)
  ElMessage.success(`已导出 ${dataRows.length} 条`)
}

async function handleExport() {
  exporting.value = true
  try {
    await doExport('experiment_subcontract_sub_orders.csv')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

async function handleExportFinished() {
  exportingFinished.value = true
  try {
    // 对齐 Java bjexport：按测试完成时间筛选导出
    await doExport('experiment_subcontract_sub_orders_finished.csv')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exportingFinished.value = false
  }
}

onMounted(async () => {
  await loadOptions()
  reload()
})
</script>

<style scoped lang="scss">
.filter-form {
  margin-bottom: 12px;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
