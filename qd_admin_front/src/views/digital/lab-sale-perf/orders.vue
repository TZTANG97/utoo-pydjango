<template>
  <admin-page-card :title="pageTitle">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item>
        <el-input v-model="filters.customer_name" clearable placeholder="客户企业名称" style="width: 160px" />
      </el-form-item>
      <el-form-item>
        <el-input v-model="filters.order_id" clearable placeholder="订单编号" style="width: 150px" />
      </el-form-item>
      <el-form-item>
        <el-input v-model="filters.goods_name" clearable placeholder="型号/产品名称" style="width: 150px" />
      </el-form-item>
      <el-form-item>
        <el-select v-model="filters.order_status" clearable placeholder="全部订单状态" style="width: 140px">
          <el-option value="" label="全部订单状态" />
          <el-option value="0" label="已取消" />
          <el-option value="5" label="待提交审核" />
          <el-option value="10" label="已驳回" />
          <el-option value="20" label="待审核" />
          <el-option value="30" label="已审核" />
          <el-option value="50" label="已完成" />
          <el-option value="66" label="待平台确认" />
          <el-option value="67" label="待客户确认" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
        <el-button @click="goBack">返回</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" align="center" label="#" />
      <el-table-column prop="orderId" label="订单编号" min-width="140" show-overflow-tooltip />
      <el-table-column prop="customerName" label="客户企业名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="supplierName" label="所属公司名称" min-width="160" show-overflow-tooltip />
      <el-table-column label="销售主管" min-width="100" show-overflow-tooltip>
        <template #default="{ row }">{{ row.managerTrueName || row.managerName || '-' }}</template>
      </el-table-column>
      <el-table-column label="销售人员" min-width="100" show-overflow-tooltip>
        <template #default="{ row }">{{ row.saleUserTrueName || row.saleUserName || '-' }}</template>
      </el-table-column>
      <el-table-column prop="totalPrice" label="订单总价" width="110" align="right" />
      <el-table-column prop="invoiceLabel" label="是否开票" width="90" align="center" />
      <el-table-column prop="orderTime" label="下单时间" width="120" />
      <el-table-column prop="addTime" label="录入订单时间" min-width="160" />
      <el-table-column prop="orderStatusLabel" label="订单状态" width="110" align="center" />
      <el-table-column label="操作" width="90" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewOrder(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="() => load(listParams())"
      />
    </div>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchLabSalePerfOrders } from '@/api/digital'
import { useDataTable } from '@/composables/useDataTable'

const route = useRoute()
const router = useRouter()

const filters = reactive({
  customer_name: '',
  order_id: '',
  goods_name: '',
  order_status: '',
})

const typeLabel = computed(() => {
  const t = String(route.query.type || '1')
  if (t === '2') return '开票'
  if (t === '3') return '收款'
  return '订单'
})

const pageTitle = computed(() => {
  const name = String(route.query.name || '')
  const month = String(route.query.month || '')
  return `${name || '销售'}实际业绩${typeLabel.value}明细${month ? `（${month}）` : ''}`
})

function listParams() {
  return {
    sale_user_id: String(route.query.sale_user_id || ''),
    month: String(route.query.month || ''),
    type: String(route.query.type || '1'),
    customer_name: filters.customer_name,
    order_id: filters.order_id,
    goods_name: filters.goods_name,
    order_status: filters.order_status,
  }
}

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchLabSalePerfOrders({ ...params, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

function goBack() {
  router.push('/digital/lab-sale-perf')
}

function viewOrder(row: Record<string, unknown>) {
  router.push(`/experiment/order-detail/${row.id}`)
}

onMounted(() => reload())
</script>

<style scoped lang="scss">
.filter-form {
  margin-bottom: 12px;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
