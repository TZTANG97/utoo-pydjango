<template>
  <admin-page-card title="设备预约">
    <el-form :inline="true" class="filter-form" @submit.prevent="reload">
      <el-form-item label="实验室编号">
        <el-select
          v-model="filters.labNum"
          clearable
          filterable
          placeholder="全部"
          style="width: 150px"
          @keyup.enter="reload"
        >
          <el-option
            v-for="lab in labs"
            :key="'n-' + String(lab.id)"
            :label="String(lab.labNum || '')"
            :value="String(lab.labNum || '')"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="实验室名称">
        <el-select
          v-model="filters.labName"
          clearable
          filterable
          placeholder="全部"
          style="width: 160px"
          @keyup.enter="reload"
        >
          <el-option
            v-for="lab in labs"
            :key="'m-' + String(lab.id)"
            :label="String(lab.labName || '')"
            :value="String(lab.labName || '')"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="实验线类型">
        <el-select
          v-model="filters.classId"
          clearable
          filterable
          placeholder="全部"
          style="width: 160px"
          @keyup.enter="reload"
        >
          <el-option
            v-for="c in classes"
            :key="String(c.id)"
            :label="String(c.className || '')"
            :value="String(c.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="实验线编号">
        <el-select
          v-model="filters.lineNum"
          clearable
          filterable
          placeholder="全部"
          style="width: 150px"
          @keyup.enter="reload"
        >
          <el-option
            v-for="line in lines"
            :key="String(line.id)"
            :label="String(line.lineNum || '')"
            :value="String(line.lineNum || '')"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="实验线状态">
        <el-select
          v-model="filters.status"
          clearable
          placeholder="全部"
          style="width: 120px"
          @keyup.enter="reload"
        >
          <el-option label="启用" value="1" />
          <el-option label="禁用" value="2" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <div v-loading="loading" class="equip-list">
      <div v-if="!rows.length && !loading" class="empty">暂无数据</div>
      <div v-for="row in rows" :key="String(row.id)" class="equip-card">
        <span class="dian" :class="dotClass(row.dot)" />
        <div class="thumb">
          <img v-if="row.photoUrl" :src="String(row.photoUrl)" alt="" />
          <div v-else class="thumb-placeholder">无图</div>
        </div>
        <div class="meta">
          <div class="title">{{ row.lineNum || row.line_num }}</div>
          <div class="sub">
            <span>{{ row.className || '-' }}</span>
            <span>{{ row.labName || '-' }} / {{ row.labNum || '-' }}</span>
            <el-tag size="small" :type="dotTagType(row.dot)">{{ row.dotLabel || statusText(row.dot) }}</el-tag>
          </div>
        </div>
        <div class="actions">
          <el-button type="primary" link @click="openDetail(row)">查看详情</el-button>
        </div>
      </div>
    </div>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50]"
        layout="sizes, total, prev, pager, next"
        :total="total"
        @size-change="reload"
        @current-change="() => load(listParams())"
      />
    </div>

    <el-drawer v-model="drawerVisible" title="设备预约详情" size="720px">
      <template v-if="lineDetail">
        <div class="detail-head">
          <div class="detail-thumb">
            <span class="dian" :class="dotClass(lineDetail.dot)" />
            <img v-if="lineDetail.photoUrl" :src="String(lineDetail.photoUrl)" alt="" />
            <div v-else class="thumb-placeholder">无图</div>
          </div>
          <el-descriptions :column="1" border size="small" class="detail-desc">
            <el-descriptions-item label="实验线编号">{{ lineDetail.lineNum }}</el-descriptions-item>
            <el-descriptions-item label="实验室名称">{{ lineDetail.labName || '-' }}</el-descriptions-item>
            <el-descriptions-item label="实验室编号">{{ lineDetail.labNum || '-' }}</el-descriptions-item>
            <el-descriptions-item label="实验线类型">{{ lineDetail.className || '-' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ lineDetail.addTimeStr || formatTime(lineDetail.addTime) }}</el-descriptions-item>
            <el-descriptions-item label="测试状态">
              <el-tag size="small" :type="dotTagType(lineDetail.dot)">
                {{ lineDetail.dotLabel || statusText(lineDetail.dot) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <h4 class="section-title">实验详情</h4>
        <el-table v-loading="logLoading" :data="logs" border size="small">
          <el-table-column type="index" width="55" label="序号" align="center" />
          <el-table-column prop="orderId" label="实验订单号" min-width="160" show-overflow-tooltip />
          <el-table-column prop="startTime" label="实验开始时间" min-width="160" />
          <el-table-column prop="endTime" label="试验结束时间" min-width="160" />
          <el-table-column prop="userName" label="测试人员" min-width="100" />
        </el-table>
        <div class="pager">
          <el-pagination
            v-model:current-page="logPage"
            v-model:page-size="logPageSize"
            layout="total, prev, pager, next"
            :total="logTotal"
            @current-change="loadLogs"
          />
        </div>
      </template>
    </el-drawer>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  fetchDeviceBookingList,
  fetchDeviceBookingOptions,
  getDeviceBookingDetail,
} from '@/api/inventory'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const filters = reactive({
  labNum: '',
  labName: '',
  lineNum: '',
  classId: '',
  status: '',
})

const labs = ref<Record<string, unknown>[]>([])
const classes = ref<Record<string, unknown>[]>([])
const lines = ref<Record<string, unknown>[]>([])

const drawerVisible = ref(false)
const logLoading = ref(false)
const lineDetail = ref<Record<string, unknown> | null>(null)
const logs = ref<Record<string, unknown>[]>([])
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = ref(10)
const currentLineId = ref('')

function listParams() {
  const p: Record<string, string> = {}
  if (filters.labNum) p.labNum = filters.labNum
  if (filters.labName) p.labName = filters.labName
  if (filters.lineNum) p.lineNum = filters.lineNum
  if (filters.classId) p.classId = filters.classId
  if (filters.status) p.status = filters.status
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchDeviceBookingList({ ...p, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

function formatTime(v: unknown) {
  if (!v) return '-'
  return String(v).replace('T', ' ').slice(0, 19)
}

function statusText(dot: unknown) {
  const n = Number(dot)
  if (n === 1) return '待机'
  if (n === 2) return '运行中'
  if (n === 3) return '禁用'
  return '离线'
}

function dotClass(dot: unknown) {
  const n = Number(dot)
  if (n === 1) return 'green'
  if (n === 2) return 'yellow'
  if (n === 3) return 'red'
  return 'gray'
}

function dotTagType(dot: unknown) {
  const n = Number(dot)
  if (n === 1) return 'success'
  if (n === 2) return 'warning'
  if (n === 3) return 'danger'
  return 'info'
}

async function loadOptions() {
  try {
    const res = await fetchDeviceBookingOptions()
    if (!isAjaxOk(res)) return
    const obj = (res.obj as Record<string, unknown>) || {}
    labs.value = (obj.labs as Record<string, unknown>[]) || []
    classes.value = (obj.classes as Record<string, unknown>[]) || []
    lines.value = (obj.lines as Record<string, unknown>[]) || []
  } catch {
    /* ignore */
  }
}

async function loadLogs() {
  if (!currentLineId.value) return
  logLoading.value = true
  try {
    const start = (logPage.value - 1) * logPageSize.value
    const res = await getDeviceBookingDetail(currentLineId.value, {
      start,
      length: logPageSize.value,
      draw: logPage.value,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
      return
    }
    const obj = (res.obj as Record<string, unknown>) || {}
    lineDetail.value = (obj.line as Record<string, unknown>) || lineDetail.value
    logs.value = (obj.logs as Record<string, unknown>[]) || []
    logTotal.value = Number(obj.logTotal || 0)
  } finally {
    logLoading.value = false
  }
}

async function openDetail(row: Record<string, unknown>) {
  currentLineId.value = String(row.id)
  logPage.value = 1
  drawerVisible.value = true
  lineDetail.value = row
  await loadLogs()
}

onMounted(() => {
  void loadOptions()
  void reload()
})
</script>

<style scoped>
.filter-form {
  margin-bottom: 12px;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.equip-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 120px;
}
.empty {
  color: #909399;
  text-align: center;
  padding: 40px 0;
}
.equip-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
}
.dian {
  position: absolute;
  left: 12px;
  top: 12px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid #fff;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.15);
  z-index: 1;
}
.dian.green {
  background: #3eb36f;
}
.dian.yellow {
  background: #efad4d;
}
.dian.red {
  background: #f05050;
}
.dian.gray {
  background: #cacaca;
}
.thumb {
  width: 72px;
  height: 72px;
  margin-left: 8px;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f7fa;
  flex-shrink: 0;
}
.thumb img,
.detail-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 12px;
}
.meta {
  flex: 1;
  min-width: 0;
}
.title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
}
.sub {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: #606266;
  font-size: 13px;
  align-items: center;
}
.actions {
  flex-shrink: 0;
}
.detail-head {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}
.detail-thumb {
  position: relative;
  width: 110px;
  height: 110px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7fa;
  flex-shrink: 0;
}
.detail-desc {
  flex: 1;
}
.section-title {
  margin: 16px 0 8px;
  font-size: 14px;
  font-weight: 600;
}
</style>
