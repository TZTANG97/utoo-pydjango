<template>
  <admin-page-card title="设备回购管理">
    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="状态">
        <el-select v-model="state" clearable placeholder="全部" style="width: 140px">
          <el-option label="待处理" value="2" />
          <el-option label="已处理" value="1" />
          <el-option label="已驳回" value="3" />
        </el-select>
      </el-form-item>
      <el-form-item label="设备名称">
        <el-input v-model="deviceName" placeholder="设备名称" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="device_name" label="设备名称" min-width="140" />
      <el-table-column prop="userName" label="用户名" min-width="120" />
      <el-table-column prop="mobile" label="手机号" min-width="120" />
      <el-table-column prop="addTime" label="申请时间" min-width="160" />
      <el-table-column label="状态" min-width="100">
        <template #default="{ row }">{{ stateLabel(row.state) }}</template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <template v-if="String(row.state) === '0'">
            <el-button link type="success" @click="handleUpdate(row, 1)">已处理</el-button>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchBuybackApplyList, updateBuybackApply } from '@/api/service-platform'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const state = ref('')
const deviceName = ref('')
const { loading, rows, total, pagination, load } = useDataTable(fetchBuybackApplyList)

const STATE_MAP: Record<string, string> = {
  '2': '待处理',
  '1': '已处理',
  '3': '已驳回',
}

onMounted(() => reload())

function stateLabel(val: unknown) {
  return STATE_MAP[String(val)] || String(val ?? '-')
}

function reload() {
  return load({
    state: state.value,
    device_name: deviceName.value.trim(),
  })
}

async function handleUpdate(row: Record<string, unknown>, newState: number) {
  const label = newState === 1 ? '已处理' : '已驳回'
  await ElMessageBox.confirm(`确认标记为「${label}」？`, '提示', { type: 'warning' })
  const res = await updateBuybackApply({ id: row.id, type: newState })
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
