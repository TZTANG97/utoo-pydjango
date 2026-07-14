<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchInvoiceList,
  fetchInvoiceDetail,
  rejectInvoice,
} from '@/api/billing'
import {
  INVOICE_STATUS,
  INVOICE_TYPE,
  formatDate,
  formatMoney,
} from '@/utils/billing-labels'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const loading = ref(false)
const rows = ref<Record<string, unknown>[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const detailVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)

const filters = reactive({
  order_startime: '',
  order_endtime: '',
  status: '',
})

async function loadData() {
  loading.value = true
  try {
    const result = await fetchInvoiceList({
      start: (page.value - 1) * pageSize.value,
      length: pageSize.value,
      draw: page.value,
      order_startime: filters.order_startime,
      order_endtime: filters.order_endtime,
      status: filters.status,
    })
    rows.value = result.data
    total.value = result.recordsTotal
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadData()
}

function handleReset() {
  filters.order_startime = ''
  filters.order_endtime = ''
  filters.status = ''
  handleSearch()
}

async function openDetail(row: Record<string, unknown>) {
  const res = await fetchInvoiceDetail(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
    return
  }
  detail.value = (res.obj || null) as Record<string, unknown> | null
  detailVisible.value = true
}

async function handleReject(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认驳回该发票申请？', '提示', { type: 'warning' })
  const res = await rejectInvoice(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '驳回失败'))
    return
  }
  ElMessage.success(res.resMsg || '驳回成功')
  loadData()
}

loadData()
</script>

<template>
  <div class="page-wrap">
    <el-card shadow="never">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="申请时间">
          <el-date-picker
            v-model="filters.order_startime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="开始时间"
          />
          <span class="range-sep">-</span>
          <el-date-picker
            v-model="filters.order_endtime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="结束时间"
          />
        </el-form-item>
        <el-form-item label="发票状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
            <el-option label="开票中" value="1" />
            <el-option label="已作废" value="3" />
            <el-option label="已开票" value="4" />
            <el-option label="已驳回" value="5" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column type="index" width="60" label="#" />
        <el-table-column prop="addTime" label="申请时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.addTime) }}</template>
        </el-table-column>
        <el-table-column prop="order_id" label="订单编号" min-width="140" />
        <el-table-column prop="userName" label="用户名" min-width="120" />
        <el-table-column prop="mobile" label="电话" min-width="120" />
        <el-table-column label="发票金额" min-width="100">
          <template #default="{ row }">{{ formatMoney(row.invoice_money) }}</template>
        </el-table-column>
        <el-table-column label="发票类型" min-width="120">
          <template #default="{ row }">{{ INVOICE_TYPE[Number(row.type)] || '-' }}</template>
        </el-table-column>
        <el-table-column prop="invoice_title" label="公司名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="credit_code" label="信用代码" min-width="160" show-overflow-tooltip />
        <el-table-column label="发票状态" min-width="100">
          <template #default="{ row }">{{ INVOICE_STATUS[Number(row.status)] || row.status }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">查看</el-button>
            <el-button
              v-if="Number(row.status) === 1"
              link
              type="danger"
              @click="handleReject(row)"
            >
              驳回
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadData"
          @size-change="handleSearch"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" title="发票申请详情" width="720px">
      <el-descriptions v-if="detail" :column="2" border>
        <el-descriptions-item label="申请时间">{{ formatDate(detail.addTime) }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ detail.userName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ detail.mobile || '-' }}</el-descriptions-item>
        <el-descriptions-item label="发票金额">{{ formatMoney(detail.invoice_money) }}</el-descriptions-item>
        <el-descriptions-item label="发票类型">{{ INVOICE_TYPE[Number(detail.type)] || '-' }}</el-descriptions-item>
        <el-descriptions-item label="发票状态">{{ INVOICE_STATUS[Number(detail.status)] || detail.status }}</el-descriptions-item>
        <el-descriptions-item label="公司名称" :span="2">{{ detail.invoice_title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="信用代码" :span="2">{{ detail.credit_code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱" :span="2">{{ detail.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detail.notes || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.range-sep {
  margin: 0 8px;
  color: #909399;
}
</style>
