<template>
  <admin-page-card title="样品管理单">
    <template #actions>
      <el-button type="warning" @click="exportVisible = true">导出样品出入库</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent="reload">
      <el-form-item label="入库编号">
        <el-input
          v-model="filters.outNum"
          clearable
          placeholder="入库编号"
          style="width: 160px"
          @keyup.enter="reload"
        />
      </el-form-item>
      <el-form-item label="实际入库时间">
        <el-date-picker
          v-model="filters.sjOutTime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
          clearable
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item label="关联单号">
        <el-input
          v-model="filters.orderId"
          clearable
          placeholder="关联单号"
          style="width: 180px"
          @keyup.enter="reload"
        />
      </el-form-item>
      <el-form-item label="仓库">
        <el-select v-model="filters.storeId" clearable filterable placeholder="全部仓库" style="width: 160px">
          <el-option
            v-for="s in stores"
            :key="String(s.value)"
            :label="String(s.label)"
            :value="String(s.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" label="#" align="center" />
      <el-table-column prop="outNum" label="样品入库编号" min-width="150" show-overflow-tooltip />
      <el-table-column label="实际入库日期" min-width="160">
        <template #default="{ row }">{{ formatTime(row.sjOutTime || row.sj_out_time) }}</template>
      </el-table-column>
      <el-table-column prop="orderNum" label="关联订单" min-width="160" show-overflow-tooltip />
      <el-table-column label="样品仓库" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ row.storeName || row.store_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="产品名称" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.goodsName || row.goods_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="产品型号" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ row.goodsSpec || row.goods_spec || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

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

    <el-drawer v-model="drawerVisible" title="样品管理单详情" size="720px">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="样品管理单编号">{{ detail.outNum }}</el-descriptions-item>
          <el-descriptions-item label="入库人员">
            {{ detail.rkryname || detail.rkryTrueName || detail.rkryUserName || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="实际入库时间">{{ formatTime(detail.sjOutTime) }}</el-descriptions-item>
          <el-descriptions-item label="关联订单">{{ detail.orderNum || '-' }}</el-descriptions-item>
          <el-descriptions-item label="入库样品仓库" :span="2">
            {{ detail.storeName || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.mark || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 class="section-title">样品明细</h4>
        <el-table :data="(detail.items as Record<string, unknown>[]) || []" border size="small">
          <el-table-column prop="childOrderId" label="关联订单" min-width="120" show-overflow-tooltip />
          <el-table-column prop="goodsBrandName" label="样品厂商" min-width="100" show-overflow-tooltip />
          <el-table-column prop="goodsName" label="样品名称" min-width="120" show-overflow-tooltip />
          <el-table-column prop="goodsSpec" label="样品型号" min-width="100" show-overflow-tooltip />
          <el-table-column prop="sampleStoreName" label="入库样品仓库" min-width="110" show-overflow-tooltip />
          <el-table-column prop="storePosition" label="入库位置" min-width="100" />
          <el-table-column prop="gotStatusLabel" label="状态" width="80" />
        </el-table>

        <h4 class="section-title">操作记录</h4>
        <el-table
          :data="(detail.logs as Record<string, unknown>[]) || []"
          border
          size="small"
          empty-text="暂无操作记录"
          stripe
        >
          <el-table-column label="操作时间" min-width="160">
            <template #default="{ row }">{{ formatTime(row.addTime) }}</template>
          </el-table-column>
          <el-table-column label="操作人员" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.operateUser || row.logUserName || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.operateInfo || row.logInfo || '-' }}
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-drawer>

    <el-dialog v-model="exportVisible" title="导出样品出入库" width="420px">
      <el-form label-width="90px">
        <el-form-item label="仓库">
          <el-select v-model="exportForm.storeId" clearable filterable placeholder="全部" style="width: 100%">
            <el-option
              v-for="s in stores"
              :key="String(s.value)"
              :label="String(s.label)"
              :value="String(s.value)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="exportForm.startime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="开始时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="exportForm.endtime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="结束时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exportVisible = false">取消</el-button>
        <el-button type="primary" :loading="exporting" @click="handleExport">导出 Excel</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  exportSampleOrders,
  fetchSampleOrderList,
  fetchSampleOrderOptions,
  getSampleOrderDetail,
} from '@/api/inventory'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const filters = reactive({
  outNum: '',
  orderId: '',
  sjOutTime: '',
  storeId: '',
})

const stores = ref<Record<string, unknown>[]>([])
const drawerVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const exportVisible = ref(false)
const exporting = ref(false)
const exportForm = reactive({
  storeId: '',
  startime: '',
  endtime: '',
})

function formatTime(v: unknown) {
  if (!v) return '-'
  return String(v).replace('T', ' ').slice(0, 19)
}

function listParams() {
  const p: Record<string, string> = {}
  if (filters.outNum) p.outNum = filters.outNum.trim()
  if (filters.orderId) p.orderId = filters.orderId.trim()
  if (filters.sjOutTime) p.sjOutTime = filters.sjOutTime
  if (filters.storeId) p.storeId = filters.storeId
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchSampleOrderList({ ...p, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

async function loadOptions() {
  try {
    const res = await fetchSampleOrderOptions()
    if (isAjaxOk(res) && res.obj) {
      const obj = res.obj as Record<string, unknown>
      stores.value = Array.isArray(obj.stores) ? (obj.stores as Record<string, unknown>[]) : []
    }
  } catch {
    /* 下拉失败不阻断列表 */
  }
}

async function openDetail(row: Record<string, unknown>) {
  if (row.ists) {
    try {
      await ElMessageBox.confirm('订单未审核完成,请勿操作入库', '提示', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      })
    } catch {
      return
    }
  }
  const res = await getSampleOrderDetail(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  detail.value = (res.obj as Record<string, unknown>) || null
  drawerVisible.value = true
}

function downloadCsv(filename: string, rows: Record<string, unknown>[]) {
  const headers = [
    ['operateTime', '操作时间'],
    ['operateUser', '操作人员'],
    ['operateInfo', '操作'],
    ['orderChildId', '子订单号'],
    ['goodsBrandName', '样品厂商'],
    ['goodsName', '样品名称'],
    ['goodsSpec', '样品型号'],
    ['storeSlot', '库位'],
    ['storeName', '样品仓库'],
  ] as const
  const escape = (v: unknown) => {
    const s = v == null ? '' : String(v)
    return `"${s.replace(/"/g, '""')}"`
  }
  const lines = [
    headers.map((h) => escape(h[1])).join(','),
    ...rows.map((r) => headers.map((h) => escape(r[h[0]])).join(',')),
  ]
  const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function handleExport() {
  exporting.value = true
  try {
    const res = await exportSampleOrders({
      storeId: exportForm.storeId || undefined,
      startime: exportForm.startime || undefined,
      endtime: exportForm.endtime || undefined,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '导出失败'))
      return
    }
    const obj = (res.obj || {}) as { rows?: Record<string, unknown>[] }
    const exportRows = Array.isArray(obj.rows) ? obj.rows : []
    if (!exportRows.length) {
      ElMessage.warning('数据为空')
      return
    }
    downloadCsv(`样品出入库_${Date.now()}.csv`, exportRows)
    ElMessage.success(`已导出 ${exportRows.length} 条`)
    exportVisible.value = false
  } finally {
    exporting.value = false
  }
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
.section-title {
  margin: 16px 0 8px;
  font-size: 14px;
  font-weight: 600;
}
</style>
