<template>
  <admin-page-card title="咨询管理">
    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="用户名">
        <el-input v-model="userName" placeholder="用户名" clearable />
      </el-form-item>
      <el-form-item label="手机号">
        <el-input v-model="mobile" placeholder="手机号" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="userName" label="用户名" min-width="120" />
      <el-table-column prop="mobile" label="手机号" min-width="120" />
      <el-table-column prop="title" label="咨询标题" min-width="160" show-overflow-tooltip />
      <el-table-column prop="addTime" label="提交时间" min-width="160" />
      <el-table-column label="状态" min-width="100">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button
            v-if="String(row.status) !== '3'"
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

    <el-dialog v-model="detailVisible" title="咨询详情" width="640px">
      <el-descriptions v-if="detail" :column="1" border>
        <el-descriptions-item label="用户名">{{ detail.userName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detail.mobile || '-' }}</el-descriptions-item>
        <el-descriptions-item label="标题">{{ detail.title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="内容">{{ detail.content || detail.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ detail.addTime || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(detail.status) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { cancelConsult, fetchConsultList, getConsultDetail } from '@admin/api/service-platform'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const userName = ref('')
const mobile = ref('')
const detailVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const { loading, rows, total, pagination, load } = useDataTable(fetchConsultList)

const STATUS_MAP: Record<string, string> = {
  '1': '待处理',
  '2': '已处理',
  '3': '已取消',
}

onMounted(() => reload())

function statusLabel(val: unknown) {
  return STATUS_MAP[String(val)] || String(val ?? '-')
}

function reload() {
  return load({
    userName: userName.value.trim(),
    mobile: mobile.value.trim(),
  })
}

async function openDetail(row: Record<string, unknown>) {
  const res = await getConsultDetail(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
    return
  }
  detail.value = res.obj as Record<string, unknown>
  detailVisible.value = true
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
