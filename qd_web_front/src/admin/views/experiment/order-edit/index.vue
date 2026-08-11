<template>
  <div v-loading="loading" class="edit-page">
    <header class="page-head">
      <button type="button" class="back-link" @click="goBack">← 返回详情</button>
      <h2>编辑订单</h2>
      <p v-if="detail" class="sub">
        <span class="mono">{{ detail.orderId }}</span>
        · {{ detail.orderStatusLabel }}
      </p>
    </header>

    <el-form v-if="detail" label-width="130px" class="form-card" @submit.prevent>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="订单编号">
            <el-input :model-value="String(detail.orderId || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col v-if="isSubcontractSub || isExpSub" :span="12">
          <el-form-item label="来源单号">
            <el-input :model-value="String(detail.parentOrderId || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col v-else :span="12">
          <el-form-item label="制单人员">
            <el-input :model-value="String(detail.addUser || '')" disabled />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="下单时间" required>
            <el-date-picker
              v-model="form.orderTime"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="yyyy-mm-dd"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col v-if="!isSubcontractSub" :span="12">
          <el-form-item :label="isExpSub ? '客户名称' : '客户名称'" :required="isMainOrder">
            <div class="inline-ops">
              <el-select
                v-model="form.customerId"
                filterable
                clearable
                placeholder="请选择"
                style="flex: 1"
              >
                <el-option
                  v-for="o in customerOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button type="primary" link @click="openAddCustomer">添加</el-button>
              <el-button type="primary" link @click="reloadCustomers">刷新</el-button>
            </div>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item :label="isExpSub ? '审核主管' : '销售主管'" required>
            <el-select
              v-model="form.saleManagerId"
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
        <el-col v-if="!isSubcontractSub" :span="12">
          <el-form-item label="销售人员" required>
            <el-select
              v-model="form.saleUserId"
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

        <el-col v-if="isSubcontractSub" :span="12">
          <el-form-item label="实验分包公司" required>
            <div class="inline-ops">
              <el-select
                v-model="form.stockCompanyId"
                filterable
                clearable
                placeholder="请选择"
                style="flex: 1"
              >
                <el-option
                  v-for="o in supplierOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button type="primary" link @click="openAddSupplier">添加</el-button>
              <el-button type="primary" link @click="reloadSuppliers">刷新</el-button>
            </div>
          </el-form-item>
        </el-col>
        <el-col v-else :span="12">
          <el-form-item label="所属公司" required>
            <div class="inline-ops">
              <el-select
                v-model="form.supplierId"
                filterable
                clearable
                placeholder="请选择"
                style="flex: 1"
              >
                <el-option
                  v-for="o in supplierOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button type="primary" link @click="openAddSupplier">添加</el-button>
              <el-button type="primary" link @click="reloadSuppliers">刷新</el-button>
            </div>
          </el-form-item>
        </el-col>
        <el-col v-if="isExpSub" :span="12">
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
        <el-col v-if="isExpSub" :span="12">
          <el-form-item label="仓库管理员" required>
            <el-select
              v-model="form.warehouseUserId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 100%"
            >
              <el-option
                v-for="o in saleUserOpts"
                :key="'w-' + String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col v-if="!isExpSub" :span="12">
          <el-form-item label="订单币种" required>
            <el-select v-model="form.currencyType" style="width: 100%">
              <el-option :value="1" label="人民币" />
              <el-option :value="2" label="美金" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col v-if="isMainOrder" :span="12">
          <el-form-item label="分成比例" required>
            <div class="inline-ops">
              <el-button type="primary" @click="openShareDialog">添加分成比例</el-button>
              <span v-if="shareSummary" class="share-summary">{{ shareSummary }}</span>
              <span v-else class="share-hint">
                {{ isSubcontractMain ? '利润合计须为 100%' : '毛利合计须为 100%' }}
              </span>
            </div>
          </el-form-item>
        </el-col>
        <el-col v-if="isMainOrder" :span="12" />

        <el-col :span="12">
          <el-form-item :label="isSubcontractSub ? '预计发货时间' : '预计收货时间'" required>
            <el-date-picker
              v-model="form.deliveryTime"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="yyyy-mm-dd"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col v-if="!isExpSub" :span="12">
          <el-form-item label="付款方式" required>
            <el-select
              v-model="form.payWay"
              filterable
              clearable
              placeholder="请选择"
              style="width: 100%"
              :disabled="payWayLocked"
              @change="onPayWayChange"
            >
              <el-option
                v-for="o in payWayOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <template v-if="collectionTimes.length && !isExpSub">
          <el-col v-for="(ct, idx) in collectionTimes" :key="`ct-${idx}`" :span="12">
            <el-form-item
              :label="`${isSubcontractSub ? '预计付款时间' : '预计收款时间'}${collectionTimes.length > 1 ? idx + 1 : ''}`"
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

        <el-col v-if="!isExpSub" :span="12">
          <el-form-item :label="isSubcontractSub ? '实验分包总价' : '订单总价'" required>
            <el-input v-model="form.totalPrice" clearable placeholder="订单总价" />
          </el-form-item>
        </el-col>
        <el-col v-if="!isExpSub" :span="12">
          <el-form-item label="是否开票">
            <el-switch v-model="form.invoiceType" inline-prompt active-text="ON" inactive-text="OFF" />
          </el-form-item>
        </el-col>

        <template v-if="form.invoiceType && !isExpSub">
          <el-col :span="12">
            <el-form-item :label="isSubcontractSub ? '进项开票类型' : '出项开票类型'" required>
              <!-- v-model 必须是成员表达式，不能写三元（否则 vite:vue 构建失败） -->
              <el-select
                v-if="isSubcontractSub"
                v-model="form.inBillTypeId"
                filterable
                clearable
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option
                  v-for="o in inBillOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-select
                v-else
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
          <el-form-item label="备注">
            <el-input v-model="form.mark" type="textarea" :rows="3" placeholder="请输入内容" />
          </el-form-item>
        </el-col>
      </el-row>

      <section class="lines-block">
        <div class="lines-head">
          <h3>产品明细</h3>
        </div>
        <!-- type9 对齐 Java experimentsub/purchase_edit_orders：成本单价 -->
        <el-table v-if="isSubcontractSub" :data="lines" border stripe empty-text="暂无产品行">
          <el-table-column prop="childOrderId" label="子订单编号" min-width="140" show-overflow-tooltip />
          <el-table-column prop="goodsName" label="产品名称" min-width="140" show-overflow-tooltip />
          <el-table-column prop="goodsBrandName" label="产品品牌" min-width="100" show-overflow-tooltip />
          <el-table-column prop="goodsSpec" label="型号" min-width="120" show-overflow-tooltip />
          <el-table-column prop="goodsNums" label="数量" width="90" />
          <el-table-column label="成本单价" width="130">
            <template #default="{ row }">
              <el-input v-model="row.costPrice" clearable @change="recalcCostTotal" />
            </template>
          </el-table-column>
        </el-table>
        <!-- type10 对齐 Java 子单详情：无金额列 -->
        <el-table v-else-if="isExpSub" :data="lines" border stripe empty-text="暂无产品行">
          <el-table-column prop="goodsName" label="产品名称" min-width="140" show-overflow-tooltip />
          <el-table-column label="产品型号" min-width="120">
            <template #default="{ row }">
              <el-input v-model="row.goodsSpec" clearable />
            </template>
          </el-table-column>
          <el-table-column prop="goodsBrandName" label="产品品牌" min-width="100" show-overflow-tooltip />
          <el-table-column label="数量" width="110">
            <template #default="{ row }">
              <el-input-number
                v-model="row.goodsNums"
                :min="1"
                :controls="false"
                style="width: 90px"
              />
            </template>
          </el-table-column>
          <el-table-column prop="projectName" label="实验测试项目" min-width="120" show-overflow-tooltip />
          <el-table-column prop="className" label="实验测试分类" min-width="120" show-overflow-tooltip />
        </el-table>
        <el-table v-else :data="lines" border stripe empty-text="暂无产品行">
          <el-table-column label="产品名称" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ row.goodsName || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="产品型号" min-width="120">
            <template #default="{ row }">
              <el-input v-model="row.goodsSpec" clearable />
            </template>
          </el-table-column>
          <el-table-column prop="goodsBrandName" label="产品品牌" min-width="100" show-overflow-tooltip />
          <el-table-column label="数量" width="110">
            <template #default="{ row }">
              <el-input-number
                v-model="row.goodsNums"
                :min="1"
                :controls="false"
                style="width: 90px"
                @change="recalcTotal"
              />
            </template>
          </el-table-column>
          <el-table-column prop="projectName" label="实验测试项目" min-width="120" show-overflow-tooltip />
          <el-table-column prop="className" label="实验测试分类" min-width="120" show-overflow-tooltip />
          <el-table-column label="实际测试金额" width="130">
            <template #default="{ row }">
              <el-input v-model="row.goodsPrice" clearable @change="recalcTotal" />
            </template>
          </el-table-column>
          <el-table-column label="标准测试金额" width="120">
            <template #default="{ row }">
              <span>{{ row.referencePrice || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="总价" width="100">
            <template #default="{ row }">
              <span>{{ lineTotal(row) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <div class="sum-row">
          <span v-if="isSubcontractSub">总成本：{{ totalCostAmount }}</span>
          <template v-else>
            <span>总计数量：{{ totalNums }}</span>
            <span v-if="!isExpSub">总计金额：{{ totalAmount }}</span>
          </template>
        </div>
      </section>

      <div class="save-bar">
        <el-button type="warning" size="large" :loading="saving" @click="onSave">保存</el-button>
        <el-button size="large" @click="goBack">取消</el-button>
      </div>
    </el-form>
    <el-empty v-else-if="!loading" description="订单不存在或不可编辑" />

    <el-dialog v-model="shareDlg.visible" title="添加分成比例" width="720px" destroy-on-close>
      <div class="share-block">
        <div class="share-head">
          <strong>{{ isSubcontractMain ? '利润分成' : '毛利分成' }}</strong>
          <el-button type="primary" link @click="addShareRow(profitRows)">添加</el-button>
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
          <el-button type="danger" link @click="profitRows.splice(idx, 1)">删除</el-button>
        </div>
      </div>
      <template v-if="!isSubcontractMain">
        <el-divider />
        <div class="share-block">
          <div class="share-head">
            <strong>成本分成</strong>
            <el-button type="primary" link @click="addShareRow(costRows)">添加</el-button>
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
            <el-input v-model="row.value" placeholder="分成金额" style="width: 140px" />
            <el-button type="danger" link @click="costRows.splice(idx, 1)">删除</el-button>
          </div>
        </div>
      </template>
      <template #footer>
        <el-button @click="shareDlg.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmShare">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  deleteExpOrderFile,
  getExpOrderDetail,
  updateExpOrderBasic,
  uploadExpOrderFile,
} from '@admin/api/experiment'
import { fetchCustomerAccounts, fetchCustomerNamesExp } from '@admin/api/member'
import { fetchBillTypeAll, fetchPaytypeAll, fetchTaxAll } from '@admin/api/order-settings'
import { fetchSupplierAll, fetchUserList } from '@admin/api/system'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type Opt = { value: string | number; label: string; nums?: number }
type ShareRow = { userId: string; value: string }
type LineRow = {
  id: string | number
  goodsName: string
  goodsSpec: string
  goodsBrandName: string
  goodsNums: number
  goodsPrice: string
  referencePrice: string
  costPrice: string
  projectName: string
  className: string
  childOrderId: string
}

const route = useRoute()
const router = useRouter()
const orderId = String(route.params.id || '')

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const lines = ref<LineRow[]>([])
const orderFiles = ref<Record<string, unknown>[]>([])
const collectionTimes = ref<string[]>([])
const payWayLocked = ref(false)

/** 6=实验主单 8=分包主单 9=分包子单 10=实验子单 */
const orderType = computed(() => String(detail.value?.orderType || detail.value?.order_type || '6'))
const isMainOrder = computed(() => orderType.value === '6' || orderType.value === '8')
/** 分包主单：对齐 Java 仅利润分成，无成本分成 */
const isSubcontractMain = computed(() => orderType.value === '8')
const isSubcontractSub = computed(() => orderType.value === '9')
const isExpSub = computed(() => orderType.value === '10')

const form = reactive({
  totalPrice: '',
  mark: '',
  deliveryTime: '',
  orderTime: '',
  currencyType: 1 as number,
  payWay: '' as string | number | '',
  invoiceType: false,
  taxes: '' as string | number | '',
  outBillTypeId: '' as string | number | '',
  inBillTypeId: '' as string | number | '',
  saleManagerId: '' as string | number | '',
  saleUserId: '' as string | number | '',
  supplierId: '' as string | number | '',
  stockCompanyId: '' as string | number | '',
  customerId: '' as string | number | '',
  customUserId: '' as string | number | '',
  warehouseUserId: '' as string | number | '',
  userScaleInfo: '',
  salecbUserScaleInfo: '',
  reversoOn: false,
})

const supplierOpts = ref<Opt[]>([])
const customerOpts = ref<Opt[]>([])
const accountOpts = ref<Opt[]>([])
const managerOpts = ref<Opt[]>([])
const saleUserOpts = ref<Opt[]>([])
const payWayOpts = ref<Opt[]>([])
const outBillOpts = ref<Opt[]>([])
const inBillOpts = ref<Opt[]>([])
const taxOpts = ref<Opt[]>([])
const shareUsers = ref<Record<string, unknown>[]>([])
const profitRows = ref<ShareRow[]>([{ userId: '', value: '' }])
const costRows = ref<ShareRow[]>([{ userId: '', value: '' }])
const shareDlg = reactive({ visible: false })
const shareSummary = ref('')

const totalNums = computed(() =>
  lines.value.reduce((s, r) => s + (Number(r.goodsNums) || 0), 0)
)
const totalAmount = computed(() =>
  lines.value
    .reduce((s, r) => s + (Number(r.goodsNums) || 0) * (parseFloat(String(r.goodsPrice || 0)) || 0), 0)
    .toFixed(2)
)
const totalCostAmount = computed(() =>
  lines.value.reduce((s, r) => s + (parseFloat(String(r.costPrice || 0)) || 0), 0).toFixed(2)
)

function goBack() {
  router.push({ name: 'ExperimentOrderDetail', params: { id: orderId } })
}

function openAddCustomer() {
  window.open(router.resolve({ name: 'MemberEnterprise' }).href, '_blank')
}
function openAddSupplier() {
  window.open(router.resolve({ name: 'SystemCompanies' }).href, '_blank')
}

function asOptValue(v: unknown): string | number | '' {
  if (v == null || v === '') return ''
  return typeof v === 'number' ? v : String(v)
}

function ensureOpt(opts: { value: Opt[] }, value: string | number | '', label?: string) {
  if (value === '' || value == null) return
  const key = String(value)
  if (opts.value.some((o) => String(o.value) === key)) return
  opts.value.unshift({ value, label: (label || key).trim() || key })
}

function mapUserRows(rows: Record<string, unknown>[]): Opt[] {
  return rows
    .map((u) => ({
      value: (u.id ?? '') as string | number,
      label: String(u.trueName || u.true_name || u.userName || u.user_name || u.id || ''),
    }))
    .filter((o) => o.value !== '' && o.value != null)
}

function lineTotal(row: LineRow) {
  const n = (Number(row.goodsNums) || 0) * (parseFloat(String(row.goodsPrice || 0)) || 0)
  return n ? n.toFixed(2) : ''
}

function recalcTotal() {
  if (!form.totalPrice || form.totalPrice === '0') {
    form.totalPrice = totalAmount.value
  }
}

function recalcCostTotal() {
  form.totalPrice = totalCostAmount.value
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

function refreshShareSummary() {
  const profitText = parseScalePairs(form.userScaleInfo)
    .filter((r) => r.userId)
    .map((r) => {
      const u = shareUsers.value.find((x) => String(x.id) === r.userId)
      return `${shareUserLabel(u || { id: r.userId })} ${r.value}%`
    })
    .join('，')
  const label = isSubcontractMain.value ? '利润' : '毛利'
  shareSummary.value = profitText
    ? `${label}：${profitText}`
    : form.userScaleInfo
      ? `${label}：${form.userScaleInfo}`
      : ''
}

function openShareDialog() {
  profitRows.value = parseScalePairs(form.userScaleInfo)
  costRows.value = isSubcontractMain.value
    ? [{ userId: '', value: '' }]
    : parseScalePairs(form.salecbUserScaleInfo)
  shareDlg.visible = true
}

function confirmShare() {
  const profitLabel = isSubcontractMain.value ? '利润分成' : '毛利分成'
  for (const r of profitRows.value) {
    if (r.userId && !String(r.value).trim()) {
      ElMessage.warning('请填写正确的分成比例!')
      return
    }
    if (!r.userId && String(r.value).trim()) {
      ElMessage.warning(`请选择${profitLabel}人员!`)
      return
    }
  }
  const sum = profitRows.value
    .filter((r) => r.userId)
    .reduce((s, r) => s + (parseFloat(String(r.value)) || 0), 0)
  if (Math.abs(sum - 100) > 0.01 && profitRows.value.some((r) => r.userId)) {
    ElMessage.warning('总的分成比例不是100，请重新输入')
    return
  }
  form.userScaleInfo = buildScaleInfo(profitRows.value)
  form.salecbUserScaleInfo = isSubcontractMain.value ? '' : buildScaleInfo(costRows.value)
  refreshShareSummary()
  shareDlg.visible = false
}

function onPayWayChange(id: string | number | '') {
  const pt = payWayOpts.value.find((p) => String(p.value) === String(id))
  const nums = Math.max(0, Number(pt?.nums || 0))
  const prev = [...collectionTimes.value]
  collectionTimes.value = Array.from({ length: nums }, (_, i) => prev[i] || '')
}

async function reloadCustomers() {
  try {
    const res = await fetchCustomerNamesExp()
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    customerOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: (r.id ?? '') as string | number,
        label: String(r.name || r.companyName || r.company_name || ''),
      }))
      .filter((o) => o.value !== '' && o.value != null && o.label)
  } catch {
    /* ignore */
  }
}

async function reloadSuppliers() {
  try {
    const res = await fetchSupplierAll({ silentError: true })
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    supplierOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: (r.id ?? '') as string | number,
        label: String(r.companyName || r.company_name || r.name || r.id || ''),
      }))
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
}

