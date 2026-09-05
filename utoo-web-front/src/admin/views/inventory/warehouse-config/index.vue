<template>
  <admin-page-card :title="pageTitle">
    <template #actions>
      <el-button @click="goBack">返回</el-button>
      <el-button type="primary" @click="openAddBlock">添加地块</el-button>
      <el-button type="primary" @click="openAddPos">添加位置</el-button>
      <el-button @click="openQrcode">生成条码</el-button>
    </template>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="地块" name="block" />
      <el-tab-pane :label="positionTabLabel" name="position" />
    </el-tabs>

    <el-form v-if="activeTab === 'position'" :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="位置标识">
        <el-input
          v-model="posFilter"
          clearable
          placeholder="如 A-01"
          style="width: 160px"
          @keyup.enter="reloadPositions"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reloadPositions">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table
      v-if="activeTab === 'block'"
      v-loading="blockLoading"
      :data="blockRows"
      border
      stripe
    >
      <el-table-column type="index" width="55" label="#" align="center" />
      <el-table-column prop="block" label="地块名称" min-width="160" />
      <el-table-column prop="addTime" label="创建时间" min-width="160" />
    </el-table>

    <el-table
      v-else
      v-loading="posLoading"
      :data="posRows"
      border
      stripe
      @selection-change="onPosSelectionChange"
    >
      <el-table-column type="selection" width="48" align="center" />
      <el-table-column prop="positionLabel" label="位置标识" min-width="120" />
      <el-table-column prop="occupiedLabel" label="是否放置产品" width="120" align="center" />
      <el-table-column prop="goodsBrandName" label="厂家" min-width="120" show-overflow-tooltip />
      <el-table-column
        v-if="isSample"
        prop="sampleName"
        label="样品名称"
        min-width="120"
        show-overflow-tooltip
      >
        <template #default="{ row }">{{ row.sampleName || row.goodsName || '-' }}</template>
      </el-table-column>
      <el-table-column prop="goodsSpec" label="型号" min-width="100" show-overflow-tooltip />
      <el-table-column
        v-if="!isSample"
        prop="serialNumber"
        label="序列号"
        min-width="120"
        show-overflow-tooltip
      />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="isSample && Number(row.positionStatus) === 1"
            link
            type="warning"
            @click="clearSample(row)"
          >
            删除样品信息
          </el-button>
          <el-button v-else link type="danger" @click="removePos(row)">删除位置</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-if="activeTab === 'block'"
        v-model:current-page="blockPagination.page"
        v-model:page-size="blockPagination.pageSize"
        layout="total, prev, pager, next"
        :total="blockTotal"
        @current-change="loadBlocks"
      />
      <el-pagination
        v-else
        v-model:current-page="posPagination.page"
        v-model:page-size="posPagination.pageSize"
        layout="total, prev, pager, next"
        :total="posTotal"
        @current-change="loadPositions"
      />
    </div>

    <el-dialog v-model="blockDialogVisible" title="添加地块" width="420px">
      <el-form label-width="90px">
        <el-form-item label="地块名称" required>
          <el-input v-model="blockForm.block" placeholder="请输入地块名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="blockDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitBlock">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="posDialogVisible" title="添加位置" width="480px">
      <el-form label-width="100px">
        <el-form-item label="地块" required>
          <el-select v-model="posForm.blockId" filterable clearable style="width: 100%">
            <el-option
              v-for="b in blockOptions"
              :key="String(b.id)"
              :label="String(b.block)"
              :value="String(b.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="批量添加">
          <el-switch v-model="posForm.batch" />
        </el-form-item>
        <template v-if="posForm.batch">
          <el-form-item label="起始编号" required>
            <el-input v-model="posForm.startNumber" placeholder="如 1" />
          </el-form-item>
          <el-form-item label="结束编号" required>
            <el-input v-model="posForm.endNumber" placeholder="如 20" />
          </el-form-item>
          <el-form-item label="字符前缀">
            <el-input v-model="posForm.charNumber" placeholder="可选" />
          </el-form-item>
        </template>
        <el-form-item v-else label="位置编号" required>
          <el-input v-model="posForm.number" placeholder="如 01" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="posDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitPos">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="qrVisible" title="生成条码" width="360px" @opened="renderQr">
      <div class="qr-wrap">
        <canvas ref="qrCanvas" />
        <p class="qr-text">{{ qrText }}</p>
      </div>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import QRCode from 'qrcode'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  addStoreBlock,
  addStorePosition,
  clearSampleStoreGoods,
  deleteStorePosition,
  fetchStoreBlockList,
  fetchStoreBlockOptions,
  fetchStorePositionList,
  fetchStorePositionQr,
  getSampleStorehouse,
  getStorehouse,
} from '@admin/api/inventory'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type Mode = 'goods' | 'sample' | 'retain'

