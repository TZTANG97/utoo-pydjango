<template>
  <admin-page-card title="建议反馈管理">
    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="用户名">
        <el-input v-model="userName" placeholder="用户名" clearable />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="status" clearable placeholder="全部" style="width: 140px">
          <el-option label="待确认" value="0" />
          <el-option label="已确认" value="1" />
          <el-option label="已解决" value="2" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="userName" label="用户名" min-width="120" />
      <el-table-column prop="mobile" label="手机号" min-width="120" />
      <el-table-column prop="title" label="建议标题" min-width="160" show-overflow-tooltip />
      <el-table-column prop="addTime" label="提交时间" min-width="160" />
      <el-table-column label="状态" min-width="100">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button
            v-if="String(row.status) === '0'"
            link
            type="success"
            @click="handleAction(row, 1)"
          >
            确认
          </el-button>
          <el-button
            v-if="String(row.status) === '1'"
            link
            type="warning"
            @click="handleAction(row, 2)"
          >
            解决
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

    <el-dialog v-model="detailVisible" title="建议详情" width="720px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">{{ detail.userName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ detail.mobile || '-' }}</el-descriptions-item>
          <el-descriptions-item label="标题" :span="2">{{ detail.title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="内容" :span="2">{{ detail.content || detail.remark || '-' }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ detail.addTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusLabel(detail.status) }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="logList.length" class="log-section">
          <div class="log-title">处理日志</div>
          <el-timeline>
            <el-timeline-item
              v-for="(log, idx) in logList"
              :key="idx"
              :timestamp="String(log.addTime || '')"
            >
              {{ log.content || log.remark || '-' }}
            </el-timeline-item>
          </el-timeline>
        </div>
      </template>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchProposalList, getProposalDetail, updateProposalImprove } from '@/api/service-platform'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const userName = ref('')
const status = ref('')
const detailVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const { loading, rows, total, pagination, load } = useDataTable(fetchProposalList)

const STATUS_MAP: Record<string, string> = {
  '0': '待确认',
  '1': '已确认',
  '2': '已解决',
}

const logList = computed(() => {
  if (!detail.value) return []
  const logs = detail.value.logList || detail.value.logs
  return Array.isArray(logs) ? (logs as Record<string, unknown>[]) : []
})

onMounted(() => reload())

function statusLabel(val: unknown) {
  return STATUS_MAP[String(val)] || String(val ?? '-')
}

function reload() {
  return load({
    userName: userName.value.trim(),
    status: status.value,
  })
}

async function openDetail(row: Record<string, unknown>) {
  const res = await getProposalDetail(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
    return
  }
  detail.value = res.obj as Record<string, unknown>
  detailVisible.value = true
}

async function handleAction(row: Record<string, unknown>, type: number) {
  const label = type === 1 ? '确认' : '解决'
  await ElMessageBox.confirm(`确认执行「${label}」操作？`, '提示', { type: 'warning' })
  const res = await updateProposalImprove({ id: row.id, type })
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success(res.resMsg || '操作成功')
  detailVisible.value = false
  await reload()
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.log-section {
  margin-top: 20px;
}
.log-title {
  margin-bottom: 12px;
  font-weight: 600;
}
</style>