async function loadOptions() {
  const silent = { silentError: true } as const
  await reloadCustomers()
  await reloadSuppliers()
  try {
    const mgr = await fetchUserList({ start: 0, length: 500, type: 1, draw: 1 }, silent)
    managerOpts.value = mapUserRows(Array.isArray(mgr.data) ? mgr.data : [])
  } catch {
    /* ignore */
  }
  try {
    const sale = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 }, silent)
    const rows = Array.isArray(sale.data) ? sale.data : []
    saleUserOpts.value = mapUserRows(rows)
    shareUsers.value = rows as Record<string, unknown>[]
  } catch {
    /* ignore */
  }
  try {
    const pay = await fetchPaytypeAll()
    const rows = Array.isArray(pay.data) ? pay.data : []
    payWayOpts.value = rows
      .map((r) => {
        const row = r as Record<string, unknown>
        return {
          value: (row.id ?? '') as string | number,
          label: String(row.name || row.payName || row.id || ''),
          nums: Number(row.nums || row.payNums || row.pay_nums || 0) || 0,
        }
      })
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
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
    /* ignore */
  }
  try {
    const billsIn = await fetchBillTypeAll(2)
    const rows = Array.isArray(billsIn.data) ? billsIn.data : []
    inBillOpts.value = rows
      .map((r) => {
        const row = r as Record<string, unknown>
        return {
          value: (row.id ?? '') as string | number,
          label: String(row.name || row.id || ''),
        }
      })
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
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
    /* ignore */
  }
}

