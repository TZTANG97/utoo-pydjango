<template>
  <admin-page-card title="企业会员管理">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="企业名称">
        <el-input v-model="filters.name" clearable placeholder="企业名称" style="width: 160px" />
      </el-form-item>
      <el-form-item label="国家">
        <el-select
          v-model="filters.country"
          clearable
          filterable
          placeholder="国家"
          style="width: 140px"
          @change="onFilterCountryChange"
        >
          <el-option
            v-for="item in countryOptions"
            :key="String(item.id)"
            :label="item.disName"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="省/市">
        <el-select
          v-model="filters.province"
          clearable
          filterable
          placeholder="省/市"
          style="width: 140px"
          @change="onFilterProvinceChange"
        >
          <el-option
            v-for="item in provinceOptions"
            :key="String(item.id)"
            :label="item.disName"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="城市">
        <el-select
          v-model="filters.city"
          clearable
          filterable
          placeholder="城市"
          style="width: 140px"
          @change="onFilterCityChange"
        >
          <el-option
            v-for="item in cityOptions"
            :key="String(item.id)"
            :label="item.disName"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="县/区">
        <el-select
          v-model="filters.areaId"
          clearable
          filterable
          placeholder="县/区"
          style="width: 140px"
        >
          <el-option
            v-for="item in areaOptions"
            :key="String(item.id)"
            :label="item.disName"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </el-form-item>
    </el-form>

    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新增公司信息</el-button>
      <el-button type="primary" :disabled="!selectedId" @click="focusDetail">查看明细</el-button>
      <el-button type="primary" :disabled="!selectedId" @click="openEditSelected">编辑</el-button>
      <el-button type="danger" :disabled="!selectedId" @click="handleDeleteSelected">删除</el-button>
    </div>

    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="rows"
      border
      stripe
      highlight-current-row
      @current-change="onCurrentChange"
      @row-click="onRowClick"
    >
      <el-table-column width="48" align="center">
        <template #default="{ row }">
          <el-radio :model-value="selectedId" :value="String(row.id)" @change="selectRow(row)">
            &nbsp;
          </el-radio>
        </template>
      </el-table-column>
      <el-table-column prop="id" label="ID" width="90" />
      <el-table-column prop="name" label="公司名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="country" label="国家" width="100" show-overflow-tooltip />
      <el-table-column prop="province" label="省" width="110" show-overflow-tooltip />
      <el-table-column prop="city" label="市" width="110" show-overflow-tooltip />
      <el-table-column prop="areaId" label="县区" width="110" show-overflow-tooltip />
      <el-table-column prop="address" label="详细地址" min-width="180" show-overflow-tooltip />
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, sizes, prev, pager, next"
        :page-sizes="[10, 20, 50]"
        :total="total"
        @current-change="reload()"
        @size-change="onPageSizeChange"
      />
    </div>

    <div ref="detailAnchor" class="detail-panel">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="基本信息" name="basic" />
        <el-tab-pane label="联系人" name="contacts" />
        <el-tab-pane label="开票明细" name="invoice" />
        <el-tab-pane label="付款明细" name="pay" />
        <el-tab-pane label="欠款明细" name="arrears" />
        <el-tab-pane label="还款明细" name="repay" />
        <el-tab-pane label="余额变更明细" name="balance" />
      </el-tabs>

      <div v-if="!selectedId" class="detail-empty">请先选择一条企业记录</div>

      <template v-else>
        <div v-if="activeTab === 'basic'" v-loading="basicLoading" class="basic-info">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="公司ID">{{ displayField(basicInfo.id) }}</el-descriptions-item>
            <el-descriptions-item label="开票付款信息" :span="2">{{ '' }}</el-descriptions-item>
            <el-descriptions-item label="公司名称" :span="2">{{ displayField(basicInfo.name) }}</el-descriptions-item>
            <el-descriptions-item label="公司名称">{{ displayField(basicInfo.name) }}</el-descriptions-item>
            <el-descriptions-item label="公司地址" :span="2">{{ displayField(basicInfo.address) }}</el-descriptions-item>
            <el-descriptions-item label="统一社会信用代码">{{ displayField(basicInfo.taxNum) }}</el-descriptions-item>
            <el-descriptions-item label="国家">{{ displayField(basicInfo.country) }}</el-descriptions-item>
            <el-descriptions-item label="省/市">{{ displayField(basicInfo.province) }}</el-descriptions-item>
            <el-descriptions-item label="开户银行">{{ displayField(basicInfo.bank) }}</el-descriptions-item>
            <el-descriptions-item label="城市">{{ displayField(basicInfo.city) }}</el-descriptions-item>
            <el-descriptions-item label="县/区">{{ displayField(basicInfo.areaId) }}</el-descriptions-item>
            <el-descriptions-item label="银行账号">{{ displayField(basicInfo.bankCardNum) }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div v-else-if="activeTab === 'contacts'">
          <div class="sub-toolbar">
            <el-button type="primary" @click="openContactCreate">新增联系人信息</el-button>
            <el-button type="primary" :disabled="!selectedContactId" @click="openContactEdit">编辑</el-button>
            <el-button type="danger" :disabled="!selectedContactId" @click="handleContactUnbind">删除</el-button>
          </div>
          <el-table
            v-loading="detailLoading"
            :data="detailRows"
            border
            stripe
            highlight-current-row
            @current-change="onContactCurrentChange"
          >
            <el-table-column width="48" align="center">
              <template #default="{ row }">
                <el-radio
                  :model-value="selectedContactId"
                  :value="String(row.id)"
                  @change="selectedContactId = String(row.id)"
                >
                  &nbsp;
                </el-radio>
              </template>
            </el-table-column>
            <el-table-column prop="trueName" label="姓名" width="100" />
            <el-table-column label="企业名称" min-width="140" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.company_name || row.companyName || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="dept" label="部门" width="100" />
            <el-table-column prop="job" label="职位" width="100" />
            <el-table-column prop="telephone" label="座机" width="110" />
            <el-table-column prop="extension" label="分机" width="80" />
            <el-table-column prop="mobile" label="手机号" width="120" />
            <el-table-column prop="email" label="邮箱" min-width="140" show-overflow-tooltip />
            <el-table-column prop="zipCode" label="邮编" width="90" />
            <el-table-column prop="addreddInfo" label="邮寄地址" min-width="160" show-overflow-tooltip />
          </el-table>
          <div class="pager">
            <el-pagination
              v-model:current-page="detailPagination.page"
              v-model:page-size="detailPagination.pageSize"
              layout="total, prev, pager, next"
              :total="detailTotal"
              @current-change="loadDetailTab()"
            />
          </div>
        </div>

        <div v-else>
          <el-table v-loading="detailLoading" :data="detailRows" border stripe>
            <el-table-column type="index" label="#" width="50" />
            <el-table-column label="创建时间" min-width="160">
              <template #default="{ row }">{{ formatTime(row.addTime) }}</template>
            </el-table-column>
            <el-table-column :label="detailNameLabel" min-width="140" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.companyName || row.trueName || row.userName || '-' }}
              </template>
            </el-table-column>
            <el-table-column :label="detailAmountLabel" width="120">
              <template #default="{ row }">
                {{ row.money ?? row.receive_amount ?? '-' }}
              </template>
            </el-table-column>
            <el-table-column label="关联订单" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.orderId || row.orderNum || row.order_id || '-' }}
              </template>
            </el-table-column>
          </el-table>
          <div class="pager">
            <el-pagination
              v-model:current-page="detailPagination.page"
              v-model:page-size="detailPagination.pageSize"
              layout="total, prev, pager, next"
              :total="detailTotal"
              @current-change="loadDetailTab()"
            />
          </div>
        </div>
      </template>
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑公司信息' : '新增公司信息'" width="720px">
      <el-form label-width="120px">
        <el-form-item label="企业名称" required>
          <el-input v-model="form.name" />
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
              v-for="item in countryOptions"
              :key="String(item.id)"
              :label="item.disName"
              :value="String(item.id)"
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
              v-for="item in formProvinceOptions"
              :key="String(item.id)"
              :label="item.disName"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="城市">
          <el-select
            v-model="form.cityId"
            clearable
            filterable
            style="width: 100%"
            @change="onFormCityChange"
          >
            <el-option
              v-for="item in formCityOptions"
              :key="String(item.id)"
              :label="item.disName"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="县/区">
          <el-select v-model="form.areaId" clearable filterable style="width: 100%">
            <el-option
              v-for="item in formAreaOptions"
              :key="String(item.id)"
              :label="item.disName"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="详细地址">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.contractPhone" />
        </el-form-item>
        <el-divider content-position="left">开票付款信息</el-divider>
        <el-form-item label="纳税人识别号">
          <el-input v-model="form.taxNum" />
        </el-form-item>
        <el-form-item label="开户银行">
          <el-input v-model="form.bank" />
        </el-form-item>
        <el-form-item label="银行账号">
          <el-input v-model="form.bankCardNum" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="contactDialogVisible"
      :title="contactIsEdit ? '编辑联系人' : '新增联系人'"
      width="640px"
    >
      <el-form label-width="110px">
        <el-form-item label="企业名称">
          <el-input v-model="contactForm.company_name" disabled />
        </el-form-item>
        <el-form-item label="联系人姓名" required>
          <el-input v-model="contactForm.trueName" />
        </el-form-item>
        <el-form-item v-if="!contactIsEdit" label="密码">
          <el-input v-model="contactForm.password" placeholder="默认 123456" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="contactForm.dept" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="contactForm.job" />
        </el-form-item>
        <el-form-item label="座机">
          <el-input v-model="contactForm.telephone" />
        </el-form-item>
        <el-form-item label="分机">
          <el-input v-model="contactForm.extension" />
        </el-form-item>
        <el-form-item label="手机号" required>
          <el-input v-model="contactForm.mobile" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="contactForm.email" />
        </el-form-item>
        <el-form-item label="邮编">
          <el-input v-model="contactForm.zipCode" />
        </el-form-item>
        <el-form-item label="邮寄地址">
          <el-input v-model="contactForm.addreddInfo" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="contactDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="contactSaving" @click="handleContactSubmit">保存</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  addCompanyContact,
  deleteEnterprise,
  editCompanyContact,
  fetchCompanyArrears,
  fetchCompanyBalanceLogs,
  fetchCompanyContacts,
  fetchCompanyInvoices,
  fetchCompanyPayLogs,
  fetchDistrictOptions,
  fetchEnterpriseList,
  getEnterprise,
  getEnterpriseDetail,
  getMember,
  saveEnterprise,
  type DistrictOption,
  unbindCompanyContact,
  updateEnterprise,
} from '@admin/api/member'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type TabName = 'basic' | 'contacts' | 'invoice' | 'pay' | 'arrears' | 'repay' | 'balance'

