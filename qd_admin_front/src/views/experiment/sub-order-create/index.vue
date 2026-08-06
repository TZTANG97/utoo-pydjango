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

      <!-- 实验子订单：对齐小程序 add_em_sub_order -->
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
              <el-form-item label="客户名称">
                <el-select
                  v-model="form.customerName"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                  @change="onCustomerChange"
                >
                  <el-option
                    v-for="c in customerOptions"
                    :key="String(c.id)"
                    :label="String(c.name || '')"
                    :value="String(c.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="所属公司" required>
                <el-select
                  v-model="form.supplierName"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="s in supplierOptions"
                    :key="String(s.id)"
                    :label="String(s.companyName || s.company_name || s.name || '')"
                    :value="String(s.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="客户账号">
                <el-select
                  v-model="form.customUserId"
                  filterable
                  clearable
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option
                    v-for="a in accountOptions"
                    :key="String(a.id)"
                    :label="String(a.mobile || a.id || '')"
                    :value="String(a.id)"
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
              <el-form-item label="订单资料">
                <div class="file-ops">
                  <el-upload
                    :show-file-list="false"
                    :http-request="onUploadOrderFile"
                    accept="*/*"
                  >
                    <el-button type="primary" link :loading="uploading">上传</el-button>
                  </el-upload>
                  <div v-if="orderFiles.length" class="file-list">
                    <div v-for="(f, idx) in orderFiles" :key="String(f.id || idx)" class="file-item">
                      <span>{{ String(f.info || f.name || '附件') }}</span>
                      <el-button type="danger" link @click="removeOrderFile(idx)">删除</el-button>
                    </div>
                  </div>
                </div>
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
          v-if="isSubcontract || isExperiment"
          prop="goodsBrand"
          label="产品品牌"
          min-width="90"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="isSubcontract || isExperiment"
          prop="goodsCount"
          label="数量"
          width="70"
          align="center"
        />
        <el-table-column prop="projectName" label="实验测试项目" min-width="120" show-overflow-tooltip />
        <el-table-column
          v-if="isExperiment"
          prop="className"
          label="实验分类"
          min-width="100"
          show-overflow-tooltip
        />
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
                v-for="u in testerOptionsForRow(row)"
                :key="String(u.id)"
                :label="userLabel(u)"
                :value="String(u.id)"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column v-if="isExperiment" label="实验平台" width="170">
          <template #default="{ row }">
            <el-select
              v-model="row._lineId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 150px"
            >
              <el-option
                v-for="p in platformOptions"
                :key="String(p.id)"
                :label="String(p.lineNum || p.line_num || p.id || '')"
                :value="String(p.id)"
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
import { createExpSubOrder, getExpOrderDetail, uploadExpOrderFile } from '@/api/experiment'
import { fetchCustomerAccounts, fetchCustomerNamesExp, fetchEnterpriseList } from '@/api/member'
import { fetchSelLineList } from '@/api/inventory'
import {
  fetchBillTypeAll,
  fetchPaytypeAll,
  fetchTaxAll,
  formatTaxDisplay,
} from '@/api/order-settings'
import { fetchSupplierAll, fetchTestUsers, fetchUserList } from '@/api/system'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

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
/** 实验子单测试人员：按 classId 缓存 queryTestUsers 结果 */
const testerByClass = ref<Record<string, Record<string, unknown>[]>>({})
const testerDefault = ref<Record<string, unknown>[]>([])
const companyOptions = ref<Record<string, unknown>[]>([])
const customerOptions = ref<Record<string, unknown>[]>([])
const supplierOptions = ref<Record<string, unknown>[]>([])
const accountOptions = ref<Record<string, unknown>[]>([])
const platformOptions = ref<Record<string, unknown>[]>([])
const paytypeOptions = ref<Record<string, unknown>[]>([])
const billTypeOptions = ref<Record<string, unknown>[]>([])
const taxOptions = ref<Record<string, unknown>[]>([])
const orderFiles = ref<Record<string, unknown>[]>([])
const uploading = ref(false)

