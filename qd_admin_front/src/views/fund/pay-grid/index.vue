<template>
  <admin-page-card :title="title">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item v-if="mode === 'company' || mode === 'loan'" :label="mode === 'company' ? '请选择所属公司' : '公司'">
        <el-select
          v-model="companyId"
          filterable
          clearable
          :placeholder="mode === 'company' ? '请选择' : '选择公司'"
          style="width: 220px"
          @change="onFilterChange"
        >
          <el-option v-if="mode === 'loan' || (mode === 'company' && isAdminViewOnly)" label="全部汇总" value="-1" />
          <el-option
            v-for="c in companies"
            :key="String(c.id)"
            :label="String(c.companyName || '')"
            :value="String(c.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item v-if="mode === 'personal'" label="选择用户">
        <el-select
          v-model="userId"
          filterable
          clearable
          placeholder="请选择"
          style="width: 220px"
          @change="onFilterChange"
        >
          <el-option v-if="isAdminViewOnly" label="全部汇总" value="-1" />
          <el-option
            v-for="u in users"
            :key="String(u.id)"
            :label="`${u.trueName || ''} (${u.userName || ''})`"
            :value="String(u.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item v-if="mode === 'project'" label="选择项目">
        <el-select
          v-model="projectUserId"
          filterable
          clearable
          placeholder="请选择"
          style="width: 180px"
          @change="onProjectUserChange"
        >
          <el-option
            v-for="u in projectUsers"
            :key="String(u.id)"
            :label="String(u.userName || u.user_name || '')"
            :value="String(u.id)"
          />
        </el-select>
        <el-select
          v-model="labId"
          filterable
          clearable
          placeholder="选择实验室"
          style="width: 200px; margin-left: 8px"
        >
          <el-option
            v-for="l in labs"
            :key="String(l.id)"
            :label="String(l.labName || l.lab_name || '')"
            :value="String(l.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="isFundPayMode ? '币种选择' : '币种'">
        <el-select v-model="accountType" style="width: 140px" @change="onFilterChange">
          <el-option :value="1" :label="isFundPayMode ? '人民币账户' : '人民币'" />
          <el-option :value="2" :label="isFundPayMode ? '美元账户' : '美金'" />
        </el-select>
      </el-form-item>
      <el-form-item :label="isFundPayMode ? '请选择年份' : '年份'">
        <el-date-picker
          v-model="year"
          type="year"
          value-format="YYYY"
          :placeholder="isFundPayMode ? '请选择' : undefined"
          style="width: 140px"
          @change="onFilterChange"
        />
      </el-form-item>
      <el-form-item v-if="!isFundPayMode">
        <el-button type="primary" :loading="loading" @click="loadRows">查询</el-button>
        <el-button
          v-if="!isOpsHidden"
          type="success"
          :loading="saving"
          :disabled="companyId === '-1'"
          @click="handleSave"
        >
          保存
        </el-button>
      </el-form-item>
    </el-form>

    <el-table
      v-loading="loading"
      :data="rows"
      border
      stripe
      :show-summary="isFundPayMode && rows.length > 0"
      :summary-method="fundSummary"
      empty-text="暂无数据"
    >
      <el-table-column label="月份" width="80" align="center">
        <template #default="{ row }">{{ formatMonth(row.month) }}</template>
      </el-table-column>
      <!-- 对齐 Java companyPayPag -->
      <template v-if="mode === 'company'">
        <el-table-column label="日常运营费用" min-width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.fees"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcCompanyRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="人员工资福利" min-width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.wages"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcCompanyRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="税费及财务费用" min-width="130">
          <template #default="{ row }">
            <el-input-number
              v-model="row.taxes"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcCompanyRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="系统费用" min-width="110">
          <template #default="{ row }">
            <el-input-number
              v-model="row.systemCost"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcCompanyRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="借贷款还款" min-width="110">
          <template #default="{ row }">
            <el-input-number
              v-model="row.loan"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcCompanyRow(row)"
            />
          </template>
        </el-table-column>
      </template>
      <template v-else-if="mode === 'personal'">
        <el-table-column label="工资福利" min-width="110">
          <template #default="{ row }">
            <el-input-number
              v-model="row.wages"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcPersonalRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="税费" min-width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.taxes"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcPersonalRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="贷款利息" min-width="110">
          <template #default="{ row }">
            <el-input-number
              v-model="row.loanInterest"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcPersonalRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="月末摊销购车款" min-width="130">
          <template #default="{ row }">
            <el-input-number
              v-model="row.carAmount"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcPersonalRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="个人订单费用" min-width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.orderAmount"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcPersonalRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="其他" min-width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.otherAmount"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcPersonalRow(row)"
            />
          </template>
        </el-table-column>
      </template>
      <template v-else-if="mode === 'loan'">
        <el-table-column label="还款本金" min-width="140">
          <template #default="{ row }">
            <el-input-number
              v-model="row.loan"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isOpsHidden || companyId === '-1' || Number(row.status) === 1"
              @change="recalcLoanRow(row)"
            />
          </template>
        </el-table-column>
      </template>
      <template v-else>
        <el-table-column label="租金" min-width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.rentFees"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcProjectRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="电费" min-width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.elecFees"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcProjectRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="人工" min-width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.laborFees"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcProjectRow(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="配件" min-width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.partsFees"
              :min="0"
              :precision="2"
              controls-position="right"
              size="small"
              :disabled="isRowLocked(row)"
              @change="recalcProjectRow(row)"
            />
          </template>
        </el-table-column>
      </template>
      <el-table-column label="支出总额" width="120" align="right">
        <template #default="{ row }">{{ formatMoney(row.payAmount) }}</template>
      </el-table-column>
      <el-table-column v-if="isFundPayMode" label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <template v-if="!isOpsHidden">
            <el-button
              type="success"
              size="small"
              :disabled="Number(row.status) === 1 || acting"
              @click="handleChargeBack(row)"
            >
              扣款
            </el-button>
            <el-button
              size="small"
              :disabled="Number(row.status) === 2 || !row.id || acting"
              @click="handleCorrect(row)"
            >
              修正
            </el-button>
          </template>
        </template>
      </el-table-column>
      <el-table-column v-else label="状态" width="80">
        <template #default="{ row }">{{ Number(row.status) === 1 ? '已扣' : '未扣' }}</template>
      </el-table-column>
    </el-table>

    <div v-if="isFundPayMode" class="company-footer">
      <el-button
        v-if="!isOpsHidden"
        type="warning"
        size="large"
        :loading="saving"
        :disabled="isSummarySelected"
        @click="handleSave"
      >
        保存
      </el-button>
      <p class="ops-tip">
        <template v-if="mode === 'company'">
          操作说明:1.请先选择所属公司 2.再选择操作年份 3.进行录入
          当出现错误提示对话框时请刷新页面重复如上步骤
        </template>
        <template v-else>
          操作说明:1.请先选择用户 2.再选择操作年份 3.进行录入
          当出现错误提示对话框时请刷新页面重复如上步骤
        </template>
      </p>
    </div>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { useUserStore } from '@/stores/user'
