<template>
  <admin-page-card title="资金账户">
    <!-- 非管理员：账户统计三卡（对齐 Java asset_account.html userType==2） -->
    <div v-if="showAccountCards" v-loading="summaryLoading" class="asset-cards">
      <div class="asset-card">
        <div class="asset-card__tip">
          <div class="asset-icon asset-icon--stat">¥</div>
          <div class="asset-card__name">账户统计</div>
        </div>
        <div class="asset-card__body">
          <div>
            实际可用总资产（人民币）：<b class="av">￥{{ money(summary.totala) }}</b>
          </div>
          <div>投资冻结总额（人民币）：<b>￥{{ money(summary.totalf) }}</b></div>
          <div v-if="showRateFields">
            人民币利息可用总额：<b class="ye">￥{{ money(summary.rmbi) }}</b>
          </div>
          <div>美金利息可用总额：<b>$ {{ money(summary.usi) }}</b></div>
        </div>
      </div>
      <div class="asset-card">
        <div class="asset-card__tip">
          <div class="asset-icon asset-icon--cny">￥</div>
          <div class="asset-card__name">人民币账户</div>
        </div>
        <div class="asset-card__body">
          <div>可用余额：<b class="av">￥{{ money(summary.rmbAvailable) }}</b></div>
          <div>冻结金额：<b>￥{{ money(summary.rmbFreezing) }}</b></div>
          <template v-if="showRateFields">
            <div>昨日收益：<b class="ye">￥{{ money(summary.rmbYesterday) }}</b></div>
            <div>年化利率：<b>{{ summary.rmbRate }}%</b></div>
          </template>
        </div>
      </div>
      <div class="asset-card">
        <div class="asset-card__tip">
          <div class="asset-icon asset-icon--usd">$</div>
          <div class="asset-card__name">美元账户</div>
        </div>
        <div class="asset-card__body">
          <div>可用余额：<b class="av">${{ money(summary.usdAvailable) }}</b></div>
          <div>冻结金额：<b>${{ money(summary.usdFreezing) }}</b></div>
          <template v-if="showRateFields">
            <div>昨日收益：<b class="ye">${{ money(summary.usdYesterday) }}</b></div>
            <div>年化利率：<b>{{ summary.usRate }}%</b></div>
          </template>
        </div>
      </div>
    </div>

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
          <div class="exp-link" @click="goExpJump('total')">
            实验总额：￥{{ money(exp.qnsyzermb) }} & ${{ money(exp.qnsyzeus) }}
          </div>
          <div class="exp-link" @click="goExpJump('income')">
            实验回款总收益：￥{{ money(exp.rmbSyhkzsy) }} & ${{ money(exp.usSyhkzsy) }}
          </div>
          <div class="exp-split" />
          <div class="exp-link" @click="goExpJump('receivable')">
            实验应收款总额：￥{{ money(exp.rmbSyyskze) }} & ${{ money(exp.usSyyskze) }}
          </div>
          <div class="exp-link" @click="goExpJump('subPay')">
            实验分包应付款总额：￥{{ money(exp.rmbSyfbyfkze) }} & ${{ money(exp.usSyfbyfkze) }}
          </div>
        </div>
      </div>
      <div class="action-panel">
        <button type="button" class="asset-btn asset-btn--teal" @click="openApply('recharge')">
          充值申请
        </button>
        <button type="button" class="asset-btn asset-btn--orange" @click="openApply('withdraw')">
          提现申请
        </button>
        <button type="button" class="asset-btn asset-btn--teal" @click="openApply('transfer')">
          转账申请
        </button>
        <button type="button" class="asset-btn asset-btn--orange" @click="openApply('loan')">
          借贷款申请
        </button>
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
      <el-table-column label="关联订单" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">
          <el-button
            v-if="relatedOrderText(row)"
            link
            type="primary"
            class="order-link"
            @click="openRelatedOrder(row)"
          >
            {{ relatedOrderText(row) }}
          </el-button>
          <span v-else>-</span>
        </template>
      </el-table-column>
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

    <el-dialog v-model="applyVisible" :title="applyTitle" width="480px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="账户类型" required>
          <el-select
            v-model="applyForm.accountType"
            style="width: 100%"
            @change="onApplyAccountTypeChange"
          >
            <el-option :value="1" label="人民币账户" />
            <el-option :value="2" label="美元账户" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="applyKind === 'recharge'" label="充值用户" required>
          <el-select
            v-model="applyForm.userId"
            filterable
            remote
            clearable
            :remote-method="searchUsers"
            :loading="userLoading"
            placeholder="搜索用户名/姓名"
            style="width: 100%"
            @change="loadAvailableBalance"
          >
            <el-option
              v-for="u in userOptions"
              :key="String(u.id)"
              :label="userOptionLabel(u)"
              :value="String(u.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="applyKind === 'recharge'" label="可用余额">
          <span class="balance-text">{{ balanceLoading ? '加载中…' : money(availableBalance) }}</span>
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  cancelAccountApply,
  fetchAccountLogList,
  fetchAssetAccountSummary,
  fetchAssetOverview,
  fetchExpSumByYear,
  fetchFundUsers,
  fetchFundYears,
  fetchUserAvailableBalance,
  fetchYesterdayIncome,
  submitAccountApply,
  submitLoanApply,
  submitTransferApply,
} from '@admin/api/fund'
import { useDataTable } from '@admin/composables/useDataTable'
import { useUserStore } from '@admin/stores/user'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type ExpJump = 'total' | 'income' | 'receivable' | 'subPay'
type ApplyKind = 'recharge' | 'withdraw' | 'transfer' | 'loan'