async function load() {
  if (!orderId) return
  loading.value = true
  try {
    const res = await getExpOrderDetail(orderId)
    if (!isAjaxOk(res) || !res.obj) {
      detail.value = null
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    detail.value = obj
    const st = Number(obj.orderStatus ?? obj.order_status ?? 0)
    // 对齐 Java：已审核/已完成不可改付款方式
    payWayLocked.value = st === 30 || st === 50

    const files = Array.isArray(obj.files) ? (obj.files as Record<string, unknown>[]) : []
    orderFiles.value = files.map((f) => ({ ...f }))
    form.totalPrice = obj.totalPrice != null ? String(obj.totalPrice) : ''
    form.mark = String(obj.mark || obj.msg || '')
    form.deliveryTime = String(obj.deliveryTime || '').slice(0, 10)
    form.orderTime = String(obj.orderTime || '').slice(0, 10)
    form.currencyType = Number(obj.currencyType || 1) === 2 ? 2 : 1
    form.payWay = asOptValue(obj.payWay)
    form.invoiceType = String(obj.invoiceType || '') === '1' || obj.invoiceLabel === '是'
    form.taxes = obj.taxes != null && String(obj.taxes) !== '' ? String(obj.taxes) : ''
    form.outBillTypeId = asOptValue(obj.outBillTypeId)
    form.inBillTypeId = asOptValue(obj.inBillTypeId)
    form.saleManagerId = asOptValue(obj.saleManagerId)
    form.saleUserId = asOptValue(obj.saleUserId)
    form.supplierId = asOptValue(obj.supplierId)
    form.stockCompanyId = asOptValue(
      obj.stockCompanyId || obj.stock_company_name || obj.stockCompanyName
    )
    form.customerId = asOptValue(obj.customerId)
    form.customUserId = asOptValue(obj.customUserId)
    form.warehouseUserId = asOptValue(obj.warehouseUserId || obj.stockUserId)
    form.userScaleInfo = String(obj.userScaleInfo || obj.scaleInfo || '')
    form.salecbUserScaleInfo = String(obj.salecbUserScaleInfo || '')
    form.reversoOn =
      String(obj.reversoContext || '').toUpperCase() === 'ON' ||
      String(obj.reversoLabel || '') === '是' ||
      Number(obj.reversoContext) === 1

    ensureOpt(supplierOpts, form.supplierId, String(obj.supplierName || ''))
    ensureOpt(
      supplierOpts,
      form.stockCompanyId,
      String(obj.stockCompanyName || obj.supplierName || '')
    )
    ensureOpt(customerOpts, form.customerId, String(obj.customerName || obj.companyName || ''))
    ensureOpt(managerOpts, form.saleManagerId, String(obj.saleManager || ''))
    ensureOpt(saleUserOpts, form.saleUserId, String(obj.saleUser || ''))
    ensureOpt(
      saleUserOpts,
      form.warehouseUserId,
      String(obj.warehouseUser || obj.stockUser || '')
    )
    ensureOpt(payWayOpts, form.payWay, String(obj.payWayName || ''))
    ensureOpt(outBillOpts, form.outBillTypeId, String(obj.outBillTypeName || ''))
    ensureOpt(inBillOpts, form.inBillTypeId, String(obj.inBillTypeName || ''))
    if (form.taxes !== '') ensureOpt(taxOpts, form.taxes, String(form.taxes))

    if (form.customerId) {
      try {
        const acc = await fetchCustomerAccounts(form.customerId)
        const list = Array.isArray(acc.obj) ? acc.obj : Array.isArray(acc.data) ? acc.data : []
        accountOpts.value = (list as Record<string, unknown>[])
          .map((r) => ({
            value: (r.id ?? '') as string | number,
            label: String(r.mobile || r.userName || r.id || ''),
          }))
          .filter((o) => o.value !== '' && o.value != null)
        ensureOpt(accountOpts, form.customUserId, String(obj.customMobile || obj.mobile || ''))
      } catch {
        /* ignore */
      }
    }

    const coll = String(obj.collectionTime || '')
    onPayWayChange(form.payWay)
    if (coll && collectionTimes.value.length) {
      const parts = coll.split(',').map((x) => x.trim().slice(0, 10))
      collectionTimes.value = collectionTimes.value.map((_, i) => parts[i] || '')
    } else if (coll && !collectionTimes.value.length) {
      collectionTimes.value = coll
        .split(',')
        .map((x) => x.trim().slice(0, 10))
        .filter(Boolean)
    }

    refreshShareSummary()

    const children = Array.isArray(obj.children) ? (obj.children as Record<string, unknown>[]) : []
    lines.value = children.map((ch) => ({
      id: (ch.id ?? '') as string | number,
      goodsName: String(ch.goodsName || ''),
      goodsSpec: String(ch.goodsSpec || ''),
      goodsBrandName: String(ch.goodsBrandName || ch.goodsBrand || ''),
      goodsNums: Number(ch.goodsNums || ch.goodsCount || 1) || 1,
      goodsPrice: ch.price != null ? String(ch.price) : ch.goodsPrice != null ? String(ch.goodsPrice) : '',
      referencePrice:
        ch.referencePrice != null
          ? String(ch.referencePrice)
          : ch.reference_price != null
            ? String(ch.reference_price)
            : '',
      costPrice: ch.costPrice != null ? String(ch.costPrice) : '',
      projectName: String(ch.projectName || ch.experimentProjectName || ''),
      className: String(ch.className || ch.experimentClassName || ch.deviceName || ''),
      childOrderId: String(ch.childOrderId || ch.orderId || ''),
    }))
  } finally {
    loading.value = false
  }
}

async function onSave() {
  if (!isSubcontractSub.value && !form.customerId) {
    ElMessage.warning('请选择客户名称')
    return
  }
  if (!form.saleManagerId) {
    ElMessage.warning(isExpSub.value ? '请选择审核主管' : '请选择销售主管')
    return
  }
  if (!isSubcontractSub.value && !form.saleUserId) {
    ElMessage.warning('请选择销售人员')
    return
  }
  if (isSubcontractSub.value && !form.stockCompanyId) {
    ElMessage.warning('请选择实验分包公司')
    return
  }
  if (!isSubcontractSub.value && !form.supplierId) {
    ElMessage.warning('请选择所属公司')
    return
  }
  if (isExpSub.value && !form.warehouseUserId) {
    ElMessage.warning('请选择仓库管理员')
    return
  }
  if (!form.deliveryTime) {
    ElMessage.warning(isSubcontractSub.value ? '请填写预计发货时间' : '请填写预计收货时间')
    return
  }
  if (!isExpSub.value && !form.payWay) {
    ElMessage.warning('请选择付款方式')
    return
  }
  if (!isExpSub.value && collectionTimes.value.length && collectionTimes.value.some((t) => !t)) {
    ElMessage.warning(isSubcontractSub.value ? '请填写预计付款时间' : '请填写预计收款时间')
    return
  }
  if (isSubcontractSub.value) {
    if (lines.value.some((r) => !String(r.costPrice || '').trim())) {
      ElMessage.warning('请填写成本单价')
      return
    }
    form.totalPrice = totalCostAmount.value
  }
  if (!isExpSub.value && !form.totalPrice) {
    ElMessage.warning(isSubcontractSub.value ? '请填写实验分包总价' : '请填写订单总价')
    return
  }
  if (isMainOrder.value && !form.userScaleInfo) {
    ElMessage.warning('请填写分成比例')
    return
  }
  if (form.invoiceType && !isExpSub.value) {
    const billId = isSubcontractSub.value ? form.inBillTypeId : form.outBillTypeId
    if (!billId || form.taxes === '') {
      ElMessage.warning(
        isSubcontractSub.value ? '请填写进项开票类型和税率' : '请填写出项开票类型和税率'
      )
      return
    }
  }
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      id: orderId,
      totalPrice: form.totalPrice,
      mark: form.mark,
      deliveryTime: form.deliveryTime,
      orderTime: form.orderTime,
      collectionTime: collectionTimes.value.filter(Boolean).join(','),
      currencyType: form.currencyType,
      payWay: form.payWay,
      invoiceType: form.invoiceType ? 1 : 0,
      taxes: form.invoiceType ? form.taxes : '',
      saleManagerId: form.saleManagerId,
      saleUserId: form.saleUserId,
      customerId: form.customerId,
      customUserId: form.customUserId,
      children: lines.value.map((row) => ({
        id: row.id,
        goodsNums: row.goodsNums,
        goodsPrice: row.goodsPrice,
        goodsSpec: row.goodsSpec,
        referencePrice: row.referencePrice,
        costPrice: row.costPrice,
      })),
    }
    if (isMainOrder.value) {
      payload.supplierId = form.supplierId
      payload.outBillTypeId = form.invoiceType ? form.outBillTypeId : ''
      payload.userScaleInfo = form.userScaleInfo
      payload.salecbUserScaleInfo = isSubcontractMain.value ? '' : form.salecbUserScaleInfo
    } else if (isSubcontractSub.value) {
      payload.stockCompanyId = form.stockCompanyId
      payload.inBillTypeId = form.invoiceType ? form.inBillTypeId : ''
    } else if (isExpSub.value) {
      payload.supplierId = form.supplierId
      payload.warehouseUser = form.warehouseUserId
      payload.stockUser = form.warehouseUserId
    }
    const res = await updateExpOrderBasic(payload)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success('保存成功')
    goBack()
  } finally {
    saving.value = false
  }
}

