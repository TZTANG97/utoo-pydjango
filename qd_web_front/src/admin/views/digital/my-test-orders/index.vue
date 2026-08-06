<template>
  <div class="page-wrap">
    <section class="filter-panel">
      <el-form :inline="true" @submit.prevent="reload">
        <el-form-item>
          <el-input v-model="filters.orderId" clearable placeholder="来源订单编号" style="width: 180px" @keyup.enter="reload" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="reload">查询</el-button>
        </el-form-item>
      </el-form>
      <p class="hint">
        <template v-if="month">月份：{{ month }} · </template>
        测试人员：{{ userId || '-' }}
        <template v-if="saleUser"> · 销售：{{ saleUser }}</template>
      </p>
    </section>
    <section class="table-panel">
      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="parentOrderId" label="来源订单" min-width="150" show-overflow-tooltip />
        <el-table-column label="子订单编号" min-width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">{{ row.orderId || '-' }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="className" label="实验测试分类" min-width="140" show-overflow-tooltip />
        <el-table-column prop="goodsNums" label="数量" width="80" align="center" />
        <el-table-column prop="testUser" label="测试人员" width="110" />
        <el-table-column prop="finishTime" label="实际完成时间" width="160" />
        <el-table-column prop="saleUser" label="销售人员" width="110" />
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
import { fetchMyTestOrderList } from '@admin/api/fund'
import { useDataTable } from '@admin/composables/useDataTable'

const route = useRoute()
const router = useRouter()
const month = computed(() => String(route.query.month || ''))
const userId = computed(() => String(route.query.userId || ''))
const saleUser = computed(() => String(route.query.sale_user || route.query.saleUser || ''))

const filters = reactive({ orderId: '' })

function listParams() {
  const p: Record<string, unknown> = {}
  if (userId.value) p.userId = userId.value
  if (month.value) p.month = month.value
  if (saleUser.value) p.sale_user = saleUser.value
  if (filters.orderId) p.order_id = filters.orderId.trim()
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchMyTestOrderList({ ...p, ...listParams() }),
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

function openDetail(row: Record<string, unknown>) {
  const id = String(row.ofId || row.id || '')
  if (!id) return
  router.push({
    name: 'ExperimentOrderDetail',
    params: { id },
    query: { from: 'my-test', orderNo: String(row.parentOrderId || row.orderId || '') },
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
