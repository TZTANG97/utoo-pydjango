<template>
  <admin-page-card title="服务申请">
    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="服务类型">
        <el-select v-model="caliType" clearable placeholder="全部" style="width: 140px">
          <el-option label="校准" value="3" />
          <el-option label="维修" value="4" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="caliStatus" clearable placeholder="全部" style="width: 140px">
          <el-option label="待处理" value="1" />
          <el-option label="已处理" value="2" />
          <el-option label="已驳回" value="3" />
        </el-select>
      </el-form-item>
      <el-form-item label="订单编号">
        <el-input v-model="orderId" placeholder="订单编号" clearable />
      </el-form-item>
      <el-form-item label="客户名称">
        <el-input v-model="customerName" placeholder="客户名称" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="caliNo" label="申请编号" min-width="120" />
      <el-table-column label="服务类型" min-width="90">
        <template #default="{ row }">{{ row.caliTypeLabel || typeLabel(row.caliType) }}</template>
      </el-table-column>
      <el-table-column prop="orderId" label="订单编号" min-width="150" show-overflow-tooltip />
      <el-table-column prop="customerName" label="客户名称" min-width="140" show-overflow-tooltip />
      <el-table-column prop="goodsName" label="商品名称" min-width="140" show-overflow-tooltip />
      <el-table-column prop="goodsSpec" label="规格" min-width="120" show-overflow-tooltip />
      <el-table-column prop="dept" label="部门" min-width="100" />
      <el-table-column prop="caliAddTime" label="申请时间" min-width="160" />
      <el-table-column label="状态" min-width="100">
        <template #default="{ row }">{{ row.caliStatusLabel || statusLabel(row.caliStatus) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <template v-if="String(row.caliStatus) === '1'">
            <el-button link type="success" @click="handleUpdate(row, 2)">已处理</el-button>
            <el-button link type="danger" @click="handleUpdate(row, 3)">已驳回</el-button>
          </template>
          <span v-else class="muted">-</span>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="reload"
      />
    </div>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { fetchServiceApplyList, updateServiceApply } from '@admin/api/service-platform'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const route = useRoute()
const caliType = ref('')
const caliStatus = ref('')
const orderId = ref('')
const customerName = ref('')
const { loading, rows, total, pagination, load } = useDataTable(fetchServiceApplyList)

const TYPE_MAP: Record<string, string> = { '3': '校准', '4': '维修' }
const STATUS_MAP: Record<string, string> = { '1': '待处理', '2': '已处理', '3': '已驳回' }

onMounted(() => {
  const query = route.query
  if (query.caliType) caliType.value = String(query.caliType)
  if (query.caliStatus) caliStatus.value = String(query.caliStatus)
  reload()
})

function typeLabel(val: unknown) {
  return TYPE_MAP[String(val)] || String(val ?? '-')
}

function statusLabel(val: unknown) {
  return STATUS_MAP[String(val)] || String(val ?? '-')
}

function reload() {
  return load({
    caliType: caliType.value,
    caliStatus: caliStatus.value,
    order_id: orderId.value.trim(),
    customer_name: customerName.value.trim(),
  })
}

async function handleUpdate(row: Record<string, unknown>, newStatus: number) {
  const label = newStatus === 2 ? '已处理' : '已驳回'
  await ElMessageBox.confirm(`确认标记为「${label}」？`, '提示', { type: 'warning' })
  const res = await updateServiceApply({ id: row.id, type: newStatus })
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success(res.resMsg || '操作成功')
  await reload()
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.muted {
  color: #909399;
}
</style>
