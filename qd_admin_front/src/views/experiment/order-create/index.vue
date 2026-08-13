<template>
  <div v-loading="loading" class="create-page">
    <header class="page-head">
      <button type="button" class="back-link" @click="goBack">← 返回列表</button>
      <h2>{{ pageTitle }}</h2>
    </header>

    <el-form label-width="120px" class="create-form">
      <el-row :gutter="16">
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
          <el-form-item label="订单类型" required>
            <el-select
              v-model="form.classId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 100%"
            >
              <el-option
                v-for="o in classOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
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
                v-for="o in managerOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="客户名称">
            <div class="inline-ops">
              <el-select
                v-model="form.customerName"
                filterable
                clearable
                placeholder="请选择"
                style="flex: 1"
                @change="onCustomerChange"
              >
                <el-option
                  v-for="o in customerOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="String(o.value)"
                />
              </el-select>
              <el-button type="primary" link @click="openAddCustomer">添加</el-button>
              <el-button type="primary" link @click="reloadCustomers">刷新</el-button>
            </div>
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
                v-for="o in accountOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
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
                v-for="o in saleUserOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="所属公司" required>
            <div class="inline-ops">
              <el-select
                v-model="form.supplierName"
                filterable
                clearable
                placeholder="请选择"
                style="flex: 1"
              >
                <el-option
                  v-for="o in supplierOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="String(o.value)"
                />
              </el-select>
              <el-button type="primary" link @click="openAddSupplier">添加</el-button>
              <el-button type="primary" link @click="reloadSuppliers">刷新</el-button>
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
          <el-form-item label="预计收货时间" required>
            <el-date-picker
              v-model="form.deliveryTime"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="yyyy-mm-dd"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="客户付款方式">
            <el-select
              v-model="form.payWay"
              filterable
              :clearable="!(isCopyMode && isOnlineOrder)"
              :disabled="isCopyMode && isOnlineOrder"
              :placeholder="isCopyMode && isOnlineOrder ? '线上订单不可修改' : '请选择'"
              style="width: 100%"
              @change="onPayWayChange"
            >
              <el-option
                v-for="o in payWayOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="String(o.value)"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="订单总价">
            <el-input v-model="form.totalPrice" clearable placeholder="自动汇总或手动填写" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否开票">
            <el-switch v-model="form.invoiceOn" inline-prompt active-text="ON" inactive-text="OFF" />
          </el-form-item>
        </el-col>

        <template v-if="form.invoiceOn">
          <el-col :span="12">
            <el-form-item label="出项开票类型" required>
              <el-select
                v-model="form.outBillTypeId"
                filterable
                clearable
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option
                  v-for="o in outBillOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税率" required>
              <el-select
                v-model="form.taxes"
                filterable
                clearable
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option
                  v-for="o in taxOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </template>

        <el-col :span="12">
          <el-form-item label="样品是否回收">
            <el-switch
              v-model="form.reversoOn"
              inline-prompt
              active-text="ON"
              inactive-text="OFF"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="分成比例" required>
            <div class="inline-ops">
              <el-button type="primary" @click="openShareDialog">添加分成比例</el-button>
              <span v-if="shareSummary" class="share-summary">{{ shareSummary }}</span>
              <span v-else class="share-hint">
                {{ isSubcontractCreate ? '利润合计须为 100%' : '毛利合计须为 100%' }}
              </span>
            </div>
          </el-form-item>
        </el-col>
        <el-col v-if="form.reversoOn" :span="12">
          <el-form-item label="样品回收地址">
            <el-input v-model="form.sendAddress" clearable />
          </el-form-item>
        </el-col>

        <template v-if="form.reversoOn">
          <el-col :span="12">
            <el-form-item label="收件人姓名">
              <el-input v-model="form.addresseeName" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="收件人电话">
              <el-input v-model="form.addresseeMobile" clearable />
            </el-form-item>
          </el-col>
        </template>

        <template v-if="collectionTimes.length">
          <el-col
            v-for="(ct, idx) in collectionTimes"
            :key="`ct-${idx}`"
            :span="12"
          >
            <el-form-item
              :label="`预计收款时间${collectionTimes.length > 1 ? idx + 1 : ''}`"
              required
            >
              <el-date-picker
                v-model="collectionTimes[idx]"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="yyyy-mm-dd"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </template>

        <el-col :span="24">
          <el-form-item label="订单资料">
            <div class="file-row">
              <el-upload :show-file-list="false" :http-request="onUploadOrderFile">
                <el-button type="primary" :loading="uploading">上传文件</el-button>
              </el-upload>
              <div v-if="orderFiles.length" class="file-list">
                <el-tag
                  v-for="(f, idx) in orderFiles"
                  :key="String(f.id || idx)"
                  closable
                  class="file-tag"
                  @close="removeOrderFile(idx)"
                >
                  {{ String(f.info || f.name || f.id || '附件') }}
                </el-tag>
              </div>
            </div>
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="订单备注">
            <el-input v-model="form.msg" type="textarea" :rows="3" placeholder="请输入内容" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <section class="lines-card">
      <div class="lines-head">
        <h3>产品明细</h3>
        <el-button type="primary" @click="addLine">添加产品</el-button>
      </div>
      <el-table :data="lines" border stripe>
        <el-table-column label="产品名称" min-width="140">
          <template #default="{ row }">
            <el-input
              v-model="row.goodsName"
              readonly
              placeholder="点击选择"
              @click="openGoodsPicker(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="产品型号" min-width="120">
          <template #default="{ row }">
            <el-select v-model="row.goodsSpec" filterable allow-create clearable style="width: 100%">
              <el-option v-for="s in row.specOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="产品品牌" min-width="100">
          <template #default="{ row }">
            <el-input v-model="row.goodsBrandName" readonly />
          </template>
        </el-table-column>
        <el-table-column label="数量" width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.goodsNums"
              :min="0.1"
              :step="1"
              controls-position="right"
              style="width: 100%"
              @change="recalcLine(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="实验测试项目" min-width="130">
          <template #default="{ row }">
            <el-input
              v-model="row.projectName"
              readonly
              placeholder="点击选择"
              @click="openProjectPicker(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="实验测试分类" min-width="120">
          <template #default="{ row }">
            <el-input v-model="row.className" readonly />
          </template>
        </el-table-column>
        <el-table-column label="实际测试金额" width="120">
          <template #default="{ row }">
            <el-input v-model="row.goodsPrice" @change="recalcLine(row)" />
          </template>
        </el-table-column>
        <el-table-column label="标准测试金额" width="120">
          <template #default="{ row }">
            <el-input v-model="row.referencePrice" />
          </template>
        </el-table-column>
        <el-table-column label="总价" width="100">
          <template #default="{ row }">
            <span>{{ lineTotal(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ $index }">
            <el-button type="primary" link @click="addLine">+</el-button>
            <el-button type="danger" link :disabled="lines.length <= 1" @click="removeLine($index)">
              -
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="sum-row">
        <span>总计数量：{{ totalNums }}</span>
        <span>总计金额：{{ totalAmount }}</span>
      </div>
    </section>

    <div class="save-bar">
      <el-button type="warning" size="large" :loading="saving" @click="onSave">保存</el-button>
    </div>

    <!-- 选商品 -->
    <el-dialog v-model="goodsDlg.visible" title="选择商品" width="720px" destroy-on-close>
      <el-form inline class="dlg-filter">
        <el-form-item label="名称">
          <el-input v-model="goodsDlg.keyword" clearable @keyup.enter="loadGoods" />
        </el-form-item>
        <el-button type="primary" @click="loadGoods">查询</el-button>
      </el-form>
      <el-table
        v-loading="goodsDlg.loading"
        :data="goodsDlg.rows"
        highlight-current-row
        max-height="360"
        @row-click="onPickGoods"
      >
        <el-table-column prop="goodsName" label="产品名称" min-width="140" />
        <el-table-column prop="goodsModel" label="型号" min-width="120" />
        <el-table-column prop="brandName" label="品牌" min-width="100" />
      </el-table>
    </el-dialog>

    <!-- 选测试项目 -->
    <el-dialog v-model="projectDlg.visible" title="选择实验测试项目" width="720px" destroy-on-close>
      <el-form inline class="dlg-filter">
        <el-form-item label="名称">
          <el-input v-model="projectDlg.keyword" clearable @keyup.enter="loadProjects" />
        </el-form-item>
        <el-button type="primary" @click="loadProjects">查询</el-button>
      </el-form>
      <el-table
        v-loading="projectDlg.loading"
        :data="projectDlg.rows"
        highlight-current-row
        max-height="360"
        @row-click="onPickProject"
      >
        <el-table-column prop="projectName" label="项目名称" min-width="160" />
        <el-table-column prop="className" label="分类" min-width="120" />
        <el-table-column prop="secName" label="二级" min-width="100" />
        <el-table-column label="测试金额" width="110" align="right">
          <template #default="{ row }">
            {{ formatPrice(row.testPrice ?? row.test_price) }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 分成比例：实验订单(6)=毛利+成本；分包订单(8)对齐 Java 仅利润分成 -->
    <el-dialog v-model="shareDlg.visible" title="添加分成比例" width="720px" destroy-on-close>
      <div class="share-block">
        <div class="share-block-head">
          <strong>{{ isSubcontractCreate ? '利润分成' : '毛利分成' }}</strong>
          <span class="share-hint">比例合计须为 100%</span>
          <el-button link type="primary" @click="addShareRow(profitRows)">添加一行</el-button>
        </div>
        <div v-for="(row, idx) in profitRows" :key="`p-${idx}`" class="share-row">
          <el-select
            v-model="row.userId"
            filterable
            clearable
            placeholder="分成人员"
            style="width: 220px"
          >
            <el-option
              v-for="u in shareUsers"
              :key="String(u.id)"
              :label="shareUserLabel(u)"
              :value="String(u.id)"
            />
          </el-select>
          <el-input v-model="row.value" placeholder="比例" style="width: 120px">
            <template #append>%</template>
          </el-input>
          <el-button link type="danger" @click="profitRows.splice(idx, 1)">删除</el-button>
        </div>
      </div>
      <div v-if="!isSubcontractCreate" class="share-block" style="margin-top: 16px">
        <div class="share-block-head">
          <strong>成本分成</strong>
          <span class="share-hint">按固定金额</span>
          <el-button link type="primary" @click="addShareRow(costRows)">添加一行</el-button>
        </div>
        <div v-for="(row, idx) in costRows" :key="`c-${idx}`" class="share-row">
          <el-select
            v-model="row.userId"
            filterable
            clearable
            placeholder="分成人员"
            style="width: 220px"
          >
            <el-option
              v-for="u in shareUsers"
              :key="String(u.id)"
              :label="shareUserLabel(u)"
              :value="String(u.id)"
            />
          </el-select>
          <el-input v-model="row.value" placeholder="金额" style="width: 140px" />
          <el-button link type="danger" @click="costRows.splice(idx, 1)">删除</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="shareDlg.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmShare">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchExpGoodsList,
  fetchManageOptions,
  fetchProjectList,
  getExpOrderDetail,
  submitExpOrder,
  uploadExpOrderFile,
} from '@/api/experiment'
import { fetchCustomerAccounts, fetchCustomerNamesExp } from '@/api/member'
import { fetchBillTypeAll, fetchPaytypeAll, fetchTaxAll } from '@/api/order-settings'
import { fetchSupplierAll, fetchUserList } from '@/api/system'
import { useTagsViewStore } from '@/stores/tags-view'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

type Opt = { value: string | number; label: string; nums?: number; scaleVal?: string }
type ShareRow = { userId: string; value: string }

type LineRow = {
  key: number
  goodsId: string
  goodsName: string
  goodsSpec: string
  goodsBrandId: string
  goodsBrandName: string
  goodsNums: number
  projectId: string
  projectName: string
  classId: string
  className: string
  goodsPrice: string
  referencePrice: string
  specOptions: string[]
}

const router = useRouter()
const route = useRoute()
const tagsView = useTagsViewStore()
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
let lineKey = 1

/** 对齐 Java editPage.htm?type=2 → experiment_copy_orders */
const copyFromId = computed(() => {
  const raw = route.query.copyFrom ?? route.query.id
  const s = String(raw || '').trim()
  return s && s !== '0' ? s : ''
})
const isCopyMode = computed(() => Boolean(copyFromId.value))
/** 6=实验订单，8=实验分包订单 */
const createOrderType = computed(() => {
  const raw = String(route.query.orderType || route.query.type || '6').trim()
  return raw === '8' ? '8' : '6'
})
const isSubcontractCreate = computed(() => createOrderType.value === '8')
const pageTitle = computed(() => {
  if (isSubcontractCreate.value) {
    return isCopyMode.value ? '复制实验分包订单' : '新增实验分包订单'
  }
  return isCopyMode.value ? '复制订单' : '新增实验订单'
})
/** Java 复制页：线上订单 is_online=1 时付款方式不可改 */
const isOnlineOrder = ref(false)

/** 关闭复制标签后异步 load 可能仍回调；route 已切回列表时禁止回写标签标题 */
function syncCreateTabTitle() {
  if (route.name !== 'ExperimentOrderCreate') return
  tagsView.updateViewTitle(route.path, pageTitle.value)
}

function pad2(n: number) {
  return n < 10 ? `0${n}` : String(n)
}
function nowStr() {
  const d = new Date()
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())} ${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`
}

const form = reactive({
  orderTime: nowStr(),
  classId: '' as string | number | '',
  saleManager: '' as string | number | '',
  customerName: '' as string | number | '',
  customUserId: '' as string | number | '',
  saleUser: '' as string | number | '',
  supplierName: '' as string | number | '',
  currencyType: '1',
  deliveryTime: '',
  payWay: '' as string | number | '',
  totalPrice: '',
  invoiceOn: true,
  outBillTypeId: '' as string | number | '',
  taxes: '' as string | number | '',
  reversoOn: true,
  sendAddress: '',
  addresseeName: '',
  addresseeMobile: '',
  msg: '',
  userScaleInfo: '',
  salecbUserScaleInfo: '',
})

const supplierOpts = ref<Opt[]>([])
const managerOpts = ref<Opt[]>([])
const saleUserOpts = ref<Opt[]>([])
const classOpts = ref<Opt[]>([])
const payWayOpts = ref<Opt[]>([])
const outBillOpts = ref<Opt[]>([])
const taxOpts = ref<Opt[]>([])
const customerOpts = ref<Opt[]>([])
const accountOpts = ref<Opt[]>([])
const orderFiles = ref<Record<string, unknown>[]>([])
const collectionTimes = ref<string[]>([])
const shareUsers = ref<Record<string, unknown>[]>([])
const profitRows = ref<ShareRow[]>([{ userId: '', value: '' }])
const costRows = ref<ShareRow[]>([{ userId: '', value: '' }])
const shareDlg = reactive({ visible: false })
const shareSummary = ref('')

function emptyLine(): LineRow {
  return {
    key: lineKey++,
    goodsId: '',
    goodsName: '',
    goodsSpec: '',
    goodsBrandId: '',
    goodsBrandName: '',
    goodsNums: 1,
    projectId: '',
    projectName: '',
    classId: '',
    className: '',
    goodsPrice: '',
    referencePrice: '',
    specOptions: [],
  }
}

const lines = ref<LineRow[]>([emptyLine()])

const goodsDlg = reactive({
  visible: false,
  loading: false,
  keyword: '',
  rows: [] as Record<string, unknown>[],
  target: null as LineRow | null,
})
const projectDlg = reactive({
  visible: false,
  loading: false,
  keyword: '',
  rows: [] as Record<string, unknown>[],
  target: null as LineRow | null,
})

function goBack() {
  router.push({ name: 'ExperimentOrders' })
}

function openAddCustomer() {
  window.open(router.resolve({ name: 'MemberEnterprise' }).href, '_blank')
}
function openAddSupplier() {
  window.open(router.resolve({ name: 'SystemCompanies' }).href, '_blank')
}

function mapUserRows(rows: Record<string, unknown>[]): Opt[] {
  return rows
    .map((u) => ({
      value: (u.id ?? '') as string | number,
      label: String(u.trueName || u.true_name || u.userName || u.user_name || u.id || ''),
    }))
    .filter((o) => o.value !== '' && o.value != null)
}

async function reloadSuppliers() {
  try {
    const res = await fetchSupplierAll({ silentError: true } as never)
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    supplierOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: String(r.id ?? ''),
        label: String(r.companyName || r.company_name || r.name || r.id || ''),
      }))
      .filter((o) => o.value !== '')
  } catch {
    supplierOpts.value = []
  }
}

async function reloadCustomers() {
  try {
    const res = await fetchCustomerNamesExp()
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    customerOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: String(r.id ?? ''),
        label: String(r.name || r.companyName || r.company_name || ''),
      }))
      .filter((o) => o.value !== '' && o.label)
  } catch {
    customerOpts.value = []
  }
}

async function reloadAccounts(parentId?: string | number) {
  try {
    const res = await fetchCustomerAccounts(parentId || '')
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    accountOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: String(r.id ?? ''),
        label: String(r.mobile || r.userName || r.trueName || r.id || ''),
      }))
      .filter((o) => o.value !== '')
  } catch {
    accountOpts.value = []
  }
}

async function onCustomerChange(id: string | number) {
  form.customUserId = ''
  await reloadAccounts(id || '')
}

function ensureOpt(list: Opt[], value: string | number | '', label?: string) {
  if (value === '' || value == null) return
  const key = String(value)
  const hit = list.find((o) => String(o.value) === key)
  const nice = String(label || '').trim()
  if (hit) {
    hit.value = key
    if (nice && (!hit.label || hit.label === key || hit.label === String(hit.value))) {
      hit.label = nice
    }
    return
  }
  list.push({ value: key, label: nice || key })
}

function bindSelectValue(
  list: Opt[],
  value: string | number | '',
  label?: string
): string {
  if (value === '' || value == null) return ''
  ensureOpt(list, value, label)
  return String(value)
}

function truthyOn(v: unknown): boolean {
  const s = String(v ?? '')
    .trim()
    .toLowerCase()
  return s === '1' || s === 'true' || s === 'on' || s === '是'
}

function refreshShareSummary() {
  const label = isSubcontractCreate.value ? '利润' : '毛利'
  const profitText = parseScalePairs(form.userScaleInfo)
    .filter((r) => r.userId)
    .map((r) => {
      const u = shareUsers.value.find((x) => String(x.id) === r.userId)
      return `${shareUserLabel(u || { id: r.userId })} ${r.value}%`
    })
    .join('，')
  shareSummary.value = profitText
    ? `${label}：${profitText}`
    : form.userScaleInfo
      ? `${label}：${form.userScaleInfo}`
      : ''
}

async function fillFromCopy(sourceId: string) {
  const res = await getExpOrderDetail(sourceId)
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载源订单失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  isOnlineOrder.value = Number(obj.isOnline ?? obj.is_online ?? 0) === 1

  // Java 复制页：下单时间需重新填写，其余字段带回
  form.orderTime = nowStr()
  form.classId = bindSelectValue(classOpts.value, obj.classId as string | number | '', String(obj.testClassName || ''))
  form.saleManager = bindSelectValue(
    managerOpts.value,
    obj.saleManagerId as string | number | '',
    String(obj.saleManager || obj.saleManagerTrueName || obj.saleManagerName || '')
  )
  form.saleUser = bindSelectValue(
    saleUserOpts.value,
    obj.saleUserId as string | number | '',
    String(obj.saleUser || obj.saleUserTrueName || obj.saleUserName || '')
  )
  form.supplierName = bindSelectValue(
    supplierOpts.value,
    obj.supplierId as string | number | '',
    String(obj.supplierName || '')
  )
  form.customerName = bindSelectValue(
    customerOpts.value,
    obj.customerId as string | number | '',
    String(obj.customerName || obj.companyName || '')
  )
  form.customUserId = String(obj.customUserId ?? '')
  form.currencyType = Number(obj.currencyType || 1) === 2 ? '2' : '1'
  form.deliveryTime = String(obj.deliveryTime || '').slice(0, 10)
  form.payWay = bindSelectValue(
    payWayOpts.value,
    obj.payWay as string | number | '',
    String(obj.payWayName || '')
  )
  form.totalPrice = obj.totalPrice != null ? String(obj.totalPrice) : ''
  form.invoiceOn = Number(obj.invoiceType) === 1 || String(obj.invoiceLabel || '') === '是'
  form.outBillTypeId = bindSelectValue(
    outBillOpts.value,
    obj.outBillTypeId as string | number | '',
    String(obj.outBillTypeName || '')
  )
  form.taxes =
    obj.taxes != null && String(obj.taxes) !== ''
      ? bindSelectValue(taxOpts.value, String(obj.taxes), String(obj.taxes))
      : ''
  form.reversoOn =
    truthyOn(obj.reversoContext) || String(obj.reversoLabel || '') === '是'
  form.sendAddress = String(obj.shipAddress || '')
  form.addresseeName = String(obj.shipUser || '')
  form.addresseeMobile = String(obj.shipPhone || '')
  form.msg = String(obj.msg || '')
  form.userScaleInfo = String(obj.userScaleInfo || obj.scaleInfo || '')
  form.salecbUserScaleInfo = String(obj.salecbUserScaleInfo || '')

  // 先绑定付款方式选项，再生成收款时间槽并回填
  onPayWayChange(form.payWay)
  const coll = String(obj.collectionTime || '').trim()
  if (coll && collectionTimes.value.length) {
    const parts = coll.split(',').map((s) => s.trim()).filter(Boolean)
    collectionTimes.value = collectionTimes.value.map((_, i) => parts[i] || '')
  }

  if (form.customerName) {
    await reloadAccounts(form.customerName)
  }
  form.customUserId = bindSelectValue(
    accountOpts.value,
    form.customUserId,
    String(obj.customUserMobile || obj.customMobile || obj.mobile || form.customUserId || '')
  )

  refreshShareSummary()

  const children = Array.isArray(obj.children)
    ? (obj.children as Record<string, unknown>[])
    : []
  if (children.length) {
    lines.value = children.map((ch) => {
      const spec = String(ch.goodsSpec || '')
      return {
        key: lineKey++,
        goodsId: String(ch.goodsId || ''),
        goodsName: String(ch.goodsName || ''),
        goodsSpec: spec,
        goodsBrandId: String(ch.goodsBrandId || ''),
        goodsBrandName: String(ch.goodsBrand || ch.goodsBrandName || ''),
        goodsNums: Number(ch.goodsCount ?? ch.goodsNums ?? 1) || 1,
        projectId: String(ch.projectId || ch.experimentProjectId || ''),
        projectName: String(ch.projectName || ''),
        classId: String(ch.classId || ch.experimentClassId || ''),
        className: String(ch.className || ''),
        goodsPrice: String(ch.price ?? ch.goodsPrice ?? ''),
        referencePrice: String(ch.referencePrice ?? ch.price ?? ''),
        specOptions: spec ? [spec] : [],
      } satisfies LineRow
    })
    syncTotalPrice()
  }

  // Java 复制页模板未渲染源单资料；本仓对齐业务预期：带回订单资料（type=3），排除发票/预约单/测试数据
  const files = Array.isArray(obj.files) ? (obj.files as Record<string, unknown>[]) : []
  orderFiles.value = files
    .filter((f) => {
      const t = String(f.type ?? '').trim()
      return t === '' || t === '3' || t === '7'
    })
    .map((f) => ({ ...f }))
}

async function loadOptions() {
  loading.value = true
  const silent = { silentError: true } as const
  try {
    await Promise.all([
      reloadSuppliers(),
      reloadCustomers(),
      reloadAccounts(),
      (async () => {
        try {
          const mgr = await fetchUserList({ start: 0, length: 500, type: 1, draw: 1 }, silent)
          managerOpts.value = mapUserRows(Array.isArray(mgr.data) ? mgr.data : [])
        } catch {
          managerOpts.value = []
        }
      })(),
      (async () => {
        try {
          const sale = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 }, silent)
          saleUserOpts.value = mapUserRows(Array.isArray(sale.data) ? sale.data : [])
        } catch {
          saleUserOpts.value = []
        }
      })(),
      (async () => {
        try {
          const cls = await fetchManageOptions(3)
          const list = Array.isArray(cls.obj) ? (cls.obj as Record<string, unknown>[]) : []
          classOpts.value = list
            .map((r) => ({
              value: (r.id ?? r.value ?? '') as string | number,
              label: String(r.name || r.label || r.id || ''),
            }))
            .filter((o) => o.value !== '' && o.value != null)
        } catch {
          classOpts.value = []
        }
      })(),
      (async () => {
        try {
          const pay = await fetchPaytypeAll()
          const rows = Array.isArray(pay.data) ? pay.data : []
          payWayOpts.value = rows
            .map((r) => {
              const row = r as Record<string, unknown>
              return {
                value: String(row.id ?? ''),
                label: String(row.name || row.payName || row.id || ''),
                nums: Number(row.nums || 0) || 0,
                scaleVal: String(row.scaleVal || row.scale_val || ''),
              }
            })
            .filter((o) => o.value !== '')
        } catch {
          payWayOpts.value = []
        }
      })(),
      (async () => {
        try {
          const bills = await fetchBillTypeAll(1)
          const rows = Array.isArray(bills.data) ? bills.data : []
          outBillOpts.value = rows
            .map((r) => {
              const row = r as Record<string, unknown>
              return {
                value: (row.id ?? '') as string | number,
                label: String(row.name || row.id || ''),
              }
            })
            .filter((o) => o.value !== '' && o.value != null)
        } catch {
          outBillOpts.value = []
        }
      })(),
      (async () => {
        try {
          const tax = await fetchTaxAll()
          const list = Array.isArray(tax.obj)
            ? (tax.obj as Record<string, unknown>[])
            : Array.isArray(tax.data)
              ? (tax.data as Record<string, unknown>[])
              : []
          taxOpts.value = list
            .map((r) => ({
              value: (r.taxValue ?? r.tax_value ?? r.id ?? '') as string | number,
              label: String(
                r.name ||
                  (r.taxValue != null || r.tax_value != null
                    ? `${Number(r.taxValue ?? r.tax_value) * 100}%`
                    : r.id) ||
                  ''
              ),
            }))
            .filter((o) => o.value !== '' && o.value != null)
        } catch {
          taxOpts.value = []
        }
      })(),
      (async () => {
        try {
          const share = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 }, silent)
          shareUsers.value = Array.isArray(share.data) ? share.data : []
        } catch {
          shareUsers.value = []
        }
      })(),
    ])
    if (copyFromId.value) {
      await fillFromCopy(copyFromId.value)
      syncCreateTabTitle()
    } else {
      syncCreateTabTitle()
    }
  } finally {
    loading.value = false
  }
}

function onPayWayChange(id: string | number) {
  const pt = payWayOpts.value.find((p) => String(p.value) === String(id))
  const nums = Math.max(0, Number(pt?.nums || 0))
  collectionTimes.value = Array.from({ length: nums }, () => '')
}

function shareUserLabel(u: Record<string, unknown>) {
  return String(u.trueName || u.true_name || u.userName || u.user_name || u.id || '')
}

function addShareRow(list: ShareRow[]) {
  list.push({ userId: '', value: '' })
}

function buildScaleInfo(rows: ShareRow[]) {
  return rows
    .filter((r) => r.userId && String(r.value).trim() !== '')
    .map((r) => `${r.userId}_${String(r.value).trim()}`)
    .join(',')
}

function parseScalePairs(raw: unknown): ShareRow[] {
  const s = String(raw || '').trim()
  if (!s) return [{ userId: '', value: '' }]
  const rows = s
    .split(',')
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => {
      const idx = p.indexOf('_')
      if (idx < 0) return { userId: p, value: '' }
      return { userId: p.slice(0, idx), value: p.slice(idx + 1) }
    })
  return rows.length ? rows : [{ userId: '', value: '' }]
}

async function openShareDialog() {
  if (!shareUsers.value.length) {
    try {
      const share = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 })
      shareUsers.value = Array.isArray(share.data) ? share.data : []
    } catch {
      shareUsers.value = []
    }
  }
  profitRows.value = parseScalePairs(form.userScaleInfo)
  // 分包订单无成本分成
  costRows.value = isSubcontractCreate.value
    ? [{ userId: '', value: '' }]
    : parseScalePairs(form.salecbUserScaleInfo)
  shareDlg.visible = true
}

function confirmShare() {
  const profitLabel = isSubcontractCreate.value ? '利润分成' : '毛利分成'
  let total = 0
  for (const r of profitRows.value) {
    if (!r.userId && !String(r.value).trim()) continue
    if (!r.userId) {
      ElMessage.warning(`请选择${profitLabel}人员!`)
      return
    }
    const n = Number(r.value)
    if (Number.isNaN(n) || n <= 0) {
      ElMessage.warning('请填写正确的分成比例!')
      return
    }
    total += n
  }
  if (Number(total.toFixed(2)) !== 100) {
    ElMessage.warning('总的分成比例不是100，请重新输入')
    return
  }
  form.userScaleInfo = buildScaleInfo(profitRows.value)
  form.salecbUserScaleInfo = isSubcontractCreate.value ? '' : buildScaleInfo(costRows.value)
  const profitText = profitRows.value
    .filter((r) => r.userId)
    .map((r) => `${shareUserLabel(shareUsers.value.find((u) => String(u.id) === r.userId) || { id: r.userId })} ${r.value}%`)
    .join('，')
  const summaryLabel = isSubcontractCreate.value ? '利润' : '毛利'
  shareSummary.value = profitText ? `${summaryLabel}：${profitText}` : ''
  shareDlg.visible = false
}

function formatPrice(v: unknown) {
  if (v == null || v === '') return '-'
  const n = Number(v)
  return Number.isNaN(n) ? String(v) : n.toFixed(2)
}

function applyProjectPrice(target: LineRow, row: Record<string, unknown>) {
  const price = row.testPrice ?? row.test_price ?? row.price
  if (price == null || price === '') return
  const n = Number(price)
  if (Number.isNaN(n)) return
  target.goodsPrice = String(n)
  target.referencePrice = String(n)
}
function addLine() {
  lines.value.push(emptyLine())
}
function removeLine(idx: number) {
  if (lines.value.length <= 1) {
    ElMessage.warning('实验订单至少选择一个产品，不可删除最后一个')
    return
  }
  lines.value.splice(idx, 1)
  syncTotalPrice()
}

function lineTotal(row: LineRow) {
  const p = parseFloat(String(row.goodsPrice || 0)) || 0
  const n = Number(row.goodsNums) || 0
  return (p * n).toFixed(2)
}

function recalcLine(row: LineRow) {
  void row
  syncTotalPrice()
}

const totalNums = computed(() =>
  lines.value.reduce((s, r) => s + (Number(r.goodsNums) || 0), 0).toFixed(1)
)
const totalAmount = computed(() =>
  lines.value.reduce((s, r) => s + (parseFloat(lineTotal(r)) || 0), 0).toFixed(2)
)

function syncTotalPrice() {
  form.totalPrice = totalAmount.value
}

function openGoodsPicker(row: LineRow) {
  goodsDlg.target = row
  goodsDlg.keyword = ''
  goodsDlg.visible = true
  loadGoods()
}

async function loadGoods() {
  goodsDlg.loading = true
  try {
    const res = await fetchExpGoodsList({
      start: 0,
      length: 50,
      draw: 1,
      name: goodsDlg.keyword || '',
    })
    goodsDlg.rows = Array.isArray(res.data) ? res.data : []
  } catch {
    goodsDlg.rows = []
  } finally {
    goodsDlg.loading = false
  }
}

function onPickGoods(row: Record<string, unknown>) {
  const target = goodsDlg.target
  if (!target) return
  target.goodsId = String(row.id || '')
  target.goodsName = String(row.goodsName || '')
  target.goodsBrandId = String(row.brandId || '')
  target.goodsBrandName = String(row.brandName || '')
  const model = String(row.goodsModel || '')
  target.specOptions = model
    ? model
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
    : []
  target.goodsSpec = target.specOptions[0] || model
  goodsDlg.visible = false
  openProjectPicker(target)
}

function openProjectPicker(row: LineRow) {
  projectDlg.target = row
  projectDlg.keyword = ''
  projectDlg.visible = true
  loadProjects()
}

async function loadProjects() {
  projectDlg.loading = true
  try {
    const res = await fetchProjectList({
      start: 0,
      length: 50,
      draw: 1,
      name: projectDlg.keyword || '',
    })
    projectDlg.rows = Array.isArray(res.data) ? res.data : []
  } catch {
    projectDlg.rows = []
  } finally {
    projectDlg.loading = false
  }
}

function onPickProject(row: Record<string, unknown>) {
  const target = projectDlg.target
  if (!target) return
  target.projectId = String(row.id || '')
  target.projectName = String(row.projectName || '')
  target.classId = String(row.classId || '')
  target.className = String(row.className || '')
  applyProjectPrice(target, row)
  projectDlg.visible = false
  syncTotalPrice()
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
    ElMessage.success('上传成功')
  } finally {
    uploading.value = false
  }
}

function removeOrderFile(idx: number) {
  orderFiles.value.splice(idx, 1)
}

function validate(): string | null {
  if (!form.orderTime) return '请选择下单时间'
  if (!form.classId) return '请选择订单类型'
  if (!form.saleManager) return '请选择销售主管'
  if (!form.saleUser) return '请选择销售人员'
  if (!form.supplierName) return '请选择所属公司'
  if (!form.deliveryTime) return '请选择预计收货时间'
  if (!form.customerName && !form.customUserId) return '客户名称和客户账号不能同时为空'
  if (!form.userScaleInfo) return '请填写分成比例!'
  if (form.invoiceOn && !form.outBillTypeId) return '请选择出项开票类型'
  if (form.invoiceOn && !form.taxes) return '请选择税率'
  if (collectionTimes.value.length && collectionTimes.value.some((t) => !t)) {
    return '请填写预计收款时间'
  }
  if (!lines.value.length) return '实验订单至少选择一个产品才可提交'
  for (const [i, row] of lines.value.entries()) {
    if (!row.goodsId && !row.goodsName) return `第 ${i + 1} 行请选择产品`
    if (!row.projectId && !row.projectName) return `第 ${i + 1} 行请选择测试项目`
  }
  return null
}

async function onSave() {
  const err = validate()
  if (err) {
    ElMessage.warning(err)
    return
  }
  syncTotalPrice()
  const header: Record<string, unknown> = {
    order_type: createOrderType.value,
    order_time: form.orderTime,
    class_id: form.classId,
    sale_manager: form.saleManager,
    customer_name: form.customerName || null,
    custom_user_id: form.customUserId || null,
    sale_user: form.saleUser,
    supplier_name: form.supplierName,
    currency_type: form.currencyType,
    delivery_time: form.deliveryTime,
    pay_way: form.payWay || null,
    is_online: isOnlineOrder.value ? 1 : 0,
    collection_time: collectionTimes.value.filter(Boolean).join(','),
    totalPrice: form.totalPrice || totalAmount.value,
    invoiceType: form.invoiceOn ? 1 : 2,
    outBillTypeId: form.invoiceOn ? form.outBillTypeId : null,
    taxes: form.invoiceOn ? form.taxes : null,
    reverso_context: form.reversoOn ? 1 : 2,
    send_address: form.reversoOn ? form.sendAddress : '',
    addressee_name: form.reversoOn ? form.addresseeName : '',
    addressee_mobile: form.reversoOn ? form.addresseeMobile : '',
    msg: form.msg,
    user_scale_info: form.userScaleInfo,
    // 分包主单对齐 Java：仅利润分成，不传成本分成
    salecb_user_scale_info: isSubcontractCreate.value ? '' : form.salecbUserScaleInfo,
    accessoryId: orderFiles.value
      .map((f) => f.id)
      .filter((id) => id != null && String(id) !== ''),
  }
  const children = lines.value.map((row) => ({
    goods_id: row.goodsId || null,
    goods_spec: row.goodsSpec,
    goods_nums: row.goodsNums,
    goods_name: row.goodsName,
    goods_brand_id: row.goodsBrandId || null,
    goods_brand_name: row.goodsBrandName,
    experiment_project_id: row.projectId || null,
    experiment_project_name: row.projectName,
    experiment_class_id: row.classId || null,
    experiment_class_name: row.className,
    goods_price: row.goodsPrice || 0,
    reference_price: row.referencePrice || row.goodsPrice || 0,
  }))

  saving.value = true
  try {
    const res = await submitExpOrder([header, ...children])
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    const newId = res.resMsg || res.obj
    ElMessage.success('保存成功')
    if (newId) {
      router.push({
        name: 'ExperimentOrderDetail',
        params: { id: String(newId) },
        query: {
          from: isSubcontractCreate.value ? 'subcontract-orders' : 'orders',
        },
      })
    } else {
      router.push({
        name: isSubcontractCreate.value ? 'ExperimentSubcontractOrders' : 'ExperimentOrders',
      })
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadOptions()
})

// keep-alive / 同 path 换 query：仅 onMounted 时二次「复制」会落到空的新增表单
watch(
  () => `${createOrderType.value}|${copyFromId.value}`,
  (next, prev) => {
    if (!prev || next === prev) return
    loadOptions()
  }
)
</script>

<style scoped>
.create-page {
  padding: 16px 20px 48px;
}
.page-head {
  margin-bottom: 16px;
}
.page-head h2 {
  margin: 8px 0 0;
  font-size: 20px;
  font-weight: 600;
}
.back-link {
  border: 0;
  background: transparent;
  color: #409eff;
  cursor: pointer;
  padding: 0;
  font-size: 14px;
}
.create-form {
  background: #fff;
  padding: 16px 16px 4px;
  border-radius: 4px;
}
.inline-ops {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.file-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.file-tag {
  max-width: 240px;
}
.lines-card {
  margin-top: 16px;
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}
.lines-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.lines-head h3 {
  margin: 0;
  font-size: 16px;
}
.sum-row {
  display: flex;
  gap: 32px;
  margin-top: 12px;
  font-weight: 600;
}
.save-bar {
  margin-top: 32px;
  text-align: center;
}
.dlg-filter {
  margin-bottom: 8px;
}
.share-summary {
  color: #606266;
  font-size: 13px;
}
.share-hint {
  color: #909399;
  font-size: 12px;
}
.share-block-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.share-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
