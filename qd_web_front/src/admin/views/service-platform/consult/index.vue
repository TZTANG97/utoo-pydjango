<template>
  <admin-page-card title="咨询管理">
    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="姓名">
        <el-input v-model="userName" placeholder="姓名" clearable />
      </el-form-item>
      <el-form-item label="手机号">
        <el-input v-model="mobile" placeholder="手机号" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" label="#" />
      <el-table-column prop="order_num" label="订单号" min-width="120" show-overflow-tooltip />
      <el-table-column prop="addTime" label="咨询时间" min-width="160" />
      <el-table-column prop="className" label="测试分类" min-width="120" show-overflow-tooltip />
      <el-table-column prop="userName" label="姓名" min-width="100" />
      <el-table-column prop="mobile" label="手机号" min-width="120" />
      <el-table-column prop="company_name" label="公司名" min-width="140" show-overflow-tooltip />
      <el-table-column prop="content" label="咨询详情" min-width="180" show-overflow-tooltip />
      <el-table-column prop="syUserName" label="客服人员" min-width="100" />
      <el-table-column label="状态" min-width="100">
        <template #default="{ row }">{{ row.statusLabel || statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goDetail(row, 'edit')">查看</el-button>
          <el-button link type="primary" @click="goDetail(row, 'view')">详情</el-button>
          <el-button
            v-if="Number(row.status) !== 3"
            link
            type="danger"
            @click="handleCancel(row)"
          >
            取消
          </el-button>
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { cancelConsult, fetchConsultList } from '@admin/api/service-platform'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const router = useRouter()
const userName = ref('')
const mobile = ref('')
const { loading, rows, total, pagination, load } = useDataTable(fetchConsultList)

const STATUS_MAP: Record<number, string> = {
  0: '待处理',
  1: '已处理',
  2: '已生成订单',
  3: '已取消',
}

onMounted(() => reload())

function statusLabel(val: unknown) {
  const n = Number(val)
  if (Number.isNaN(n) || n < 0) return '未回复'
  return STATUS_MAP[n] ?? '未回复'
}

function reload() {
  return load({
    userName: userName.value.trim(),
    mobile: mobile.value.trim(),
  })
}

function goDetail(row: Record<string, unknown>, mode: 'edit' | 'view') {
  router.push({
    name: 'ServiceConsultDetail',
    params: { id: String(row.id) },
    query: { mode },
  })
}

async function handleCancel(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认取消该咨询？', '提示', { type: 'warning' })
  const res = await cancelConsult(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '取消失败'))
    return
  }
  ElMessage.success(res.resMsg || '取消成功')
  await reload()
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
