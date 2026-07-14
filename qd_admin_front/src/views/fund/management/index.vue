<template>
  <admin-page-card title="资金管理">
    <div class="toolbar">
      <el-radio-group v-model="filters.accType" class="type-tabs" @change="onTabChange">
        <el-radio-button v-for="t in typeTabs" :key="t.value" :label="t.value">
          {{ t.label }}
        </el-radio-button>
      </el-radio-group>
      <div class="toolbar-actions">
        <el-button type="primary" @click="openDialog('recharge')">添加充值</el-button>
        <el-button type="primary" @click="openDialog('withdraw')">添加提现</el-button>
        <el-button type="primary" @click="openDialog('chargeback')">添加扣款</el-button>
        <el-button type="primary" @click="openDialog('transfer')">添加转账</el-button>
        <el-button type="primary" @click="openDialog('loanClear')">借贷利息清算</el-button>
        <el-button type="primary" @click="openDialog('loan')">借贷款申请</el-button>
        <el-select v-model="filters.accountType" style="width: 140px" @change="reload">
          <el-option value="1" label="人民币账户" />
          <el-option value="2" label="美金账户" />
        </el-select>
      </div>
    </div>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item :label="timeLabel">
        <el-date-picker
          v-model="filters.addTime"
          type="date"
          value-format="YYYY-MM-DD"
          clearable
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item :label="orderLabel">
        <el-input v-model="filters.czNum" clearable style="width: 160px" />
      </el-form-item>
      <el-form-item :label="userLabel">
        <el-input v-model="filters.userName" clearable style="width: 140px" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.logStatus" clearable placeholder="全部状态" style="width: 130px">
          <el-option value="" label="全部状态" />
          <el-option value="2" label="待审核" />
          <el-option value="3" label="待打款" />
          <el-option value="4" label="待付款" />
          <el-option value="5" label="待确认" />
          <el-option value="1" label="交易成功" />
          <el-option value="-1" label="已驳回" />
          <el-option value="-2" label="取消申请" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" align="center" label="#" />
      <el-table-column :label="orderLabel" min-width="160">
        <template #default="{ row }">
          <span class="linkish">{{ row.czNum || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="150">
        <template #default="{ row }">{{ formatTime(row.addTime) }}</template>
      </el-table-column>
      <el-table-column :label="userLabel" min-width="110" prop="userName" show-overflow-tooltip />
      <el-table-column v-if="showInUser" label="转入用户" min-width="110" prop="inUserName" />
      <el-table-column :label="amountLabel" width="140" align="right">
        <template #default="{ row }">{{ money(row.logAmount) }}</template>
      </el-table-column>
      <el-table-column prop="pdLogInfo" label="备注" min-width="160" show-overflow-tooltip />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">{{ statusLabel(row.logStatus) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center" fixed="right">
        <template #default="{ row }">
          <template v-if="Number(row.logStatus) === 2">
            <el-button link type="primary" @click="handlePass(row, 1)">通过</el-button>
            <el-button link type="danger" @click="handlePass(row, -1)">驳回</el-button>
          </template>
          <template v-else-if="[3, 4, 5].includes(Number(row.logStatus))">
            <el-button link type="primary" @click="handlePass(row, 1)">确认</el-button>
          </template>
          <template v-else-if="Number(row.logStatus) === 1">
            <el-button type="primary" size="small" @click="onUploadVoucher(row)">上传凭证</el-button>
          </template>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="sizes, total, prev, pager, next"
        :total="total"
        @size-change="reload"
        @current-change="() => load(listParams())"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="账户类型" required>
          <el-select v-model="form.accountType" style="width: 100%">
            <el-option :value="1" label="人民币账户" />
            <el-option :value="2" label="美金账户" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户" required>
          <el-select
            v-model="form.userId"
            filterable
            remote
            clearable
            :remote-method="searchUsers"
            :loading="userLoading"
            placeholder="搜索用户名/姓名"
            style="width: 100%"
          >
            <el-option
              v-for="u in userOptions"
              :key="String(u.id)"
              :label="userOptionLabel(u)"
              :value="String(u.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dialogKind === 'transfer'" label="转入用户" required>
          <el-select
            v-model="form.inUserId"
            filterable
            remote
            clearable
            :remote-method="searchUsers"
            :loading="userLoading"
            placeholder="搜索转入用户"
            style="width: 100%"
          >
            <el-option
              v-for="u in userOptions"
              :key="`in-${u.id}`"
              :label="userOptionLabel(u)"
              :value="String(u.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input v-model="form.logAmount" placeholder="请输入金额" />
        </el-form-item>
        <el-form-item v-if="dialogKind === 'withdraw'" label="开户行">
          <el-input v-model="form.bankName" />
        </el-form-item>
        <el-form-item v-if="dialogKind === 'withdraw'" label="银行卡号">
          <el-input v-model="form.cardNum" />
        </el-form-item>
        <el-form-item
          v-if="dialogKind === 'chargeback' || dialogKind === 'loanClear'"
          label="立即入账"
        >
          <el-switch v-model="form.autoPass" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.pdLogInfo" type="textarea" :rows="2" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  fetchAccountLogList,
  fetchFundUsers,
  passAccountLog,
  submitAccountApply,
  submitChargeback,
  submitLoanApply,
  submitLoanClear,
  submitTransferApply,
} from '@/api/fund'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

type DialogKind = 'recharge' | 'withdraw' | 'chargeback' | 'transfer' | 'loan' | 'loanClear'

const typeTabs = [
  { value: '1', label: '充值记录' },
  { value: '2', label: '提现记录' },
  { value: '10', label: '扣款记录' },
  { value: '-1', label: '其他记录' },
  { value: '11', label: '转账记录' },
  { value: '12', label: '借贷记录' },
  { value: '14', label: '借调转账' },
  { value: '17', label: '借贷利息清算' },
] as const

const filters = reactive({
  accType: '1',
  accountType: '1',
  addTime: '',
  czNum: '',
  userName: '',
  logStatus: '',
})

const dialogVisible = ref(false)
const saving = ref(false)
const dialogKind = ref<DialogKind>('recharge')
const userLoading = ref(false)
const userOptions = ref<Record<string, unknown>[]>([])
const form = reactive({
  accountType: 1,
  userId: '',
  inUserId: '',
  logAmount: '',
  bankName: '',
  cardNum: '',
  pdLogInfo: '',
  autoPass: false,
})

const tabMeta = computed(() => {
  const map: Record<string, { time: string; order: string; user: string; amount: string }> = {
    '1': { time: '充值时间', order: '充值单号', user: '充值账户', amount: '充值金额' },
    '2': { time: '提现时间', order: '提现单号', user: '提现账户', amount: '提现金额' },
    '10': { time: '扣款时间', order: '扣款单号', user: '扣款账户', amount: '扣款金额' },
    '-1': { time: '时间', order: '单号', user: '账户', amount: '金额' },
    '11': { time: '转账时间', order: '转账单号', user: '转出账户', amount: '转账金额' },
    '12': { time: '借贷时间', order: '借贷单号', user: '借贷账户', amount: '借贷金额' },
    '14': { time: '时间', order: '单号', user: '账户', amount: '金额' },
    '17': { time: '清算时间', order: '清算单号', user: '账户', amount: '清算金额' },
  }
  return map[filters.accType] || map['1']
})

const timeLabel = computed(() => tabMeta.value.time)
const orderLabel = computed(() => tabMeta.value.order)
const userLabel = computed(() => tabMeta.value.user)
const amountLabel = computed(() => {
  const cur = filters.accountType === '2' ? '美金' : '人民币'
  return `${tabMeta.value.amount}(${cur})`
})
const showInUser = computed(() => ['11', '14'].includes(filters.accType))

const dialogTitle = computed(() => {
  const map: Record<DialogKind, string> = {
    recharge: '添加充值',
    withdraw: '添加提现',
    chargeback: '添加扣款',
    transfer: '添加转账',
    loan: '借贷款申请',
    loanClear: '借贷利息清算',
  }
  return map[dialogKind.value]
})

function listParams() {
  return {
    accType: filters.accType,
    accountType: filters.accountType,
    addTime: filters.addTime,
    czNum: filters.czNum,
    userName: filters.userName,
    logStatus: filters.logStatus,
  }
}

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchAccountLogList({ ...params, ...listParams() })
)

