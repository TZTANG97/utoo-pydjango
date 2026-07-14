<template>
  <admin-page-card title="沟通记录管理">
    <el-form :inline="true" class="filter-form" @submit.prevent="reload">
      <el-form-item>
        <el-select
          v-model="filters.trueName"
          clearable
          filterable
          placeholder="全部用户"
          style="width: 160px"
        >
          <el-option
            v-for="item in userOptions"
            :key="String(item.id)"
            :label="displayUser(item)"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="关键字">
        <el-input
          v-model="filters.keywords"
          clearable
          placeholder="关键字"
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item label="问题提出时间">
        <el-date-picker
          v-model="filters.order_startime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="开始时间"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item label="至">
        <el-date-picker
          v-model="filters.order_endtime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="结束时间"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column label="用户名" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.trueName || row.userName || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="problemContent"
        label="常见问题"
        min-width="200"
        show-overflow-tooltip
      />
      <el-table-column
        prop="replyContent"
        label="回复内容"
        min-width="200"
        show-overflow-tooltip
      />
      <el-table-column label="问题提出时间" width="140">
        <template #default="{ row }">{{ formatDate(row.addTime) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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

    <el-dialog v-model="detailVisible" title="沟通记录详情" width="640px">
      <el-descriptions v-if="detail" :column="1" border>
        <el-descriptions-item label="用户名">
          {{ detail.trueName || detail.userName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detail.mobile || '-' }}</el-descriptions-item>
        <el-descriptions-item label="常见问题">
          {{ detail.problemContent || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="回复内容">
          {{ detail.replyContent || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="问题提出时间">
          {{ formatDateTime(detail.addTime) }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchMemberList } from '@/api/member'
import {
  deleteRecords,
  fetchRecordsList,
  getRecordsDetail,
} from '@/api/service-platform'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const filters = reactive({
  trueName: '',
  keywords: '',
  order_startime: '',
  order_endtime: '',
})

const userOptions = ref<Record<string, unknown>[]>([])
const detailVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const { loading, rows, total, pagination, load } = useDataTable(fetchRecordsList)

function displayUser(item: Record<string, unknown>) {
  return String(item.trueName || item.true_name || item.userName || item.user_name || item.mobile || item.id)
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

async function loadUserOptions() {
  try {
    const res = await fetchMemberList({ start: 0, length: 2000, draw: 1 })
    userOptions.value = Array.isArray(res.data) ? res.data : []
  } catch {
    userOptions.value = []
  }
}

async function openDetail(row: Record<string, unknown>) {
  const res = await getRecordsDetail(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
    return
  }
  detail.value = res.obj as Record<string, unknown>
  detailVisible.value = true
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('请确认是否删除？', '提示', { type: 'warning' })
  const res = await deleteRecords(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await load({ ...filters })
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

onMounted(async () => {
  await loadUserOptions()
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
