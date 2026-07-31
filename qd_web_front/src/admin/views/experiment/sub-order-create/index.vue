<template>
  <div v-loading="loading" class="create-page">
    <header class="page-head">
      <button type="button" class="back-link" @click="goBack">← 返回详情</button>
      <h2>{{ titleText }}</h2>
      <p v-if="parent" class="sub">
        来源主单
        <span class="mono">{{ parent.orderId }}</span>
      </p>
    </header>

    <template v-if="parent">
      <!-- 实验分包子订单：对齐 Java purchase_create_orders 上半表单 -->
      <section v-if="isSubcontract" class="form-card">
        <el-form label-width="120px" class="create-form">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="来源单号">
                <strong class="mono">{{ parent.orderId }}</strong>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="下单时间" required>
                <el-date-picker
                  v-model="form.orderTime"
                  type="datetime"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  placeholder="yyyy-mm-dd HH:mm:ss"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="销售主管" required>
                <el-select
                  v-model="form.saleManager"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="u in managerOptions"
                    :key="String(u.id)"
                    :label="userLabel(u)"
                    :value="String(u.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="预计完成时间" required>
                <el-date-picker
                  v-model="form.deliveryTime"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="实验室测试主管" required>
                <el-select
                  v-model="form.testManager"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="u in testManagerOptions"
                    :key="String(u.id)"
                    :label="userLabel(u)"
                    :value="String(u.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="付款方式" required>
                <el-select
                  v-model="form.payWay"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                  @change="onPayWayChange"
                >
                  <el-option
                    v-for="p in paytypeOptions"
                    :key="String(p.id)"
                    :label="String(p.name || '')"
                    :value="String(p.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="实验分包公司" required>
                <div class="inline-ops">
                  <el-select
                    v-model="form.stockCompanyName"
                    filterable
                    clearable
                    allow-create
                    default-first-option
                    placeholder="请选择或输入"
                    style="flex: 1"
                  >
                    <el-option
                      v-for="c in companyOptions"
                      :key="String(c.id || c.name)"
                      :label="String(c.name || c.companyName || '')"
                      :value="String(c.name || c.companyName || '')"
                    />
                  </el-select>
                  <el-button type="primary" link @click="reloadCompanies">刷新</el-button>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="订单币种" required>
                <el-select v-model="form.currencyType" style="width: 100%">
                  <el-option label="人民币" value="1" />
                  <el-option label="美金" value="2" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="是否开票">
                <el-switch
                  v-model="form.invoiceOn"
                  inline-prompt
                  active-text="ON"
                  inactive-text="OFF"
                />
              </el-form-item>
            </el-col>
            <el-col v-if="form.invoiceOn" :span="12">
              <el-form-item label="进项开票类型" required>
                <el-select
                  v-model="form.inBillTypeId"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="b in billTypeOptions"
                    :key="String(b.id)"
                    :label="String(b.name || '')"
                    :value="String(b.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col v-if="form.invoiceOn" :span="12">
              <el-form-item label="税率" required>
                <el-select
                  v-model="form.taxes"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="t in taxOptions"
                    :key="String(t.id)"
                    :label="taxLabel(t)"
                    :value="String(t.taxValue ?? t.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col v-for="(ct, idx) in form.collectionTimes" :key="`ct-${idx}`" :span="12">
              <el-form-item :label="`预计付款时间${form.collectionTimes.length > 1 ? idx + 1 : ''}`" required>
                <el-date-picker
                  v-model="form.collectionTimes[idx]"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="yyyy-mm-dd"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="备注">
                <el-input
                  v-model="form.msg"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入内容"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </section>

      <el-alert
        v-else-if="!isExperiment"
        type="info"
        :closable="false"
        show-icon
        class="hint"
        title="仅显示主单中待处理（op_status=1）的产品行。创建后将生成子订单并挂接所选行。"
      />

      <!-- 实验子订单：对齐 Java purchase_create_orders -->
      <section v-if="isExperiment" class="form-card">
        <el-form label-width="120px" class="create-form">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="来源单号">
                <strong class="mono">{{ parent.orderId }}</strong>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="下单时间" required>
                <el-date-picker
                  v-model="form.orderTime"
                  type="datetime"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  placeholder="yyyy-mm-dd HH:mm:ss"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="实验室主管" required>
                <el-select
                  v-model="form.saleManager"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="u in managerOptions"
                    :key="String(u.id)"
                    :label="userLabel(u)"
                    :value="String(u.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="销售人员" required>
                <el-select
                  v-model="form.saleUser"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="u in staffOptions"
                    :key="String(u.id)"
                    :label="userLabel(u)"
                    :value="String(u.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="仓库管理员" required>
                <el-select
                  v-model="form.stockUser"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="u in staffOptions"
                    :key="'w-' + String(u.id)"
                    :label="userLabel(u)"
                    :value="String(u.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="预计收货时间" required>
                <el-date-picker
                  v-model="form.deliveryTime"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="备注">
                <el-input v-model="form.msg" type="textarea" :rows="3" placeholder="请输入内容" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </section>

      <el-table
        :data="pendingRows"
        border
        stripe
        class="line-table"
        @selection-change="onSel"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="childOrderId" label="子订单编号" min-width="150" show-overflow-tooltip />
        <el-table-column prop="goodsName" label="产品名称" min-width="120" show-overflow-tooltip />
        <el-table-column prop="goodsSpec" label="产品型号" min-width="100" show-overflow-tooltip />
        <el-table-column
          v-if="isSubcontract"
          prop="goodsBrand"
          label="产品品牌"
          min-width="90"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="isSubcontract"
          prop="goodsCount"
          label="数量"
          width="70"
          align="center"
        />
        <el-table-column prop="projectName" label="实验测试项目" min-width="120" show-overflow-tooltip />
        <el-table-column v-if="isSubcontract || isExperiment" label="测试人员" width="150">
          <template #default="{ row }">
            <el-select
              v-model="row._testUserId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 130px"
            >
              <el-option label="抢单" value="22" />
              <el-option
                v-for="u in staffOptions"
                :key="String(u.id)"
                :label="userLabel(u)"
                :value="String(u.id)"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column v-if="isExperiment" label="预计完成时间" width="170">
          <template #default="{ row }">
            <el-date-picker
              v-model="row._finishTime"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="预计完成"
              style="width: 158px"
            />
          </template>
        </el-table-column>
        <el-table-column v-if="isSubcontract" label="分包单价" width="120">
          <template #default="{ row }">
            <el-input
              v-model="row._costPrice"
              placeholder="单价"
              @input="recalcTotal"
            />
          </template>
        </el-table-column>
        <el-table-column v-if="!isSubcontract && !isExperiment" prop="price" label="单价" width="90" align="right" />
        <el-table-column v-if="!isSubcontract && !isExperiment" prop="orderStatusLabel" label="状态" width="100" />
      </el-table>

      <div class="actions">
        <el-button
          type="warning"
          :loading="saving"
          :disabled="!selected.length"
          @click="onCreate"
        >
          {{ isSubcontract ? '提交审核' : '创建子订单' }}
        </el-button>
        <span v-if="isSubcontract" class="total-cost">总成本：{{ totalCostText }}</span>
        <el-button @click="goBack">取消</el-button>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="主单不存在或没有待处理行" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createExpSubOrder, getExpOrderDetail } from '@admin/api/experiment'
