<template>
  <admin-page-card title="个人会员管理">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="公司/学校">
        <el-input v-model="filters.company_name" clearable placeholder="公司/学校" style="width: 160px" />
      </el-form-item>
      <el-form-item label="姓名">
        <el-input v-model="filters.trueName" clearable placeholder="姓名" style="width: 140px" />
      </el-form-item>
      <el-form-item label="手机号">
        <el-input v-model="filters.mobile" clearable placeholder="手机号" style="width: 140px" />
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
      <el-button type="primary" @click="openCreate">新增个人信息</el-button>
      <el-button type="primary" :disabled="!selectedId" @click="focusDetail">查看明细</el-button>
      <el-button type="primary" :disabled="!selectedId" @click="openEditSelected">编辑</el-button>
      <el-button type="danger" :disabled="!selectedId" @click="handleDeleteSelected">删除</el-button>
    </div>

    <el-table
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
      <el-table-column label="公司/学校" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.company_name || row.companyName || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="trueName" label="姓名" width="110" />
      <el-table-column prop="mobile" label="手机号" width="130" />
      <el-table-column prop="province" label="省/市" width="110" show-overflow-tooltip />
      <el-table-column prop="city" label="城市" width="110" show-overflow-tooltip />
      <el-table-column prop="areaInfo" label="县/区" width="110" show-overflow-tooltip />
      <el-table-column prop="addreddInfo" label="地址" min-width="180" show-overflow-tooltip />
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
        <el-tab-pane label="开票明细" name="invoice" />
        <el-tab-pane label="付款明细" name="pay" />
        <el-tab-pane label="欠款明细" name="arrears" />
        <el-tab-pane label="还款明细" name="repay" />
        <el-tab-pane label="余额变更明细" name="balance" />
      </el-tabs>

      <div v-if="!selectedId" class="detail-empty">请先选择一条会员记录</div>

      <template v-else>
        <div v-if="activeTab === 'basic'" v-loading="basicLoading" class="basic-info">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="公司/学校" :span="2">
              {{ basicInfo.company_name || basicInfo.companyName || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="余额">{{ basicInfo.amount ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="姓名" :span="2">{{ basicInfo.trueName || '-' }}</el-descriptions-item>
            <el-descriptions-item label="欠款金额">{{ basicInfo.arrearAmount ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="地址" :span="3">{{ basicInfo.addreddInfo || '-' }}</el-descriptions-item>
            <el-descriptions-item label="国家">中国</el-descriptions-item>
            <el-descriptions-item label="省/市">{{ basicInfo.province || '-' }}</el-descriptions-item>
            <el-descriptions-item label="城市">{{ basicInfo.city || '-' }}</el-descriptions-item>
            <el-descriptions-item label="县/区">{{ basicInfo.areaInfo || '-' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ basicInfo.mobile || '-' }}</el-descriptions-item>
            <el-descriptions-item label="接受公众号消息">
              {{ Number(basicInfo.is_accept_message ?? basicInfo.isAcceptMessage) === 0 ? '是' : '否' }}
            </el-descriptions-item>
            <el-descriptions-item label="所属公司" :span="3">
              <template v-if="companyNames.length">
                <div v-for="(name, idx) in companyNames" :key="idx">{{ name }}</div>
              </template>
              <template v-else>-</template>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div v-else>
          <el-table v-loading="detailLoading" :data="detailRows" border stripe>
            <el-table-column type="index" label="#" width="50" />
            <el-table-column label="创建时间" min-width="160">
              <template #default="{ row }">{{ formatTime(row.addTime) }}</template>
            </el-table-column>
            <el-table-column
              v-if="activeTab === 'balance'"
              label="个人姓名"
              min-width="120"
              show-overflow-tooltip
            >
              <template #default="{ row }">{{ row.trueName || row.userName || '-' }}</template>
            </el-table-column>
            <el-table-column
              v-else
              :label="activeTab === 'invoice' || activeTab === 'arrears' ? '名称' : '个人姓名'"
              min-width="120"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                {{ row.userName || row.trueName || '-' }}
              </template>
            </el-table-column>
            <el-table-column v-if="activeTab === 'balance'" label="操作类型" width="100">
              <template #default="{ row }">{{ balanceTypeLabel(row) }}</template>
            </el-table-column>
            <el-table-column :label="detailAmountLabel" width="130">
              <template #default="{ row }">
                <template v-if="activeTab === 'balance'">
                  {{ Number(row.payType) === 1 ? '+' : '-' }}{{ row.money ?? '-' }}
                </template>
                <template v-else>
                  {{ row.money ?? row.receive_amount ?? '-' }}
                </template>
              </template>
            </el-table-column>
            <el-table-column label="关联订单" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.orderId || row.orderNum || row.order_id || row.rechargeNum || '-' }}
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑个人信息' : '新增个人信息'" width="680px">
      <el-form label-width="110px">
        <el-form-item label="公司/学校">
          <el-input v-model="form.company_name" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.trueName" />
        </el-form-item>
        <el-form-item label="手机号" required>
          <el-input v-model="form.mobile" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码">
          <el-input v-model="form.password" placeholder="默认 123456" />
        </el-form-item>
        <el-form-item label="电子邮件">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="身份证">
          <el-input v-model="form.idcard" />
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
        <el-form-item label="收货地址">
          <el-input v-model="form.addreddInfo" />
        </el-form-item>
        <el-form-item label="公众号消息">
          <el-radio-group v-model="form.is_accept_message">
            <el-radio :value="0">接受</el-radio>
            <el-radio :value="1">不接受</el-radio>
          </el-radio-group>
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
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  addMember,
  deleteMember,
  editMember,
  fetchDistrictOptions,
  fetchMemberList,
  fetchUserArrears,
  fetchUserBalanceLogs,
  fetchUserInvoices,
  fetchUserPayLogs,
  getMember,
  type DistrictOption,
} from '@admin/api/member'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type TabName = 'basic' | 'invoice' | 'pay' | 'arrears' | 'repay' | 'balance'

const filters = reactive({
  company_name: '',
  trueName: '',
  mobile: '',
  province: '',
  city: '',
  areaId: '',
})

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchMemberList({ ...params, ...filters })
)

const detailAnchor = ref<HTMLElement | null>(null)
const selectedId = ref('')
const selectedMobile = ref('')
const activeTab = ref<TabName>('basic')

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
  company_name: '',
  trueName: '',
  mobile: '',
  password: '123456',
  email: '',
  idcard: '',
  provinceId: '',
  cityId: '',
  areaId: '',
  addreddInfo: '',
  is_accept_message: 0,
  userType: 1,
})

