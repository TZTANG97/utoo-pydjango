<template>
  <div class="page-wrap">
    <section class="filter-panel">
      <el-form :inline="true" class="filter-form" @submit.prevent>
        <el-form-item label="产品名称">
          <el-input v-model="filters.goodsName" clearable placeholder="模糊搜索" style="width: 160px" />
        </el-form-item>
        <el-form-item label="产品型号">
          <el-input v-model="filters.goodsSpec" clearable placeholder="模糊搜索" style="width: 140px" />
        </el-form-item>
        <el-form-item label="产品序列号">
          <el-input v-model="filters.serialNumber" clearable placeholder="序列号" style="width: 140px" />
        </el-form-item>
        <el-form-item label="实验平台">
          <el-select
            v-model="filters.expmanageLineId"
            clearable
            filterable
            placeholder="全部平台"
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
            placeholder="全部类型"
            style="width: 160px"
          >
            <el-option v-for="name in leaseOptions" :key="name" :label="name" :value="name" />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-actions">
          <el-button type="primary" @click="reload">查询</el-button>
          <el-button type="danger" class="btn-reset" @click="resetFilters">清空筛选</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="table-panel">
      <div class="table-toolbar">
        <div class="toolbar-left">
          <div class="toolbar-title">
            <span class="title-text">库存列表</span>
            <span class="title-meta">共 {{ total }} 条</span>
          </div>
          <div class="summary-chip">
            UT实验租用总量
            <strong>{{ inventoryNum }}</strong>
          </div>
          <div v-if="selectedChildren.length" class="select-chip">
            已选明细 <strong>{{ selectedChildren.length }}</strong>
          </div>
        </div>
        <div class="actions">
          <el-button type="danger" class="btn-reset" plain @click="clearSelection">清空勾选</el-button>
          <el-button type="primary" @click="editSelected">编辑</el-button>
          <el-button type="success" @click="showQr">生成二维码</el-button>
          <el-button type="warning" @click="exportExcel">导出EXCEL</el-button>
        </div>
      </div>

      <el-table
        ref="parentTableRef"
        v-loading="loading"
        :data="rows"
        class="data-table"
        stripe
        row-key="rowKey"
        :header-cell-style="headerCellStyle"
        @expand-change="onExpand"
        @selection-change="onParentSelect"
      >
        <el-table-column type="expand" width="46">
          <template #default="{ row }">
            <div class="child-wrap">
              <el-table
                :ref="(el) => setChildTableRef(String(row.rowKey), el)"
                v-loading="!!childLoading[row.rowKey]"
                :data="childRows[row.rowKey] || []"
                size="small"
                class="child-table"
                stripe
                row-key="id"
                :header-cell-style="childHeaderStyle"
                @selection-change="(sel) => onChildSelect(row.rowKey, sel)"
              >
                <el-table-column type="selection" width="42" />
                <el-table-column prop="inventoryId" label="库存编号" min-width="120">
                  <template #default="{ row: child }">
                    <span class="cell-code">{{ child.inventoryId || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="serialNumber" label="序列号" min-width="110">
                  <template #default="{ row: child }">
                    <span class="cell-muted">{{ child.serialNumber || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="storeName" label="仓库" min-width="110">
                  <template #default="{ row: child }">
                    <span class="cell-strong">{{ child.storeName || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="storePosition" label="保存位置" width="100">
                  <template #default="{ row: child }">
                    <span class="cell-muted">{{ child.storePosition || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="inventoryNum" label="数量" width="70" align="center" />
                <el-table-column label="状态" width="110" align="center">
                  <template #default="{ row: child }">
                    <el-tag
                      :type="statusTagType(child.giStatusLabel)"
                      size="small"
                      effect="light"
                      round
                    >
                      {{ child.giStatusLabel || '-' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="expmanageName" label="自用租赁" min-width="110">
                  <template #default="{ row: child }">
                    <span class="cell-muted">{{ child.expmanageName || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="companyName" label="所属公司" min-width="120" show-overflow-tooltip />
                <el-table-column prop="mark" label="备注" min-width="120" show-overflow-tooltip>
                  <template #default="{ row: child }">
                    <span class="cell-muted">{{ child.mark || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80" fixed="right" align="center">
                  <template #default="{ row: child }">
                    <el-button link type="primary" @click="openEdit(child)">编辑</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column type="selection" width="42" />
        <el-table-column prop="inventoryId" label="库存编号" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-code">{{ row.inventoryId || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="goodsName" label="商品名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-strong">{{ row.goodsName || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="goodsSpec" label="产品型号" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag size="small" effect="plain" class="type-tag">{{ row.goodsSpec || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="goodsBrandName" label="产品厂家" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-muted">{{ row.goodsBrandName || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="110" align="center">
          <template #default="{ row }">
            <span class="qty">
              <em>{{ row.nums ?? 0 }}</em>
              <span class="qty-sep">/</span>
              <span>{{ row.totalnum ?? 0 }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="serialNumber" label="序列号" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-muted">{{ row.serialNumber || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="lineNum" label="自用相关实验平台" min-width="140">
          <template #default="{ row }">
            <span class="cell-muted">{{ row.lineNum || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="zlckj" label="租赁参考价" width="120" align="right">
          <template #default="{ row }">
            <span class="money">¥ {{ formatPrice(row.zlckj) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="nbzlj" label="内部租赁价" width="120" align="right">
          <template #default="{ row }">
            <span class="money">¥ {{ formatPrice(row.nbzlj) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="produceTime" label="生产日期" min-width="120">
          <template #default="{ row }">
            <span class="cell-muted">{{ row.produceTime || '-' }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          background
          layout="sizes, total, prev, pager, next"
          :total="total"
          @size-change="reload"
          @current-change="() => load(listParams())"
        />
      </div>
    </section>

    <el-dialog v-model="dialogVisible" title="编辑库存" width="540px" destroy-on-close>
      <el-form label-width="100px" class="edit-form">
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

    <el-dialog v-model="qrVisible" title="生成二维码" width="560px" destroy-on-close @opened="renderQrCodes">
      <p class="qr-tip">内容格式：厂家;型号;序列号</p>
      <div v-if="qrItems.length" class="qr-list">
        <div v-for="(item, idx) in qrItems" :key="idx" class="qr-item">
          <canvas :ref="(el) => setQrCanvasRef(idx, el)" class="qr-canvas" />
          <div class="qr-meta">
            <div class="qr-text">{{ item }}</div>
            <el-button size="small" type="primary" plain @click="copyText(item)">复制</el-button>
          </div>
        </div>
      </div>
      <el-empty v-else description="请先勾选明细行" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type TableInstance } from 'element-plus'
import QRCode from 'qrcode'
import {
  fetchInventoryChildren,
  fetchInventoryList,
  fetchInventorySummary,
  updateInventory,
} from '@/api/inventory'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const headerCellStyle = {
  background: '#f3f6fb',
  color: '#3a4660',
  fontWeight: 600,
  borderBottom: '1px solid #e4ebf5',
}

const childHeaderStyle = {
  background: '#eef4fb',
  color: '#3a4660',
  fontWeight: 600,
}

function formatPrice(value: unknown) {
  const num = Number(value ?? 0)
  return Number.isFinite(num) ? num.toFixed(2) : '0.00'
}

function statusTagType(label: unknown): 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  const text = String(label || '')
  if (/在库|可用|正常|入库/.test(text)) return 'success'
  if (/在途|预约|锁定|待/.test(text)) return 'warning'
  if (/已出|出库|租用|借出/.test(text)) return 'primary'
  if (/损坏|报废|丢失|停用/.test(text)) return 'danger'
  return 'info'
}

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

<style scoped lang="scss">
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.filter-panel,
.table-panel {
  background: #fff;
  border: 1px solid #e8eef6;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(31, 45, 61, 0.04);
}

.filter-panel {
  padding: 16px 18px 2px;
  background: linear-gradient(180deg, #fbfcfe 0%, #ffffff 55%);
}

.filter-form {
  :deep(.el-form-item) {
    margin-right: 16px;
    margin-bottom: 14px;
  }

  :deep(.el-form-item__label) {
    color: #5b6780;
    font-weight: 500;
  }
}

.filter-actions {
  :deep(.el-form-item__content) {
    gap: 8px;
  }
}

.btn-reset {
  --el-button-bg-color: #f56c6c;
  --el-button-border-color: #f56c6c;
  --el-button-text-color: #fff;
  --el-button-hover-bg-color: #f78989;
  --el-button-hover-border-color: #f78989;
  --el-button-hover-text-color: #fff;
  --el-button-active-bg-color: #dd6161;
  --el-button-active-border-color: #dd6161;
}

.btn-reset:not(.is-plain) {
  color: #fff !important;
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
}

.table-panel {
  padding: 14px 16px 16px;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eef2f8;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.toolbar-title {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.title-text {
  font-size: 15px;
  font-weight: 600;
  color: #24324a;
}

.title-meta {
  font-size: 12px;
  color: #8a95a8;
}

.summary-chip,
.select-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  color: #5b6780;
  background: #f3f7ff;
  border: 1px solid #dce8fb;
}

.summary-chip strong,
.select-chip strong {
  color: #2f6fed;
  font-size: 14px;
  font-variant-numeric: tabular-nums;
}

.select-chip {
  background: #fff8ef;
  border-color: #ffe2b8;
}

.select-chip strong {
  color: #d48806;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.data-table {
  --el-table-border-color: #eef2f8;
  --el-table-row-hover-bg-color: #f5f9ff;

  :deep(.el-table__inner-wrapper::before) {
    display: none;
  }

  :deep(.el-table__expand-icon) {
    color: #5b7cba;
  }
}

.child-wrap {
  margin: 4px 8px 10px 36px;
  padding: 10px;
  border-radius: 8px;
  background: linear-gradient(180deg, #f7faff 0%, #ffffff 100%);
  border: 1px solid #e4ebf5;
}

.child-table {
  --el-table-border-color: #e8eef6;
  --el-table-row-hover-bg-color: #eef6ff;
}

.cell-code {
  color: #2f6fed;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.cell-strong {
  color: #24324a;
  font-weight: 550;
}

.cell-muted {
  color: #6b768a;
  font-size: 13px;
}

.type-tag {
  --el-tag-bg-color: #f0f4fa;
  --el-tag-border-color: #dce5f2;
  --el-tag-text-color: #4d5d78;
}

.qty {
  font-variant-numeric: tabular-nums;
  color: #5b6780;

  em {
    font-style: normal;
    color: #2f6fed;
    font-weight: 700;
  }
}

.qty-sep {
  margin: 0 3px;
  color: #b0b8c6;
}

.money {
  color: #e6a23c;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}

.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.edit-form {
  :deep(.el-form-item__label) {
    color: #5b6780;
    font-weight: 500;
  }
}

.qr-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.qr-item {
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #e8eef6;
  border-radius: 10px;
  padding: 12px 14px;
  background: #fbfcfe;
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
  color: #4d5d78;
  font-size: 13px;
}

.qr-tip {
  margin: 0 0 12px;
  color: #8a95a8;
  font-size: 13px;
}
</style>
