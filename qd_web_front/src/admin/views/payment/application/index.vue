<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  agreePaymentApply,
  fetchPaymentApplyDetail,
  fetchPaymentApplyList,
  refusePaymentApply,
} from '@admin/api/billing'
import {
  PAYMENT_APPLY_STATUS,
  PAYMENT_ORDER_TYPE,
  formatDate,
  formatMoney,
} from '@admin/utils/billing-labels'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

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

const STATUS_OPTIONS = [
  { label: '待审核', value: '1', tag: 'warning' as const },
  { label: '已审核', value: '2', tag: 'success' as const },
  { label: '已拒绝', value: '3', tag: 'danger' as const },
]

function statusTagType(status: unknown): 'warning' | 'success' | 'danger' | 'info' {
  const key = String(status ?? '')
  if (key === '1') return 'warning'
  if (key === '2') return 'success'
  if (key === '3') return 'danger'
  return 'info'
}

function statusLabel(status: unknown) {
  return PAYMENT_APPLY_STATUS[String(status)] || String(status ?? '-')
}

function orderTypeLabel(orderType: unknown) {
  return PAYMENT_ORDER_TYPE[String(orderType)] || String(orderType ?? '-')
}

async function loadData() {
  loading.value = true
  try {
    const result = await fetchPaymentApplyList({
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
  const res = await fetchPaymentApplyDetail(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
    return
  }
  detail.value = (res.obj || null) as Record<string, unknown> | null
  detailVisible.value = true
}

async function handleAgree(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认通过该付款申请？', '提示', { type: 'warning' })
  const res = await agreePaymentApply(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success(res.resMsg || '确认付款成功')
  detailVisible.value = false
  loadData()
}

async function handleRefuse(row: Record<string, unknown>) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因', '拒绝付款', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  })
  const res = await refusePaymentApply(String(row.id), value || '')
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success(res.resMsg || '拒绝付款成功')
  detailVisible.value = false
  loadData()
}

loadData()
</script>

<template>
  <div class="page-wrap">
    <section class="filter-panel">
      <el-form :inline="true" class="filter-form" @submit.prevent="handleSearch">
        <el-form-item label="申请时间">
          <div class="date-range">
            <el-date-picker
              v-model="filters.order_startime"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="开始时间"
              class="date-input"
            />
            <span class="range-sep">至</span>
            <el-date-picker
              v-model="filters.order_endtime"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="结束时间"
              class="date-input"
            />
          </div>
        </el-form-item>
        <el-form-item label="审核状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态" class="status-select">
            <el-option
              v-for="opt in STATUS_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            >
              <span class="status-option">
                <el-tag :type="opt.tag" size="small" effect="light" round>{{ opt.label }}</el-tag>
              </span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item class="filter-actions">
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button type="danger" class="btn-reset" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="table-panel">
      <div class="table-toolbar">
        <div class="toolbar-title">
          <span class="title-text">申请列表</span>
          <span class="title-meta">共 {{ total }} 条</span>
        </div>
        <div class="legend">
          <span v-for="opt in STATUS_OPTIONS" :key="opt.value" class="legend-item">
            <el-tag :type="opt.tag" size="small" effect="plain" round>{{ opt.label }}</el-tag>
          </span>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="rows"
        class="data-table"
        stripe
        :header-cell-style="{
          background: '#f3f6fb',
          color: '#3a4660',
          fontWeight: 600,
          borderBottom: '1px solid #e4ebf5',
        }"
        :row-class-name="
          ({ row }) => (String(row.applyStatus) === '1' ? 'row-pending' : '')
        "
      >
        <el-table-column type="index" width="56" label="#" align="center" />
        <el-table-column label="申请时间" min-width="168">
          <template #default="{ row }">
            <span class="cell-muted">{{ formatDate(row.addTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="用户名" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-strong">{{ row.trueName || row.userName || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="mobile" label="电话" min-width="120">
          <template #default="{ row }">
            <span class="cell-muted">{{ row.mobile || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="金额" min-width="110" align="right">
          <template #default="{ row }">
            <span class="money">¥ {{ formatMoney(row.money) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="申请类型" min-width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" class="type-tag">
              {{ orderTypeLabel(row.orderType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核状态" min-width="110" align="center">
          <template #default="{ row }">
            <el-tag
              :type="statusTagType(row.applyStatus)"
              size="small"
              effect="light"
              round
              class="status-tag"
            >
              {{ statusLabel(row.applyStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="mark" label="备注" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-muted">{{ row.mark || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <div class="op-group">
              <el-button link type="primary" @click="openDetail(row)">查看</el-button>
              <template v-if="String(row.applyStatus) === '1'">
                <el-button link type="success" @click="handleAgree(row)">确认付款</el-button>
                <el-button link type="danger" @click="handleRefuse(row)">拒绝付款</el-button>
              </template>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          background
          layout="total, sizes, prev, pager, next"
          @current-change="loadData"
          @size-change="handleSearch"
        />
      </div>
    </section>

    <el-dialog
      v-model="detailVisible"
      title="付款申请详情"
      width="720px"
      class="detail-dialog"
      destroy-on-close
    >
      <template v-if="detail">
        <div class="detail-hero">
          <div class="detail-hero-main">
            <div class="detail-amount">¥ {{ formatMoney(detail.money) }}</div>
            <div class="detail-user">
              {{ detail.trueName || detail.userName || '-' }}
              <span v-if="detail.mobile" class="detail-mobile">{{ detail.mobile }}</span>
            </div>
          </div>
          <el-tag
            :type="statusTagType(detail.applyStatus)"
            size="large"
            effect="dark"
            round
          >
            {{ statusLabel(detail.applyStatus) }}
          </el-tag>
        </div>

        <el-descriptions :column="2" border class="detail-desc">
          <el-descriptions-item label="申请时间">{{ formatDate(detail.addTime) }}</el-descriptions-item>
          <el-descriptions-item label="申请类型">{{ orderTypeLabel(detail.orderType) }}</el-descriptions-item>
          <el-descriptions-item label="关联订单" :span="2">{{ detail.orderId || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.mark || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="String(detail.applyStatus) === '1'" class="detail-actions">
          <el-button type="danger" plain @click="handleRefuse(detail)">拒绝付款</el-button>
          <el-button type="success" @click="handleAgree(detail)">确认付款</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

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
  padding: 16px 18px 2px;
  background: linear-gradient(180deg, #fbfcfe 0%, #ffffff 55%);
}

.filter-form {
  :deep(.el-form-item) {
    margin-right: 18px;
    margin-bottom: 14px;
  }

  :deep(.el-form-item__label) {
    color: #5b6780;
    font-weight: 500;
  }
}

.date-range {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.date-input {
  width: 190px;
}

.range-sep {
  color: #94a0b4;
  font-size: 13px;
}

.status-select {
  width: 150px;
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
  gap: 12px;
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

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.legend-item {
  display: inline-flex;
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
  letter-spacing: 0.2px;
}

.type-tag {
  --el-tag-bg-color: #f0f4fa;
  --el-tag-border-color: #dce5f2;
  --el-tag-text-color: #4d5d78;
}

.status-tag {
  min-width: 68px;
  justify-content: center;
}

.op-group {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 2px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.detail-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px 18px;
  border-radius: 10px;
  background: linear-gradient(120deg, #f4f8ff 0%, #fff8ef 100%);
  border: 1px solid #e8eef6;
}

.detail-amount {
  font-size: 26px;
  font-weight: 700;
  color: #d48806;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.detail-user {
  margin-top: 6px;
  color: #24324a;
  font-size: 14px;
  font-weight: 550;
}

.detail-mobile {
  margin-left: 10px;
  color: #8a95a8;
  font-weight: 400;
  font-size: 13px;
}

.detail-desc {
  :deep(.el-descriptions__label) {
    width: 96px;
    color: #6b768a;
    background: #f7f9fc;
  }
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}
</style>