const basicLoading = ref(false)
const basicInfo = reactive<Record<string, unknown>>({})
const detailLoading = ref(false)
const detailRows = ref<Record<string, unknown>[]>([])
const detailTotal = ref(0)
const detailPagination = reactive({ page: 1, pageSize: 10 })

const detailAmountLabel = computed(() => {
  if (activeTab.value === 'invoice') return '开票金额'
  if (activeTab.value === 'pay') return '付款金额'
  if (activeTab.value === 'arrears') return '欠款金额'
  if (activeTab.value === 'repay') return '还款金额'
  if (activeTab.value === 'balance') return '余额变更金额'
  return '金额'
})

const companyNames = computed(() => {
  const list = basicInfo.companyList
  if (!Array.isArray(list)) return [] as string[]
  return list
    .map((item) => String((item as Record<string, unknown>)?.name || ''))
    .filter(Boolean)
})

function formatTime(value: unknown) {
  if (value == null || value === '') return '-'
  if (typeof value === 'number') {
    const ms = value < 1e12 ? value * 1000 : value
    return new Date(ms).toLocaleString()
  }
  return String(value)
}

function balanceTypeLabel(row: Record<string, unknown>) {
  const payType = Number(row.payType)
  const payWay = Number(row.payWay)
  if (payType === 1) return payWay === 7 ? '赠送' : '充值'
  if (payType === 2 || payType === 3) return '支付'
  if (payType === 4) return '提现'
  return '-'
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
  selectedMobile.value = String(row.mobile || '')
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
    ElMessage.warning('请先选择会员')
    return
  }
  detailAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  loadDetailTab()
}