import {
  chargeBackCompanyPay,
  chargeBackUserPay,
  fetchCompanyLoanList,
  fetchCompanyOptions,
  fetchCompanyPayList,
  fetchProjectPayLabsByUser,
  fetchProjectPayList,
  fetchProjectPayUsers,
  fetchUserPayList,
  fetchUserPayOptions,
  saveCompanyLoan,
  saveCompanyPay,
  saveProjectPay,
  saveUserPay,
  updateCompanyPayStatus,
  updateUserPayStatus,
  isAjaxOk,
} from '@/api/fund'

const props = defineProps<{
  mode: 'company' | 'personal' | 'loan' | 'project'
  title: string
}>()

const userStore = useUserStore()
const isFundPayMode = computed(() => props.mode === 'company' || props.mode === 'personal')

/** 对齐 Java：登录名为 admin / 系统管理员角色 → 仅可查看 */
const isAdminViewOnly = computed(() => {
  const login = String(
    userStore.loginName ||
      userStore.welcome?.loginName ||
      (userStore.welcome as { currentUser?: string } | null)?.currentUser ||
      ''
  ).toLowerCase()
  const name = String(userStore.welcome?.userName || userStore.userName || '').toLowerCase()
  const role = String(userStore.welcome?.roleName || userStore.roleName || '')
  const t = Number(userStore.welcome?.userType ?? userStore.userType ?? 0)
  if (login === 'admin' || name === 'admin') return true
  if (t === 1) return true
  if (role.includes('系统管理员') || role.includes('超级管理员') || role.toUpperCase() === 'ADMIN') {
    return true
  }
  return false
})

/** 对齐 Java userPay userType=2（公司账号）才可录入 */
const isCompanyRole = computed(() => {
  const t = Number(userStore.welcome?.userType ?? userStore.userType ?? 0)
  const role = String(userStore.welcome?.roleName || userStore.roleName || '')
  if (t === 2) return true
  return role.includes('公司基金') || role.includes('公司账号') || role === '公司'
})

