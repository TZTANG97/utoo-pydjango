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
        <el-col :span="12">
          <el-form-item label="制单人员">
            <el-input :model-value="String(detail.addUser || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="客户名称">
            <el-select
              v-model="form.customerId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 100%"
              @change="onCustomerChange"
            >
              <el-option
                v-for="o in customerOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
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
                v-for="o in accountOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="所属公司">
            <el-select v-model="form.supplierId" filterable clearable placeholder="请选择" style="width: 100%">
              <el-option
                v-for="o in supplierOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="销售主管">
            <el-select v-model="form.saleManagerId" filterable clearable placeholder="请选择" style="width: 100%">
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
          <el-form-item label="销售人员">
            <el-select v-model="form.saleUserId" filterable clearable placeholder="请选择" style="width: 100%">
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
          <el-form-item label="测试分类">
            <el-select v-model="form.classId" filterable clearable placeholder="请选择" style="width: 100%">
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
          <el-form-item label="订单总价">
            <el-input v-model="form.totalPrice" placeholder="订单总价" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="币种">
            <el-select v-model="form.currencyType" style="width: 100%">
              <el-option :value="1" label="人民币" />
              <el-option :value="2" label="美金" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="付款方式">
            <el-select v-model="form.payWay" filterable clearable placeholder="请选择" style="width: 100%">
              <el-option
                v-for="o in payWayOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="下单时间">
            <el-date-picker
              v-model="form.orderTime"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="预计收货时间">
            <el-date-picker
              v-model="form.deliveryTime"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="预计收款时间">
            <el-input v-model="form.collectionTime" placeholder="可填多个，逗号分隔" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否开票">
            <el-switch v-model="form.invoiceType" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="出项发票类型">
            <el-select v-model="form.outBillTypeId" filterable clearable placeholder="请选择" style="width: 100%">
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
          <el-form-item label="税率">
            <el-input v-model="form.taxes" clearable placeholder="如 6 / 13" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否含视频">
            <el-switch v-model="form.isVideo" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="样品是否回收">
            <el-switch v-model="form.reversoContext" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="实验测试地址">
            <el-select v-model="form.testAddressId" filterable clearable placeholder="请选择" style="width: 100%">
              <el-option
                v-for="o in addressOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="公司汇款账户">
            <el-select v-model="form.companyAccountId" filterable clearable placeholder="请选择" style="width: 100%">
              <el-option
                v-for="o in companyAccountOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="收件人">
            <el-input v-model="form.shipUser" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话">
            <el-input v-model="form.shipPhone" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="寄回地址">
            <el-input v-model="form.shipAddress" type="textarea" :rows="2" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="备注">
            <el-input v-model="form.mark" type="textarea" :rows="3" clearable />
          </el-form-item>
        </el-col>
      </el-row>

      <div class="lines-block">
        <h3>产品明细</h3>
        <el-table :data="lines" border stripe empty-text="暂无产品行">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="goodsName" label="产品名称" min-width="140" />
          <el-table-column prop="goodsSpec" label="产品型号" min-width="120" />
          <el-table-column prop="goodsBrandName" label="产品品牌" min-width="100" />
          <el-table-column label="数量" width="110">
            <template #default="{ row }">
              <el-input-number v-model="row.goodsNums" :min="1" :controls="false" style="width: 90px" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <el-input v-model="row.goodsPrice" clearable />
            </template>
          </el-table-column>
          <el-table-column prop="projectName" label="实验项目" min-width="120" />
          <el-table-column prop="className" label="实验分类" min-width="120" />
        </el-table>
      </div>

      <el-form-item>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
        <el-button @click="goBack">取消</el-button>
      </el-form-item>
    </el-form>
    <el-empty v-else-if="!loading" description="订单不存在或不可编辑" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchManageOptions, getExpOrderDetail, updateExpOrderBasic } from '@admin/api/experiment'
import { fetchCustomerAccounts, fetchCustomerNames } from '@admin/api/member'
import { fetchBillTypeAll, fetchPaytypeAll } from '@admin/api/order-settings'
import {
  fetchCompanyAccountList,
  fetchSupplierAll,
  fetchTestAddressList,
  fetchUserList,
} from '@admin/api/system'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type Opt = { value: string | number; label: string }
type LineRow = {
  id: string | number
  goodsName: string
  goodsSpec: string
  goodsBrandName: string
  goodsNums: number
  goodsPrice: string
  projectName: string
  className: string
}

