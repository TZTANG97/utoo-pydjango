<template>
  <admin-page-card title="所属公司管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">添加所属公司</el-button>
    </template>

    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="用户名">
        <el-input v-model="filters.userName" placeholder="用户名" clearable />
      </el-form-item>
      <el-form-item label="企业名称">
        <el-input v-model="filters.companyName" placeholder="企业名称" clearable />
      </el-form-item>
      <el-form-item label="联系人">
        <el-input v-model="filters.trueName" placeholder="联系人" clearable />
      </el-form-item>
      <el-form-item label="联系电话">
        <el-input v-model="filters.mobile" placeholder="联系电话" clearable />
      </el-form-item>
      <el-form-item label="区域">
        <el-select v-model="filters.areaId" clearable filterable style="width: 140px">
          <el-option
            v-for="item in areaOptions"
            :key="String(item.id)"
            :label="String(item.areaName || item.id)"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="userName" label="用户名" min-width="120" />
      <el-table-column prop="companyName" label="企业名称" min-width="160" />
      <el-table-column prop="areaName" label="区域" width="120" />
      <el-table-column prop="addressLabel" label="注册地址" min-width="140" show-overflow-tooltip />
      <el-table-column prop="trueName" label="联系人" width="100" />
      <el-table-column prop="mobile" label="联系电话" min-width="120" />
      <el-table-column prop="companyCode" label="公司代码" min-width="120" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="680px" destroy-on-close>
      <el-form label-width="140px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.userName" :disabled="!!editingId" maxlength="20" />
        </el-form-item>
        <el-form-item label="企业名称" required>
          <el-input v-model="form.companyName" />
        </el-form-item>
        <el-form-item label="区域" required>
          <el-select v-model="form.areaInfo" filterable placeholder="--请选择区域--" style="width: 100%">
            <el-option
              v-for="item in areaOptions"
              :key="String(item.id)"
              :label="String(item.areaName || item.id)"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="详细地址：省(市)" required>
          <el-select
            v-model="form.province"
            filterable
            placeholder="--请选择省（市）--"
            style="width: 100%"
            @change="onProvinceChange"
          >
            <el-option
              v-for="item in provinceOptions"
              :key="String(item.id)"
              :label="String(item.disName)"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="市" required>
          <el-select
            v-model="form.city"
            filterable
            placeholder="--选择市--"
            style="width: 100%"
            @change="onCityChange"
          >
            <el-option
              v-for="item in cityOptions"
              :key="String(item.id)"
              :label="String(item.disName)"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="县(区)" required>
          <el-select
            v-model="form.address"
            filterable
            placeholder="--请选择县（区）--"
            style="width: 100%"
            @change="onAddressChange"
          >
            <el-option
              v-for="item in districtOptions"
              :key="String(item.id)"
              :label="String(item.disName)"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人" required>
          <el-input v-model="form.trueName" />
        </el-form-item>
        <el-form-item label="联系电话" required>
          <el-input v-model="form.mobile" placeholder="座机格式例如: 010-9999999" />
        </el-form-item>
        <el-form-item label="公司代码" required>
          <el-input v-model="form.companyCode" placeholder="公司代码格式 ARXXX" maxlength="5" />
        </el-form-item>
        <el-form-item label="公司坐标" required>
          <el-input v-model="form.companyCoord" placeholder="坐标格式: 120.400599,36.11" />
          <div class="coord-link">
            <a href="http://api.map.baidu.com/lbsapi/getpoint/index.html" target="_blank" rel="noopener">
              百度地图坐标系统
            </a>
          </div>
        </el-form-item>
        <el-form-item label="关联账号" required>
          <el-select
            v-model="form.syuserId"
            filterable
            clearable
            :loading="userLoading"
            placeholder="请选择"
            style="width: 100%"
          >
            <el-option
              v-for="item in userOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { fetchDistrictOptions, type DistrictOption } from '@admin/api/member'
