<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  agreeRetest,
  fetchRetestDetail,
  fetchRetestList,
  refuseRetest,
} from '@/api/billing'
import { RETEST_STATUS, formatDate } from '@/utils/billing-labels'
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
    const result = await fetchRetestList({
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
  const res = await fetchRetestDetail(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
    return
  }
  detail.value = (res.obj || null) as Record<string, unknown> | null
  detailVisible.value = true
}

async function handleAgree(row: Record<string, unknown>) {
  const { value } = await ElMessageBox.prompt('请输入客服备注（可选）', '同意复测', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPlaceholder: '客服备注',
  })
  const res = await agreeRetest(String(row.id), value || '')
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success(res.resMsg || '同意复测成功')
  loadData()
}

async function handleRefuse(row: Record<string, unknown>) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因', '拒绝复测', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
  })
  const res = await refuseRetest(String(row.id), value || '')
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success(res.resMsg || '拒绝复测成功')
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
        <el-form-item label="审核状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
            <el-option label="待审核" value="0" />
            <el-option label="已同意" value="1" />
            <el-option label="已拒绝" value="2" />
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
        <el-table-column prop="fc_no" label="申请编号" min-width="140" />
        <el-table-column label="申请时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.addTime) }}</template>
        </el-table-column>
        <el-table-column label="用户名" min-width="120">
          <template #default="{ row }">{{ row.trueName || row.userName || '-' }}</template>
        </el-table-column>
        <el-table-column prop="mobile" label="电话" min-width="120" />
        <el-table-column label="审核状态" min-width="100">
          <template #default="{ row }">{{ RETEST_STATUS[Number(row.applyStatus)] || row.applyStatus }}</template>
        </el-table-column>
        <el-table-column prop="mark" label="用户备注" min-width="140" show-overflow-tooltip />
        <el-table-column prop="remeasurement_require" label="客服备注" min-width="140" show-overflow-tooltip />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">查看</el-button>
            <template v-if="Number(row.applyStatus) === 0">
              <el-button link type="success" @click="handleAgree(row)">同意复测</el-button>
              <el-button link type="danger" @click="handleRefuse(row)">拒绝复测</el-button>
            </template>
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

    <el-dialog v-model="detailVisible" title="复测申请详情" width="720px">
      <el-descriptions v-if="detail" :column="2" border>
        <el-descriptions-item label="申请编号">{{ detail.fc_no || detail.order_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="申请时间">{{ formatDate(detail.addTime) }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ detail.trueName || detail.userName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ detail.mobile || '-' }}</el-descriptions-item>
        <el-descriptions-item label="子订单ID">{{ detail.orderId || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核状态">{{ RETEST_STATUS[Number(detail.applyStatus)] || detail.applyStatus }}</el-descriptions-item>
        <el-descriptions-item label="用户备注" :span="2">{{ detail.mark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="客服备注" :span="2">{{ detail.remeasurement_require || '-' }}</el-descriptions-item>
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