const route = useRoute()
const router = useRouter()
const orderId = String(route.params.id || '')

const loading = ref(false)
const saving = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const lines = ref<LineRow[]>([])
const form = reactive({
  totalPrice: '',
  shipUser: '',
  shipPhone: '',
  shipAddress: '',
  mark: '',
  deliveryTime: '',
  orderTime: '',
  collectionTime: '',
  currencyType: 1 as number,
  payWay: '' as string | number | '',
  invoiceType: false,
  reversoContext: false,
  isVideo: false,
  taxes: '',
  outBillTypeId: '' as string | number | '',
  saleManagerId: '' as string | number | '',
  saleUserId: '' as string | number | '',
  supplierId: '' as string | number | '',
  customerId: '' as string | number | '',
  customUserId: '' as string | number | '',
  classId: '' as string | number | '',
  testAddressId: '' as string | number | '',
  companyAccountId: '' as string | number | '',
})

const supplierOpts = ref<Opt[]>([])
const customerOpts = ref<Opt[]>([])
const accountOpts = ref<Opt[]>([])
const managerOpts = ref<Opt[]>([])
const saleUserOpts = ref<Opt[]>([])
const classOpts = ref<Opt[]>([])
const payWayOpts = ref<Opt[]>([])
const outBillOpts = ref<Opt[]>([])
const addressOpts = ref<Opt[]>([])
const companyAccountOpts = ref<Opt[]>([])

function goBack() {
  router.push({ name: 'ExperimentOrderDetail', params: { id: orderId } })
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

async function loadCustomers() {
  try {
    const res = await fetchCustomerNames()
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    customerOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: (r.id ?? '') as string | number,
        label: String(r.name || r.companyName || r.company_name || r.id || ''),
      }))
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
}

async function loadAccounts(parentId: string | number | '') {
  accountOpts.value = []
  if (parentId === '' || parentId == null) return
  try {
    const res = await fetchCustomerAccounts(parentId)
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    accountOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: (r.id ?? '') as string | number,
        label: String(r.mobile || r.userName || r.trueName || r.id || ''),
      }))
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
}

async function onCustomerChange(val: string | number | '') {
  form.customUserId = ''
  await loadAccounts(val)
}

