<template>
  <admin-page-card title="璧勯噾璐︽埛">
    <div class="top-row">
      <div class="exp-panel">
        <div class="exp-head">
          <span class="exp-title">瀹為獙璇︽儏(鍖呭惈瀹為獙鍒嗗寘)</span>
          <el-select v-model="statYear" style="width: 120px" @change="loadExpSum">
            <el-option label="ALL" value="" />
            <el-option v-for="y in years" :key="y" :label="`${y}骞碻" :value="String(y)" />
          </el-select>
        </div>
        <div v-loading="expLoading" class="exp-body">
          <div class="exp-link" @click="goExpJump('total')">
            瀹為獙鎬婚锛氾骏{{ money(exp.qnsyzermb) }} / ${{ money(exp.qnsyzeus) }}
          </div>
          <div class="exp-link" @click="goExpJump('income')">
            瀹為獙鍥炴鎬绘敹鐩婏細锟{ money(exp.rmbSyhkzsy) }} / ${{ money(exp.usSyhkzsy) }}
          </div>
          <div class="exp-split" />
          <div class="exp-link" @click="goExpJump('receivable')">
            瀹為獙搴旀敹娆炬€婚锛氾骏{{ money(exp.rmbSyyskze) }} / ${{ money(exp.usSyyskze) }}
          </div>
          <div class="exp-link" @click="goExpJump('subPay')">
            瀹為獙鍒嗗寘搴斾粯娆炬€婚锛氾骏{{ money(exp.rmbSyfbyfkze) }} / ${{ money(exp.usSyfbyfkze) }}
          </div>
        </div>
      </div>
      <div class="action-panel">
        <el-button type="success" @click="openApply('recharge')">鍏呭€肩敵璇?/el-button>
        <el-button type="warning" @click="openApply('withdraw')">鎻愮幇鐢宠</el-button>
        <el-button type="success" plain @click="openApply('transfer')">杞处鐢宠</el-button>
        <el-button type="warning" plain @click="openApply('loan')">鍊熻捶娆剧敵璇?/el-button>
      </div>
    </div>

    <div class="nav-row">
      <el-radio-group v-model="filters.accType" @change="reload">
        <el-radio-button label="">鍏ㄩ儴</el-radio-button>
        <el-radio-button label="13">瀹為獙鍥炴</el-radio-button>
      </el-radio-group>
      <el-form :inline="true" class="filter-form" @submit.prevent>
        <el-form-item>
          <el-input v-model="filters.order_id" clearable placeholder="璁㈠崟缂栧彿" style="width: 160px" />
        </el-form-item>
        <el-form-item>
          <el-select v-model="filters.accountType" style="width: 140px">
            <el-option value="1" label="浜烘皯甯佽处鎴? />
            <el-option value="2" label="缇庡厓璐︽埛" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="reload">鏌ヨ</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" align="center" />
      <el-table-column prop="addTime" label="鍒涘缓鏃堕棿" min-width="160" />
      <el-table-column label="鍚嶇О" min-width="120">
        <template #default="{ row }">{{ accTypeLabel(row) }}</template>
      </el-table-column>
      <el-table-column prop="logAmount" label="閲戦" width="110" />
      <el-table-column prop="afterLogAmount" label="鍙敤閲戦" width="120" />
      <el-table-column prop="userName" label="璐︽埛" width="120" show-overflow-tooltip />
      <el-table-column label="鐘舵€? width="100" align="center">
        <template #default="{ row }">{{ statusLabel(row.logStatus) }}</template>
      </el-table-column>
      <el-table-column label="鍏宠仈璁㈠崟" min-width="140" show-overflow-tooltip>
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
      <el-table-column prop="pdLogInfo" label="浜ゆ槗澶囨敞" min-width="140" show-overflow-tooltip />
      <el-table-column label="鎿嶄綔" width="120" align="center" fixed="right">
        <template #default="{ row }">
          <el-button v-if="canCancel(row)" link type="primary" @click="handleCancel(row)">
            鍙栨秷鐢宠
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
        <el-form-item label="璐︽埛绫诲瀷" required>
          <el-select
            v-model="applyForm.accountType"
            style="width: 100%"
            @change="onApplyAccountTypeChange"
          >
            <el-option :value="1" label="浜烘皯甯佽处鎴? />
            <el-option :value="2" label="缇庡厓璐︽埛" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="applyKind === 'recharge'" label="鍏呭€肩敤鎴? required>
          <el-select
            v-model="applyForm.userId"
            filterable
            remote
            clearable
            :remote-method="searchUsers"
            :loading="userLoading"
            placeholder="鎼滅储鐢ㄦ埛鍚?濮撳悕"
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
        <el-form-item v-if="applyKind === 'recharge'" label="鍙敤浣欓">
          <span class="balance-text">{{ balanceLoading ? '鍔犺浇涓€? : money(availableBalance) }}</span>
        </el-form-item>
        <el-form-item label="閲戦" required>
          <el-input v-model="applyForm.logAmount" placeholder="璇疯緭鍏ラ噾棰? />
        </el-form-item>
        <el-form-item v-if="applyKind === 'withdraw'" label="寮€鎴疯">
          <el-input v-model="applyForm.bankName" />
        </el-form-item>
        <el-form-item v-if="applyKind === 'withdraw'" label="閾惰鍗″彿">
          <el-input v-model="applyForm.cardNum" />
        </el-form-item>
        <el-form-item v-if="applyKind === 'transfer'" label="杞叆鐢ㄦ埛ID">
          <el-input v-model="applyForm.inUserId" placeholder="sy_users.id" />
        </el-form-item>
        <el-form-item label="澶囨敞">
          <el-input v-model="applyForm.pdLogInfo" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyVisible = false">鍙栨秷</el-button>
        <el-button type="primary" :loading="saving" @click="submitApply">鎻愪氦</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  cancelAccountApply,
  fetchAccountLogList,
  fetchExpSumByYear,
  fetchFundUsers,
  fetchFundYears,
  fetchAvailableBalance,
  submitAccountApply,
  submitLoanApply,
  submitTransferApply,
} from '@/api/fund'
import { useDataTable } from '@/composables/useDataTable'
import { useUserStore } from '@/stores/user'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

type ExpJump = 'total' | 'income' | 'receivable' | 'subPay'
type ApplyKind = 'recharge' | 'withdraw' | 'transfer' | 'loan'

const router = useRouter()
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
    recharge: '鍏呭€肩敵璇?,
    withdraw: '鎻愮幇鐢宠',
    transfer: '杞处鐢宠',
    loan: '鍊熻捶娆剧敵璇?,
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
    1: '鍏呭€艰褰?,
    2: '鎻愮幇璁板綍',
    4: name || '骞村寲鏀剁泭',
    5: name || '绉熻祦鍥炴',
    8: name || '閿€鍞洖娆?,
    10: '鎵ｆ璁板綍',
    11: '杞处璁板綍',
    12: name || '鍊熻捶璁板綍',
    13: name || '瀹為獙鍥炴',
    17: name || '鍊熻捶鍒╂伅娓呯畻',
    20: '鍊熻捶娆炬湰閲戞墸娆?,
    21: '椤圭洰璧勯噾鏀嚭',
  }
  return map[t] || name || String(row.accType ?? '-')
}