import { fetchEnterpriseList } from '@admin/api/member'
import {
  fetchBillTypeAll,
  fetchPaytypeAll,
  fetchTaxAll,
  formatTaxDisplay,
} from '@admin/api/order-settings'
import { fetchUserList } from '@admin/api/system'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const route = useRoute()
const router = useRouter()
const saleOrderId = String(route.query.saleOrderId || route.query.parentId || '')

const loading = ref(false)
const saving = ref(false)
const parent = ref<Record<string, unknown> | null>(null)
const children = ref<Record<string, unknown>[]>([])
const selected = ref<Record<string, unknown>[]>([])

const managerOptions = ref<Record<string, unknown>[]>([])
const testManagerOptions = ref<Record<string, unknown>[]>([])
const staffOptions = ref<Record<string, unknown>[]>([])
const companyOptions = ref<Record<string, unknown>[]>([])
const paytypeOptions = ref<Record<string, unknown>[]>([])
const billTypeOptions = ref<Record<string, unknown>[]>([])
const taxOptions = ref<Record<string, unknown>[]>([])

const form = reactive({
  saleManager: '',
  saleUser: '',
  stockUser: '',
  testManager: '',
  stockCompanyName: '',
  invoiceOn: true,
  inBillTypeId: '',
  taxes: '',
  orderTime: '',
  deliveryTime: '',
  payWay: '',
  currencyType: '1',
  collectionTimes: [] as string[],
  msg: '',
})

