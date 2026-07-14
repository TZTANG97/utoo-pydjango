<template>
  <admin-page-card title="资金账户">
    <div class="top-row">
      <div class="exp-panel">
        <div class="exp-head">
          <span class="exp-title">实验详情(包含实验分包)</span>
          <el-select v-model="statYear" style="width: 120px" @change="loadExpSum">
            <el-option label="ALL" value="" />
            <el-option v-for="y in years" :key="y" :label="`${y}年`" :value="String(y)" />
          </el-select>
        </div>
        <div v-loading="expLoading" class="exp-body">
          <div>实验总额：￥{{ money(exp.qnsyzermb) }} / ${{ money(exp.qnsyzeus) }}</div>
          <div>实验回款总收益：￥{{ money(exp.rmbSyhkzsy) }} / ${{ money(exp.usSyhkzsy) }}</div>
          <div class="exp-split" />
          <div>实验应收款总额：￥{{ money(exp.rmbSyyskze) }} / ${{ money(exp.usSyyskze) }}</div>
          <div>实验分包应付款总额：￥{{ money(exp.rmbSyfbyfkze) }} / ${{ money(exp.usSyfbyfkze) }}</div>
        </div>
      </div>
      <div class="action-panel">
        <el-button type="success" @click="openApply('recharge')">充值申请</el-button>
        <el-button type="warning" @click="openApply('withdraw')">提现申请</el-button>
        <el-button type="success" plain @click="openApply('transfer')">转账申请</el-button>
        <el-button type="warning" plain @click="openApply('loan')">借贷款申请</el-button>
      </div>
    </div>

    <div class="nav-row">
      <el-radio-group v-model="filters.accType" @change="reload">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="13">实验回款</el-radio-button>
      </el-radio-group>
      <el-form :inline="true" class="filter-form" @submit.prevent>
        <el-form-item>
          <el-input v-model="filters.order_id" clearable placeholder="订单编号" style="width: 160px" />
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.accountType" style="width: 140px">
            <el-option value="1" label="人民币账户" />
            <el-option value="2" label="美元账户" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="reload">查询</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" align="center" />
      <el-table-column prop="addTime" label="创建时间" min-width="160" />
      <el-table-column label="名称" min-width="120">
        <template #default="{ row }">{{ accTypeLabel(row) }}</template>
      </el-table-column>
      <el-table-column prop="logAmount" label="金额" width="110" />
      <el-table-column prop="afterLogAmount" label="可用金额" width="120" />
      <el-table-column prop="userName" label="账户" width="120" show-overflow-tooltip />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">{{ statusLabel(row.logStatus) }}</template>
      </el-table-column>
      <el-table-column prop="czNum" label="关联订单" min-width="140" show-overflow-tooltip />
      <el-table-column prop="pdLogInfo" label="交易备注" min-width="140" show-overflow-tooltip />
      <el-table-column label="操作" width="120" align="center" fixed="right">
        <template #default="{ row }">
          <el-button v-if="canCancel(row)" link type="primary" @click="handleCancel(row)">
            取消申请
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="() => load(listParams())"
      />
    </div>

    <el-dialog v-model="applyVisible" :title="applyTitle" width="480px">
      <el-form label-width="100px">
        <el-form-item label="账户类型" required>
          <el-select v-model="applyForm.accountType" style="width: 100%">
            <el-option :value="1" label="人民币账户" />
            <el-option :value="2" label="美元账户" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input v-model="applyForm.logAmount" placeholder="请输入金额" />
        </el-form-item>
        <el-form-item v-if="applyKind === 'withdraw'" label="开户行">
          <el-input v-model="applyForm.bankName" />
        </el-form-item>
        <el-form-item v-if="applyKind === 'withdraw'" label="银行卡号">
          <el-input v-model="applyForm.cardNum" />
        </el-form-item>
        <el-form-item v-if="applyKind === 'transfer'" label="转入用户ID">
          <el-input v-model="applyForm.inUserId" placeholder="sy_users.id" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="applyForm.pdLogInfo" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitApply">提交</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  cancelAccountApply,
  fetchAccountLogList,
  fetchExpSumByYear,
  fetchFundYears,
  submitAccountApply,
  submitLoanApply,
  submitTransferApply,
} from '@/api/fund'
import { useDataTable } from '@/composables/useDataTable'
import { useUserStore } from '@/stores/user'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const userStore = useUserStore()
const years = ref<number[]>([])
const statYear = ref('')
const expLoading = ref(false)
const exp = reactive<Record<string, unknown>>({})
const filters = reactive({
  accType: '',
  order_id: '',
  accountType: '1',
})

const applyVisible = ref(false)
const saving = ref(false)
const applyKind = ref<'recharge' | 'withdraw' | 'transfer' | 'loan'>('recharge')
const applyForm = reactive({
  accountType: 1,
  logAmount: '',
  bankName: '',
  cardNum: '',
  inUserId: '',
  pdLogInfo: '',
})

