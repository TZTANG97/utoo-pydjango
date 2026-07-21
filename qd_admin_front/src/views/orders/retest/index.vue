<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  agreeRetest,
  fetchRetestDetail,
  fetchRetestList,
  refuseRetest,
} from '@/api/billing'
import { RETEST_STATUS, formatDate } from '@/utils/billing-labels'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const router = useRouter()
const loading = ref(false)
const detailLoading = ref(false)
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

const testFiles = computed(() => {
  const list = detail.value?.testfiles
  return Array.isArray(list) ? (list as Record<string, unknown>[]) : []
})

const detailLogs = computed(() => {
  const list = detail.value?.logs
  return Array.isArray(list) ? (list as Record<string, unknown>[]) : []
})

const relatedOrder = computed(() => {
  const eo = detail.value?.experimentOrder
  return eo && typeof eo === 'object' ? (eo as Record<string, unknown>) : null
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
  detailLoading.value = true
  detailVisible.value = true
  detail.value = null
  try {
    const res = await fetchRetestDetail(String(row.id))
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
      detailVisible.value = false
      return
    }
    detail.value = (res.obj || null) as Record<string, unknown> | null
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载详情失败')
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

function openRelatedOrder() {
  const id = relatedOrder.value?.id
  if (!id) {
    ElMessage.warning('未找到关联订单')
    return
  }
  router.push(`/experiment/order-detail/${id}`)
}

function fileHref(file: Record<string, unknown>) {
  const url = String(file.url || '')
  if (url) return url
  const path = String(file.path || '').replace(/\/$/, '')
  const name = String(file.name || '')
  return path && name ? `${path}/${name}` : path || name
}

async function handleAgree(row: Record<string, unknown>) {
  const { value } = await ElMessageBox.prompt('请输入客服备注（可选）', '同意复测', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPlaceholder: '客服备注',
  }).catch(() => ({ value: null as string | null }))
  if (value === null) return
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
  }).catch(() => ({ value: null as string | null }))
  if (value === null) return
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

    <el-dialog v-model="detailVisible" title="复测申请详情" width="820px" destroy-on-close>
      <div v-loading="detailLoading">
        <template v-if="detail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="编号">
              {{ detail.fc_no || detail.order_id || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="申请日期">
              {{ formatDate(detail.addTime) }}
            </el-descriptions-item>
            <el-descriptions-item label="申请人">
              {{ detail.trueName || detail.userName || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="电话">
              {{ detail.mobile || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="审核状态">
              {{ RETEST_STATUS[Number(detail.applyStatus)] || detail.applyStatus }}
            </el-descriptions-item>
            <el-descriptions-item label="来源单号">
              <el-button
                v-if="relatedOrder?.order_id || relatedOrder?.id"
                link
                type="primary"
                @click="openRelatedOrder"
              >
                {{ relatedOrder?.order_id || relatedOrder?.id }}
              </el-button>
              <span v-else>{{ detail.orderId || '-' }}</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="testFiles.length" label="订单资料" :span="2">
              <div class="file-list">
                <a
                  v-for="file in testFiles"
                  :key="String(file.id)"
                  class="file-link"
                  :href="fileHref(file)"
                  target="_blank"
                  rel="noopener"
                >
                  {{ file.info || file.name || file.url || '附件' }}
                </a>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="用户需求描述" :span="2">
              <el-input :model-value="String(detail.mark || '')" type="textarea" :rows="3" disabled />
            </el-descriptions-item>
            <el-descriptions-item label="客服咨询后的需求描述" :span="2">
              <el-input
                :model-value="String(detail.remeasurement_require || '')"
                type="textarea"
                :rows="3"
                disabled
              />
            </el-descriptions-item>
          </el-descriptions>

          <div class="log-title">操作记录</div>
          <el-table :data="detailLogs" border size="small" empty-text="暂无操作记录">
            <el-table-column prop="addTime" label="操作时间" min-width="160">
              <template #default="{ row }">{{ formatDate(row.addTime) }}</template>
            </el-table-column>
            <el-table-column prop="addusername" label="操作人员" min-width="120" />
            <el-table-column prop="content" label="操作" min-width="180" show-overflow-tooltip />
          </el-table>
        </template>
      </div>
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
.file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.file-link {
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}
.file-link:hover {
  text-decoration: underline;
}
.log-title {
  margin: 16px 0 8px;
  font-weight: 600;
  color: #303133;
}
</style>