const route = useRoute()
const router = useRouter()

const mode = computed<Mode>(() => {
  const m = String(route.query.mode || 'goods')
  if (m === 'sample' || m === 'retain') return m
  return 'goods'
})
const storeId = computed(() => String(route.query.id || ''))
const isSample = computed(() => mode.value !== 'goods')
const storeName = ref('')
const pageTitle = computed(() => {
  const base =
    mode.value === 'retain' ? '样品留存仓库配置' : mode.value === 'sample' ? '样品仓库配置' : '仓库配置'
  return storeName.value ? `${base} - ${storeName.value}` : base
})
const positionTabLabel = computed(() => (isSample.value ? '样品仓库位置' : '仓库位置'))

const activeTab = ref('block')
const blockLoading = ref(false)
const posLoading = ref(false)
const blockRows = ref<Record<string, unknown>[]>([])
const posRows = ref<Record<string, unknown>[]>([])
const blockTotal = ref(0)
const posTotal = ref(0)
const blockPagination = reactive({ page: 1, pageSize: 10 })
const posPagination = reactive({ page: 1, pageSize: 10 })
const posFilter = ref('')
const posSelected = ref<Record<string, unknown>[]>([])
const blockOptions = ref<{ id: string | number; block: string }[]>([])

const saving = ref(false)
const blockDialogVisible = ref(false)
const posDialogVisible = ref(false)
const blockForm = reactive({ block: '' })
const posForm = reactive({
  blockId: '',
  batch: false,
  number: '',
  startNumber: '',
  endNumber: '',
  charNumber: '',
})

const qrVisible = ref(false)
const qrText = ref('')
const qrCanvas = ref<HTMLCanvasElement | null>(null)

function goBack() {
  if (mode.value === 'retain') {
    router.push({ name: 'InventorySampleRetainWarehouses' })
  } else if (mode.value === 'sample') {
    router.push({ name: 'InventorySampleWarehouses' })
  } else {
    router.push({ name: 'InventoryWarehouses' })
  }
}

async function loadStoreMeta() {
  if (!storeId.value) return
  try {
    const res =
      mode.value === 'goods'
        ? await getStorehouse(storeId.value)
        : await getSampleStorehouse(mode.value === 'retain', storeId.value)
    if (isAjaxOk(res) && res.obj) {
      const obj = res.obj as Record<string, unknown>
      storeName.value = String(obj.storeName || obj.sample_store_name || '')
    }
  } catch {
    // ignore
  }
}

async function loadBlocks() {
  if (!storeId.value) return
  blockLoading.value = true
  try {
    const res = await fetchStoreBlockList(mode.value, {
      store_id: storeId.value,
      start: (blockPagination.page - 1) * blockPagination.pageSize,
      length: blockPagination.pageSize,
      draw: blockPagination.page,
    })
    blockRows.value = Array.isArray(res.data) ? res.data : []
    blockTotal.value = Number(res.recordsTotal || 0)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载地块失败')
  } finally {
    blockLoading.value = false
  }
}

async function loadPositions() {
  if (!storeId.value) return
  posLoading.value = true
  try {
    const res = await fetchStorePositionList(mode.value, {
      store_id: storeId.value,
      block_pos: posFilter.value.trim(),
      start: (posPagination.page - 1) * posPagination.pageSize,
      length: posPagination.pageSize,
      draw: posPagination.page,
    })
    posRows.value = Array.isArray(res.data) ? res.data : []
    posTotal.value = Number(res.recordsTotal || 0)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载位置失败')
  } finally {
    posLoading.value = false
  }
}