const router = useRouter()
const userStore = useUserStore()
const years = ref<number[]>([])
const statYear = ref('')
const expLoading = ref(false)
const summaryLoading = ref(false)
const exp = reactive<Record<string, unknown>>({})
const filters = reactive({
  accType: '',
  order_id: '',
  accountType: '1',
})

/** Java：非 ADMIN 才展示顶部账户三卡 */
const isAdminUser = computed(() => {
  const t = Number(userStore.welcome?.userType ?? userStore.userType ?? 0)
  return t === 1
})
const showAccountCards = computed(() => !isAdminUser.value)

const summary = reactive({
  totala: 0,
  totalf: 0,
  rmbi: 0,
  usi: 0,
  rmbAvailable: 0,
  rmbFreezing: 0,
  usdAvailable: 0,
  usdFreezing: 0,
  rmbYesterday: 0,
  usdYesterday: 0,
  rmbRate: 0,
  usRate: 0,
  isRate: 0,
})
const showRateFields = computed(() => Number(summary.isRate) === 1)

const applyVisible = ref(false)
const saving = ref(false)
const applyKind = ref<ApplyKind>('recharge')
const userLoading = ref(false)
const balanceLoading = ref(false)
const availableBalance = ref(0)
const userOptions = ref<Record<string, unknown>[]>([])
const applyForm = reactive({
  accountType: 1,
  userId: '',
  logAmount: '',
  bankName: '',
  cardNum: '',
  inUserId: '',
  pdLogInfo: '',
})

const applyTitle = computed(() => {
  const map: Record<ApplyKind, string> = {
    recharge: '充值申请',
    withdraw: '提现申请',
    transfer: '转账申请',
    loan: '借贷款申请',
  }
  return map[applyKind.value]
})

function currentUserId() {
  const profile = (userStore.profile || {}) as Record<string, unknown>
  return String(
    profile.id ||
      profile.userId ||
      userStore.welcome?.userId ||
      userStore.userId ||
      ''
  )
}