async function loadOptions() {
  const silent = { silentError: true } as const
  await loadCustomers()
  try {
    const res = await fetchSupplierAll(silent)
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
  try {
    const mgr = await fetchUserList({ start: 0, length: 500, type: 1, draw: 1 }, silent)
    managerOpts.value = mapUserRows(Array.isArray(mgr.data) ? mgr.data : [])
  } catch {
    /* ignore */
  }
  try {
    const sale = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 }, silent)
    saleUserOpts.value = mapUserRows(Array.isArray(sale.data) ? sale.data : [])
  } catch {
    /* ignore */
  }
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
    const addr = await fetchTestAddressList({ start: 0, length: 500, draw: 1 })
    addressOpts.value = (Array.isArray(addr.data) ? addr.data : [])
      .map((a) => {
        const row = a as Record<string, unknown>
        return {
          value: (row.id ?? '') as string | number,
          label: String(
            row.name ||
              [row.trueName || row.true_name, row.mobile, row.address].filter(Boolean).join(' ') ||
              row.id ||
              ''
          ),
        }
      })
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
  try {
    const acc = await fetchCompanyAccountList({ start: 0, length: 500, draw: 1 })
    companyAccountOpts.value = (Array.isArray(acc.data) ? acc.data : [])
      .map((a) => {
        const row = a as Record<string, unknown>
        return {
          value: (row.id ?? '') as string | number,
          label: String(
            [
              row.companyName || row.company_name,
              row.bankCardNum || row.bank_card_num,
              row.bank,
            ]
              .filter(Boolean)
              .join(' ') ||
              row.id ||
              ''
          ),
        }
      })
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
    form.totalPrice = obj.totalPrice != null ? String(obj.totalPrice) : ''
    form.shipUser = String(obj.shipUser || '')
    form.shipPhone = String(obj.shipPhone || '')
    form.shipAddress = String(obj.shipAddress || '')
    form.mark = String(obj.mark || obj.msg || '')
    form.deliveryTime = String(obj.deliveryTime || '').slice(0, 10)
    form.orderTime = String(obj.orderTime || '').slice(0, 10)
    form.collectionTime = String(obj.collectionTime || '')
    form.currencyType = Number(obj.currencyType || 1) === 2 ? 2 : 1
    form.payWay = asOptValue(obj.payWay)
    form.invoiceType = String(obj.invoiceType || '') === '1' || obj.invoiceLabel === '是'
    form.reversoContext =
      String(obj.reversoContext || '').toUpperCase() === 'ON' ||
      String(obj.reversoLabel || '') === '是'
    form.isVideo = String(obj.isVideo || '') === '1' || obj.isVideoLabel === '是'
    form.taxes = obj.taxes != null ? String(obj.taxes) : ''
    form.outBillTypeId = asOptValue(obj.outBillTypeId)
    form.saleManagerId = asOptValue(obj.saleManagerId)
    form.saleUserId = asOptValue(obj.saleUserId)
    form.supplierId = asOptValue(obj.supplierId)
    form.customerId = asOptValue(obj.customerId)
    form.customUserId = asOptValue(obj.customUserId)
    form.classId = asOptValue(obj.classId)
    form.testAddressId = asOptValue(obj.testAddressId)
    form.companyAccountId = asOptValue(obj.companyAccountId)

    ensureOpt(supplierOpts, form.supplierId, String(obj.supplierName || ''))
    ensureOpt(
      customerOpts,
      form.customerId,
      String(obj.customerName || obj.companyName || '')
    )
    ensureOpt(managerOpts, form.saleManagerId, String(obj.saleManager || ''))
    ensureOpt(saleUserOpts, form.saleUserId, String(obj.saleUser || ''))
    ensureOpt(classOpts, form.classId, String(obj.testClassName || ''))
    ensureOpt(payWayOpts, form.payWay, String(obj.payWayName || ''))

    await loadAccounts(form.customerId)
    ensureOpt(accountOpts, form.customUserId, String(obj.customMobile || obj.mobile || ''))

    const children = Array.isArray(obj.children) ? (obj.children as Record<string, unknown>[]) : []
    lines.value = children.map((ch) => ({
      id: (ch.id ?? '') as string | number,
      goodsName: String(ch.goodsName || ''),
      goodsSpec: String(ch.goodsSpec || ''),
      goodsBrandName: String(ch.goodsBrandName || ch.goodsBrand || ''),
      goodsNums: Number(ch.goodsNums || ch.goodsCount || 1) || 1,
      goodsPrice: ch.goodsPrice != null ? String(ch.goodsPrice) : '',
      projectName: String(ch.projectName || ch.experimentProjectName || ''),
      className: String(ch.className || ch.experimentClassName || ch.deviceName || ''),
    }))
  } finally {
    loading.value = false
  }
}

async function onSave() {
  if (!form.customerId && !form.customUserId) {
    ElMessage.warning('客户名称和客户账号不能同时为空')
    return
  }
  saving.value = true
  try {
    const res = await updateExpOrderBasic({
      id: orderId,
      totalPrice: form.totalPrice,
      shipUser: form.shipUser,
      shipPhone: form.shipPhone,
      shipAddress: form.shipAddress,
      mark: form.mark,
      deliveryTime: form.deliveryTime,
      orderTime: form.orderTime,
      collectionTime: form.collectionTime,
      currencyType: form.currencyType,
      payWay: form.payWay,
      invoiceType: form.invoiceType ? 1 : 0,
      reversoContext: form.reversoContext ? 'ON' : 'OFF',
      isVideo: form.isVideo ? 1 : 0,
      taxes: form.taxes,
      outBillTypeId: form.outBillTypeId,
      saleManagerId: form.saleManagerId,
      saleUserId: form.saleUserId,
      supplierId: form.supplierId,
      customerId: form.customerId,
      customUserId: form.customUserId,
      classId: form.classId,
      testAddressId: form.testAddressId,
      companyAccountId: form.companyAccountId,
      children: lines.value.map((row) => ({
        id: row.id,
        goodsNums: row.goodsNums,
        goodsPrice: row.goodsPrice,
      })),
    })
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

onMounted(async () => {
  await Promise.all([loadOptions(), load()])
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
.lines-block {
  margin: 8px 0 20px;
}
.lines-block h3 {
  margin: 0 0 12px;
  font-size: 16px;
}
</style>