async function loadDistrictRoots() {
  provinceOptions.value = await fetchDistrictOptions(-1)
  formProvinceOptions.value = provinceOptions.value
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
  form.company_name = ''
  form.trueName = ''
  form.mobile = ''
  form.password = '123456'
  form.email = ''
  form.idcard = ''
  form.provinceId = ''
  form.cityId = ''
  form.areaId = ''
  form.addreddInfo = ''
  form.is_accept_message = 0
  form.userType = 1
  formCityOptions.value = []
  formAreaOptions.value = []
}

function openCreate() {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

async function handleDeleteSelected() {
  if (!selectedId.value) {
    ElMessage.warning('请先选择会员')
    return
  }
  await ElMessageBox.confirm(
    '删除后该个人会员将从列表中回收（软删除），确定继续？',
    '提示',
    { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' },
  )
  const res = await deleteMember(selectedId.value)
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    selectedId.value = ''
    selectedMobile.value = ''
    Object.keys(basicInfo).forEach((k) => delete basicInfo[k])
    detailRows.value = []
    detailTotal.value = 0
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

async function openEditSelected() {
  if (!selectedId.value) {
    ElMessage.warning('请先选择会员')
    return
  }
  const res = await getMember(selectedId.value)
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const row = res.obj as Record<string, unknown>
  resetForm()
  form.id = String(row.id || '')
  form.company_name = String(row.company_name || row.companyName || '')
  form.trueName = String(row.trueName || '')
  form.mobile = String(row.mobile || '')
  form.email = String(row.email || '')
  form.idcard = String(row.idcard || '')
  form.provinceId = row.provinceId != null ? String(row.provinceId) : ''
  form.cityId = row.cityId != null ? String(row.cityId) : ''
  form.areaId = row.areaId != null ? String(row.areaId) : ''
  form.addreddInfo = String(row.addreddInfo || '')
  form.is_accept_message = Number(row.is_accept_message ?? row.isAcceptMessage ?? 0)
  form.userType = Number(row.userType || 1)
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
  if (!form.trueName.trim() || !form.mobile.trim()) {
    ElMessage.warning('请填写姓名和手机号')
    return
  }
  if (!/^1\d{10}$/.test(form.mobile.trim())) {
    ElMessage.warning('手机号格式不正确，请输入 11 位手机号')
    return
  }
  saving.value = true
  try {
    const payload = {
      id: form.id || undefined,
      company_name: form.company_name,
      trueName: form.trueName.trim(),
      mobile: form.mobile.trim(),
      password: form.password,
      email: form.email,
      idcard: form.idcard,
      areaId: form.areaId || undefined,
      addreddInfo: form.addreddInfo,
      is_accept_message: form.is_accept_message,
      userType: 1,
    }
    const res = isEdit.value ? await editMember(payload) : await addMember(payload)
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

async function loadBasicInfo() {
  if (!selectedId.value) return
  basicLoading.value = true
  try {
    const res = await getMember(selectedId.value)
    if (isAjaxOk(res) && res.obj) {
      Object.keys(basicInfo).forEach((k) => delete basicInfo[k])
      Object.assign(basicInfo, res.obj as Record<string, unknown>)
    } else {
      Object.keys(basicInfo).forEach((k) => delete basicInfo[k])
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
  try {
    const start = (detailPagination.page - 1) * detailPagination.pageSize
    const base = {
      draw: detailPagination.page,
      start,
      length: detailPagination.pageSize,
      user_id: selectedId.value,
      mobile: selectedMobile.value,
    }
    let res
    if (activeTab.value === 'invoice') {
      res = await fetchUserInvoices(base)
    } else if (activeTab.value === 'pay') {
      res = await fetchUserPayLogs({ ...base, pay_type: 3 })
    } else if (activeTab.value === 'repay') {
      res = await fetchUserPayLogs({ ...base, pay_type: 2 })
    } else if (activeTab.value === 'arrears') {
      res = await fetchUserArrears(base)
    } else {
      res = await fetchUserBalanceLogs(base)
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