/**
 * 隐藏保存/扣款/修正：
 * - 各公司资金支出 / 借贷款 / 项目：admin 仅查看
 * - 个人资金支出：仅公司账号可录入（admin 及其他角色只读）
 */
const isOpsHidden = computed(() => {
  if (isAdminViewOnly.value) return true
  if (props.mode === 'personal') return !isCompanyRole.value
  return false
})

const isSummarySelected = computed(() => {
  if (props.mode === 'company' || props.mode === 'loan') return companyId.value === '-1'
  if (props.mode === 'personal') return userId.value === '-1'
  return false
})
const loading = ref(false)
const saving = ref(false)
const acting = ref(false)
/** 公司/个人资金支出对齐 Java：年份初始为空，选齐筛选项再拉表 */
const year = ref(isFundPayMode.value ? '' : String(new Date().getFullYear()))
const accountType = ref(1)
const companyId = ref('')
const userId = ref('')
const projectUserId = ref('')
const labId = ref('')
const companies = ref<Record<string, unknown>[]>([])
const users = ref<Record<string, unknown>[]>([])
const projectUsers = ref<Record<string, unknown>[]>([])
const labs = ref<Record<string, unknown>[]>([])
const rows = ref<Record<string, unknown>[]>([])

/** 对齐 Java addTable：进页即展示 01–12 月零值模板 */
function emptyCompanyRows(): Record<string, unknown>[] {
  return Array.from({ length: 12 }, (_, i) => ({
    id: 0,
    month: String(i + 1),
    fees: 0,
    wages: 0,
    taxes: 0,
    systemCost: 0,
    loan: 0,
    payAmount: 0,
    status: 2,
  }))
}

function emptyPersonalRows(): Record<string, unknown>[] {
  return Array.from({ length: 12 }, (_, i) => ({
    id: 0,
    month: String(i + 1),
    wages: 0,
    taxes: 0,
    loanInterest: 0,
    carAmount: 0,
    orderAmount: 0,
    otherAmount: 0,
    payAmount: 0,
    status: 2,
  }))
}

function emptyFundRows() {
  return props.mode === 'personal' ? emptyPersonalRows() : emptyCompanyRows()
}

onMounted(async () => {
  if (isFundPayMode.value) {
    rows.value = emptyFundRows()
  }
  if (props.mode === 'company' || props.mode === 'loan') {
    const res = await fetchCompanyOptions()
    if (isAjaxOk(res)) companies.value = (res.obj as Record<string, unknown>[]) || []
  }
  if (props.mode === 'personal') {
    const res = await fetchUserPayOptions()
    if (isAjaxOk(res)) users.value = (res.obj as Record<string, unknown>[]) || []
  }
  if (props.mode === 'project') {
    const res = await fetchProjectPayUsers()
    if (isAjaxOk(res)) projectUsers.value = (res.obj as Record<string, unknown>[]) || []
  }
})

async function onProjectUserChange() {
  labId.value = ''
  labs.value = []
  year.value = ''
  rows.value = []
  if (!projectUserId.value) return
  const res = await fetchProjectPayLabsByUser(projectUserId.value)
  if (isAjaxOk(res)) labs.value = (res.obj as Record<string, unknown>[]) || []
}

function formatMonth(m: unknown) {
  const n = Number(m)
  if (!Number.isFinite(n) || n <= 0) return String(m ?? '')
  return String(n).padStart(2, '0')
}

