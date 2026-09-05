<template>
  <div class="page-wrap">
    <section class="filter-panel">
      <el-form :inline="true" class="filter-form" @submit.prevent="reload">
        <el-form-item>
          <el-input
            v-model="filters.customerName"
            clearable
            placeholder="客户名称"
            style="width: 150px"
            @keyup.enter="reload"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="filters.parentOrderId"
            clearable
            placeholder="来源订单"
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
            <el-option v-for="o in statusOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.testUserId" clearable filterable placeholder="全部测试人员" style="width: 140px">
            <el-option v-for="o in testUserOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="reload">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="table-panel">
      <el-table
        v-loading="loading"
        :data="rows"
        border
        stripe
        :header-cell-style="headerCellStyle"
        @row-dblclick="(row: Record<string, unknown>) => openDetail(row)"
      >
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column label="订单编号" min-width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">{{ row.orderId || '-' }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="parentOrderId" label="来源订单" min-width="140" show-overflow-tooltip />
        <el-table-column prop="customerName" label="客户名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="saleManager" label="销售主管" width="110" show-overflow-tooltip />
        <el-table-column prop="saleUser" label="采购人员" width="110" show-overflow-tooltip />
        <el-table-column prop="testName" label="测试人员" width="110" show-overflow-tooltip />
        <el-table-column prop="orderTime" label="下单时间" width="160" />
        <el-table-column prop="orderStatusLabel" label="订单状态" width="120" align="center" />
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  fetchExpOrderStatusOptions,
  fetchExpWelcomeOrderList,
} from '@admin/api/experiment'
import { fetchUserList } from '@admin/api/system'
import { useDataTable } from '@admin/composables/useDataTable'
import { isAjaxOk } from '@admin/utils/request'

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
  saleManager: '',
  saleUser: '',
  orderStatus: '',
  testUserId: '',
})

const orderStatusOut = computed(() => {
  const v = route.query.order_status_out
  if (v == null || String(v) === '' || String(v) === 'null') return ''
  return String(v)
})
const isTimeout = computed(() => {
  const v = route.query.is_timeout
  if (v == null || String(v) === '' || String(v) === 'null') return ''
  return String(v)
})

const statusOpts = ref<Record<string, unknown>[]>([])
const managerOpts = ref<Record<string, unknown>[]>([])
const purchaseOpts = ref<Record<string, unknown>[]>([])
const testUserOpts = ref<Record<string, unknown>[]>([])

function listParams() {
  const p: Record<string, unknown> = {}
  if (orderStatusOut.value !== '') p.order_status_out = orderStatusOut.value
  if (isTimeout.value !== '') p.is_timeout = isTimeout.value
  if (filters.customerName) p.customerName = filters.customerName.trim()
  if (filters.parentOrderId) p.parentOrderId = filters.parentOrderId.trim()
  if (filters.orderId) p.orderId = filters.orderId.trim()
  if (filters.saleManager) p.saleManager = filters.saleManager
  if (filters.saleUser) p.saleUser = filters.saleUser
  if (filters.orderStatus) p.orderStatus = filters.orderStatus
  if (filters.testUserId) p.testUserId = filters.testUserId
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchExpWelcomeOrderList({ ...p, ...listParams() }),
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
    saleManager: '',
    saleUser: '',
    orderStatus: '',
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
  const statusRes = await fetchExpOrderStatusOptions({ kind: 'sub' })
  if (isAjaxOk(statusRes) && Array.isArray(statusRes.obj)) {
    statusOpts.value = statusRes.obj as Record<string, unknown>[]
  }
  const [mgr, purchase, tester] = await Promise.all([
    fetchUserList({ type: 1 }),
    fetchUserList({ type: 4 }),
    fetchUserList({ type: 3 }),
  ])
  if (isAjaxOk(mgr) && Array.isArray(mgr.obj)) {
    managerOpts.value = mapUserRows(mgr.obj as Record<string, unknown>[])
  }
  if (isAjaxOk(purchase) && Array.isArray(purchase.obj)) {
    purchaseOpts.value = mapUserRows(purchase.obj as Record<string, unknown>[])
  }
  if (isAjaxOk(tester) && Array.isArray(tester.obj)) {
    testUserOpts.value = mapUserRows(tester.obj as Record<string, unknown>[])
  }
}

function openDetail(row: Record<string, unknown>) {
  const id = String(row.id || '')
  if (!id) return
  router.push({
    name: 'ExperimentOrderDetail',
    params: { id },
    query: { from: 'welcome-orders', orderNo: String(row.orderId || '') },
  })
}

onMounted(async () => {
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

.filter-form {
  :deep(.el-form-item) {
    margin-right: 12px;
    margin-bottom: 14px;
  }
}

.pager {
  display: flex;
  justify-content: flex-end;
  padding: 12px 4px 4px;
}
</style>
