<template>
  <admin-page-card title="库存管理">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="产品名称">
        <el-input v-model="filters.goodsName" clearable style="width: 160px" />
      </el-form-item>
      <el-form-item label="产品型号">
        <el-input v-model="filters.goodsSpec" clearable style="width: 140px" />
      </el-form-item>
      <el-form-item label="产品序列号">
        <el-input v-model="filters.serialNumber" clearable style="width: 140px" />
      </el-form-item>
      <el-form-item label="实验平台">
        <el-select
          v-model="filters.expmanageLineId"
          clearable
          filterable
          placeholder="全部"
          style="width: 160px"
        >
          <el-option
            v-for="item in expLines"
            :key="String(item.id)"
            :label="String(item.lineNum || item.id)"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="自用租赁">
        <el-select
          v-model="filters.privateLeaseType"
          clearable
          filterable
          placeholder="全部"
          style="width: 160px"
        >
          <el-option v-for="name in leaseOptions" :key="name" :label="name" :value="name" />
        </el-select>
      </el-form-item>
      <!-- 状态分类筛选暂不开放
      <el-form-item label="状态分类">
        <el-select v-model="filters.type" clearable placeholder="全部" style="width: 130px">
          <el-option value="1" label="在库相关" />
          <el-option value="2" label="出库相关" />
          <el-option value="3" label="在途" />
        </el-select>
      </el-form-item>
      -->
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
        <el-button @click="resetFilters">清空筛选</el-button>
      </el-form-item>
    </el-form>

    <div class="toolbar">
      <div class="summary">UT实验租用总数量：{{ inventoryNum }}</div>
      <div class="actions">
        <el-button @click="clearSelection">清空勾选</el-button>
        <el-button type="primary" @click="editSelected">编辑</el-button>
        <el-button type="success" @click="showQr">生成二维码</el-button>
        <el-button type="warning" @click="exportExcel">导出EXCEL</el-button>
      </div>
    </div>

    <el-table
      ref="parentTableRef"
      v-loading="loading"
      :data="rows"
      border
      stripe
      row-key="rowKey"
      @expand-change="onExpand"
      @selection-change="onParentSelect"
    >
      <el-table-column type="expand" width="46">
        <template #default="{ row }">
          <el-table
            :ref="(el) => setChildTableRef(String(row.rowKey), el)"
            v-loading="!!childLoading[row.rowKey]"
            :data="childRows[row.rowKey] || []"
            size="small"
            border
            class="child-table"
            row-key="id"
            @selection-change="(sel) => onChildSelect(row.rowKey, sel)"
          >
            <el-table-column type="selection" width="42" />
            <el-table-column prop="inventoryId" label="库存编号" min-width="120" />
            <el-table-column prop="serialNumber" label="序列号" min-width="110" />
            <el-table-column prop="storeName" label="仓库" min-width="110" />
            <el-table-column prop="storePosition" label="保存位置" width="100" />
            <el-table-column prop="inventoryNum" label="数量" width="70" />
            <el-table-column prop="giStatusLabel" label="状态" width="110" />
            <el-table-column prop="expmanageName" label="自用租赁" min-width="110" />
            <el-table-column prop="companyName" label="所属公司" min-width="120" />
            <el-table-column prop="mark" label="备注" min-width="120" show-overflow-tooltip />
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row: child }">
                <el-button link type="primary" @click="openEdit(child)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </el-table-column>
      <el-table-column type="selection" width="42" />
      <el-table-column prop="inventoryId" label="库存编号" min-width="120" show-overflow-tooltip />
      <el-table-column prop="goodsName" label="商品名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="goodsSpec" label="产品型号" min-width="120" show-overflow-tooltip />
      <el-table-column prop="goodsBrandName" label="产品厂家" min-width="130" show-overflow-tooltip />
      <el-table-column label="数量" width="100" align="center">
        <template #default="{ row }">{{ row.nums ?? 0 }} / {{ row.totalnum ?? 0 }}</template>
      </el-table-column>
      <el-table-column prop="serialNumber" label="序列号" min-width="120" show-overflow-tooltip />
      <el-table-column prop="lineNum" label="自用相关实验平台" min-width="130" />
      <el-table-column prop="zlckj" label="租赁参考价" width="110" align="right" />
      <el-table-column prop="nbzlj" label="内部租赁价" width="110" align="right" />
      <el-table-column prop="produceTime" label="生产日期" min-width="120" />
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

    <el-dialog v-model="dialogVisible" title="编辑库存" width="520px">
      <el-form label-width="100px">
        <el-form-item label="序列号"><el-input v-model="form.serialNumber" /></el-form-item>
        <el-form-item label="仓库ID"><el-input v-model="form.storeId" /></el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.inventoryNum" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="form.goodsPrice" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.giStatus" style="width: 100%">
            <el-option
              v-for="opt in statusOptions"
              :key="opt.value"
              :label="`${opt.value} ${opt.label}`"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="租赁参考价">
          <el-input-number v-model="form.zlckj" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="内部租赁价">
          <el-input-number v-model="form.nbzlj" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="生产日期">
          <el-date-picker
            v-model="form.produceTime"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.mark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="qrVisible" title="生成二维码" width="560px" @opened="renderQrCodes">
      <p class="qr-tip">内容格式：厂家;型号;序列号</p>
      <div v-if="qrItems.length" class="qr-list">
        <div v-for="(item, idx) in qrItems" :key="idx" class="qr-item">
          <canvas :ref="(el) => setQrCanvasRef(idx, el)" class="qr-canvas" />
          <div class="qr-meta">
            <div class="qr-text">{{ item }}</div>
            <el-button size="small" @click="copyText(item)">复制</el-button>
          </div>
        </div>
      </div>
      <el-empty v-else description="请先勾选明细行" />
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type TableInstance } from 'element-plus'
import QRCode from 'qrcode'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  fetchInventoryChildren,
  fetchInventoryList,
  fetchInventorySummary,
  updateInventory,
} from '@/api/inventory'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const filters = reactive({
  goodsName: '',
  goodsSpec: '',
  serialNumber: '',
  expmanageLineId: '',
  privateLeaseType: '',
})