import {
  deleteSupplier,
  fetchAreaOptions,
  fetchSupplierList,
  fetchUserList,
  getSupplierById,
  saveSupplier,
} from '@admin/api/system'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const filters = reactive({
  userName: '',
  companyName: '',
  trueName: '',
  mobile: '',
  areaId: '',
})
const areaOptions = ref<Record<string, unknown>[]>([])
const provinceOptions = ref<DistrictOption[]>([])
const cityOptions = ref<DistrictOption[]>([])
const districtOptions = ref<DistrictOption[]>([])
const userOptions = ref<{ value: string; label: string }[]>([])
const userLoading = ref(false)

const { loading, rows, total, pagination, load } = useDataTable(fetchSupplierList)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  userName: '',
  companyName: '',
  areaInfo: '',
  province: '',
  city: '',
  address: '',
  addressInfo: '',
  trueName: '',
  mobile: '',
  companyCode: '',
  companyCoord: '',
  syuserId: '',
})

const dialogTitle = computed(() => (editingId.value ? '编辑所属公司' : '新增所属公司'))

onMounted(async () => {
  areaOptions.value = await fetchAreaOptions()
  provinceOptions.value = await fetchDistrictOptions(-1)
  await loadUserOptions()
  await reload()
})

async function loadUserOptions() {
  userLoading.value = true
  try {
    const res = await fetchUserList(
      { start: 0, length: 1000, type: -1, draw: 1 },
      { silentError: true }
    )
    const list = Array.isArray(res.data) ? res.data : []
    userOptions.value = list
      .map((u) => {
        const id = String(u.id ?? u.userId ?? '')
        const name = String(u.userName || u.user_name || '')
        const trueName = String(u.trueName || u.true_name || '')
        const label = trueName ? `${name}（${trueName}）` : name || id
        return { value: id, label }
      })
      .filter((o) => o.value)
  } catch {
    userOptions.value = []
  } finally {
    userLoading.value = false
  }
}

function reload() {
  return load({
    userName: filters.userName.trim(),
    company_name: filters.companyName.trim(),
    trueName: filters.trueName.trim(),
    mobile: filters.mobile.trim(),
    areaId: filters.areaId,
  })
}

function resetForm() {
  editingId.value = null
  form.userName = ''
  form.companyName = ''
  form.areaInfo = ''
  form.province = ''
  form.city = ''
  form.address = ''
  form.addressInfo = ''
  form.trueName = ''
  form.mobile = ''
  form.companyCode = ''
  form.companyCoord = ''
  form.syuserId = ''
  cityOptions.value = []
  districtOptions.value = []
}

function districtName(list: DistrictOption[], id: string) {
  const hit = list.find((d) => String(d.id) === String(id))
  return hit ? String(hit.disName || '') : ''
}

function syncAddressInfo() {
  const p = districtName(provinceOptions.value, form.province)
  const c = districtName(cityOptions.value, form.city)
  const a = districtName(districtOptions.value, form.address)
  form.addressInfo = `${p}${c}${a}`
}

async function onProvinceChange() {
  form.city = ''
  form.address = ''
  districtOptions.value = []
  cityOptions.value = form.province ? await fetchDistrictOptions(form.province) : []
  syncAddressInfo()
}

async function onCityChange() {
  form.address = ''
  districtOptions.value = form.city ? await fetchDistrictOptions(form.city) : []
  syncAddressInfo()
}

function onAddressChange() {
  syncAddressInfo()
}

