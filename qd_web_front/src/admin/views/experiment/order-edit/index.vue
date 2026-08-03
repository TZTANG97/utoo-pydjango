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
            <el-input :model-value="String(detail.customerName || detail.companyName || '')" disabled />
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
                v-for="o in accountOpts"
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
import { fetchBillTypeAll, fetchPaytypeAll } from '@admin/api/order-settings'
import {
  fetchCompanyAccountList,
  fetchSupplierAll,
  fetchTestAddressList,
  fetchUserList,
} from '@admin/api/system'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type Opt = { value: string | number; label: string }

const route = useRoute()
const router = useRouter()
const orderId = String(route.params.id || '')

const loading = ref(false)
const saving = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
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
  classId: '' as string | number | '',
  testAddressId: '' as string | number | '',
  companyAccountId: '' as string | number | '',
})

const supplierOpts = ref<Opt[]>([])
const managerOpts = ref<Opt[]>([])
const saleUserOpts = ref<Opt[]>([])
const classOpts = ref<Opt[]>([])
const payWayOpts = ref<Opt[]>([])
const outBillOpts = ref<Opt[]>([])
const addressOpts = ref<Opt[]>([])
const accountOpts = ref<Opt[]>([])

function goBack() {
  router.push({ name: 'ExperimentOrderDetail', params: { id: orderId } })
}

function mapUserRows(rows: Record<string, unknown>[]): Opt[] {
  return rows
    .map((u) => ({
      value: (u.id ?? '') as string | number,
      label: String(u.trueName || u.true_name || u.userName || u.user_name || u.id || ''),
    }))
    .filter((o) => o.value !== '' && o.value != null)
}

async function loadOptions() {
  const silent = { silentError: true } as const
  try {
    const res = await fetchSupplierAll(silent)
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    supplierOpts.value = (list as Record<string, unknown>[]).map((r) => ({
      value: (r.id ?? '') as string | number,
      label: String(r.companyName || r.company_name || r.name || r.id || ''),
    })).filter((o) => o.value !== '' && o.value != null)
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
    accountOpts.value = (Array.isArray(acc.data) ? acc.data : [])
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
              .join(' ') || row.id || ''
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
    form.payWay = (obj.payWay ?? '') as string | number | ''
    form.invoiceType = String(obj.invoiceType || '') === '1' || obj.invoiceLabel === '是'
    form.reversoContext =
      String(obj.reversoContext || '').toUpperCase() === 'ON' ||
      String(obj.reversoLabel || '') === '是'
    form.isVideo = String(obj.isVideo || '') === '1' || obj.isVideoLabel === '是'
    form.taxes = obj.taxes != null ? String(obj.taxes) : ''
    form.outBillTypeId = (obj.outBillTypeId ?? '') as string | number | ''
    form.saleManagerId = (obj.saleManagerId ?? '') as string | number | ''
    form.saleUserId = (obj.saleUserId ?? '') as string | number | ''
    form.supplierId = (obj.supplierId ?? '') as string | number | ''
    form.classId = (obj.classId ?? '') as string | number | ''
    form.testAddressId = (obj.testAddressId ?? '') as string | number | ''
    form.companyAccountId = (obj.companyAccountId ?? '') as string | number | ''
  } finally {
    loading.value = false
  }
}

async function onSave() {
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
      classId: form.classId,
      testAddressId: form.testAddressId,
      companyAccountId: form.companyAccountId,
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
  max-width: 1100px;
}
</style>
