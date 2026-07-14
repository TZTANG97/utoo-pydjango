<template>
  <admin-page-card title="会员申请管理">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="公司名称">
        <el-input v-model="filters.company_name" clearable />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.state" clearable style="width: 140px">
          <el-option label="已转会员" :value="1" />
          <el-option label="已拒绝" :value="2" />
          <el-option label="待处理" :value="3" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload()">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="addTime" label="申请时间" min-width="160" />
      <el-table-column prop="applyUser" label="申请人" width="120" />
      <el-table-column prop="phone" label="电话" min-width="120" />
      <el-table-column prop="companyName" label="公司名称" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="stateType(row.state)">{{ stateLabel(row.state) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="lastOperatorName" label="处理人" width="120" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <template v-if="Number(row.state) === 3">
            <el-button link type="success" @click="openApprove(row)">转会员</el-button>
            <el-button link type="danger" @click="handleReject(row)">拒绝</el-button>
          </template>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="reload()"
      />
    </div>

    <el-dialog v-model="approveVisible" title="确认转会员" width="520px">
      <el-form label-width="100px">
        <el-form-item label="公司名称" required>
          <el-input v-model="approveForm.name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="approveForm.contractPeople" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="approveForm.contractPhone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleApprove">确认</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchApplyVipList, saveEnterprise, updateApplyVip } from '@/api/member'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const filters = reactive({ company_name: '', state: undefined as number | undefined })
const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchApplyVipList({ ...params, ...filters })
)
const approveVisible = ref(false)
const saving = ref(false)
const approveForm = reactive({
  applyuserId: '',
  name: '',
  contractPeople: '',
  contractPhone: '',
  type: 3,
})

function stateLabel(state: unknown) {
  if (Number(state) === 1) return '已转会员'
  if (Number(state) === 2) return '已拒绝'
  return '待处理'
}

function stateType(state: unknown) {
  if (Number(state) === 1) return 'success'
  if (Number(state) === 2) return 'danger'
  return 'warning'
}

function reload() {
  return load()
}

onMounted(() => reload())

function openApprove(row: Record<string, unknown>) {
  approveForm.applyuserId = String(row.id)
  approveForm.name = String(row.companyName || '')
  approveForm.contractPeople = String(row.applyUser || '')
  approveForm.contractPhone = String(row.phone || '')
  approveVisible.value = true
}

async function handleApprove() {
  if (!approveForm.name.trim()) {
    ElMessage.warning('请填写公司名称')
    return
  }
  saving.value = true
  try {
    const res = await saveEnterprise({ ...approveForm })
    if (isAjaxOk(res)) {
      ElMessage.success('已转为企业会员')
      approveVisible.value = false
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  } finally {
    saving.value = false
  }
}

async function handleReject(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定拒绝该申请吗？', '提示', { type: 'warning' })
  const res = await updateApplyVip({ id: row.id, type: 2 })
  if (isAjaxOk(res)) {
    ElMessage.success('已拒绝')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}
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