const titleText = computed(() =>
  String(parent.value?.orderType || '') === '8' ? '创建实验分包子订单' : '创建实验子订单'
)
const isSubcontract = computed(() => String(parent.value?.orderType || '') === '8')
const isExperiment = computed(() => String(parent.value?.orderType || '') === '6')

const pendingRows = computed(() =>
  children.value.filter((r) => Number(r.opStatus ?? 0) === 1)
)

const totalCostText = computed(() => {
  let sum = 0
  for (const row of selected.value) {
    const n = Number(row._costPrice)
    const qty = Number(row.goodsCount || 1)
    if (Number.isFinite(n) && n >= 0) sum += n * (Number.isFinite(qty) && qty > 0 ? qty : 1)
  }
  return sum.toFixed(2)
})

function userLabel(u: Record<string, unknown>) {
  const name = String(u.trueName || u.userName || '')
  const uname = String(u.userName || '')
  return name && uname && name !== uname ? `${name}（${uname}）` : name || uname || String(u.id)
}

function taxLabel(t: Record<string, unknown>) {
  const name = String(t.name || '')
  const val = formatTaxDisplay(Number(t.taxValue))
  return name ? `${name} ${val}` : val
}

function goBack() {
  if (saleOrderId) {
    router.push({ name: 'ExperimentOrderDetail', params: { id: saleOrderId } })
  } else {
    router.push('/experiment/subcontract-orders')
  }
}

function onSel(rows: Record<string, unknown>[]) {
  selected.value = rows
  recalcTotal()
}

function recalcTotal() {
  // computed 自动更新
}

function onPayWayChange(id: string) {
  const pt = paytypeOptions.value.find((p) => String(p.id) === String(id))
  const nums = Math.max(0, Number(pt?.nums || 0))
  form.collectionTimes = Array.from({ length: nums }, () => '')
}

async function reloadCompanies() {
  try {
    const res = await fetchEnterpriseList({ start: 0, length: 500, draw: 1 })
    companyOptions.value = res.data || []
  } catch {
    companyOptions.value = []
  }
}

async function loadOptions() {
  const silent = { silentError: true } as const
  const [mgr, testMgr, staff, payRes, billRes, taxRes] = await Promise.all([
    fetchUserList({ start: 0, length: 500, type: 1, draw: 1 }, silent),
    fetchUserList({ start: 0, length: 500, type: 3, draw: 1 }, silent),
    fetchUserList({ start: 0, length: 500, type: -1, draw: 1 }, silent),
    fetchPaytypeAll(),
    fetchBillTypeAll(2),
    fetchTaxAll(),
  ])
  managerOptions.value = mgr.data || []
  testManagerOptions.value = testMgr.data || []
  staffOptions.value = staff.data || []
  paytypeOptions.value = (payRes.data || []).filter((p) => !p.delStatus && Number(p.del_status || 0) === 0)
  billTypeOptions.value = (billRes.data || []).filter((b) => !b.delStatus)
  if (isAjaxOk(taxRes) && Array.isArray(taxRes.obj)) {
    taxOptions.value = taxRes.obj as Record<string, unknown>[]
  } else if (Array.isArray(taxRes.data)) {
    taxOptions.value = taxRes.data as Record<string, unknown>[]
  }
  await reloadCompanies()
}

