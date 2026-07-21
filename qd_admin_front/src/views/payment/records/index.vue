<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchPayLogList } from '@/api/billing'
import { PAY_TYPE, PAY_WAY, formatDate, formatMoney } from '@/utils/billing-labels'

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
  router.push(`/experiment/order-detail/${id}`)
}

loadData()
</script>

<template>
  <div class="page-wrap">
    <el-card shadow="never">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="订单编号">
          <el-input v-model="filters.order_num" clearable placeholder="模糊搜索" />
        </el-form-item>
        <el-form-item label="支付类型">
          <el-select v-model="filters.pay_type" clearable placeholder="全部" style="width: 120px">
            <el-option label="充值" value="1" />
            <el-option label="还款" value="2" />
            <el-option label="支付" value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="支付方式">
          <el-select v-model="filters.pay_way" clearable placeholder="全部" style="width: 120px">
            <el-option label="支付宝" value="1" />
            <el-option label="微信" value="2" />
            <el-option label="线下" value="3" />
            <el-option label="余额" value="4" />
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
        <el-table-column label="客户账号" min-width="120">
          <template #default="{ row }">{{ row.mobile || row.userName || '-' }}</template>
        </el-table-column>
        <el-table-column label="金额" min-width="100">
          <template #default="{ row }">{{ formatMoney(row.money) }}</template>
        </el-table-column>
        <el-table-column label="支付类型" min-width="100">
          <template #default="{ row }">{{ PAY_TYPE[Number(row.pay_type)] || '-' }}</template>
        </el-table-column>
        <el-table-column label="支付方式" min-width="100">
          <template #default="{ row }">{{ PAY_WAY[Number(row.pay_way)] || '-' }}</template>
        </el-table-column>
        <el-table-column label="关联订单" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button
              v-if="row.order_num && row.order_id"
              link
              type="primary"
              @click="openOrderDetail(row)"
            >
              {{ row.order_num }}
            </el-button>
            <span v-else>{{ row.order_num || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="支付时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.payTime || row.addTime) }}</template>
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
</style>
