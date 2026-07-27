<template>
  <admin-page-card title="内部收益明细">
    <div class="summary-panel">
      <div class="hero">
        <div class="hero-label">当前总收益(元)</div>
        <div class="hero-value" :class="{ neg: Number(overview.dqzsy) < 0 }">
          ¥ {{ money(overview.dqzsy) }}
        </div>
      </div>
      <div class="kpi-grid">
        <div v-for="item in kpiItems" :key="item.label" class="kpi-item">
          <span class="kpi-label">{{ item.label }}</span>
          <span class="kpi-value">{{ item.empty ? '-' : `¥ ${money(item.value)}` }}</span>
        </div>
      </div>
      <el-button class="refresh-btn" @click="loadOverview">刷新汇总</el-button>
    </div>

    <div class="section-head">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="投资明细" name="invest" />
        <el-tab-pane label="税费明细" name="tax" />
        <el-tab-pane label="投资比例明细" name="ratio" />
      </el-tabs>
      <div class="section-actions">
        <el-button type="primary" @click="openDialog('disinvest')">添加撤资</el-button>
        <el-button type="primary" @click="openDialog('invest')">添加投资</el-button>
        <el-button type="primary" @click="openDialog('tax')">添加税费</el-button>
      </div>
    </div>

    <template v-if="activeTab !== 'ratio'">
      <el-table v-loading="loading" :data="rows" border stripe>
        <el-table-column prop="dealTime" :label="activeTab === 'tax' ? '税费时间' : '投资/撤资时间'" min-width="160" />
        <el-table-column
          :prop="activeTab === 'tax' ? 'jlr' : 'userName'"
          :label="activeTab === 'tax' ? '记录人' : '参与人'"
          min-width="120"
        />
        <el-table-column label="币种" width="90">
          <template #default="{ row }">{{ row.accountTypeLabel || (Number(row.accountType) === 2 ? '美金' : '人民币') }}</template>
        </el-table-column>
        <el-table-column prop="tzAmount" :label="activeTab === 'tax' ? '金额' : '投资金额(负数为撤资)'" width="160" />
        <el-table-column v-if="activeTab === 'invest'" prop="thAmount" label="退还金额" width="110" />
        <el-table-column v-if="activeTab === 'invest'" prop="totalAmount" label="投资总额" width="110" />
        <el-table-column v-if="activeTab === 'tax'" prop="payTypeLabel" label="代付类型" width="120" />
        <el-table-column prop="mark" label="备注" min-width="140" show-overflow-tooltip />
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
    </template>

    <div v-else v-loading="ratioLoading" class="ratio-wrap">
      <el-table :data="ratioRows" border stripe>
        <el-table-column prop="userName" label="投资人" fixed width="120" />
        <el-table-column
          v-for="(m, idx) in ratioMonths"
          :key="m"
          :label="m"
          min-width="140"
          align="center"
        >
          <template #default="{ row }">
            <div>{{ money(row.amounts[idx]) }}</div>
            <div class="scale">{{ row.scales[idx] }}%</div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!ratioRows.length" description="暂无比例数据" />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="账户类型" required>
          <el-select v-model="form.accountType" style="width: 100%" @change="onAccountTypeChange">
            <el-option :value="1" label="人民币" />
            <el-option :value="2" label="美金" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dialogKind !== 'tax'" label="参与人" required>
          <el-select
            v-model="form.userId"
            filterable
            remote
            clearable
            :remote-method="searchUsers"
            :loading="userLoading"
            style="width: 100%"
            placeholder="搜索用户"
          >
            <el-option
              v-for="u in userOptions"
              :key="String(u.id || u.userId)"
              :label="userLabel(u)"
              :value="String(u.id || u.userId)"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="dialogKind === 'tax' ? '金额' : '金额'" required>
          <el-input-number v-model="form.logAmount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item v-if="dialogKind === 'disinvest'" label="退还金额">
          <el-input-number v-model="form.thAmount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item v-if="dialogKind === 'tax'" label="代付类型" required>
          <el-select v-model="form.payType" style="width: 100%">
            <el-option :value="1" label="进口增值税" />
            <el-option :value="2" label="关税" />
            <el-option :value="3" label="手续费" />
            <el-option :value="4" label="运费" />
            <el-option :value="5" label="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="成交时间">
          <el-date-picker
            v-model="form.dealTime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.mark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitDialog">提交</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  fetchIncomeInvestUsers,
  fetchIncomeList,
  fetchIncomeOverview,
  fetchIncomeRatio,
  fetchIncomeUsers,
  submitIncomeDisinvest,
  submitIncomeInvest,
  submitIncomeTax,
} from '@admin/api/inventory'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type DialogKind = 'invest' | 'disinvest' | 'tax'