async function onUploadOrderFile(options: { file: File }) {
  if (!orderId) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('orderdata', options.file)
    fd.append('id', orderId)
    fd.append('type', '3')
    const res = await uploadExpOrderFile(fd)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '上传成功'))
    await load()
  } finally {
    uploading.value = false
  }
}

async function removeOrderFile(idx: number) {
  const f = orderFiles.value[idx]
  if (!f) return
  const aid = f.id
  if (aid != null && String(aid) !== '') {
    const res = await deleteExpOrderFile(aid as string | number)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '删除失败'))
      return
    }
  }
  orderFiles.value.splice(idx, 1)
  ElMessage.success('已删除')
}

onMounted(async () => {
  await loadOptions()
  await load()
})
</script>

<style scoped>
.edit-page {
  padding: 8px 4px 24px;
}
.page-head {
  margin-bottom: 16px;
}
.back-link {
  border: 0;
  background: transparent;
  color: #409eff;
  cursor: pointer;
  padding: 0;
  margin-bottom: 8px;
}
.page-head h2 {
  margin: 0 0 4px;
  font-size: 20px;
}
.sub {
  margin: 0;
  color: #909399;
  font-size: 13px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.form-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px 20px 8px;
  max-width: 1200px;
}
.inline-ops {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.share-summary {
  color: #606266;
  font-size: 13px;
}
.share-hint {
  color: #c0c4cc;
  font-size: 12px;
}
.file-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.file-tag {
  max-width: 220px;
}
.lines-block {
  margin: 8px 0 20px;
}
.lines-head h3 {
  margin: 0 0 12px;
  font-size: 16px;
}
.sum-row {
  display: flex;
  gap: 24px;
  margin-top: 10px;
  color: #606266;
  font-size: 13px;
}
.save-bar {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 8px 0 16px;
}
.share-block {
  margin-bottom: 8px;
}
.share-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.share-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
</style>