function reloadPositions() {
  posPagination.page = 1
  return loadPositions()
}

function onTabChange(name: string | number) {
  if (String(name) === 'block') void loadBlocks()
  else void loadPositions()
}

function onPosSelectionChange(rows: Record<string, unknown>[]) {
  posSelected.value = rows
}

function openAddBlock() {
  blockForm.block = ''
  blockDialogVisible.value = true
}

async function ensureBlockOptions() {
  const res = await fetchStoreBlockOptions(mode.value, storeId.value)
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    blockOptions.value = res.obj as { id: string | number; block: string }[]
  }
}

async function openAddPos() {
  await ensureBlockOptions()
  Object.assign(posForm, {
    blockId: '',
    batch: false,
    number: '',
    startNumber: '',
    endNumber: '',
    charNumber: '',
  })
  posDialogVisible.value = true
}

async function submitBlock() {
  if (!blockForm.block.trim()) {
    ElMessage.warning('请填写地块名')
    return
  }
  saving.value = true
  try {
    const res = await addStoreBlock(mode.value, {
      store_id: storeId.value,
      block: blockForm.block.trim(),
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '添加失败'))
      return
    }
    ElMessage.success('添加成功')
    blockDialogVisible.value = false
    await loadBlocks()
  } finally {
    saving.value = false
  }
}

async function submitPos() {
  if (!posForm.blockId) {
    ElMessage.warning('请选择地块')
    return
  }
  if (posForm.batch) {
    if (!posForm.startNumber || !posForm.endNumber) {
      ElMessage.warning('请填写起止编号')
      return
    }
  } else if (!posForm.number.trim()) {
    ElMessage.warning('请填写位置编号')
    return
  }
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      store_id: storeId.value,
      block: posForm.blockId,
    }
    if (posForm.batch) {
      payload.all = 1
      payload.startnumber = posForm.startNumber
      payload.endnumber = posForm.endNumber
      if (posForm.charNumber) payload.charnumber = posForm.charNumber
    } else {
      payload.number = posForm.number.trim()
    }
    const res = await addStorePosition(mode.value, payload)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '添加失败'))
      return
    }
    ElMessage.success('添加成功')
    posDialogVisible.value = false
    activeTab.value = 'position'
    await reloadPositions()
  } finally {
    saving.value = false
  }
}

async function removePos(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认删除该位置？', '提示', { type: 'warning' })
  const res = await deleteStorePosition(mode.value, String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
    return
  }
  ElMessage.success('操作成功')
  await loadPositions()
}

async function clearSample(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认清除该位置的样品信息？', '提示', { type: 'warning' })
  const res = await clearSampleStoreGoods(mode.value as 'sample' | 'retain', String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success('操作成功')
  await loadPositions()
}

async function openQrcode() {
  if (posSelected.value.length !== 1) {
    ElMessage.warning('只能选择一条数据!')
    return
  }
  const res = await fetchStorePositionQr(mode.value, String(posSelected.value[0].id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '生成失败'))
    return
  }
  qrText.value = String((res.obj as Record<string, unknown>).text || '')
  qrVisible.value = true
}

async function renderQr() {
  await nextTick()
  const canvas = qrCanvas.value
  if (!canvas || !qrText.value) return
  try {
    await QRCode.toCanvas(canvas, qrText.value, {
      width: 228,
      margin: 1,
      errorCorrectionLevel: 'H',
    })
  } catch {
    ElMessage.error('二维码生成失败')
  }
}

onMounted(async () => {
  if (!storeId.value) {
    ElMessage.error('缺少仓库参数')
    goBack()
    return
  }
  await loadStoreMeta()
  await loadBlocks()
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
.qr-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 8px 0 4px;
}
.qr-text {
  margin: 0;
  font-size: 12px;
  color: #666;
  word-break: break-all;
  text-align: center;
}
</style>