const overview = ref<Record<string, unknown>>({})
const activeTab = ref('invest')
const ratioLoading = ref(false)
const ratioMonths = ref<string[]>([])
const ratioRows = ref<{ userName: string; amounts: number[]; scales: number[] }[]>([])

const dialogVisible = ref(false)
const saving = ref(false)
const dialogKind = ref<DialogKind>('invest')
const userLoading = ref(false)
const userOptions = ref<Record<string, unknown>[]>([])
const form = reactive({
  accountType: 1,
  userId: '',
  logAmount: 0,
  thAmount: 0,
  payType: 5,
  dealTime: '',
  mark: '',
})

const kpiItems = computed(() => [
  { label: '库存总价值', value: overview.value.kczjz },
  { label: '租赁订单总销售额', value: overview.value.zlxszejz, empty: overview.value.zlxszejz == null },
  { label: '租赁已分成总额', value: overview.value.zlyhkzh },
  { label: '平台租赁已分成总额', value: overview.value.ptzlyhkze },
  { label: '个人租赁已分成总额', value: overview.value.grzlyhkze },
  { label: '库存销售成本回款总和', value: overview.value.kcxscbhkze },
  { label: '平台已回款总额', value: overview.value.yhkze },
  { label: '采购订单总销售额', value: overview.value.syxszejz, empty: overview.value.syxszejz == null },
  { label: '库存销售毛利总和', value: overview.value.zzsccbze },
  { label: '平台实验已分成总额', value: overview.value.syzhk },
  { label: '自主采购未付款总额', value: overview.value.zzcgwfk },
])

const dialogTitle = computed(() => {
  if (dialogKind.value === 'disinvest') return '添加撤资'
  if (dialogKind.value === 'tax') return '添加税费'
  return '添加投资'
})

function listParams() {
  return { type: activeTab.value === 'tax' ? '3' : '1' }
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchIncomeList({ ...p, ...listParams() })
)