function nowOrderTime() {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

async function load() {
  if (!saleOrderId) {
    ElMessage.warning('缺少主单 ID')
    return
  }
  loading.value = true
  try {
    const res = await getExpOrderDetail(saleOrderId)
    if (!isAjaxOk(res) || !res.obj) {
      parent.value = null
      children.value = []
      ElMessage.error(ajaxErrorMessage(res, '加载主单失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    parent.value = obj
    children.value = ((obj.children as Record<string, unknown>[]) || []).map((c) => ({
      ...c,
      _testUserId: '',
      _costPrice: c.price != null ? String(c.price) : '',
      _finishTime: '',
    }))
    const ot = String(obj.orderType || '')
    if (ot === '8' || ot === '6') {
      await loadOptions()
      form.orderTime = nowOrderTime()
    }
  } finally {
    loading.value = false
  }
}

function validateSubcontract(): string | null {
  if (!form.saleManager) return '请选择销售主管'
  if (!form.testManager) return '请选择实验室测试主管'
  if (!form.stockCompanyName.trim()) return '请选择实验分包公司'
  if (!form.orderTime) return '请填写下单时间'
  if (!form.deliveryTime) return '请填写预计完成时间'
  if (!form.payWay) return '请选择付款方式'
  if (!form.currencyType) return '请选择订单币种'
  if (form.invoiceOn) {
    if (!form.inBillTypeId) return '请选择进项开票类型'
    if (!form.taxes) return '请选择税率'
  }
  if (form.collectionTimes.length) {
    if (form.collectionTimes.some((t) => !t)) return '请填写预计付款时间'
  }
  for (const row of selected.value) {
    if (!row._testUserId) return '所选行测试人员不能为空'
    const price = String(row._costPrice ?? '').trim()
    if (!price) return '所选分包单价不能为空'
    if (!/^\d+(\.\d{1,2})?$/.test(price)) return '分包单价格式错误（最多两位小数）'
  }
  return null
}

function validateExperiment(): string | null {
  if (!form.orderTime) return '请填写下单时间'
  if (!form.saleManager) return '请选择实验室主管'
  if (!form.saleUser) return '请选择销售人员'
  if (!form.stockUser) return '请选择仓库管理员'
  if (!form.deliveryTime) return '请填写预计收货时间'
  return null
}

async function onCreate() {
  const ids = selected.value.map((r) => r.id).filter((id) => id != null)
  if (!ids.length) {
    ElMessage.warning('请至少选择一个子订单')
    return
  }
  if (isSubcontract.value) {
    const err = validateSubcontract()
    if (err) {
      ElMessage.warning(err)
      return
    }
  } else if (isExperiment.value) {
    const err = validateExperiment()
    if (err) {
      ElMessage.warning(err)
      return
    }
  }
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      saleOrderId,
      childIds: ids,
    }
    if (isSubcontract.value) {
      payload.saleManager = form.saleManager
      payload.testManager = form.testManager
      payload.stockCompanyName = form.stockCompanyName.trim()
      payload.invoiceType = form.invoiceOn ? 1 : 0
      payload.inBillTypeId = form.invoiceOn ? form.inBillTypeId : ''
      payload.taxes = form.invoiceOn ? form.taxes : ''
      payload.orderTime = form.orderTime
      payload.deliveryTime = form.deliveryTime
      payload.payWay = form.payWay
      payload.currencyType = form.currencyType
      payload.collectionTime = form.collectionTimes.filter(Boolean).join(',')
      payload.msg = form.msg
      payload.submitAudit = true
      payload.testUserIds = selected.value.map((r) => String(r._testUserId || ''))
      payload.costPrices = selected.value.map((r) => String(r._costPrice || ''))
      payload.totalPrice = Number(totalCostText.value)
    } else if (isExperiment.value) {
      payload.saleManager = form.saleManager
      payload.saleUser = form.saleUser
      payload.stockUser = form.stockUser
      payload.orderTime = form.orderTime
      payload.deliveryTime = form.deliveryTime
      payload.msg = form.msg
      payload.testUserIds = selected.value.map((r) => String(r._testUserId || '22'))
      payload.finishTimes = selected.value.map((r) => String(r._finishTime || ''))
    }
    const res = await createExpSubOrder(payload)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '创建失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '创建成功'))
    const newId = (res.obj as { id?: number } | undefined)?.id
    if (newId) {
      router.push({ name: 'ExperimentOrderDetail', params: { id: String(newId) } })
    } else {
      goBack()
    }
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.create-page {
  padding: 8px 4px 32px;
}
.page-head {
  margin-bottom: 14px;
}
.page-head h2 {
  margin: 0;
  font-size: 20px;
}
.sub {
  margin: 6px 0 0;
  color: #5f7068;
  font-size: 13px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.back-link {
  border: 0;
  background: transparent;
  color: #1f6f5b;
  padding: 0;
  margin-bottom: 8px;
  cursor: pointer;
  font-size: 13px;
}
.hint {
  margin-bottom: 12px;
}
.form-card {
  margin-bottom: 16px;
  padding: 16px 16px 4px;
  background: #fff;
  border: 1px solid #d7e0db;
  border-radius: 10px;
}
.inline-ops {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.line-table {
  margin-bottom: 16px;
}
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.total-cost {
  font-size: 16px;
  font-weight: 600;
  color: #1f2a24;
}
</style>