const inventoryNum = ref(0)
const leaseOptions = ref<string[]>([])
const expLines = ref<Record<string, unknown>[]>([])
const statusOptions = ref<{ value: number; label: string }[]>([])
const childRows = reactive<Record<string, Record<string, unknown>[]>>({})
const childLoading = reactive<Record<string, boolean>>({})
const childSelection = reactive<Record<string, Record<string, unknown>[]>>({})
const selectedChildren = ref<Record<string, unknown>[]>([])

const parentTableRef = ref<TableInstance>()
const childTableRefs = reactive<Record<string, TableInstance | null>>({})
const qrCanvasRefs = reactive<Record<number, HTMLCanvasElement | null>>({})
const selectedParentKeys = ref<Set<string>>(new Set())

const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref('')
const qrVisible = ref(false)
const qrItems = ref<string[]>([])
const form = reactive({
  serialNumber: '',
  storeId: '',
  inventoryNum: 0,
  goodsPrice: 0,
  giStatus: 1,
  zlckj: 0,
  nbzlj: 0,
  produceTime: '',
  mark: '',
})

function listParams() {
  return { ...filters, mode: 'statis' }
}

const { loading, rows, total, pagination, load } = useDataTable(async (params) => {
  const res = await fetchInventoryList({ ...params, ...listParams() })
  const data = (res.data || []).map((row, idx) => ({
    ...row,
    rowKey: `${row.goodsId || ''}_${row.goodsBrandId || ''}_${row.goodsSpec || ''}_${idx}`,
  }))
  return { ...res, data }
})

function reload() {
  pagination.page = 1
  Object.keys(childRows).forEach((k) => delete childRows[k])
  Object.keys(childSelection).forEach((k) => delete childSelection[k])
  selectedChildren.value = []
  return load(listParams())
}

function resetFilters() {
  Object.assign(filters, {
    goodsName: '',
    goodsSpec: '',
    serialNumber: '',
    expmanageLineId: '',
    privateLeaseType: '',
  })
  reload()
}

function setChildTableRef(rowKey: string, el: unknown) {
  childTableRefs[rowKey] = (el as TableInstance) || null
}