const filters = reactive({
  name: '',
  country: '',
  province: '',
  city: '',
  areaId: '',
})

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchEnterpriseList({ ...params, ...filters })
)

const tableRef = ref()
const detailAnchor = ref<HTMLElement | null>(null)
const selectedId = ref('')
const selectedName = ref('')
const activeTab = ref<TabName>('basic')

const countryOptions = ref<DistrictOption[]>([])
const provinceOptions = ref<DistrictOption[]>([])
const cityOptions = ref<DistrictOption[]>([])
const areaOptions = ref<DistrictOption[]>([])

const formProvinceOptions = ref<DistrictOption[]>([])
const formCityOptions = ref<DistrictOption[]>([])
const formAreaOptions = ref<DistrictOption[]>([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const form = reactive({
  id: '',
  name: '',
  country: '',
  provinceId: '',
  cityId: '',
  areaId: '',
  address: '',
  contractPhone: '',
  taxNum: '',
  bank: '',
  bankCardNum: '',
  type: 3,
})

const basicLoading = ref(false)
const basicInfo = reactive<Record<string, unknown>>({})
const detailLoading = ref(false)
const detailRows = ref<Record<string, unknown>[]>([])
const detailTotal = ref(0)
const detailPagination = reactive({ page: 1, pageSize: 10 })
const selectedContactId = ref('')

const contactDialogVisible = ref(false)
const contactIsEdit = ref(false)
const contactSaving = ref(false)
const contactForm = reactive({
  id: '',
  company_name: '',
  trueName: '',
  password: '123456',
  dept: '',
  job: '',
  telephone: '',
  extension: '',
  mobile: '',
  email: '',
  zipCode: '',
  addreddInfo: '',
  parent_id: '',
  userType: 2,
})

const detailNameLabel = computed(() => '企业名称')
const detailAmountLabel = computed(() => {
  if (activeTab.value === 'invoice') return '开票金额'
  if (activeTab.value === 'pay') return '付款金额'
  if (activeTab.value === 'arrears') return '欠款金额'
  if (activeTab.value === 'repay') return '还款金额'
  if (activeTab.value === 'balance') return '余额变更金额'
  return '金额'
})

function formatTime(value: unknown) {
  if (value == null || value === '') return '-'
  if (typeof value === 'number') {
    const ms = value < 1e12 ? value * 1000 : value
    return new Date(ms).toLocaleString()
  }
  return String(value)
}

function displayField(value: unknown) {
  if (value == null || value === '') return '-'
  return String(value)
}

function clearBasicInfo() {
  Object.keys(basicInfo).forEach((k) => delete basicInfo[k])
}

async function reload() {
  return load()
}

function handleSearch() {
  pagination.page = 1
  return reload()
}

function onPageSizeChange() {
  pagination.page = 1
  return reload()
}

function selectRow(row: Record<string, unknown>) {
  selectedId.value = String(row.id || '')
  selectedName.value = String(row.name || '')
  selectedContactId.value = ''
  detailPagination.page = 1
  loadDetailTab()
}

function onCurrentChange(row: Record<string, unknown> | null) {
  if (!row) return
  selectRow(row)
}

function onRowClick(row: Record<string, unknown>) {
  selectRow(row)
}

function focusDetail() {
  if (!selectedId.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  detailAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  loadDetailTab()
}

async function loadDistrictRoots() {
  countryOptions.value = await fetchDistrictOptions(0)
  provinceOptions.value = await fetchDistrictOptions(-1)
  formProvinceOptions.value = provinceOptions.value
}

async function onFilterCountryChange(val: string) {
  filters.province = ''
  filters.city = ''
  filters.areaId = ''
  cityOptions.value = []
  areaOptions.value = []
  // Java：选国家后省列表按 country 的子节点加载；未选时回退 type=1 全省
  provinceOptions.value = await fetchDistrictOptions(val || -1)
}

async function onFilterProvinceChange(val: string) {
  filters.city = ''
  filters.areaId = ''
  areaOptions.value = []
  cityOptions.value = val ? await fetchDistrictOptions(val) : []
}

async function onFilterCityChange(val: string) {
  filters.areaId = ''
  areaOptions.value = val ? await fetchDistrictOptions(val) : []
}

async function onFormCountryChange(val: string) {
  form.provinceId = ''
  form.cityId = ''
  form.areaId = ''
  formCityOptions.value = []
  formAreaOptions.value = []
  formProvinceOptions.value = await fetchDistrictOptions(val || -1)
}

async function onFormProvinceChange(val: string) {
  form.cityId = ''
  form.areaId = ''
  formAreaOptions.value = []
  formCityOptions.value = val ? await fetchDistrictOptions(val) : []
}

async function onFormCityChange(val: string) {
  form.areaId = ''
  formAreaOptions.value = val ? await fetchDistrictOptions(val) : []
}

function resetForm() {
  form.id = ''
  form.name = ''
  form.country = ''
  form.provinceId = ''
  form.cityId = ''
  form.areaId = ''
  form.address = ''
  form.contractPhone = ''
  form.taxNum = ''
  form.bank = ''
  form.bankCardNum = ''
  form.type = 3
  formCityOptions.value = []
  formAreaOptions.value = []
}

function openCreate() {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

async function openEditSelected() {
  if (!selectedId.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  const res = await getEnterprise(selectedId.value)
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const row = res.obj as Record<string, unknown>
  resetForm()
  form.id = String(row.id || '')
  form.name = String(row.name || '')
  form.country = row.country != null ? String(row.country) : ''
  form.provinceId = row.provinceId != null ? String(row.provinceId) : ''
  form.cityId = row.cityId != null ? String(row.cityId) : ''
  form.areaId = row.areaId != null ? String(row.areaId) : ''
  form.address = String(row.address || '')
  form.contractPhone = String(row.contractPhone || '')
  form.taxNum = String(row.taxNum || '')
  form.bank = String(row.bank || '')
  form.bankCardNum = String(row.bankCardNum || '')
  form.type = Number(row.type || 3)
  if (form.provinceId) {
    formCityOptions.value = await fetchDistrictOptions(form.provinceId)
  }
  if (form.cityId) {
    formAreaOptions.value = await fetchDistrictOptions(form.cityId)
  }
  isEdit.value = true
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写企业名称')
    return
  }
  saving.value = true
  try {
    const payload = {
      id: form.id || undefined,
      name: form.name.trim(),
      country: form.country || undefined,
      areaId: form.areaId || undefined,
      address: form.address,
      contractPhone: form.contractPhone,
      taxNum: form.taxNum,
      bank: form.bank,
      bankCardNum: form.bankCardNum,
      type: 3,
    }
    const res = isEdit.value ? await updateEnterprise(payload) : await saveEnterprise(payload)
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function handleDeleteSelected() {
  if (!selectedId.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  await ElMessageBox.confirm('删除将解绑关联联系人，确定继续？', '提示', { type: 'warning' })
  const res = await deleteEnterprise(selectedId.value)
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    selectedId.value = ''
    selectedName.value = ''
    Object.keys(basicInfo).forEach((k) => delete basicInfo[k])
    detailRows.value = []
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

async function loadBasicInfo() {
  if (!selectedId.value) return
  basicLoading.value = true
  try {
    const res = await getEnterpriseDetail(selectedId.value)
    clearBasicInfo()
    if (isAjaxOk(res) && res.obj && typeof res.obj === 'object') {
      Object.assign(basicInfo, res.obj as Record<string, unknown>)
    } else {
      ElMessage.error(ajaxErrorMessage(res, '加载基本信息失败'))
    }
  } finally {
    basicLoading.value = false
  }
}

async function loadDetailTab() {
  if (!selectedId.value) return
  if (activeTab.value === 'basic') {
    await loadBasicInfo()
    return
  }
  detailLoading.value = true
  selectedContactId.value = ''
  try {
    const start = (detailPagination.page - 1) * detailPagination.pageSize
    const base = {
      draw: detailPagination.page,
      start,
      length: detailPagination.pageSize,
      company_id: selectedId.value,
      parent_id: selectedId.value,
    }
    let res
    if (activeTab.value === 'contacts') {
      res = await fetchCompanyContacts(base)
    } else if (activeTab.value === 'invoice') {
      res = await fetchCompanyInvoices(base)
    } else if (activeTab.value === 'pay') {
      res = await fetchCompanyPayLogs({ ...base, pay_type: 3 })
    } else if (activeTab.value === 'repay') {
      res = await fetchCompanyPayLogs({ ...base, pay_type: 2 })
    } else if (activeTab.value === 'arrears') {
      res = await fetchCompanyArrears(base)
    } else {
      res = await fetchCompanyBalanceLogs(base)
    }
    detailRows.value = Array.isArray(res.data) ? res.data : []
    detailTotal.value = Number(res.recordsTotal || 0)
  } finally {
    detailLoading.value = false
  }
}

function onTabChange() {
  detailPagination.page = 1
  loadDetailTab()
}

function onContactCurrentChange(row: Record<string, unknown> | null) {
  selectedContactId.value = row ? String(row.id || '') : ''
}

function resetContactForm() {
  contactForm.id = ''
  contactForm.company_name = selectedName.value
  contactForm.trueName = ''
  contactForm.password = '123456'
  contactForm.dept = ''
  contactForm.job = ''
  contactForm.telephone = ''
  contactForm.extension = ''
  contactForm.mobile = ''
  contactForm.email = ''
  contactForm.zipCode = ''
  contactForm.addreddInfo = ''
  contactForm.parent_id = selectedId.value
  contactForm.userType = 2
}

function openContactCreate() {
  if (!selectedId.value) {
    ElMessage.warning('请先选择企业')
    return
  }
  resetContactForm()
  contactIsEdit.value = false
  contactDialogVisible.value = true
}

async function openContactEdit() {
  if (!selectedContactId.value) {
    ElMessage.warning('请先选择联系人')
    return
  }
  const res = await getMember(selectedContactId.value)
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载联系人失败'))
    return
  }
  const row = res.obj as Record<string, unknown>
  contactForm.id = String(row.id || '')
  contactForm.company_name = String(row.companyName || selectedName.value || '')
  contactForm.trueName = String(row.trueName || '')
  contactForm.password = ''
  contactForm.dept = String(row.dept || '')
  contactForm.job = String(row.job || '')
  contactForm.telephone = String(row.telephone || '')
  contactForm.extension = String(row.extension || '')
  contactForm.mobile = String(row.mobile || '')
  contactForm.email = String(row.email || '')
  contactForm.zipCode = String(row.zipCode || '')
  contactForm.addreddInfo = String(row.addreddInfo || '')
  contactForm.parent_id = selectedId.value
  contactForm.userType = 2
  contactIsEdit.value = true
  contactDialogVisible.value = true
}

async function handleContactSubmit() {
  if (!contactForm.trueName.trim() || !contactForm.mobile.trim()) {
    ElMessage.warning('请填写姓名和手机号')
    return
  }
  contactSaving.value = true
  try {
    const payload = {
      ...contactForm,
      parent_id: selectedId.value,
      comId: selectedId.value,
      userType: 2,
    }
    const res = contactIsEdit.value
      ? await editCompanyContact(payload)
      : await addCompanyContact(payload)
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      contactDialogVisible.value = false
      await loadDetailTab()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } finally {
    contactSaving.value = false
  }
}

async function handleContactUnbind() {
  if (!selectedContactId.value) {
    ElMessage.warning('请先选择联系人')
    return
  }
  await ElMessageBox.confirm('确定解绑该联系人？', '提示', { type: 'warning' })
  const res = await unbindCompanyContact(selectedContactId.value)
  if (isAjaxOk(res)) {
    ElMessage.success('操作成功')
    selectedContactId.value = ''
    await loadDetailTab()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}

onMounted(async () => {
  await loadDistrictRoots()
  await reload()
  await nextTick()
})
</script>

<style scoped lang="scss">
.filter-form {
  margin-bottom: 8px;
}
.toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 12px;
}
.sub-toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 12px;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.detail-panel {
  margin-top: 20px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}
.detail-empty {
  color: var(--el-text-color-secondary);
  padding: 24px 0;
  text-align: center;
}
.basic-info {
  padding: 8px 0 16px;
}
</style>
