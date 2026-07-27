<template>
  <admin-page-card :title="title">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item v-if="mode === 'company' || mode === 'loan'" label="公司">
        <el-select v-model="companyId" filterable clearable placeholder="选择公司" style="width: 220px">
          <el-option label="全部汇总" value="-1" />
          <el-option
            v-for="c in companies"
            :key="String(c.id)"
            :label="String(c.companyName || '')"
            :value="String(c.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item v-if="mode === 'personal'" label="用户">
        <el-select v-model="userId" filterable clearable placeholder="选择用户" style="width: 220px">
          <el-option
            v-for="u in users"
            :key="String(u.id)"
            :label="`${u.trueName || ''} (${u.userName || ''})`"
            :value="String(u.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item v-if="mode === 'project'" label="实验室">
        <el-select v-model="labId" filterable clearable placeholder="选择实验室" style="width: 220px">
          <el-option
            v-for="l in labs"
            :key="String(l.id)"
            :label="String(l.labName || '')"
            :value="String(l.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="年份">
        <el-date-picker v-model="year" type="year" value-format="YYYY" style="width: 120px" />
      </el-form-item>
      <el-form-item label="币种">
        <el-select v-model="accountType" style="width: 110px">
          <el-option :value="1" label="人民币" />
          <el-option :value="2" label="美金" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="loadRows">查询</el-button>
        <el-button type="success" :loading="saving" :disabled="companyId === '-1'" @click="handleSave">
          保存
        </el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="month" label="月份" width="70" />
      <template v-if="mode === 'company'">
        <el-table-column label="工资" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.wages" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="税费" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.taxes" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="费用" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.fees" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="系统成本" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.systemCost" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="贷款利息" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.loan" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
      </template>
      <template v-else-if="mode === 'personal'">
        <el-table-column label="工资" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.wages" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="税费" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.taxes" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="贷款利息" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.loanInterest" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="车补" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.carAmount" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="订单" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.orderAmount" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="其他" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.otherAmount" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
      </template>
      <template v-else-if="mode === 'loan'">
        <el-table-column label="还款本金" min-width="140">
          <template #default="{ row }"><el-input-number v-model="row.loan" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
      </template>
      <template v-else>
        <el-table-column label="租金" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.rentFees" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="电费" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.elecFees" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="人工" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.laborFees" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
        <el-table-column label="配件" min-width="100">
          <template #default="{ row }"><el-input-number v-model="row.partsFees" :min="0" :precision="2" controls-position="right" size="small" /></template>
        </el-table-column>
      </template>
      <el-table-column prop="payAmount" label="合计" width="110" />
      <el-table-column label="状态" width="80">
        <template #default="{ row }">{{ Number(row.status) === 1 ? '已扣' : '未扣' }}</template>
      </el-table-column>
    </el-table>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  fetchCompanyLoanList,
  fetchCompanyOptions,
  fetchCompanyPayList,
  fetchLabOptions,
  fetchProjectPayList,
  fetchUserPayList,
  fetchUserPayOptions,
  saveCompanyLoan,
  saveCompanyPay,
  saveProjectPay,
  saveUserPay,
  isAjaxOk,
} from '@admin/api/fund'

const props = defineProps<{
  mode: 'company' | 'personal' | 'loan' | 'project'
  title: string
}>()

const loading = ref(false)
const saving = ref(false)
const year = ref(String(new Date().getFullYear()))
const accountType = ref(1)
const companyId = ref('')
const userId = ref('')
const labId = ref('')
const companies = ref<Record<string, unknown>[]>([])
const users = ref<Record<string, unknown>[]>([])
const labs = ref<Record<string, unknown>[]>([])
const rows = ref<Record<string, unknown>[]>([])

onMounted(async () => {
  if (props.mode === 'company' || props.mode === 'loan') {
    const res = await fetchCompanyOptions()
    if (isAjaxOk(res)) companies.value = (res.obj as Record<string, unknown>[]) || []
  }
  if (props.mode === 'personal') {
    const res = await fetchUserPayOptions()
    if (isAjaxOk(res)) users.value = (res.obj as Record<string, unknown>[]) || []
  }
  if (props.mode === 'project') {
    const res = await fetchLabOptions()
    if (isAjaxOk(res)) labs.value = (res.obj as Record<string, unknown>[]) || []
  }
})

async function loadRows() {
  if (!year.value) {
    ElMessage.warning('请选择年份')
    return
  }
  if ((props.mode === 'company' || props.mode === 'loan') && !companyId.value) {
    ElMessage.warning('请选择公司')
    return
  }
  if (props.mode === 'personal' && !userId.value) {
    ElMessage.warning('请选择用户')
    return
  }
  if (props.mode === 'project' && !labId.value) {
    ElMessage.warning('请选择实验室')
    return
  }
  loading.value = true
  try {
    let res
    const common = { year: year.value, accountType: accountType.value }
    if (props.mode === 'company') {
      res = await fetchCompanyPayList({ ...common, companyId: companyId.value })
    } else if (props.mode === 'personal') {
      res = await fetchUserPayList({ ...common, userId: userId.value })
    } else if (props.mode === 'loan') {
      res = await fetchCompanyLoanList({ ...common, companyId: companyId.value })
    } else {
      res = await fetchProjectPayList({ ...common, labId: labId.value })
    }
    if (!isAjaxOk(res)) {
      ElMessage.error(String(res.msg || '加载失败'))
      return
    }
    rows.value = ((res.obj as Record<string, unknown>[]) || []).map((r) => ({ ...r }))
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (companyId.value === '-1') {
    ElMessage.warning('汇总模式不可保存')
    return
  }
  if (!rows.value.length) {
    ElMessage.warning('请先查询')
    return
  }
  saving.value = true
  try {
    const list = rows.value.map((r) => ({
      ...r,
      year: year.value,
      accountType: accountType.value,
      companyId: companyId.value,
      userId: userId.value,
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
</script>

<style scoped>
.filter-form { margin-bottom: 12px; }
</style>
