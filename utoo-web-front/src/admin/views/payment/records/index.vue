<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchPayLogList } from '@admin/api/billing'
import { PAY_TYPE, PAY_WAY, formatDate, formatMoney } from '@admin/utils/billing-labels'

const router = useRouter()
const loading = ref(false)
const rows = ref<Record<string, unknown>[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const filters = reactive({
  order_num: '',
  pay_type: '',
  pay_way: '',
})

const PAY_TYPE_OPTIONS = [
  { label: '充值', value: '1', tag: 'success' as const },
  { label: '还款', value: '2', tag: 'warning' as const },
  { label: '支付', value: '3', tag: 'primary' as const },
]

const PAY_WAY_OPTIONS = [
  { label: '支付宝', value: '1', tag: 'primary' as const },
  { label: '微信', value: '2', tag: 'success' as const },
  { label: '线下', value: '3', tag: 'info' as const },
  { label: '余额', value: '4', tag: 'warning' as const },
]

function payTypeTag(type: unknown): 'success' | 'warning' | 'primary' | 'info' {
  const key = Number(type)
  if (key === 1) return 'success'
  if (key === 2) return 'warning'
  if (key === 3) return 'primary'
  return 'info'
}

function payWayTag(way: unknown): 'success' | 'warning' | 'primary' | 'info' {
  const key = Number(way)
  if (key === 1) return 'primary'
  if (key === 2) return 'success'
  if (key === 3) return 'info'
  if (key === 4) return 'warning'
  return 'info'
}

function payTypeLabel(type: unknown) {
  return PAY_TYPE[Number(type)] || '-'
}

function payWayLabel(way: unknown) {
  return PAY_WAY[Number(way)] || '-'
}

async function loadData() {
  loading.value = true
  try {
    const result = await fetchPayLogList({
      start: (page.value - 1) * pageSize.value,
      length: pageSize.value,
      draw: page.value,
      order_num: filters.order_num,
      pay_type: filters.pay_type,
      pay_way: filters.pay_way,
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
  filters.order_num = ''
  filters.pay_type = ''
  filters.pay_way = ''
  handleSearch()
}

function openOrderDetail(row: Record<string, unknown>) {
  const id = row.order_id
  if (id == null || id === '') {
    ElMessage.warning('未找到关联订单')
    return
  }
  const orderNo = String(row.order_num || '').trim()
  router.push({
    name: 'ExperimentOrderDetail',
    params: { id: String(id) },
    query: {
      ...(orderNo ? { orderNo } : {}),
    },
  })
}

loadData()
</script>

<template>
  <div class="page-wrap">
    <section class="filter-panel">
      <el-form :inline="true" class="filter-form" @submit.prevent="handleSearch">
        <el-form-item label="订单编号">
          <el-input
            v-model="filters.order_num"
            clearable
            placeholder="模糊搜索"
            class="order-input"
          />
        </el-form-item>
        <el-form-item label="支付类型">
          <el-select v-model="filters.pay_type" clearable placeholder="全部类型" class="select-sm">
            <el-option
              v-for="opt in PAY_TYPE_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            >
              <span class="option-tag">
                <el-tag :type="opt.tag" size="small" effect="light" round>{{ opt.label }}</el-tag>
              </span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="支付方式">
          <el-select v-model="filters.pay_way" clearable placeholder="全部方式" class="select-sm">
            <el-option
              v-for="opt in PAY_WAY_OPTIONS"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            >
              <span class="option-tag">
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
          <span class="title-text">支付记录</span>
          <span class="title-meta">共 {{ total }} 条</span>
        </div>
        <div class="legend">
          <span v-for="opt in PAY_TYPE_OPTIONS" :key="opt.value" class="legend-item">
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
      >
        <el-table-column type="index" width="56" label="#" align="center" />
        <el-table-column label="客户账号" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-strong">{{ row.mobile || row.userName || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="金额" min-width="120" align="right">
          <template #default="{ row }">
            <span class="money">¥ {{ formatMoney(row.money) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="支付类型" min-width="110" align="center">
          <template #default="{ row }">
            <el-tag
              :type="payTypeTag(row.pay_type)"
              size="small"
              effect="light"
              round
              class="status-tag"
            >
              {{ payTypeLabel(row.pay_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="支付方式" min-width="110" align="center">
          <template #default="{ row }">
            <el-tag
              :type="payWayTag(row.pay_way)"
              size="small"
              effect="plain"
              round
              class="status-tag"
            >
              {{ payWayLabel(row.pay_way) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联订单" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button
              v-if="row.order_num && row.order_id"
              link
              type="primary"
              class="order-link"
              @click="openOrderDetail(row)"
            >
              {{ row.order_num }}
            </el-button>
            <span v-else class="cell-muted">{{ row.order_num || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="支付时间" min-width="168">
          <template #default="{ row }">
            <span class="cell-muted">{{ formatDate(row.payTime || row.addTime) }}</span>
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

.order-input {
  width: 200px;
}

.select-sm {
  width: 140px;
}

.option-tag {
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

.data-table {
  --el-table-border-color: #eef2f8;
  --el-table-row-hover-bg-color: #f5f9ff;

  :deep(.el-table__inner-wrapper::before) {
    display: none;
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

.status-tag {
  min-width: 56px;
  justify-content: center;
}

.order-link {
  font-weight: 550;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
