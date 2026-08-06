<template>
  <div class="page-wrap">
    <section class="filter-panel">
      <el-form :inline="true" @submit.prevent="reload">
        <el-form-item>
          <el-input v-model="filters.orderId" clearable placeholder="订单编号" style="width: 180px" @keyup.enter="reload" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="reload">查询</el-button>
        </el-form-item>
      </el-form>
      <p v-if="month" class="hint">月份：{{ month }} · 类型：{{ orderTypeLabel }}</p>
    </section>
    <section class="table-panel">
      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column label="订单编号" min-width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">{{ row.orderId || '-' }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="customerName" label="客户" min-width="140" show-overflow-tooltip />
        <el-table-column prop="supplierName" label="所属公司" min-width="120" show-overflow-tooltip />
        <el-table-column prop="saleManager" label="销售主管" width="110" />
        <el-table-column prop="saleUser" label="销售人员" width="110" />
        <el-table-column prop="totalPrice" label="金额" width="110" align="right" />
        <el-table-column prop="currencyLabel" label="币种" width="90" align="center" />
        <el-table-column prop="orderTime" label="下单时间" width="160" />
        <el-table-column prop="orderStatusLabel" label="状态" width="110" align="center" />
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
import { computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchExpAmountList } from '@/api/fund'
import { useDataTable } from '@/composables/useDataTable'

const route = useRoute()
const router = useRouter()
const month = computed(() => String(route.query.month || ''))
const orderType = computed(() => String(route.query.order_type || ''))
const orderTypeLabel = computed(() =>
  orderType.value === '1' ? '实验' : orderType.value === '2' ? '实验分包' : '全部',
)

const filters = reactive({ orderId: '' })

function listParams() {
  const p: Record<string, unknown> = {}
  if (month.value) p.month = month.value
  if (orderType.value) p.order_type = orderType.value
  if (filters.orderId) p.order_id = filters.orderId.trim()
  if (route.query.userId) p.userId = String(route.query.userId)
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchExpAmountList({ ...p, ...listParams() }),
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

function openDetail(row: Record<string, unknown>) {
  const id = String(row.id || '')
  if (!id) return
  router.push({
    name: 'ExperimentOrderDetail',
    params: { id },
    query: { from: 'exp-amount', orderNo: String(row.orderId || '') },
  })
}

onMounted(() => reload())
</script>

<style scoped lang="scss">
.page-wrap { display: flex; flex-direction: column; gap: 14px; }
.filter-panel, .table-panel {
  background: #fff; border: 1px solid #e8eef6; border-radius: 10px; padding: 14px 18px;
}
.hint { margin: 0 0 8px; color: #6b7280; font-size: 13px; }
.pager { display: flex; justify-content: flex-end; padding-top: 12px; }
</style>