function setQrCanvasRef(idx: number, el: unknown) {
  qrCanvasRefs[idx] = (el as HTMLCanvasElement) || null
}

function refreshSelected() {
  selectedChildren.value = Object.values(childSelection).flat()
}

function clearSelection() {
  parentTableRef.value?.clearSelection()
  Object.values(childTableRefs).forEach((table) => table?.clearSelection())
  Object.keys(childSelection).forEach((k) => {
    childSelection[k] = []
  })
  selectedParentKeys.value = new Set()
  selectedChildren.value = []
}

function syncChildTableSelection(rowKey: string) {
  const childTable = childTableRefs[rowKey]
  const children = childRows[rowKey]
  const selected = childSelection[rowKey]
  if (!childTable || !children?.length || !selected?.length) return
  children.forEach((child) => {
    const checked = selected.some((s) => String(s.id) === String(child.id))
    childTable.toggleRowSelection(child, checked)
  })
}

async function ensureChildren(row: Record<string, unknown>) {
  const key = String(row.rowKey)
  if (childRows[key]) return childRows[key]
  childLoading[key] = true
  try {
    const res = await fetchInventoryChildren({
      goodsId: row.goodsId,
      goodsBrandId: row.goodsBrandId,
      goodsSpec: row.goodsSpec,
      serialNumber: filters.serialNumber,
      privateLeaseType: filters.privateLeaseType,
      expmanageLineId: filters.expmanageLineId,
    })
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      childRows[key] = res.obj as Record<string, unknown>[]
    } else {
      childRows[key] = []
      ElMessage.error(ajaxErrorMessage(res, '加载明细失败'))
    }
  } finally {
    childLoading[key] = false
  }
  return childRows[key]
}

async function onParentSelect(selection: Record<string, unknown>[]) {
  const currentKeys = new Set(selection.map((r) => String(r.rowKey)))

  for (const key of selectedParentKeys.value) {
    if (!currentKeys.has(key)) {
      childTableRefs[key]?.clearSelection()
      childSelection[key] = []
    }
  }
  selectedParentKeys.value = currentKeys

  for (const row of selection) {
    const key = String(row.rowKey)
    const children = await ensureChildren(row)
    await nextTick()
    const childTable = childTableRefs[key]
    if (childTable && children?.length) {
      children.forEach((child) => childTable.toggleRowSelection(child, true))
      childSelection[key] = [...children]
    } else if (children?.length) {
      childSelection[key] = [...children]
    }
  }
  refreshSelected()
}

function onChildSelect(rowKey: string, sel: Record<string, unknown>[]) {
  childSelection[rowKey] = sel
  refreshSelected()
}

async function onExpand(row: Record<string, unknown>, expanded: Record<string, unknown>[]) {
  const key = String(row.rowKey)
  const open = expanded.some((r) => String(r.rowKey) === key)
  if (!open) return
  await ensureChildren(row)
  await nextTick()
  syncChildTableSelection(key)
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  Object.assign(form, {
    serialNumber: String(row.serialNumber || ''),
    storeId: String(row.storeId || ''),
    inventoryNum: Number(row.inventoryNum || 0),
    goodsPrice: Number(row.goodsPrice || 0),
    giStatus: Number(row.giStatus || 1),
    zlckj: Number(row.zlckj || 0),
    nbzlj: Number(row.nbzlj || 0),
    produceTime: String(row.produceTime || '').slice(0, 10),
    mark: String(row.mark || ''),
  })
  dialogVisible.value = true
}

function editSelected() {
  if (!selectedChildren.value.length) {
    ElMessage.warning('请先勾选明细行（可勾选父行自动加载并选中明细）')
    return
  }
  if (selectedChildren.value.length > 1) {
    ElMessage.warning('请仅勾选一条明细进行编辑')
    return
  }
  openEdit(selectedChildren.value[0])
}

async function showQr() {
  if (!selectedChildren.value.length) {
    ElMessage.warning('请先勾选明细行（可勾选父行自动加载并选中明细）')
    return
  }
  qrItems.value = selectedChildren.value.map((row) => {
    const brand = String(row.goodsBrandName || '')
    const spec = String(row.goodsSpec || '')
    const serial = String(row.serialNumber || '')
    return `${brand};${spec};${serial}`
  })
  qrVisible.value = true
}