function listParams() {
  const p: Record<string, unknown> = {
    accType: filters.accType,
    order_id: filters.order_id,
    accountType: filters.accountType,
    excludeZero: 1,
  }
  // 非管理员只看本人流水（对齐 Java asset_account d.userId）
  if (!isAdminUser.value) {
    const uid = currentUserId()
    if (uid) p.userId = uid
  }
  return p
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

async function loadAccountSummary() {
  if (!showAccountCards.value) return
  summaryLoading.value = true
  try {
    const uid = currentUserId()
    const [sumRes, balRes, yesRes] = await Promise.all([
      fetchAssetAccountSummary(uid ? { userId: uid } : {}),
      fetchAssetOverview(uid ? { userId: uid } : {}),
      fetchYesterdayIncome(uid ? { userId: uid } : {}),
    ])
    if (isAjaxOk(sumRes) && sumRes.obj) {
      const obj = sumRes.obj as Record<string, unknown>
      summary.totala = Number(obj.totala || 0)
      summary.totalf = Number(obj.totalf || 0)
      summary.rmbi = Number(obj.rmbi || 0)
      summary.usi = Number(obj.usi || 0)
      const sy = (obj.syUsers || {}) as Record<string, unknown>
      summary.isRate = Number(sy.is_rate ?? sy.isRate ?? 0)
      const setting = (obj.setting || {}) as Record<string, unknown>
      summary.rmbRate = Number(setting.rmbRate || 0)
      summary.usRate = Number(setting.usRate || 0)
    }
    if (isAjaxOk(balRes) && balRes.obj) {
      const obj = balRes.obj as Record<string, unknown>
      summary.rmbAvailable = Number(obj.rmbAvailable || 0)
      summary.rmbFreezing = Number(obj.rmbFreezing || 0)
      summary.usdAvailable = Number(obj.usdAvailable || 0)
      summary.usdFreezing = Number(obj.usdFreezing || 0)
      const accounts = Array.isArray(obj.accounts) ? (obj.accounts as Record<string, unknown>[]) : []
      for (const a of accounts) {
        const t = Number(a.accountType || a.account_type || 0)
        if (t === 1) {
          summary.rmbAvailable = Number(
            a.availableBalance ?? a.available_balance ?? summary.rmbAvailable
          )
          summary.rmbFreezing = Number(
            a.freezingBalance ?? a.freezing_balance ?? summary.rmbFreezing
          )
        } else if (t === 2) {
          summary.usdAvailable = Number(
            a.availableBalance ?? a.available_balance ?? summary.usdAvailable
          )
          summary.usdFreezing = Number(
            a.freezingBalance ?? a.freezing_balance ?? summary.usdFreezing
          )
        }
      }
    }
    if (isAjaxOk(yesRes) && yesRes.obj) {
      const obj = yesRes.obj as Record<string, unknown>
      summary.rmbYesterday = Number(obj.rmbzrsy || 0)
      summary.usdYesterday = Number(obj.uszrsy || 0)
    }
  } finally {
    summaryLoading.value = false
  }
}

function goExpJump(kind: ExpJump) {
  const year = String(statYear.value || '').trim()
  const yearQuery = year ? { year } : {}

  if (kind === 'income') {
    filters.accType = '13'
    reload()
    return
  }
  if (kind === 'total' || kind === 'receivable') {
    router.push({
      name: 'ExperimentOrders',
      query: { ...yearQuery, from: 'fund-account', fundJump: kind },
    })
    return
  }
  router.push({
    name: 'ExperimentSubcontractOrders',
    query: { ...yearQuery, from: 'fund-account', fundJump: kind },
  })
}

function relatedOrderText(row: Record<string, unknown>) {
  return String(row.czNum || row.orderNum || '').trim()
}

/** 资金模块自有流水类型：关联单号是资金单（CZ/JD 等），不应跳实验订单 */
const FUND_NATIVE_ACC_TYPES = new Set([1, 2, 10, 11, 12, 14, 17, 20])

function isFundNativeSlip(row: Record<string, unknown>, orderNo: string) {
  const accType = Number(row.accType)
  if (FUND_NATIVE_ACC_TYPES.has(accType)) return true
  // 单号前缀兜底：充值 CZ / 借贷 JD / 提现 TX / 转账 ZZ / 扣款 KK 等
  return /^(CZ|JD|TX|ZZ|KK|QD|JK)/i.test(orderNo)
}

function openRelatedOrder(row: Record<string, unknown>) {
  const orderNo = relatedOrderText(row)
  if (!orderNo) return

  // FUND-002：借贷/充值等资金单留在资金管理，勿误进实验订单
  if (isFundNativeSlip(row, orderNo)) {
    const accType = String(row.accType || filters.accType || '1')
    router.push({
      name: 'FundManagement',
      query: {
        accType: FUND_NATIVE_ACC_TYPES.has(Number(accType)) ? accType : '12',
        czNum: orderNo,
        from: 'fund-account',
      },
    })
    return
  }

  const pk = String(row.orderId || '').trim()
  if (pk && pk !== '0') {
    router.push({
      name: 'ExperimentOrderDetail',
      params: { id: pk },
      query: {
        from: 'fund-account',
        orderNo,
      },
    })
    return
  }
  router.push({
    name: 'ExperimentOrders',
    query: { orderId: orderNo, from: 'fund-account' },
  })
}

async function loadExpSum() {
  expLoading.value = true
  try {
    const p: Record<string, unknown> = { statistics_time: statYear.value }
    if (!isAdminUser.value) {
      const uid = currentUserId()
      if (uid) p.userId = uid
    }
    const res = await fetchExpSumByYear(p)
    if (isAjaxOk(res) && res.obj) {
      Object.assign(exp, res.obj as Record<string, unknown>)
    }
  } finally {
    expLoading.value = false
  }
}

function userOptionLabel(u: Record<string, unknown>) {
  const name = String(u.userName || '')
  const trueName = String(u.trueName || '')
  return trueName ? `${name}（${trueName}）` : name || String(u.id || '')
}

async function searchUsers(keyword: string) {
  userLoading.value = true
  try {
    const res = await fetchFundUsers(keyword || '')
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      userOptions.value = res.obj as Record<string, unknown>[]
    }
  } finally {
    userLoading.value = false
  }
}

