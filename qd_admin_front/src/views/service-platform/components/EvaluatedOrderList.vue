<template>
  <admin-page-card :title="title">
    <el-form :inline="true" class="filter-form" @submit.prevent="reload">
      <el-form-item>
        <el-input
          v-model="filters.customer_name"
          clearable
          placeholder="客户企业名称"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-input
          v-model="filters.order_id"
          clearable
          placeholder="订单编号"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-input
          v-model="filters.goods_name"
          clearable
          placeholder="型号/产品名称"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-date-picker
          v-model="filters.order_startime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="下单开始时间"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-date-picker
          v-model="filters.order_endtime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="下单结束时间"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="filters.supplier_name"
          clearable
          filterable
          placeholder="全部所属公司"
          style="width: 160px"
        >
          <el-option
            v-for="item in supplierOptions"
            :key="String(item.id)"
            :label="String(item.companyName || item.company_name || item.id)"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="filters.sale_Manager"
          clearable
          filterable
          placeholder="全部销售主管"
          style="width: 150px"
        >
          <el-option
            v-for="item in saleManagerOptions"
            :key="String(item.id)"
            :label="displayUser(item)"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="filters.sale_user"
          clearable
          filterable
          placeholder="全部销售人员"
          style="width: 150px"
        >
          <el-option
            v-for="item in saleUserOptions"
            :key="String(item.id)"
            :label="displayUser(item)"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="50" label="#" />
      <el-table-column prop="orderId" label="订单编号" min-width="160" show-overflow-tooltip />
      <el-table-column label="客户企业名称" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.customerCompanyName || '-' }}</template>
      </el-table-column>
      <el-table-column label="所属公司名称" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.supplierCompanyName || '-' }}</template>
      </el-table-column>
      <el-table-column label="销售主管" width="100" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.saleManagerName || row.saleManagerUserName || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="销售人员" width="100" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.saleUserName || row.saleUserUserName || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="订单总价" width="100">
        <template #default="{ row }">{{ formatMoney(row.totalPrice) }}</template>
      </el-table-column>
      <el-table-column v-if="showMaoli" label="毛利金额" width="100">
        <template #default="{ row }">{{ formatMoney(row.maoli) }}</template>
      </el-table-column>
      <el-table-column label="是否开票" width="80">
        <template #default="{ row }">{{ Number(row.invoiceType) === 1 ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="下单时间" width="110">
        <template #default="{ row }">{{ formatDate(row.orderTime) }}</template>
      </el-table-column>
      <el-table-column v-if="showAddTime" label="录入订单时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.addTime) }}</template>
      </el-table-column>
      <el-table-column label="订单状态" width="90">
        <template #default="{ row }">
          {{ Number(row.isEvaluate) === 1 ? '已评价' : statusLabel(row.orderStatus) }}
        </template>
      </el-table-column>
      <el-table-column prop="star" label="评价分数" width="90" />
      <el-table-column prop="content" label="评价内容" min-width="140" show-overflow-tooltip />
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
        layout="total, prev, pager, next"
        :total="total"
        @current-change="() => load({ ...filters })"
      />
    </div>

    <el-dialog v-model="detailVisible" title="评价订单详情" width="640px">
      <el-descriptions v-if="detail" :column="1" border>
        <el-descriptions-item label="订单编号">{{ detail.orderId || '-' }}</el-descriptions-item>
        <el-descriptions-item label="客户企业">
          {{ detail.customerCompanyName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="所属公司">
          {{ detail.supplierCompanyName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="销售主管">
          {{ detail.saleManagerName || detail.saleManagerUserName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="销售人员">
          {{ detail.saleUserName || detail.saleUserUserName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="订单总价">{{ formatMoney(detail.totalPrice) }}</el-descriptions-item>
        <el-descriptions-item label="是否开票">
          {{ Number(detail.invoiceType) === 1 ? '是' : '否' }}
        </el-descriptions-item>
        <el-descriptions-item label="下单时间">{{ formatDate(detail.orderTime) }}</el-descriptions-item>
        <el-descriptions-item label="录入时间">{{ formatDateTime(detail.addTime) }}</el-descriptions-item>
        <el-descriptions-item label="评价分数">{{ detail.star || '-' }}</el-descriptions-item>
        <el-descriptions-item label="评价内容">{{ detail.content || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { useDataTable } from '@/composables/useDataTable'
import { fetchSupplierAll, fetchUserList } from '@/api/system'
import { isAjaxOk } from '@/utils/request'

const props = withDefaults(
  defineProps<{
    title: string
    fetcher: (params: Record<string, unknown>) => Promise<unknown>
    /** 分包页展示毛利、录入时间（对齐 Java 分包评价列表） */
    showMaoli?: boolean
    showAddTime?: boolean
  }>(),
  {
    showMaoli: false,
    showAddTime: false,
  }
)

const filters = reactive({
  customer_name: '',
  order_id: '',
  goods_name: '',
  order_startime: '',
  order_endtime: '',
  supplier_name: '',
  sale_Manager: '',
  sale_user: '',
})

const supplierOptions = ref<Record<string, unknown>[]>([])
const saleManagerOptions = ref<Record<string, unknown>[]>([])
const saleUserOptions = ref<Record<string, unknown>[]>([])
const detailVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)

const { loading, rows, total, pagination, load } = useDataTable(
  props.fetcher as (params: Record<string, unknown>) => Promise<{
    data?: Record<string, unknown>[]
    recordsTotal?: number
  }>
)

const ORDER_STATUS: Record<string, string> = {
  '0': '已取消',
  '5': '待提交审核',
  '10': '已驳回',
  '20': '待审核',
  '30': '已审核',
  '40': '已确认',
  '50': '已完成',
  '55': '已评价',
}

function displayUser(item: Record<string, unknown>) {
  return String(item.trueName || item.true_name || item.userName || item.user_name || item.id)
}

function statusLabel(status: unknown) {
  return ORDER_STATUS[String(status)] || String(status ?? '-')
}

function formatMoney(val: unknown) {
  if (val === null || val === undefined || val === '') return '-'
  const n = Number(val)
  return Number.isFinite(n) ? n.toFixed(2) : '-'
}

function formatDate(val: unknown) {
  if (!val) return '-'
  const s = String(val)
  return s.length >= 10 ? s.slice(0, 10) : s
}

function formatDateTime(val: unknown) {
  return val ? String(val) : '-'
}

function reload() {
  pagination.page = 1
  return load({ ...filters })
}

function openDetail(row: Record<string, unknown>) {
  detail.value = row
  detailVisible.value = true
}

async function loadOptions() {
  try {
    const [supplierRes, managerRes, saleRes] = await Promise.all([
      fetchSupplierAll().catch(() => null),
      fetchUserList({ start: 0, length: 500, draw: 1 }).catch(() => ({ data: [] })),
      fetchUserList({ start: 0, length: 500, draw: 1 }).catch(() => ({ data: [] })),
    ])
    if (supplierRes && isAjaxOk(supplierRes)) {
      const obj = supplierRes.obj
      supplierOptions.value = Array.isArray(obj) ? obj : []
    }
    saleManagerOptions.value = Array.isArray(managerRes?.data) ? managerRes.data : []
    saleUserOptions.value = Array.isArray(saleRes?.data) ? saleRes.data : []
  } catch {
    // 下拉失败不阻塞列表
  }
}

onMounted(async () => {
  await loadOptions()
  await reload()
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