async function renderQrCodes() {
  await nextTick()
  for (let i = 0; i < qrItems.value.length; i++) {
    const canvas = qrCanvasRefs[i]
    if (!canvas) continue
    try {
      await QRCode.toCanvas(canvas, qrItems.value[i], { width: 160, margin: 1 })
    } catch {
      ElMessage.warning(`第 ${i + 1} 条二维码生成失败`)
    }
  }
}

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选择文本')
  }
}

function csvCell(v: unknown) {
  return `"${String(v ?? '').replace(/"/g, '""')}"`
}

async function exportExcel() {
  try {
    await ElMessageBox.confirm('确认导出当前数据为 Excel（CSV）？', '导出确认', {
      type: 'warning',
      confirmButtonText: '导出',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  const detailSelected = selectedChildren.value
  let header: string[]
  let lines: string[]

  if (detailSelected.length) {
    header = [
      '库存编号',
      '商品名称',
      '产品型号',
      '产品厂家',
      '数量',
      '序列号',
      '仓库',
      '保存位置',
      '状态',
      '自用租赁',
      '所属公司',
      '备注',
    ]
    lines = detailSelected.map((row) =>
      [
        row.inventoryId,
        row.goodsName,
        row.goodsSpec,
        row.goodsBrandName,
        row.inventoryNum,
        row.serialNumber,
        row.storeName,
        row.storePosition,
        row.giStatusLabel,
        row.expmanageName,
        row.companyName,
        row.mark,
      ]
        .map(csvCell)
        .join(',')
    )
  } else {
    if (!rows.value.length) {
      ElMessage.warning('当前无数据可导出')
      return
    }
    header = [
      '库存编号',
      '商品名称',
      '产品型号',
      '产品厂家',
      '可用数量',
      '总数量',
      '序列号',
      '实验平台',
      '租赁参考价',
      '内部租赁价',
      '生产日期',
    ]
    lines = rows.value.map((row) =>
      [
        row.inventoryId,
        row.goodsName,
        row.goodsSpec,
        row.goodsBrandName,
        row.nums,
        row.totalnum,
        row.serialNumber,
        row.lineNum,
        row.zlckj,
        row.nbzlj,
        row.produceTime,
      ]
        .map(csvCell)
        .join(',')
    )
  }

  const bom = '\uFEFF'
  const blob = new Blob([bom + [header.join(','), ...lines].join('\n')], {
    type: 'application/vnd.ms-excel;charset=utf-8;',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `库存列表_${new Date().toISOString().slice(0, 10)}.xls`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功（CSV 内容，可用 Excel 打开）')
}

async function handleSubmit() {
  saving.value = true
  try {
    const res = await updateInventory({ id: editingId.value, ...form })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    Object.keys(childRows).forEach((k) => delete childRows[k])
    await load(listParams())
  } finally {
    saving.value = false
  }
}

async function loadSummary() {
  const res = await fetchInventorySummary()
  if (!isAjaxOk(res) || !res.obj) return
  const obj = res.obj as Record<string, unknown>
  inventoryNum.value = Number(obj.inventorynum || 0)
  leaseOptions.value = Array.isArray(obj.leaseOptions) ? (obj.leaseOptions as string[]) : []
  expLines.value = Array.isArray(obj.expLines) ? (obj.expLines as Record<string, unknown>[]) : []
  statusOptions.value = Array.isArray(obj.statusOptions)
    ? (obj.statusOptions as { value: number; label: string }[])
    : []
}

onMounted(async () => {
  await loadSummary()
  await reload()
})
</script>

<style scoped>
.filter-form {
  margin-bottom: 8px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.summary {
  color: #303133;
  font-weight: 600;
}
.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.child-table {
  margin: 8px 12px 12px;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.qr-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.qr-item {
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
}
.qr-canvas {
  flex-shrink: 0;
}
.qr-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
  flex: 1;
}
.qr-text {
  word-break: break-all;
  color: #606266;
}
.qr-tip {
  margin: 0 0 12px;
  color: #909399;
  font-size: 13px;
}
</style>
