<template>
  <admin-page-card :title="title">
    <template #actions>
      <el-button v-if="showExport" type="warning" :loading="exporting" @click="handleExport">导出</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="订单号">
        <el-input v-model="filters.orderId" clearable placeholder="订单号" style="width: 180px" />
      </el-form-item>
      <el-form-item v-if="isGrab" label="来源单号">
        <el-input v-model="filters.sourceOrder" clearable placeholder="来源单号" style="width: 180px" />
      </el-form-item>
      <el-form-item label="客户">
        <el-input v-model="filters.companyName" clearable placeholder="客户名称" style="width: 160px" />
      </el-form-item>
      <el-form-item v-if="!isGrab" label="销售经理">
        <el-input v-model="filters.saleManager" clearable placeholder="销售经理" style="width: 140px" />
      </el-form-item>
      <el-form-item v-if="!isGrab" label="销售员">
        <el-input v-model="filters.saleUser" clearable placeholder="销售员" style="width: 140px" />
      </el-form-item>
      <el-form-item v-if="!isGrab" label="状态">
        <el-select v-model="filters.orderStatus" clearable placeholder="全部" style="width: 130px">
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
      <el-table-column type="index" width="55" label="#" align="center" />
      <el-table-column prop="orderId" label="订单号" min-width="160" show-overflow-tooltip />
      <el-table-column v-if="showParent" prop="parentOrderId" label="来源单号" min-width="140" show-overflow-tooltip />
      <el-table-column prop="companyName" label="客户" min-width="140" show-overflow-tooltip />
      <el-table-column prop="saleManager" label="销售经理" min-width="110" />
      <el-table-column prop="saleUser" :label="isGrab ? '采购人员' : '销售员'" min-width="100" />
      <el-table-column prop="orderStatusLabel" label="状态" width="100" />
      <el-table-column v-if="!isGrab" prop="totalPrice" label="金额" width="100" align="right" />
      <el-table-column prop="addTime" :label="isGrab ? '下单时间' : '创建时间'" width="170" />
      <el-table-column label="操作" :width="isGrab ? 160 : 200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button v-if="isGrab" link type="success" @click="handleGrab(row)">抢单</el-button>
          <template v-if="showAudit && !isGrab">
            <el-button link type="warning" @click="handleAudit(row, true)">通过</el-button>
            <el-button link type="danger" @click="handleAudit(row, false)">驳回</el-button>
          </template>
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

    <el-drawer v-model="drawerVisible" title="订单详情" size="720px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ detail.orderId }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detail.orderStatusLabel }}</el-descriptions-item>
          <el-descriptions-item label="客户">{{ detail.companyName }}</el-descriptions-item>
          <el-descriptions-item label="金额">{{ detail.totalPrice ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="销售经理">{{ detail.saleManager }}</el-descriptions-item>
          <el-descriptions-item label="销售员">{{ detail.saleUser }}</el-descriptions-item>
          <el-descriptions-item label="来源单号">{{ detail.parentOrderId || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detail.addTime }}</el-descriptions-item>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  auditExpOrder,
  exportExpOrders,
  fetchExpOrderList,
  fetchExpOrderStatusOptions,
  fetchGrabOrderList,
  getExpOrderDetail,
  grabExpOrder,
} from '@/api/experiment'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const props = withDefaults(
  defineProps<{
    title: string
    orderType?: string | number
    mode?: 'list' | 'grab'
    showAudit?: boolean
    showExport?: boolean
  }>(),
  {
    orderType: '6',
    mode: 'list',
    showAudit: false,
    showExport: false,
  }
)

const isGrab = computed(() => props.mode === 'grab')
const showParent = computed(() => isGrab.value || ['8', '9', '10'].includes(String(props.orderType)))

const filters = reactive({
  orderId: '',
  sourceOrder: '',
  companyName: '',
  saleManager: '',
  saleUser: '',
  orderStatus: '',
})
const statusOpts = ref<Record<string, unknown>[]>([])
const drawerVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const exporting = ref(false)

function listParams() {
  const p: Record<string, unknown> = {}
  if (filters.orderId) p.orderId = filters.orderId.trim()
  if (filters.companyName) p.companyName = filters.companyName.trim()
  if (isGrab.value) {
    if (filters.sourceOrder) p.sourceOrder = filters.sourceOrder.trim()
  } else {
    p.orderType = props.orderType
    if (filters.saleManager) p.saleManager = filters.saleManager.trim()
    if (filters.saleUser) p.saleUser = filters.saleUser.trim()
    if (filters.orderStatus) p.orderStatus = filters.orderStatus
  }
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) => {
  const params = { ...p, ...listParams() }
  return isGrab.value ? fetchGrabOrderList(params) : fetchExpOrderList(params)
})

function reload() {
  pagination.page = 1
  return load(listParams())
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

async function handleGrab(row: Record<string, unknown>) {
  await ElMessageBox.confirm(`确认抢单 ${row.orderId || ''}？`, '抢单', { type: 'warning' })
  const res = await grabExpOrder(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success(String(res.resMsg || '抢单成功'))
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '抢单失败'))
  }
}

async function handleAudit(row: Record<string, unknown>, pass: boolean) {
  const action = pass ? '通过' : '驳回'
  const { value } = await ElMessageBox.prompt(`确认${action}订单 ${row.orderId || ''}？可填写备注`, action, {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPlaceholder: '备注（可选）',
    inputValue: '',
  }).catch(() => ({ value: null as string | null }))
  if (value === null) return
  const res = await auditExpOrder({ id: row.id, pass, remark: value || '' })
  if (isAjaxOk(res)) {
    ElMessage.success(String(res.resMsg || '操作成功'))
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}

function downloadCsv(filename: string, dataRows: Record<string, unknown>[]) {
  const headers = [
    ['orderId', '订单号'],
    ['companyName', '客户'],
    ['saleManager', '销售经理'],
    ['saleUser', '销售员'],
    ['orderStatusLabel', '状态'],
    ['totalPrice', '金额'],
    ['addTime', '创建时间'],
    ['parentOrderId', '来源单号'],
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
    const res = await exportExpOrders({ orderType: props.orderType })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '导出失败'))
      return
    }
    const dataRows = Array.isArray(res.obj) ? (res.obj as Record<string, unknown>[]) : []
    downloadCsv(`experiment_orders_${props.orderType}.csv`, dataRows)
    ElMessage.success(`已导出 ${dataRows.length} 条`)
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  if (!isGrab.value) {
    const res = await fetchExpOrderStatusOptions()
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      statusOpts.value = res.obj as Record<string, unknown>[]
    }
  }
  reload()
})
</script>

<style scoped lang="scss">
.filter-form { margin-bottom: 12px; }
.pager { display: flex; justify-content: flex-end; margin-top: 16px; }
.section-title { margin: 20px 0 10px; font-size: 14px; font-weight: 600; }
</style>