const form = reactive({
  saleManager: '',
  saleUser: '',
  stockUser: '',
  testManager: '',
  stockCompanyName: '',
  customerName: '',
  supplierName: '',
  customUserId: '',
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

function testerOptionsForRow(row: Record<string, unknown>) {
  if (isSubcontract.value) return staffOptions.value
  const cid = String(row.classId || parent.value?.classId || '')
  if (cid && testerByClass.value[cid]?.length) return testerByClass.value[cid]
  return testerDefault.value
}

async function loadTestersForClasses(classIds: string[]) {
  const silent = { silentError: true } as const
  const uniq = Array.from(new Set(classIds.map((x) => String(x || '').trim()).filter(Boolean)))
  if (!uniq.length) {
    try {
      const res = await fetchTestUsers('', silent)
      testerDefault.value = Array.isArray(res.obj) ? (res.obj as Record<string, unknown>[]) : []
    } catch {
      testerDefault.value = []
    }
    return
  }
  await Promise.all(
    uniq.map(async (cid) => {
      if (testerByClass.value[cid]?.length) return
      try {
        const res = await fetchTestUsers(cid, silent)
        testerByClass.value[cid] = Array.isArray(res.obj)
          ? (res.obj as Record<string, unknown>[])
          : []
      } catch {
        testerByClass.value[cid] = []
      }
    })
  )
  // 默认取第一个分类列表，便于无 classId 行回退
  const first = uniq[0]
  if (first) testerDefault.value = testerByClass.value[first] || []
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

async function reloadCustomerAccounts(parentId?: string) {
  try {
    const res = await fetchCustomerAccounts(parentId || '')
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    accountOptions.value = list as Record<string, unknown>[]
  } catch {
    accountOptions.value = []
  }
}

async function onCustomerChange(id: string) {
  form.customUserId = ''
  await reloadCustomerAccounts(id || '')
}

async function onUploadOrderFile(options: { file: File }) {
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('orderdata', options.file)
    fd.append('type', '3')
    const res = await uploadExpOrderFile(fd)
    if (!isAjaxOk(res) || !res.obj) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    orderFiles.value.push(res.obj as Record<string, unknown>)
    ElMessage.success(String(res.resMsg || '上传成功'))
  } catch (e: unknown) {
    const msg =
      e && typeof e === 'object' && 'response' in e
        ? ajaxErrorMessage((e as { response?: { data?: unknown } }).response?.data as never, '上传失败')
        : '上传失败'
    ElMessage.error(msg)
  } finally {
    uploading.value = false
  }
}

function removeOrderFile(idx: number) {
  orderFiles.value.splice(idx, 1)
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
  if (isExperiment.value) {
    try {
      const cust = await fetchCustomerNamesExp()
      const list = Array.isArray(cust.obj) ? cust.obj : Array.isArray(cust.data) ? cust.data : []
      customerOptions.value = list as Record<string, unknown>[]
    } catch {
      customerOptions.value = []
    }
    try {
      const sup = await fetchSupplierAll(silent)
      const list = Array.isArray(sup.obj) ? sup.obj : Array.isArray(sup.data) ? sup.data : []
      supplierOptions.value = list as Record<string, unknown>[]
    } catch {
      supplierOptions.value = []
    }
    try {
      // 对齐 Java /lab/selLineList.ajax（全量实验线，不依赖 lab_id）
      const lines = await fetchSelLineList({ start: 0, length: 999, draw: 1, line_num: '' })
      platformOptions.value = lines.data || []
    } catch {
      platformOptions.value = []
    }
    const classIds = children.value
      .map((c) => String(c.classId || parent.value?.classId || ''))
      .filter(Boolean)
    if (parent.value?.classId) classIds.push(String(parent.value.classId))
    await loadTestersForClasses(classIds)
    await reloadCustomerAccounts(form.customerName || '')
  }
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
      _testUserId: c.testUserId != null ? String(c.testUserId) : '',
      _lineId: c.lineId != null ? String(c.lineId) : '',
      _costPrice: c.price != null ? String(c.price) : '',
      _finishTime: '',
    }))
    const ot = String(obj.orderType || '')
    if (ot === '8' || ot === '6') {
      form.customerName = obj.customerId != null ? String(obj.customerId) : ''
      form.supplierName = obj.supplierId != null ? String(obj.supplierId) : ''
      form.customUserId = obj.customUserId != null ? String(obj.customUserId) : ''
      form.saleManager = obj.saleManagerId != null ? String(obj.saleManagerId) : ''
      form.saleUser = obj.saleUserId != null ? String(obj.saleUserId) : ''
      form.stockUser = obj.warehouseUserId != null ? String(obj.warehouseUserId) : ''
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
  // 对齐 Java：客户名称与客户账号不能同时为空（有一个即可）
  if (!form.customerName && !form.customUserId) return '客户名称和客户账号不能同时为空'
  if (!form.supplierName) return '请选择所属公司'
  if (!form.saleUser) return '请选择销售人员'
  if (!form.stockUser) return '请选择仓库管理员'
  if (!form.deliveryTime) return '请填写预计收货时间'
  for (const row of selected.value) {
    if (!row._testUserId) return '请选择测试人员'
    if (!row._lineId) return '请选择实验平台'
  }
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
      payload.warehouseUser = form.stockUser
      payload.customerName = form.customerName
      payload.supplierName = form.supplierName
      payload.customUserId = form.customUserId
      payload.orderTime = form.orderTime
      payload.deliveryTime = form.deliveryTime
      payload.msg = form.msg
      payload.orderdata = orderFiles.value
        .map((f) => f.id)
        .filter((id) => id != null && String(id) !== '')
        .join(',')
      payload.testUserIds = selected.value.map((r) => String(r._testUserId || '22'))
      payload.lineIds = selected.value.map((r) => String(r._lineId || ''))
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
.file-ops {
  width: 100%;
}
.file-list {
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #3a4a43;
  font-size: 13px;
}
</style>
