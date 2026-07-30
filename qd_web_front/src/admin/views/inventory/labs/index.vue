<template>
  <admin-page-card title="实验室管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增实验室</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="实验室编号">
        <el-select
          v-model="filters.labNum"
          clearable
          filterable
          allow-create
          default-first-option
          placeholder="请选择/输入"
          style="width: 150px"
        >
          <el-option
            v-for="o in options.labNums"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="实验室名称">
        <el-select
          v-model="filters.labName"
          clearable
          filterable
          allow-create
          default-first-option
          placeholder="请选择/输入"
          style="width: 160px"
        >
          <el-option
            v-for="o in options.labNames"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="负责人">
        <el-select
          v-model="filters.labUserid"
          clearable
          filterable
          placeholder="请选择"
          style="width: 150px"
        >
          <el-option
            v-for="o in options.users"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="国家">
        <el-select
          v-model="filters.country"
          clearable
          filterable
          placeholder="请选择"
          style="width: 140px"
          @change="onCountryChange"
        >
          <el-option
            v-for="o in options.countries"
            :key="String(o.value)"
            :label="String(o.label)"
            :value="String(o.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="省/市">
        <el-select
          v-model="filters.province"
          clearable
          filterable
          placeholder="请选择"
          style="width: 140px"
          @change="onProvinceChange"
        >
          <el-option
            v-for="d in provinces"
            :key="String(d.id)"
            :label="String(d.disName || d.dis_name)"
            :value="String(d.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="市">
        <el-select
          v-model="filters.city"
          clearable
          filterable
          placeholder="请选择"
          style="width: 140px"
          @change="onCityChange"
        >
          <el-option
            v-for="d in cities"
            :key="String(d.id)"
            :label="String(d.disName || d.dis_name)"
            :value="String(d.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="县/区">
        <el-select
          v-model="filters.areaId"
          clearable
          filterable
          placeholder="请选择"
          style="width: 140px"
        >
          <el-option
            v-for="d in areas"
            :key="String(d.id)"
            :label="String(d.disName || d.dis_name)"
            :value="String(d.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" label="#" align="center" />
      <el-table-column prop="labNum" label="实验室编号" min-width="120" />
      <el-table-column prop="labName" label="实验室名称" min-width="140" show-overflow-tooltip />
      <el-table-column prop="userName" label="负责人" min-width="120" show-overflow-tooltip />
      <el-table-column prop="address" label="注册地址" min-width="140" show-overflow-tooltip />
      <el-table-column prop="countryName" label="国家" width="90" />
      <el-table-column prop="provinceName" label="省/市" min-width="100" />
      <el-table-column prop="cityName" label="市" min-width="100" />
      <el-table-column prop="areaName" label="县/区" min-width="100" />
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="Number(row.status) === 1 ? 'success' : 'info'" size="small">
            {{ Number(row.status) === 1 ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="warning" @click="toggleStatus(row)">
            {{ Number(row.status) === 1 ? '禁用' : '启用' }}
          </el-button>
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

    <!-- 查看实验室 + 实验线管理（对齐 Java labDetail） -->
    <el-dialog
      v-model="detailVisible"
      title="查看实验室"
      width="920px"
      destroy-on-close
      @closed="onDetailClosed"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="实验室编号">{{ detail.labNum }}</el-descriptions-item>
        <el-descriptions-item label="实验室名称">{{ detail.labName }}</el-descriptions-item>
        <el-descriptions-item label="注册地址" :span="2">{{ detail.address }}</el-descriptions-item>
        <el-descriptions-item label="国家">{{ detail.countryName }}</el-descriptions-item>
        <el-descriptions-item label="省/市">{{ detail.provinceName }}</el-descriptions-item>
        <el-descriptions-item label="市">{{ detail.cityName }}</el-descriptions-item>
        <el-descriptions-item label="县/区">{{ detail.areaName }}</el-descriptions-item>
        <el-descriptions-item label="负责人">{{ detail.userName }}</el-descriptions-item>
        <el-descriptions-item label="关联账号">{{ detail.syUserName || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="line-toolbar">
        <el-button type="primary" @click="openLineCreate">添加实验线</el-button>
        <el-button @click="openQrcode">生成二维码</el-button>
      </div>

      <el-table
        v-loading="lineLoading"
        :data="lineRows"
        border
        stripe
        @selection-change="onLineSelectionChange"
      >
        <el-table-column type="selection" width="48" align="center" />
        <el-table-column type="index" width="55" label="#" align="center" />
        <el-table-column prop="lineNum" label="实验线编号" min-width="140" />
        <el-table-column prop="className" label="实验线类型" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            {{ lineStatusLabel(row.lineStatus ?? row.line_status) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openLineEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="toggleLineStatus(row)">
              {{ Number(row.status) === 1 ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="linePagination.page"
          v-model:page-size="linePagination.pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, prev, pager, next"
          :total="lineTotal"
          @size-change="reloadLines"
          @current-change="loadLines"
        />
      </div>
    </el-dialog>

    <el-dialog
      v-model="lineDialogVisible"
      :title="lineEditingId ? '编辑实验线' : '添加实验线'"
      width="480px"
      append-to-body
    >
      <el-form label-width="110px">
        <el-form-item label="实验线编号" required>
          <el-input v-model="lineForm.lineNum" placeholder="请输入实验线编号" />
        </el-form-item>
        <el-form-item label="实验线类型" required>
          <el-select
            v-model="lineForm.classId"
            filterable
            clearable
            placeholder="请选择"
            style="width: 100%"
          >
            <el-option
              v-for="o in lineClassOptions"
              :key="String(o.id)"
              :label="String(o.name)"
              :value="String(o.id)"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="lineDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="lineSaving" @click="handleLineSubmit">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="qrVisible" title="生成二维码" width="360px" append-to-body @opened="renderQr">
      <div class="qr-wrap">
        <canvas ref="qrCanvas" />
        <p class="qr-text">{{ qrText }}</p>
      </div>
    </el-dialog>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑实验室' : '新增实验室'" width="560px">
      <el-form label-width="100px">
        <el-form-item label="编号"><el-input v-model="form.labNum" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.labName" /></el-form-item>
        <el-form-item label="负责人">
          <el-select
            v-model="form.labUserIds"
            multiple
            clearable
            filterable
            collapse-tags
            collapse-tags-tooltip
            style="width: 100%"
          >
            <el-option
              v-for="o in options.users"
              :key="String(o.value)"
              :label="String(o.label)"
              :value="String(o.value)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="国家">
          <el-select
            v-model="form.country"
            clearable
            filterable
            style="width: 100%"
            @change="onFormCountryChange"
          >
            <el-option
              v-for="o in options.countries"
              :key="String(o.value)"
              :label="String(o.label)"
              :value="String(o.value)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="省/市">
          <el-select
            v-model="form.provinceId"
            clearable
            filterable
            style="width: 100%"
            @change="onFormProvinceChange"
          >
            <el-option
              v-for="d in formProvinces"
              :key="String(d.id)"
              :label="String(d.disName || d.dis_name)"
              :value="String(d.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="市">
          <el-select
            v-model="form.cityId"
            clearable
            filterable
            style="width: 100%"
            @change="onFormCityChange"
          >
            <el-option
              v-for="d in formCities"
              :key="String(d.id)"
              :label="String(d.disName || d.dis_name)"
              :value="String(d.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="县/区">
          <el-select v-model="form.areaId" clearable filterable style="width: 100%">
            <el-option
              v-for="d in formAreas"
              :key="String(d.id)"
              :label="String(d.disName || d.dis_name)"
              :value="String(d.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="注册地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 120px">
            <el-option :value="1" label="启用" />
            <el-option :value="2" label="禁用" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  fetchLabList,
  fetchLabLineClassOptions,
  fetchLabLineList,
  fetchLabOptions,
  getLab,
  saveLab,
  submitLabLine,
  updateLabLine,
  updateLabLineStatus,
  updateLabStatus,
} from '@admin/api/inventory'
import { fetchDistrictChildren } from '@admin/api/system'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const filters = reactive({
  labNum: '',
  labName: '',
  labUserid: '',
  country: '',
  province: '',
  city: '',
  areaId: '',
})

const options = reactive({
  labNums: [] as Record<string, unknown>[],
  labNames: [] as Record<string, unknown>[],
  users: [] as Record<string, unknown>[],
  countries: [] as Record<string, unknown>[],
})

const provinces = ref<Record<string, unknown>[]>([])
const cities = ref<Record<string, unknown>[]>([])
const areas = ref<Record<string, unknown>[]>([])
const formProvinces = ref<Record<string, unknown>[]>([])
const formCities = ref<Record<string, unknown>[]>([])
const formAreas = ref<Record<string, unknown>[]>([])

const dialogVisible = ref(false)
const detailVisible = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const detail = ref<Record<string, unknown>>({})
const form = reactive({
  labNum: '',
  labName: '',
  labUserIds: [] as string[],
  country: '',
  provinceId: '',
  cityId: '',
  areaId: '',
  address: '',
  status: 1,
})

const lineLoading = ref(false)
const lineRows = ref<Record<string, unknown>[]>([])
const lineTotal = ref(0)
const linePagination = reactive({ page: 1, pageSize: 10 })
const lineSelected = ref<Record<string, unknown>[]>([])
const lineDialogVisible = ref(false)
const lineEditingId = ref<string | null>(null)
const lineSaving = ref(false)
const lineClassOptions = ref<{ id: string | number; name: string }[]>([])
const lineForm = reactive({ lineNum: '', classId: '' })

const qrVisible = ref(false)
const qrText = ref('')
const qrCanvas = ref<HTMLCanvasElement | null>(null)

function listParams() {
  const p: Record<string, string> = {}
  if (filters.labNum) p.labNum = String(filters.labNum).trim()
  if (filters.labName) p.labName = String(filters.labName).trim()
  if (filters.labUserid) p.labUserid = String(filters.labUserid).trim()
  if (filters.country) p.country = String(filters.country).trim()
  if (filters.province) p.province = String(filters.province).trim()
  if (filters.city) p.city = String(filters.city).trim()
  if (filters.areaId) p.areaId = String(filters.areaId).trim()
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchLabList({ ...p, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

function lineStatusLabel(v: unknown) {
  const n = Number(v)
  if (n === 1) return '进行中'
  return '空闲中'
}

async function loadOptions() {
  try {
    const res = await fetchLabOptions()
    if (!isAjaxOk(res) || !res.obj) return
    const obj = res.obj as Record<string, unknown>
    options.labNums = Array.isArray(obj.labNums) ? (obj.labNums as Record<string, unknown>[]) : []
    options.labNames = Array.isArray(obj.labNames) ? (obj.labNames as Record<string, unknown>[]) : []
    options.users = Array.isArray(obj.users) ? (obj.users as Record<string, unknown>[]) : []
    options.countries = Array.isArray(obj.countries)
      ? (obj.countries as Record<string, unknown>[])
      : []
  } catch {
    // 筛选下拉失败不阻断列表
  }
}

async function loadDistrictChildren(superId: string) {
  if (!superId) return []
  try {
    const res = await fetchDistrictChildren(superId)
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      return res.obj as Record<string, unknown>[]
    }
    if (Array.isArray(res.data)) {
      return res.data as Record<string, unknown>[]
    }
    return []
  } catch {
    return []
  }
}

async function onCountryChange() {
  filters.province = ''
  filters.city = ''
  filters.areaId = ''
  cities.value = []
  areas.value = []
  provinces.value = filters.country ? await loadDistrictChildren(filters.country) : []
}

async function onProvinceChange() {
  filters.city = ''
  filters.areaId = ''
  areas.value = []
  cities.value = filters.province ? await loadDistrictChildren(filters.province) : []
}

async function onCityChange() {
  filters.areaId = ''
  areas.value = filters.city ? await loadDistrictChildren(filters.city) : []
}

async function onFormCountryChange() {
  form.provinceId = ''
  form.cityId = ''
  form.areaId = ''
  formCities.value = []
  formAreas.value = []
  formProvinces.value = form.country ? await loadDistrictChildren(form.country) : []
}

async function onFormProvinceChange() {
  form.cityId = ''
  form.areaId = ''
  formAreas.value = []
  formCities.value = form.provinceId ? await loadDistrictChildren(form.provinceId) : []
}

async function onFormCityChange() {
  form.areaId = ''
  formAreas.value = form.cityId ? await loadDistrictChildren(form.cityId) : []
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    labNum: '',
    labName: '',
    labUserIds: [],
    country: '',
    provinceId: '',
    cityId: '',
    areaId: '',
    address: '',
    status: 1,
  })
  formProvinces.value = []
  formCities.value = []
  formAreas.value = []
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  const res = await getLab(String(row.id))
  const obj = isAjaxOk(res) && res.obj ? (res.obj as Record<string, unknown>) : row
  const userIds = String(obj.labUserid || '')
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)
  Object.assign(form, {
    labNum: String(obj.labNum || ''),
    labName: String(obj.labName || ''),
    labUserIds: userIds,
    country: String(obj.country || ''),
    provinceId: String(obj.provinceId || ''),
    cityId: String(obj.cityId || ''),
    areaId: String(obj.areaId || ''),
    address: String(obj.address || ''),
    status: Number(obj.status || 1) === 2 ? 2 : 1,
  })
  if (form.country) formProvinces.value = await loadDistrictChildren(form.country)
  if (form.provinceId) formCities.value = await loadDistrictChildren(form.provinceId)
  if (form.cityId) formAreas.value = await loadDistrictChildren(form.cityId)
  dialogVisible.value = true
}

async function openDetail(row: Record<string, unknown>) {
  const res = await getLab(String(row.id))
  detail.value = isAjaxOk(res) && res.obj ? (res.obj as Record<string, unknown>) : row
  linePagination.page = 1
  lineSelected.value = []
  detailVisible.value = true
  await ensureLineClassOptions()
  await reloadLines()
}

function onDetailClosed() {
  lineRows.value = []
  lineSelected.value = []
  lineTotal.value = 0
}

async function ensureLineClassOptions() {
  if (lineClassOptions.value.length) return
  try {
    const res = await fetchLabLineClassOptions()
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      lineClassOptions.value = res.obj as { id: string | number; name: string }[]
    }
  } catch {
    lineClassOptions.value = []
  }
}

async function loadLines() {
  const labId = detail.value?.id
  if (!labId) return
  lineLoading.value = true
  try {
    const res = await fetchLabLineList({
      lab_id: labId,
      page: linePagination.page,
      pageSize: linePagination.pageSize,
      length: linePagination.pageSize,
      start: (linePagination.page - 1) * linePagination.pageSize,
    })
    lineRows.value = Array.isArray(res.data) ? res.data : []
    lineTotal.value = Number(res.recordsTotal || 0)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载实验线失败')
    lineRows.value = []
    lineTotal.value = 0
  } finally {
    lineLoading.value = false
  }
}

function reloadLines() {
  linePagination.page = 1
  return loadLines()
}

function onLineSelectionChange(rows: Record<string, unknown>[]) {
  lineSelected.value = rows
}

function openLineCreate() {
  lineEditingId.value = null
  lineForm.lineNum = ''
  lineForm.classId = ''
  void ensureLineClassOptions()
  lineDialogVisible.value = true
}

function openLineEdit(row: Record<string, unknown>) {
  lineEditingId.value = String(row.id)
  lineForm.lineNum = String(row.lineNum || row.line_num || '')
  lineForm.classId = String(row.classId || row.class_id || '')
  void ensureLineClassOptions()
  lineDialogVisible.value = true
}

async function handleLineSubmit() {
  if (!lineForm.lineNum.trim()) {
    ElMessage.warning('请填写实验线编号')
    return
  }
  if (!lineForm.classId) {
    ElMessage.warning('请选择实验线类型')
    return
  }
  lineSaving.value = true
  try {
    const payload = {
      id: lineEditingId.value || undefined,
      lab_id: detail.value.id,
      line_num: lineForm.lineNum.trim(),
      class_id: lineForm.classId,
    }
    const res = lineEditingId.value
      ? await updateLabLine(payload)
      : await submitLabLine(payload)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success(lineEditingId.value ? '编辑成功' : '添加成功')
    lineDialogVisible.value = false
    await loadLines()
  } finally {
    lineSaving.value = false
  }
}

async function toggleLineStatus(row: Record<string, unknown>) {
  const next = Number(row.status) === 1 ? 2 : 1
  const res = await updateLabLineStatus(String(row.id), next)
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success('操作成功')
  await loadLines()
}

function openQrcode() {
  if (lineSelected.value.length !== 1) {
    ElMessage.warning('只能选择一条数据!')
    return
  }
  const row = lineSelected.value[0]
  const id = row.id
  const lineNum = row.lineNum || row.line_num || ''
  qrText.value = `lineId_${id};${lineNum}`
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

async function handleSubmit() {
  if (!form.labName.trim()) {
    ElMessage.warning('请填写实验室名称')
    return
  }
  saving.value = true
  try {
    const res = await saveLab({
      id: editingId.value || undefined,
      labNum: form.labNum,
      labName: form.labName,
      labUserid: form.labUserIds.join(','),
      country: form.country,
      areaId: form.areaId,
      address: form.address,
      status: form.status,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await reload()
    await loadOptions()
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: Record<string, unknown>) {
  // Java: 1启用 2禁用
  const next = Number(row.status) === 1 ? 2 : 1
  const res = await updateLabStatus(String(row.id), next)
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success(next === 1 ? '已启用' : '已禁用')
  await load(listParams())
}

onMounted(() => {
  // 列表与筛选选项互不阻断
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
.line-toolbar {
  margin: 16px 0 12px;
  display: flex;
  gap: 8px;
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