function formatMoney(v: unknown) {
  return Number(v || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function isRowLocked(row: Record<string, unknown>) {
  return isOpsHidden.value || isSummarySelected.value || Number(row.status) === 1
}

function recalcCompanyRow(row: Record<string, unknown>) {
  const total =
    Number(row.fees || 0) +
    Number(row.wages || 0) +
    Number(row.taxes || 0) +
    Number(row.systemCost || 0) +
    Number(row.loan || 0)
  row.payAmount = Math.round(total * 100) / 100
}

function recalcPersonalRow(row: Record<string, unknown>) {
  const total =
    Number(row.wages || 0) +
    Number(row.taxes || 0) +
    Number(row.loanInterest || 0) +
    Number(row.carAmount || 0) +
    Number(row.orderAmount || 0) +
    Number(row.otherAmount || 0)
  row.payAmount = Math.round(total * 100) / 100
}

function recalcProjectRow(row: Record<string, unknown>) {
  const total =
    Number(row.rentFees || 0) +
    Number(row.elecFees || 0) +
    Number(row.laborFees || 0) +
    Number(row.partsFees || 0)
  row.payAmount = Math.round(total * 100) / 100
}

function recalcLoanRow(row: Record<string, unknown>) {
  row.payAmount = Math.round(Number(row.loan || 0) * 100) / 100
}

function fundSummary({ columns, data }: { columns: { property?: string }[]; data: Record<string, unknown>[] }) {
  const sums: string[] = []
  const companyKeys: Record<number, string> = {
    1: 'fees',
    2: 'wages',
    3: 'taxes',
    4: 'systemCost',
    5: 'loan',
    6: 'payAmount',
  }
  const personalKeys: Record<number, string> = {
    1: 'wages',
    2: 'taxes',
    3: 'loanInterest',
    4: 'carAmount',
    5: 'orderAmount',
    6: 'otherAmount',
    7: 'payAmount',
  }
  const keyByIndex = props.mode === 'personal' ? personalKeys : companyKeys
  columns.forEach((col, index) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    const key = String(col.property || '') || keyByIndex[index]
    if (!key) {
      sums[index] = ''
      return
    }
    const total = data.reduce((acc, row) => acc + Number(row[key] || 0), 0)
    sums[index] = formatMoney(total)
  })
  return sums
}

function onFilterChange() {
  if (!isFundPayMode.value) return
  if (props.mode === 'company' && (!companyId.value || !year.value)) {
    rows.value = emptyCompanyRows()
    return
  }
  if (props.mode === 'personal' && (!userId.value || !year.value)) {
    rows.value = emptyPersonalRows()
    return
  }
  void loadRows()
}

async function loadRows() {
  if (!year.value) {
    ElMessage.warning(props.mode === 'company' ? '请选择年份' : '请选择年份')
    return
  }
  if ((props.mode === 'company' || props.mode === 'loan') && !companyId.value) {
    ElMessage.warning(props.mode === 'company' ? '请先选择所属公司' : '请选择公司')
    return
  }
  if (props.mode === 'personal' && !userId.value) {
    ElMessage.warning('请先选择用户')
    return
  }
  if (props.mode === 'project' && !projectUserId.value) {
    ElMessage.warning('请先选择项目')
    return
  }
  loading.value = true
  try {
    let res
    const common = { year: year.value, accountType: accountType.value }
    if (props.mode === 'company') {
      res = await fetchCompanyPayList({
        ...common,
        companyId: companyId.value,
        company_id: companyId.value,
        account_type: accountType.value,
      })
    } else if (props.mode === 'personal') {
      res = await fetchUserPayList({
        ...common,
        userId: userId.value,
        user_id: userId.value,
        account_type: accountType.value,
      })
    } else if (props.mode === 'loan') {
      res = await fetchCompanyLoanList({ ...common, companyId: companyId.value })
    } else {
      res = await fetchProjectPayList({
        ...common,
        userId: projectUserId.value,
        user_id: projectUserId.value,
        labId: labId.value,
        lab_id: labId.value,
        account_type: accountType.value,
      })
    }
    if (!isAjaxOk(res)) {
      ElMessage.error(String(res.msg || '加载失败'))
      if (isFundPayMode.value) rows.value = emptyFundRows()
      return
    }
    const list = (res.obj as Record<string, unknown>[]) || []
    if (isFundPayMode.value && !list.length) {
      rows.value = emptyFundRows()
      return
    }
    rows.value = list.map((r) => {
      const row = { ...r }
      if (props.mode === 'company') recalcCompanyRow(row)
      if (props.mode === 'personal') recalcPersonalRow(row)
      return row
    })
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (isOpsHidden.value) {
    ElMessage.warning('当前账号仅可查看，不可保存')
    return
  }
  if (isSummarySelected.value || companyId.value === '-1') {
    ElMessage.warning('汇总模式不可保存')
    return
  }
  if (props.mode === 'company') {
    if (!companyId.value) {
      ElMessage.warning('请先选择所属公司')
      return
    }
    if (!year.value) {
      ElMessage.warning('请选择年份')
      return
    }
  }
  if (props.mode === 'personal') {
    if (!userId.value) {
      ElMessage.warning('请先选择用户')
      return
    }
    if (!year.value) {
      ElMessage.warning('请选择年份')
      return
    }
  }
  if (props.mode === 'project') {
    if (!projectUserId.value) {
      ElMessage.warning('请先选择项目')
      return
    }
    if (!labId.value) {
      ElMessage.warning('请选择实验室')
      return
    }
    if (!year.value) {
      ElMessage.warning('请选择年份')
      return
    }
  }
  if (!rows.value.length) {
    ElMessage.warning(
      props.mode === 'company'
        ? '请先选择公司和年份'
        : props.mode === 'personal'
          ? '请先选择用户和年份'
          : props.mode === 'project'
            ? '请先选择项目和年份'
            : '请先查询'
    )
    return
  }
  saving.value = true
  try {
    const list = rows.value.map((r) => ({
      ...r,
      year: year.value,
      accountType: accountType.value,
      companyId: companyId.value,
      userId: props.mode === 'project' ? projectUserId.value : userId.value,
      labId: labId.value,
    }))
    let res
    if (props.mode === 'company') res = await saveCompanyPay(list)
    else if (props.mode === 'personal') res = await saveUserPay(list)
    else if (props.mode === 'loan') res = await saveCompanyLoan(list)
    else res = await saveProjectPay(list)
    if (!isAjaxOk(res)) {
      ElMessage.error(String(res.msg || '保存失败'))
      return
    }
    ElMessage.success('保存成功')
    await loadRows()
  } finally {
    saving.value = false
  }
}

async function handleChargeBack(row: Record<string, unknown>) {
  if (props.mode === 'company' && !companyId.value) {
    ElMessage.warning('请先选择所属公司')
    return
  }
  if (props.mode === 'personal' && !userId.value) {
    ElMessage.warning('请先选择用户')
    return
  }
  if (!year.value) {
    ElMessage.warning('请选择年份')
    return
  }
  try {
    await ElMessageBox.confirm('确定扣款操作?', '提示', { type: 'warning' })
  } catch {
    return
  }
  acting.value = true
  try {
    let res
    if (props.mode === 'personal') {
      res = await chargeBackUserPay({
        id: row.id || 0,
        userId: userId.value,
        user_id: userId.value,
        year: year.value,
        month: formatMonth(row.month),
        pay_amount: row.payAmount,
        taxes: row.taxes,
        wages: row.wages,
        loan_interest: row.loanInterest,
        car_amount: row.carAmount,
        order_amount: row.orderAmount,
        other_amount: row.otherAmount,
        accountType: accountType.value,
        account_type: accountType.value,
      })
    } else {
      res = await chargeBackCompanyPay({
        id: row.id || 0,
        companyId: companyId.value,
        company_id: companyId.value,
        year: year.value,
        month: formatMonth(row.month),
        pay_amount: row.payAmount,
        taxes: row.taxes,
        fees: row.fees,
        wages: row.wages,
        system_cost: row.systemCost,
        loan: row.loan,
        accountType: accountType.value,
        account_type: accountType.value,
      })
    }
    if (!isAjaxOk(res)) {
      ElMessage.error(String(res.msg || res.resMsg || '扣款失败'))
      return
    }
    ElMessage.success('操作成功')
    await loadRows()
  } finally {
    acting.value = false
  }
}

async function handleCorrect(row: Record<string, unknown>) {
  if (props.mode === 'company' && !companyId.value) {
    ElMessage.warning('请先选择所属公司')
    return
  }
  if (props.mode === 'personal' && !userId.value) {
    ElMessage.warning('请先选择用户')
    return
  }
  if (!year.value) {
    ElMessage.warning('请选择年份')
    return
  }
  if (!row.id) {
    ElMessage.warning('请保存后再重试')
    return
  }
  try {
    await ElMessageBox.confirm('确定修正操作?', '提示', { type: 'warning' })
  } catch {
    return
  }
  acting.value = true
  try {
    const res =
      props.mode === 'personal'
        ? await updateUserPayStatus({
            id: row.id,
            userId: userId.value,
            user_id: userId.value,
            year: year.value,
            month: formatMonth(row.month),
            pay_amount: row.payAmount,
            accountType: accountType.value,
            account_type: accountType.value,
          })
        : await updateCompanyPayStatus({
            id: row.id,
            companyId: companyId.value,
            company_id: companyId.value,
            year: year.value,
            month: formatMonth(row.month),
            pay_amount: row.payAmount,
            loan: row.loan,
            accountType: accountType.value,
            account_type: accountType.value,
          })
    if (!isAjaxOk(res)) {
      ElMessage.error(String(res.msg || res.resMsg || '修正失败'))
      return
    }
    ElMessage.success('操作成功')
    await loadRows()
  } finally {
    acting.value = false
  }
}
</script>

<style scoped>
.filter-form {
  margin-bottom: 12px;
}
.company-footer {
  margin-top: 28px;
  text-align: center;
}
.ops-tip {
  margin-top: 16px;
  text-align: left;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}
</style>