const applyTitle = computed(() => {
  const map = {
    recharge: '充值申请',
    withdraw: '提现申请',
    transfer: '转账申请',
    loan: '借贷款申请',
  }
  return map[applyKind.value]
})

function listParams() {
  return {
    accType: filters.accType,
    order_id: filters.order_id,
    accountType: filters.accountType,
    excludeZero: 1,
  }
}

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchAccountLogList({ ...params, ...listParams() })
)

function money(v: unknown) {
  return Number(v || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function accTypeLabel(row: Record<string, unknown>) {
  const t = Number(row.accType)
  const name = String(row.logName || '')
  const map: Record<number, string> = {
    1: '充值记录',
    2: '提现记录',
    4: name || '年化收益',
    5: name || '租赁回款',
    8: name || '销售回款',
    10: '扣款记录',
    11: '转账记录',
    12: name || '借贷记录',
    13: name || '实验回款',
    17: name || '借贷利息清算',
    20: '借贷款本金扣款',
    21: '项目资金支出',
  }
  return map[t] || name || String(row.accType ?? '-')
}

function statusLabel(status: unknown) {
  const n = Number(status)
  const map: Record<number, string> = {
    [-2]: '取消申请',
    [-1]: '已驳回',
    0: '已取消',
    1: '交易成功',
    2: '待审核',
    3: '待打款',
    4: '待付款',
    5: '待确认',
  }
  return map[n] ?? String(status ?? '-')
}

function canCancel(row: Record<string, unknown>) {
  const status = Number(row.logStatus)
  const t = Number(row.accType)
  return [2, 3, 4].includes(status) && [1, 2].includes(t)
}

function reload() {
  pagination.page = 1
  return load(listParams())
}

async function loadExpSum() {
  expLoading.value = true
  try {
    const res = await fetchExpSumByYear({ statistics_time: statYear.value })
    if (isAjaxOk(res) && res.obj) {
      Object.assign(exp, res.obj as Record<string, unknown>)
    }
  } finally {
    expLoading.value = false
  }
}

function openApply(kind: typeof applyKind.value) {
  applyKind.value = kind
  Object.assign(applyForm, {
    accountType: Number(filters.accountType) || 1,
    logAmount: '',
    bankName: '',
    cardNum: '',
    inUserId: '',
    pdLogInfo: '',
  })
  applyVisible.value = true
}

function currentUserId() {
  const profile = (userStore.profile || {}) as Record<string, unknown>
  return String(profile.id || profile.userId || '')
}

async function submitApply() {
  const amount = Number(applyForm.logAmount)
  if (!amount || amount <= 0) {
    ElMessage.warning('请输入正确金额')
    return
  }
  const userId = currentUserId()
  if (!userId) {
    ElMessage.warning('无法获取当前用户，请重新登录')
    return
  }
  saving.value = true
  try {
    const base = {
      userId,
      accountType: applyForm.accountType,
      logAmount: amount,
      pdLogInfo: applyForm.pdLogInfo,
    }
    let res
    if (applyKind.value === 'recharge') {
      res = await submitAccountApply({ ...base, accType: 1 })
    } else if (applyKind.value === 'withdraw') {
      res = await submitAccountApply({
        ...base,
        accType: 2,
        bankName: applyForm.bankName,
        branKCard: applyForm.cardNum,
      })
    } else if (applyKind.value === 'transfer') {
      res = await submitTransferApply({ ...base, inUserId: applyForm.inUserId })
    } else {
      res = await submitLoanApply(base)
    }
    if (isAjaxOk(res)) {
      ElMessage.success('提交成功')
      applyVisible.value = false
      await reload()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '提交失败'))
    }
  } finally {
    saving.value = false
  }
}

async function handleCancel(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认取消该申请？', '提示', { type: 'warning' })
  const res = await cancelAccountApply(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('取消成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '取消失败'))
  }
}

onMounted(async () => {
  const yearRes = await fetchFundYears()
  if (isAjaxOk(yearRes) && Array.isArray(yearRes.obj)) {
    years.value = yearRes.obj as number[]
  }
  await loadExpSum()
  await reload()
})
</script>

<style scoped lang="scss">
.top-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.exp-panel {
  flex: 1;
  min-width: 420px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 14px 16px;
  background: #fff;
}
.exp-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.exp-title {
  font-size: 16px;
  font-weight: 600;
}
.exp-body {
  line-height: 1.9;
  color: #303133;
}
.exp-split {
  border-top: 1px dashed #ccc;
  margin: 10px 0;
}
.action-panel {
  width: 180px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  justify-content: center;
}
.nav-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.filter-form {
  margin: 0;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
