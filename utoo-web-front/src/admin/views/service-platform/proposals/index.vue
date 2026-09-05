<template>
  <admin-page-card title="建议反馈管理">
    <el-form :inline="true" class="filter-form" @submit.prevent="handleSearch">
      <el-form-item>
        <el-date-picker
          v-model="filters.order_startime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="开始时间"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-date-picker
          v-model="filters.order_endtime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="结束时间"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-select v-model="filters.platform" clearable placeholder="全部平台" style="width: 140px">
          <el-option label="愉兔" value="2" />
          <el-option label="途哲" value="4" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select
          v-model="filters.is_confirmed"
          clearable
          placeholder="全部状态"
          style="width: 140px"
        >
          <el-option label="未确认" value="0" />
          <el-option label="已确认" value="1" />
          <el-option label="已解决" value="2" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe class="data-table">
      <el-table-column type="index" width="56" label="#" align="center" />
      <el-table-column label="时间" min-width="160">
        <template #default="{ row }">{{ formatDateTime(row.addTime) }}</template>
      </el-table-column>
      <el-table-column prop="trueName" label="用户" min-width="110" show-overflow-tooltip>
        <template #default="{ row }">{{ row.trueName || '-' }}</template>
      </el-table-column>
      <el-table-column prop="userName" label="账号" min-width="110" show-overflow-tooltip>
        <template #default="{ row }">{{ row.userName || '-' }}</template>
      </el-table-column>
      <el-table-column label="文字内容" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">{{ truncate(row.content, 40) }}</template>
      </el-table-column>
      <el-table-column label="是否有查看确认" min-width="130" align="center">
        <template #default="{ row }">
          <el-tag :type="confirmedTagType(row.isConfirmed)" size="small" effect="light">
            {{ confirmedLabel(row.isConfirmed) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="平台" width="100" align="center">
        <template #default="{ row }">{{ platformLabel(row.platform) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button
            v-if="String(row.isConfirmed) === '0'"
            link
            type="success"
            @click="handleAction(row, 1)"
          >
            确认
          </el-button>
          <el-button
            v-if="String(row.isConfirmed) === '1'"
            link
            type="warning"
            @click="handleAction(row, 2)"
          >
            完成
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, sizes, prev, pager, next"
        :page-sizes="[10, 20, 50]"
        :total="total"
        @current-change="reload"
        @size-change="handleSearch"
      />
    </div>

    <el-dialog
      v-model="detailVisible"
      title="提案改善详情"
      width="720px"
      destroy-on-close
      class="detail-dialog"
    >
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="提交时间">
            {{ formatDateTime(detail.addTime) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(detail.updateTime) }}
          </el-descriptions-item>
          <el-descriptions-item label="用户">{{ detail.trueName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="账号">{{ detail.userName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="平台">{{ platformLabel(detail.platform) }}</el-descriptions-item>
          <el-descriptions-item label="是否确认">
            <el-tag :type="confirmedTagType(detail.isConfirmed)" size="small" effect="light">
              {{ confirmedLabel(detail.isConfirmed) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="类型">{{ typeLabel(detail.type) }}</el-descriptions-item>
          <el-descriptions-item label="文字内容" :span="2">
            <div class="content-text">{{ detail.content || '-' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="相关文件" :span="2">
            <div v-if="fileList.length" class="file-list">
              <a
                v-for="file in fileList"
                :key="String(file.id)"
                class="file-link"
                :href="fileUrl(file)"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ file.info || file.name || '附件' }}
              </a>
            </div>
            <span v-else class="muted">无相关文件</span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="log-section">
          <div class="log-title">操作日志</div>
          <el-timeline v-if="logList.length">
            <el-timeline-item
              v-for="(log, idx) in logList"
              :key="idx"
              :timestamp="formatDateTime(log.addTime)"
              placement="top"
            >
              <div class="log-item">
                <span class="log-user">{{ log.userName || '-' }}</span>
                <span class="log-info">{{ log.info || log.content || '-' }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
          <div v-else class="muted">无操作日志</div>
        </div>
      </template>
      <template #footer>
        <el-button
          v-if="detail && String(detail.isConfirmed) === '0'"
          type="success"
          @click="handleAction(detail, 1)"
        >
          确认
        </el-button>
        <el-button
          v-if="detail && String(detail.isConfirmed) === '1'"
          type="warning"
          @click="handleAction(detail, 2)"
        >
          完成
        </el-button>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { fetchProposalList, getProposalDetail, updateProposalImprove } from '@admin/api/service-platform'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const filters = reactive({
  order_startime: '',
  order_endtime: '',
  platform: '',
  is_confirmed: '',
})

const detailVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const logList = ref<Record<string, unknown>[]>([])
const fileList = ref<Record<string, unknown>[]>([])
const { loading, rows, total, pagination, load } = useDataTable(fetchProposalList)

const PLATFORM_MAP: Record<string, string> = {
  '2': '愉兔',
  '4': '途哲',
}

const CONFIRMED_MAP: Record<string, string> = {
  '0': '否',
  '1': '是',
  '2': '已解决',
}

onMounted(() => reload())

function confirmedLabel(val: unknown) {
  return CONFIRMED_MAP[String(val)] || String(val ?? '-')
}

function confirmedTagType(val: unknown): 'info' | 'success' | 'warning' {
  const key = String(val)
  if (key === '1') return 'success'
  if (key === '2') return 'warning'
  return 'info'
}

function platformLabel(val: unknown) {
  return PLATFORM_MAP[String(val)] || (val == null || val === '' ? '-' : String(val))
}

function typeLabel(val: unknown) {
  if (String(val) === 'proposal') return '提案'
  return String(val ?? '-')
}

function truncate(val: unknown, max = 40) {
  const text = String(val ?? '').trim()
  if (!text) return '-'
  return text.length > max ? `${text.slice(0, max)}...` : text
}

function formatDateTime(val: unknown) {
  if (val == null || val === '') return '-'
  const text = String(val)
  if (/^\d+$/.test(text)) {
    const num = Number(text)
    const ms = text.length <= 10 ? num * 1000 : num
    const d = new Date(ms)
    if (!Number.isNaN(d.getTime())) {
      const pad = (n: number) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
    }
  }
  return text.replace('T', ' ').slice(0, 19)
}

function fileUrl(file: Record<string, unknown>) {
  const path = String(file.path || '').replace(/\/$/, '')
  const name = String(file.name || '')
  if (!path && !name) return '#'
  if (path.startsWith('http')) return name ? `${path}/${name}` : path
  return `${path}/${name}`.replace(/\/{2,}/g, '/').replace(':/', '://')
}

function queryParams() {
  return {
    order_startime: filters.order_startime || '',
    order_endtime: filters.order_endtime || '',
    platform: filters.platform || '',
    is_confirmed: filters.is_confirmed || '',
  }
}

function reload() {
  return load(queryParams())
}

function handleSearch() {
  pagination.page = 1
  return reload()
}

async function openDetail(row: Record<string, unknown>) {
  const res = await getProposalDetail(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
    return
  }
  const payload = res.obj as Record<string, unknown>
  const obj = (payload.obj as Record<string, unknown>) || payload
  detail.value = obj
  logList.value = Array.isArray(payload.logs) ? (payload.logs as Record<string, unknown>[]) : []
  fileList.value = Array.isArray(payload.files) ? (payload.files as Record<string, unknown>[]) : []
  detailVisible.value = true
}

async function handleAction(row: Record<string, unknown>, type: number) {
  const label = type === 1 ? '确认' : '完成'
  await ElMessageBox.confirm(`是否${label}该提案？`, '提示', { type: 'warning' })
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
.filter-form {
  margin-bottom: 4px;
}

.data-table {
  margin-top: 4px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.content-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-link {
  color: var(--el-color-primary);
  text-decoration: none;
}

.file-link:hover {
  text-decoration: underline;
}

.log-section {
  margin-top: 24px;
}

.log-title {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.log-item {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  line-height: 1.5;
}

.log-user {
  color: var(--el-text-color-regular);
  font-weight: 500;
}

.log-info {
  color: var(--el-text-color-primary);
}

.muted {
  color: var(--el-text-color-secondary);
}
</style>