function money(v: unknown) {
  const n = Number(v)
  if (Number.isNaN(n)) return '-'
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function formatTime(v: unknown) {
  const s = String(v || '')
  if (!s) return '-'
  return s.length >= 16 ? s.slice(0, 16) : s
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

function userOptionLabel(u: Record<string, unknown>) {
  const name = String(u.userName || '')
  const trueName = String(u.trueName || '')
  return trueName ? `${name} (${trueName})` : name
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

function reload() {
  pagination.page = 1
  return load(listParams())
}

function onTabChange() {
  filters.logStatus = ''
  filters.czNum = ''
  filters.addTime = ''
  reload()
}

function openDialog(kind: DialogKind) {
  dialogKind.value = kind
  Object.assign(form, {
    accountType: Number(filters.accountType) || 1,
    userId: '',
    inUserId: '',
    logAmount: '',
    bankName: '',
    cardNum: '',
    pdLogInfo: '',
    autoPass: kind === 'chargeback',
  })
  dialogVisible.value = true
  searchUsers('')
}

async function submitDialog() {
  const amount = Number(form.logAmount)
  if (!amount || amount <= 0) {
    ElMessage.warning('请输入正确金额')
    return
  }
  if (!form.userId) {
    ElMessage.warning('请选择用户')
    return
  }
  if (dialogKind.value === 'transfer' && !form.inUserId) {
    ElMessage.warning('请选择转入用户')
    return
  }
  saving.value = true
  try {
    const base = {
      userId: form.userId,
      accountType: form.accountType,
      logAmount: amount,
      pdLogInfo: form.pdLogInfo,
    }
    let res
    if (dialogKind.value === 'recharge') {
      res = await submitAccountApply({ ...base, accType: 1 })
    } else if (dialogKind.value === 'withdraw') {
      res = await submitAccountApply({
        ...base,
        accType: 2,
        bankName: form.bankName,
        branKCard: form.cardNum,
      })
    } else if (dialogKind.value === 'chargeback') {
      res = await submitChargeback({
        ...base,
        logStatus: form.autoPass ? 1 : 5,
      })
    } else if (dialogKind.value === 'transfer') {
      res = await submitTransferApply({ ...base, inUserId: form.inUserId })
    } else if (dialogKind.value === 'loanClear') {
      res = await submitLoanClear({
        ...base,
        logStatus: form.autoPass ? 1 : 2,
      })
    } else {
      res = await submitLoanApply(base)
    }
    if (isAjaxOk(res)) {
      ElMessage.success('提交成功')
      dialogVisible.value = false
      await reload()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '提交失败'))
    }
  } finally {
    saving.value = false
  }
}

async function handlePass(row: Record<string, unknown>, status: number) {
  const tip = status === 1 ? '确认通过该记录？' : '确认驳回该记录？'
  await ElMessageBox.confirm(tip, '提示', { type: 'warning' })
  const res = await passAccountLog(String(row.id), status)
  if (isAjaxOk(res)) {
    ElMessage.success('操作成功')
    await load(listParams())
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}

function onUploadVoucher(row: Record<string, unknown>) {
  ElMessage.info(`凭证上传功能迁移中（单号：${row.czNum || row.id}）`)
}

onMounted(() => reload())
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.type-tabs {
  flex: 1;
  min-width: 0;
}
.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}
.filter-form {
  margin-bottom: 12px;
}
.linkish {
  color: #409eff;
  cursor: default;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