async function fillForm(data: Record<string, unknown>) {
  editingId.value = Number(data.id)
  form.userName = String(data.userName || '')
  form.companyName = String(data.companyName || data.company_name || '')
  form.areaInfo = data.areaInfo != null && data.areaInfo !== '' ? String(data.areaInfo) : ''
  form.trueName = String(data.trueName || '')
  form.mobile = String(data.mobile || '')
  form.companyCode = String(data.companyCode || data.company_code || '')
  form.companyCoord = String(data.companyCoord || data.company_coord || '')
  form.syuserId = String(data.syuserId || data.syuser_id || '')
  form.addressInfo = String(data.addressInfo || data.addreddInfo || data.address_info || '')

  const provinceId = data.province != null && data.province !== '' ? String(data.province) : ''
  const cityId = data.city != null && data.city !== '' ? String(data.city) : ''
  const addressId = data.address != null && data.address !== '' ? String(data.address) : ''

  form.province = provinceId
  cityOptions.value = provinceId ? await fetchDistrictOptions(provinceId) : []
  form.city = cityId
  districtOptions.value = cityId ? await fetchDistrictOptions(cityId) : []
  form.address = addressId
  if (!form.addressInfo) syncAddressInfo()

  if (form.syuserId && !userOptions.value.some((u) => u.value === form.syuserId)) {
    userOptions.value = [
      ...userOptions.value,
      { value: form.syuserId, label: form.syuserId },
    ]
  }
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  try {
    const res = await getSupplierById(String(row.id))
    if (isAjaxOk(res) && res.obj) {
      await fillForm(res.obj as Record<string, unknown>)
      dialogVisible.value = true
      return
    }
    ElMessage.warning(ajaxErrorMessage(res, '详情加载失败，已用列表数据打开编辑'))
    await fillForm(row)
    dialogVisible.value = true
  } catch (error) {
    ElMessage.warning(error instanceof Error ? error.message : '详情加载失败，已用列表数据打开编辑')
    await fillForm(row)
    dialogVisible.value = true
  }
}

function validate(): string | null {
  if (!form.userName.trim()) return '请填写用户名'
  if (!form.companyName.trim()) return '请填写企业名称'
  if (!form.areaInfo) return '请选择区域'
  if (!form.province) return '请选择省（市）'
  if (!form.city) return '请选择市'
  if (!form.address) return '请选择县（区）'
  if (!form.trueName.trim()) return '请填写联系人'
  if (!form.mobile.trim()) return '请填写联系电话'
  const mobile = form.mobile.trim()
  const isMobile = /^1[34578]\d{9}$/.test(mobile)
  const isPhone = /^([0-9]{3,4}-)?[0-9]{7,8}$/.test(mobile)
  if (!(isMobile || isPhone)) return '联系电话有误，请重填'
  if (!form.companyCode.trim()) return '请填写公司代码'
  if (form.companyCode.trim().length > 5) return '公司代码长度最大长度5'
  if (!/^[A-Z][A-Za-z0-9]{0,4}$/.test(form.companyCode.trim())) {
    return '只能输入大写字母和数字的组合'
  }
  if (!form.companyCoord.trim()) return '请填写公司坐标'
  if (!form.syuserId) return '请选择关联账号'
  return null
}

async function handleSubmit() {
  const err = validate()
  if (err) {
    ElMessage.warning(err)
    return
  }
  syncAddressInfo()
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      userName: form.userName.trim(),
      company_name: form.companyName.trim(),
      areaInfo: form.areaInfo,
      province: form.province,
      city: form.city,
      address: form.address,
      addreddInfo: form.addressInfo,
      addressInfo: form.addressInfo,
      trueName: form.trueName.trim(),
      mobile: form.mobile.trim(),
      company_code: form.companyCode.trim(),
      company_coord: form.companyCoord.trim(),
      syuser_id: form.syuserId,
    }
    if (editingId.value) {
      payload.id = editingId.value
    }
    const res = await saveSupplier(payload)
    if (isAjaxOk(res)) {
      ElMessage.success(res.resMsg || '保存成功')
      dialogVisible.value = false
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败，用户名或企业名称可能已存在'))
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除（禁用）该所属公司吗？', '提示', { type: 'warning' })
  const res = await deleteSupplier(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success(res.resMsg || '操作成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.coord-link {
  margin-top: 8px;
  a {
    color: #409eff;
  }
}
</style>