async function loadAvailableBalance() {
  if (applyKind.value !== 'recharge') return
  const uid = String(applyForm.userId || '').trim()
  if (!uid) {
    availableBalance.value = 0
    return
  }
  balanceLoading.value = true
  try {
    availableBalance.value = await fetchUserAvailableBalance(uid, Number(applyForm.accountType) || 1)
  } catch {
    availableBalance.value = 0
  } finally {
    balanceLoading.value = false
  }
}

function onApplyAccountTypeChange() {
  loadAvailableBalance()
}

async function openApply(kind: ApplyKind) {
  applyKind.value = kind
  const uid = currentUserId()
  Object.assign(applyForm, {
    accountType: Number(filters.accountType) || 1,
    userId: uid,
    logAmount: '',
    bankName: '',
    cardNum: '',
    inUserId: '',
    pdLogInfo: '',
  })
  availableBalance.value = 0
  applyVisible.value = true
  if (kind === 'recharge') {
    await searchUsers('')
    if (uid && !userOptions.value.some((u) => String(u.id) === uid)) {
      const profile = (userStore.profile || {}) as Record<string, unknown>
      userOptions.value = [
        {
          id: uid,
          userName: profile.userName || profile.username || uid,
          trueName: profile.trueName || profile.true_name || '',
        },
        ...userOptions.value,
      ]
    }
    await loadAvailableBalance()
  }
}

async function submitApply() {
  const amount = Number(applyForm.logAmount)
  if (!amount || amount <= 0) {
    ElMessage.warning('请输入正确金额')
    return
  }
  const userId =
    applyKind.value === 'recharge'
      ? String(applyForm.userId || '').trim()
      : currentUserId()
  if (!userId) {
    ElMessage.warning(applyKind.value === 'recharge' ? '请选择充值用户' : '无法获取当前用户，请重新登录')
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
      await Promise.all([reload(), loadAccountSummary()])
    } else {
      ElMessage.error(ajaxErrorMessage(res, '提交失败'))
    }
  } finally {
    saving.value = false
  }
}

async function handleCancel(row: Record<string, unknown>) {
  try {
    await ElMessageBox.confirm('确定取消该申请？', '提示', { type: 'warning' })
  } catch {
    return
  }
  const res = await cancelAccountApply(row.id as string | number)
  if (isAjaxOk(res)) {
    ElMessage.success('已取消')
    await Promise.all([reload(), loadAccountSummary()])
  } else {
    ElMessage.error(ajaxErrorMessage(res, '取消失败'))
  }
}

onMounted(async () => {
  const yRes = await fetchFundYears()
  if (isAjaxOk(yRes) && Array.isArray(yRes.obj)) {
    years.value = (yRes.obj as unknown[]).map((y) => Number(y)).filter((y) => y > 0)
  }
  await Promise.all([loadAccountSummary(), loadExpSum(), reload()])
})
</script>

<style scoped>
.asset-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.asset-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 14px 16px;
  min-height: 160px;
}
.asset-card__tip {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.asset-card__name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.asset-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 18px;
}
.asset-icon--stat,
.asset-icon--cny {
  background: #e74c3c;
}
.asset-icon--usd {
  background: #2c3e50;
}
.asset-card__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}
.asset-card__body .av {
  color: #e74c3c;
}
.asset-card__body .ye {
  color: #e6a23c;
}
.top-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  align-items: stretch;
}
.exp-panel {
  flex: 1;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 14px 16px;
  min-height: 180px;
}
.exp-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.exp-title {
  font-size: 16px;
  font-weight: 700;
}
.exp-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.exp-link {
  color: #f39800;
  cursor: pointer;
  width: fit-content;
}
.exp-link:hover {
  text-decoration: underline;
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
.asset-btn {
  height: 40px;
  border: 0;
  border-radius: 4px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}
.asset-btn--teal {
  background: #26a69a;
}
.asset-btn--orange {
  background: #ef6c00;
}
.asset-btn:hover {
  opacity: 0.92;
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
.order-link {
  padding: 0;
  font-weight: 500;
}
.balance-text {
  color: #303133;
  font-weight: 600;
}
@media (max-width: 1100px) {
  .asset-cards {
    grid-template-columns: 1fr;
  }
}
</style>