function statusLabel(status: unknown) {
  const n = Number(status)
  const map: Record<number, string> = {
    [-2]: '鍙栨秷鐢宠',
    [-1]: '宸查┏鍥?,
    0: '宸插彇娑?,
    1: '浜ゆ槗鎴愬姛',
    2: '寰呭鏍?,
    3: '寰呮墦娆?,
    4: '寰呬粯娆?,
    5: '寰呯‘璁?,
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

/** 瀵归綈灏忕▼搴?digitalOperationsCenter 鈫?experimentEdOrAble 鐨?type 鏄犲皠 */
function goExpJump(kind: ExpJump) {
  const year = String(statYear.value || '').trim()
  const yearQuery = year ? { year } : {}

  if (kind === 'income') {
    // 瀹為獙鍥炴鎬绘敹鐩?鈫?鏈〉銆屽疄楠屽洖娆俱€嶆祦姘达紙accType=13锛?
    filters.accType = '13'
    reload()
    return
  }
  if (kind === 'total' || kind === 'receivable') {
    // type=10 涓汉瀹為獙鎬婚 / type=7 涓汉瀹為獙搴旀敹 鈫?瀹為獙璁㈠崟鍒楄〃
    router.push({
      name: 'ExperimentOrders',
      query: { ...yearQuery, from: 'fund-account', fundJump: kind },
    })
    return
  }
  // type=8 涓汉瀹為獙鍒嗗寘搴斾粯娆?鈫?瀹為獙鍒嗗寘璁㈠崟
  router.push({
    name: 'ExperimentSubcontractOrders',
    query: { ...yearQuery, from: 'fund-account', fundJump: kind },
  })
}

function relatedOrderText(row: Record<string, unknown>) {
  return String(row.czNum || row.orderNum || '').trim()
}

/** 瀵归綈灏忕▼搴忥細accType=13 鐢?orderId 杩涜鍗曡鎯咃紝鍚﹀垯鏈夊叧鑱斿崟鍙蜂篃灏濊瘯杩涜鎯?鍒楄〃 */
function openRelatedOrder(row: Record<string, unknown>) {
  const orderNo = relatedOrderText(row)
  if (!orderNo) return
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
    const res = await fetchExpSumByYear({ statistics_time: statYear.value })
    if (isAjaxOk(res) && res.obj) {
      Object.assign(exp, res.obj as Record<string, unknown>)
    }
  } finally {
    expLoading.value = false
  }
}

function currentUserId() {
  const profile = (userStore.profile || {}) as Record<string, unknown>
  return String(profile.id || profile.userId || '')
}

function userOptionLabel(u: Record<string, unknown>) {
  const name = String(u.userName || '')
  const trueName = String(u.trueName || '')
  return trueName ? `${name}锛?{trueName}锛塦 : name || String(u.id || '')
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
    availableBalance.value = await fetchAvailableBalance(uid, Number(applyForm.accountType) || 1)
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
    // 纭繚褰撳墠鐢ㄦ埛鍦ㄩ€夐」閲?
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
    ElMessage.warning('璇疯緭鍏ユ纭噾棰?)
    return
  }
  const userId =
    applyKind.value === 'recharge'
      ? String(applyForm.userId || '').trim()
      : currentUserId()
  if (!userId) {
    ElMessage.warning(applyKind.value === 'recharge' ? '璇烽€夋嫨鍏呭€肩敤鎴? : '鏃犳硶鑾峰彇褰撳墠鐢ㄦ埛锛岃閲嶆柊鐧诲綍')
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
      ElMessage.success('鎻愪氦鎴愬姛')
      applyVisible.value = false
      await reload()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '鎻愪氦澶辫触'))
    }
  } finally {
    saving.value = false
  }
}

async function handleCancel(row: Record<string, unknown>) {
  await ElMessageBox.confirm('纭鍙栨秷璇ョ敵璇凤紵', '鎻愮ず', { type: 'warning' })
  const res = await cancelAccountApply(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('鍙栨秷鎴愬姛')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '鍙栨秷澶辫触'))
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
</style>