function money(v: unknown) {
  return Number(v || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function userLabel(u: Record<string, unknown>) {
  const name = String(u.userName || '')
  const trueName = String(u.trueName || '')
  const tzze = u.tzze != null ? ` / 投${u.tzze}` : ''
  return trueName ? `${name} ${trueName}${tzze}` : `${name}${tzze}`
}

async function loadOverview() {
  const res = await fetchIncomeOverview()
  const payload = (res.obj ?? res.data) as Record<string, unknown> | undefined
  if (isAjaxOk(res) && payload) {
    overview.value = {
      ...payload,
      // 兼容新旧字段名
      kczjz: payload.kczjz ?? payload.stockValue,
      dqzsy: payload.dqzsy,
      yhkze: payload.yhkze,
      zlyhkzh: payload.zlyhkzh,
      syzhk: payload.syzhk,
    }
  }
}

function reload() {
  pagination.page = 1
  return load(listParams())
}

async function loadRatio() {
  ratioLoading.value = true
  try {
    const res = await fetchIncomeRatio()
    if (!isAjaxOk(res) || !res.obj) {
      ratioMonths.value = []
      ratioRows.value = []
      return
    }
    const obj = res.obj as Record<string, unknown>
    const months = Array.isArray(obj.months) ? (obj.months as Record<string, unknown>[]) : []
    ratioMonths.value = months.map((m) => String(m.month || ''))
    const users = Array.isArray(obj.userList) ? (obj.userList as Record<string, unknown>[]) : []
    ratioRows.value = users.map((u) => {
      const mt = Array.isArray(u.monthTotal) ? (u.monthTotal as Record<string, unknown>[]) : []
      return {
        userName: String(u.userName || ''),
        amounts: mt.map((x) => Number(x.tz_amount || 0)),
        scales: mt.map((x) => Number(x.scale || 0)),
      }
    })
  } finally {
    ratioLoading.value = false
  }
}

async function onTabChange() {
  if (activeTab.value === 'ratio') {
    await loadRatio()
    return
  }
  await reload()
}

async function searchUsers(keyword: string) {
  userLoading.value = true
  try {
    if (dialogKind.value === 'disinvest') {
      const res = await fetchIncomeInvestUsers(form.accountType)
      if (isAjaxOk(res) && Array.isArray(res.obj)) {
        const list = res.obj as Record<string, unknown>[]
        const kw = (keyword || '').toLowerCase()
        userOptions.value = kw
          ? list.filter((u) => String(u.userName || '').toLowerCase().includes(kw))
          : list
      }
      return
    }
    const res = await fetchIncomeUsers(keyword || '')
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      userOptions.value = (res.obj as Record<string, unknown>[]).map((u) => ({
        ...u,
        userId: u.id,
      }))
    }
  } finally {
    userLoading.value = false
  }
}

function onAccountTypeChange() {
  form.userId = ''
  searchUsers('')
}

function openDialog(kind: DialogKind) {
  dialogKind.value = kind
  Object.assign(form, {
    accountType: 1,
    userId: '',
    logAmount: 0,
    thAmount: 0,
    payType: 5,
    dealTime: '',
    mark: '',
  })
  dialogVisible.value = true
  searchUsers('')
}

async function submitDialog() {
  if (!form.logAmount || form.logAmount <= 0) {
    ElMessage.warning('请输入正确金额')
    return
  }
  if (dialogKind.value !== 'tax' && !form.userId) {
    ElMessage.warning('请选择参与人')
    return
  }
  saving.value = true
  try {
    const base = {
      accountType: form.accountType,
      logAmount: form.logAmount,
      dealTime: form.dealTime,
      pdLogInfo: form.mark,
      userId: form.userId,
      tj_userid: form.userId,
    }
    let res
    if (dialogKind.value === 'invest') {
      res = await submitIncomeInvest(base)
    } else if (dialogKind.value === 'disinvest') {
      res = await submitIncomeDisinvest({ ...base, thAmount: form.thAmount })
    } else {
      res = await submitIncomeTax({ ...base, payType: form.payType })
    }
    if (isAjaxOk(res)) {
      ElMessage.success('提交成功')
      dialogVisible.value = false
      await loadOverview()
      if (activeTab.value === 'ratio') await loadRatio()
      else if (
        (dialogKind.value === 'tax' && activeTab.value === 'tax') ||
        (dialogKind.value !== 'tax' && activeTab.value === 'invest')
      ) {
        await reload()
      }
    } else {
      ElMessage.error(ajaxErrorMessage(res, '提交失败'))
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadOverview()
  await reload()
})
</script>

<style scoped>
.summary-panel {
  display: grid;
  grid-template-columns: 220px 1fr auto;
  gap: 16px;
  align-items: stretch;
  margin-bottom: 16px;
  padding: 16px;
  background: #f7f9fc;
  border-radius: 8px;
}
.hero {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #ebeef5;
}
.hero-label {
  color: #909399;
  font-size: 13px;
}
.hero-value {
  margin-top: 10px;
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  word-break: break-all;
}
.hero-value.neg {
  color: #f56c6c;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 20px;
  background: #fff;
  border-radius: 8px;
  padding: 14px 16px;
  border: 1px solid #ebeef5;
}
.kpi-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  line-height: 1.8;
}
.kpi-label {
  color: #606266;
}
.kpi-value {
  color: #303133;
  font-weight: 600;
}
.refresh-btn {
  align-self: start;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.section-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.ratio-wrap {
  min-height: 160px;
}
.scale {
  color: #909399;
  font-size: 12px;
}
@media (max-width: 1100px) {
  .summary-panel {
    grid-template-columns: 1fr;
  }
}
</style>
