<template>
  <div v-loading="loading" class="edit-page">
    <header class="page-head">
      <button type="button" class="back-link" @click="goBack">← 返回列表</button>
      <h2>咨询详情</h2>
      <p v-if="form.id" class="sub">
        <span class="mono">#{{ form.id }}</span>
        · {{ statusLabel(form.status) }}
        <template v-if="form.order_num"> · {{ form.order_num }}</template>
      </p>
    </header>

    <el-form v-if="form.id" label-width="130px" class="form-card" :disabled="readonly" @submit.prevent>
      <div class="section-head"><h3>预约信息</h3></div>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="实验测试分类">
            <el-select v-model="form.class_id" filterable clearable placeholder="请选择" style="width: 100%">
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
          <el-form-item label="姓名">
            <el-input v-model="form.userName" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="手机号">
            <el-input v-model="form.mobile" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="公司名">
            <el-input v-model="form.company_name" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="客服人员">
            <el-input v-model="form.syUserName" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="咨询详情">
            <el-input v-model="form.content" type="textarea" :rows="3" maxlength="500" show-word-limit />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="备注">
            <el-input v-model="form.remark" type="textarea" :rows="2" maxlength="500" />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="用户上传资料">
            <div v-if="files.length" class="file-list">
              <a
                v-for="(f, i) in files"
                :key="i"
                class="file-link"
                :href="fileHref(f)"
                target="_blank"
                rel="noopener"
              >
                {{ String(f.info || f.name || `附件${i + 1}`) }}
              </a>
            </div>
            <span v-else class="muted">无</span>
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="样品寄回地址">
            <el-input v-model="form.send_address" type="textarea" :rows="2" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="样品是否回收">
            <el-switch v-model="form.reverso_context" />
          </el-form-item>
        </el-col>
        <template v-if="form.reverso_context">
          <el-col :span="12">
            <el-form-item label="收件人姓名">
              <el-input v-model="form.addressee_name" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="收件人电话">
              <el-input v-model="form.addressee_mobile" clearable />
            </el-form-item>
          </el-col>
        </template>
      </el-row>

      <div class="section-head"><h3>订单信息</h3></div>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="所属公司">
            <el-select v-model="form.supplier_name" filterable clearable placeholder="请选择" style="width: 100%">
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
            <el-select v-model="form.sale_manager" filterable clearable placeholder="请选择" style="width: 100%">
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
          <el-form-item label="预计收货时间">
            <el-date-picker
              v-model="form.delivery_time_str"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="预计收款时间">
            <el-date-picker
              v-model="form.collection_time_str"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="订单类型">
            <el-select v-model="form.order_type" clearable placeholder="请选择" style="width: 100%">
              <el-option :value="2" label="实验订单" />
              <el-option :value="1" label="实验分包订单" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="实验测试地址">
            <el-select v-model="form.test_address_id" filterable clearable placeholder="请选择" style="width: 100%">
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
          <el-form-item label="公司汇款账号">
            <el-select
              v-model="form.company_account_id"
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
        <el-col :span="6">
          <el-form-item label="是否开票">
            <el-switch v-model="form.invoiceType" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="是否含视频">
            <el-switch v-model="form.is_video" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="是否线下到场">
            <el-switch v-model="form.is_arrive" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="是否我要上机">
            <el-switch v-model="form.is_on" />
          </el-form-item>
        </el-col>
      </el-row>

      <div v-if="sampleInfos.length" class="section-head">
        <h3>样品信息</h3>
      </div>
      <el-table v-if="sampleInfos.length" :data="sampleInfos" border stripe class="sample-table">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column label="样品数量" min-width="100">
          <template #default="{ row }">{{ row.sample_num ?? row.sampleNum ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="样品名称/类型" min-width="140">
          <template #default="{ row }">{{ row.sample_name || row.sampleName || '-' }}</template>
        </el-table-column>
        <el-table-column label="主要成分" min-width="120">
          <template #default="{ row }">{{ row.main_component || row.mainComponent || '-' }}</template>
        </el-table-column>
        <el-table-column label="是否含磁" width="100">
          <template #default="{ row }">{{ magneticLabel(row.is_magnetic ?? row.isMagnetic) }}</template>
        </el-table-column>
        <el-table-column label="是否喷金" min-width="140">
          <template #default="{ row }">
            {{ goldLabel(row.is_gold_spraying ?? row.isGoldSpraying, row.gold_desc ?? row.goldDesc) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="section-head">
        <h3>产品信息</h3>
        <el-button v-if="!readonly" type="primary" link @click="addChild">+ 添加产品</el-button>
      </div>
      <el-table :data="childs" border stripe>
        <el-table-column label="产品名称" min-width="160">
          <template #default="{ row, $index }">
            <div class="goods-cell">
              <span>{{ row.goods_name || '-' }}</span>
              <el-button v-if="!readonly" link type="primary" @click="openGoodsPicker($index)">选择</el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="产品型号" min-width="140">
          <template #default="{ row }">
            <el-select
              v-model="row.goods_spec"
              :disabled="readonly"
              clearable
              filterable
              allow-create
              default-first-option
              size="small"
              style="width: 100%"
              placeholder="请选择型号"
            >
              <el-option
                v-for="spec in modelOptions(row)"
                :key="spec"
                :label="spec"
                :value="spec"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="品牌" min-width="100">
          <template #default="{ row }">{{ row.goods_brand_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="数量" width="100">
          <template #default="{ row }">
            <el-input v-model="row.goods_nums" :disabled="readonly" size="small" @change="recalcTotals" />
          </template>
        </el-table-column>
        <el-table-column label="设备名称" min-width="160">
          <template #default="{ row, $index }">
            <div class="goods-cell">
              <span>{{ deviceLabel(row) }}</span>
              <el-button v-if="!readonly" link type="primary" @click="openDevicePicker($index)">选择</el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="实验分类" min-width="120">
          <template #default="{ row }">
            <el-input v-model="row.experiment_class_name" :disabled="readonly" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="实际测试金额" width="120">
          <template #default="{ row }">
            <el-input v-model="row.goods_price" :disabled="readonly" size="small" @change="recalcTotals" />
          </template>
        </el-table-column>
        <el-table-column label="标准测试金额" width="120">
          <template #default="{ row }">
            <el-input v-model="row.reference_price" :disabled="readonly" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="样品" min-width="140">
          <template #default="{ row }">
            <el-select v-model="row.sample_id" :disabled="readonly" clearable filterable size="small" style="width: 100%">
              <el-option
                v-for="s in sampleOpts"
                :key="String(s.value)"
                :label="s.label"
                :value="s.value"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="小计" width="100">
          <template #default="{ row }">{{ lineTotal(row) }}</template>
        </el-table-column>
        <el-table-column v-if="!readonly" label="操作" width="80" fixed="right">
          <template #default="{ $index }">
            <el-button link type="danger" @click="removeChild($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="totals">
        <span>数量合计：{{ form.goods_amount }}</span>
        <span>金额合计：{{ form.totalPrice }}</span>
      </div>
    </el-form>

    <div v-if="form.id" class="actions">
      <template v-if="!readonly">
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
        <el-button type="success" :loading="ordering" @click="onSaveOrder">生成订单</el-button>
        <el-button type="danger" plain :loading="cancelling" @click="onCancel">取消咨询</el-button>
      </template>
      <el-button @click="goBack">返回</el-button>
    </div>
    <el-empty v-else-if="!loading" description="咨询不存在" />

    <el-dialog v-model="goodsDialogVisible" title="选择产品" width="720px" destroy-on-close>
      <el-form :inline="true" @submit.prevent="searchGoods">
        <el-form-item label="关键词">
          <el-input v-model="goodsKeyword" clearable placeholder="产品名称" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchGoods">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="goodsLoading" :data="goodsRows" border stripe max-height="360" @row-click="pickGoods">
        <el-table-column prop="goods_name" label="产品名称" min-width="160" />
        <el-table-column prop="goods_model" label="型号" min-width="120" />
        <el-table-column prop="goods_brand_name" label="品牌" min-width="100" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="pickGoods(row)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="deviceDialogVisible" title="选择设备名称" width="720px" destroy-on-close>
      <el-form :inline="true" @submit.prevent="searchDevices">
        <el-form-item label="关键词">
          <el-input v-model="deviceKeyword" clearable placeholder="设备/项目名称" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchDevices">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table
        v-loading="deviceLoading"
        :data="deviceRows"
        border
        stripe
        max-height="360"
        @row-click="pickDevice"
      >
        <el-table-column prop="project_name" label="设备名称" min-width="160" />
        <el-table-column prop="class_name" label="实验分类" min-width="140" />
        <el-table-column label="测试单价" width="100">
          <template #default="{ row }">{{ row.test_price ?? row.testPrice ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="pickDevice(row)">选择</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchManageOptions,
  fetchExpGoodsList,
  fetchProjectList,
} from '@admin/api/experiment'
import {
  cancelConsult,
  getConsultDetail,
  saveConsultOrder,
  updateConsult,
} from '@admin/api/service-platform'
import {
  fetchCompanyAccountList,
  fetchSupplierAll,
  fetchTestAddressList,
  fetchUserList,
} from '@admin/api/system'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type Opt = { value: string | number; label: string }
type ChildRow = Record<string, unknown>

const route = useRoute()
const router = useRouter()
const consultId = String(route.params.id || '')
const mode = String(route.query.mode || 'edit')

const loading = ref(false)
const saving = ref(false)
const ordering = ref(false)
const cancelling = ref(false)

const form = reactive({
  id: '' as string | number,
  status: -1,
  order_num: '',
  class_id: '' as string | number | '',
  userName: '',
  mobile: '',
  company_name: '',
  syUserName: '',
  content: '',
  remark: '',
  supplier_name: '' as string | number | '',
  sale_manager: '' as string | number | '',
  delivery_time_str: '',
  collection_time_str: '',
  order_type: 2 as number | '',
  send_address: '',
  reverso_context: false,
  addressee_name: '',
  addressee_mobile: '',
  test_address_id: '' as string | number | '',
  company_account_id: '' as string | number | '',
  invoiceType: false,
  is_video: false,
  is_arrive: false,
  is_on: false,
  totalPrice: '0.00',
  goods_amount: '0.0',
})

const childs = ref<ChildRow[]>([])
const files = ref<Record<string, unknown>[]>([])
const sampleInfos = ref<Record<string, unknown>[]>([])
const sampleOpts = ref<Opt[]>([])
const classOpts = ref<Opt[]>([])
const supplierOpts = ref<Opt[]>([])
const managerOpts = ref<Opt[]>([])
const addressOpts = ref<Opt[]>([])
const accountOpts = ref<Opt[]>([])

const goodsDialogVisible = ref(false)
const goodsLoading = ref(false)
const goodsKeyword = ref('')
const goodsRows = ref<Record<string, unknown>[]>([])
const goodsPickIndex = ref(-1)

const deviceDialogVisible = ref(false)
const deviceLoading = ref(false)
const deviceKeyword = ref('')
const deviceRows = ref<Record<string, unknown>[]>([])
const devicePickIndex = ref(-1)

const readonly = computed(() => {
  if (mode === 'view') return true
  const st = Number(form.status)
  return st === 2 || st === 3
})

const STATUS_MAP: Record<number, string> = {
  0: '待处理',
  1: '已处理',
  2: '已生成订单',
  3: '已取消',
}

function statusLabel(val: unknown) {
  const n = Number(val)
  if (Number.isNaN(n) || n < 0) return '未回复'
  return STATUS_MAP[n] ?? '未回复'
}

function goBack() {
  router.push({ name: 'ServiceConsult' })
}

function fileHref(file: Record<string, unknown>) {
  const url = String(file.url || '')
  if (url) return url
  const path = String(file.path || '').replace(/\/$/, '')
  const name = String(file.name || '')
  return path && name ? `${path}/${name}` : path || name || '#'
}

function flagOn(val: unknown) {
  return val === 1 || val === '1' || val === true || String(val).toUpperCase() === 'ON'
}

function lineTotal(row: ChildRow) {
  const price = Number(row.goods_price || 0)
  const nums = Number(row.goods_nums || 0)
  return (price * nums).toFixed(2)
}

function recalcTotals() {
  let amount = 0
  let total = 0
  for (const row of childs.value) {
    const nums = Number(row.goods_nums || 0)
    const price = Number(row.goods_price || 0)
    amount += nums
    total += nums * price
  }
  form.goods_amount = amount.toFixed(1)
  form.totalPrice = total.toFixed(2)
}

function mapManageOpts(list: unknown[]): Opt[] {
  return (list as Record<string, unknown>[])
    .map((x) => ({
      value: (x.id ?? x.value ?? '') as string | number,
      label: String(x.name || x.label || x.id || ''),
    }))
    .filter((o) => o.value !== '' && o.value != null)
}

function mapUserRows(list: unknown[]): Opt[] {
  return (list as Record<string, unknown>[])
    .map((u) => ({
      value: (u.id ?? u.userId ?? '') as string | number,
      label: String(u.userName || u.trueName || u.user_name || u.true_name || u.id || ''),
    }))
    .filter((o) => o.value !== '' && o.value != null)
}

function emptyChild(): ChildRow {
  return {
    goods_id: '',
    goods_name: '',
    goods_model: '',
    goods_spec: '',
    goods_brand_name: '',
    goods_nums: '1',
    goods_price: '0',
    reference_price: '0',
    experiment_project_id: '',
    experiment_project_name: '',
    experiment_class_id: '',
    experiment_class_name: '',
    sample_id: '',
  }
}

function addChild() {
  childs.value.push(emptyChild())
}

function removeChild(index: number) {
  if (childs.value.length <= 1) {
    ElMessage.warning('至少保留一条产品信息')
    return
  }
  childs.value.splice(index, 1)
  recalcTotals()
}

/** 样品含磁/喷金：库内 0=是，非 0=否 */
function magneticLabel(v: unknown) {
  if (v == null || v === '') return '-'
  return Number(v) === 0 ? '是' : '否'
}

function goldLabel(isGold: unknown, goldDesc: unknown) {
  if (isGold == null || isGold === '') return '-'
  if (Number(isGold) === 0) return '是'
  const desc = String(goldDesc ?? '').trim()
  return desc ? `否(${desc})` : '否()'
}

function modelOptions(row: ChildRow): string[] {
  const raw = String(row.goods_model || row.goodsModel || '').trim()
  const parts = raw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  const cur = String(row.goods_spec || '').trim()
  if (cur && !parts.includes(cur)) parts.unshift(cur)
  return parts
}

function deviceLabel(row: ChildRow) {
  const name = String(row.experiment_project_name || '').trim()
  const cls = String(row.experiment_class_name || '').trim()
  if (name && cls) return `${name}（${cls}）`
  return name || '-'
}

function mapGoodsRow(row: Record<string, unknown>) {
  return {
    ...row,
    id: row.id,
    goods_name: row.goods_name || row.goodsName || '',
    goods_model: row.goods_model || row.goodsModel || row.goods_spec || '',
    goods_brand_name:
      row.goods_brand_name || row.goodsBrandName || row.brand_name || row.brandName || '',
    goods_brand_id: row.goods_brand_id || row.goodsBrandId || row.brand_id || row.brandId || '',
  }
}

function mapDeviceRow(row: Record<string, unknown>) {
  return {
    ...row,
    id: row.id,
    project_name: row.project_name || row.projectName || '',
    class_name: row.class_name || row.className || '',
    class_id: row.class_id ?? row.classId ?? '',
    test_price: row.test_price ?? row.testPrice ?? '',
  }
}

async function openGoodsPicker(index: number) {
  goodsPickIndex.value = index
  goodsDialogVisible.value = true
  await searchGoods()
}

async function searchGoods() {
  goodsLoading.value = true
  try {
    const kw = goodsKeyword.value.trim()
    const res = await fetchExpGoodsList({
      start: 0,
      length: 50,
      draw: 1,
      name: kw,
      goodsName: kw,
      goods_name: kw,
    })
    const raw = Array.isArray(res.data) ? res.data : []
    goodsRows.value = raw.map((r) => mapGoodsRow(r as Record<string, unknown>))
  } finally {
    goodsLoading.value = false
  }
}

function pickGoods(row: Record<string, unknown>) {
  const idx = goodsPickIndex.value
  if (idx < 0 || !childs.value[idx]) return
  const mapped = mapGoodsRow(row)
  const target = childs.value[idx]
  const modelRaw = String(mapped.goods_model || '')
  const specs = modelRaw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  target.goods_id = mapped.id
  target.goods_name = mapped.goods_name
  target.goods_model = modelRaw
  target.goods_spec = specs[0] || modelRaw
  target.goods_brand_name = mapped.goods_brand_name
  target.goods_brand_id = mapped.goods_brand_id
  if (!target.goods_nums) target.goods_nums = '1'
  goodsDialogVisible.value = false
  recalcTotals()
  openDevicePicker(idx)
}

async function openDevicePicker(index: number) {
  devicePickIndex.value = index
  deviceDialogVisible.value = true
  await searchDevices()
}

async function searchDevices() {
  deviceLoading.value = true
  try {
    const kw = deviceKeyword.value.trim()
    const res = await fetchProjectList({
      start: 0,
      length: 50,
      draw: 1,
      name: kw,
      projectName: kw,
      project_name: kw,
    })
    const raw = Array.isArray(res.data) ? res.data : []
    deviceRows.value = raw.map((r) => mapDeviceRow(r as Record<string, unknown>))
  } finally {
    deviceLoading.value = false
  }
}

function pickDevice(row: Record<string, unknown>) {
  const idx = devicePickIndex.value
  if (idx < 0 || !childs.value[idx]) return
  const mapped = mapDeviceRow(row)
  const target = childs.value[idx]
  target.experiment_project_id = mapped.id
  target.experiment_project_name = mapped.project_name
  target.experiment_class_id = mapped.class_id
  target.experiment_class_name = mapped.class_name
  const price = mapped.test_price
  if (price !== '' && price != null) {
    const p = String(price)
    target.goods_price = p
    target.reference_price = p
    recalcTotals()
  }
  deviceDialogVisible.value = false
}

function buildPayload(): unknown[] {
  const head = {
    id: form.id,
    class_id: form.class_id,
    userName: form.userName,
    mobile: form.mobile,
    company_name: form.company_name,
    content: form.content,
    remark: form.remark,
    syUserName: form.syUserName,
    supplier_name: form.supplier_name === '' ? '' : String(form.supplier_name),
    sale_manager: form.sale_manager === '' ? '' : String(form.sale_manager),
    delivery_time_str: form.delivery_time_str,
    collection_time_str: form.collection_time_str,
    order_type: form.order_type,
    send_address: form.send_address,
    reverso_context: form.reverso_context ? 'ON' : 'OFF',
    addressee_name: form.addressee_name,
    addressee_mobile: form.addressee_mobile,
    test_address_id: form.test_address_id,
    company_account_id: form.company_account_id,
    invoiceType: form.invoiceType ? 'ON' : 'OFF',
    is_video: form.is_video ? 1 : 0,
    is_arrive: form.is_arrive ? 1 : 0,
    is_on: form.is_on ? 1 : 0,
    totalPrice: form.totalPrice,
    goods_amount: form.goods_amount,
  }
  const rows = childs.value.map((c) => ({
    goods_id: c.goods_id,
    goods_name: c.goods_name,
    goods_spec: c.goods_spec,
    goods_brand_name: c.goods_brand_name,
    goods_nums: c.goods_nums,
    goods_price: c.goods_price,
    reference_price: c.reference_price,
    experiment_project_id: c.experiment_project_id,
    experiment_project_name: c.experiment_project_name,
    experiment_class_id: c.experiment_class_id,
    experiment_class_name: c.experiment_class_name,
    sample_id: c.sample_id,
  }))
  return [head, ...rows]
}

async function loadOptions() {
  const silent = { silentError: true }
  try {
    const cls = await fetchManageOptions(3)
    if (isAjaxOk(cls) && Array.isArray(cls.obj)) {
      classOpts.value = mapManageOpts(cls.obj as unknown[])
    }
  } catch {
    /* ignore */
  }
  try {
    const supRes = await fetchSupplierAll(silent)
    if (isAjaxOk(supRes)) {
      const raw = (supRes.obj || supRes.data) as unknown
      const list = Array.isArray(raw)
        ? raw
        : Array.isArray((raw as Record<string, unknown>)?.list)
          ? ((raw as Record<string, unknown>).list as unknown[])
          : []
      supplierOpts.value = (list as Record<string, unknown>[])
        .map((s) => ({
          value: (s.id ?? '') as string | number,
          label: String(s.companyName || s.company_name || s.name || s.id || ''),
        }))
        .filter((o) => o.value !== '' && o.value != null)
    }
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
    const addr = await fetchTestAddressList({ start: 0, length: 500, draw: 1 })
    addressOpts.value = (Array.isArray(addr.data) ? addr.data : []).map((a) => {
      const row = a as Record<string, unknown>
      return {
        value: (row.id ?? '') as string | number,
        label: String(
          row.name ||
            [row.true_name, row.mobile, row.address].filter(Boolean).join(' ') ||
            row.id ||
            ''
        ),
      }
    }).filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
  try {
    const acc = await fetchCompanyAccountList({ start: 0, length: 500, draw: 1 })
    accountOpts.value = (Array.isArray(acc.data) ? acc.data : []).map((a) => {
      const row = a as Record<string, unknown>
      return {
        value: (row.id ?? '') as string | number,
        label: String(
          row.name ||
            [row.company_name, row.bankCardNum, row.bank].filter(Boolean).join(' ') ||
            row.id ||
            ''
        ),
      }
    }).filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
}

async function loadDetail() {
  if (!consultId) return
  loading.value = true
  try {
    const res = await getConsultDetail(consultId)
    if (!isAjaxOk(res) || !res.obj) {
      ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    const consult = (obj.consult || obj) as Record<string, unknown>
    form.id = (consult.id as string | number) || consultId
    form.status = Number(consult.status ?? -1)
    form.order_num = String(consult.order_num || consult.orderNum || '')
    form.class_id = (consult.class_id ?? consult.classId ?? '') as string | number | ''
    form.userName = String(consult.userName || '')
    form.mobile = String(consult.mobile || '')
    form.company_name = String(consult.company_name || consult.companyName || '')
    form.syUserName = String(consult.syUserName || obj.syUserName || '')
    form.content = String(consult.content || consult.zxcontent || '')
    form.remark = String(consult.remark || '')
    form.supplier_name = (consult.supplier_name ?? consult.supplierName ?? '') as string | number | ''
    form.sale_manager = (consult.sale_manager ?? consult.saleManager ?? '') as string | number | ''
    form.delivery_time_str = String(
      consult.delivery_time_str || consult.deliveryTimeStr || ''
    ).slice(0, 10)
    form.collection_time_str = String(
      consult.collection_time_str || consult.collectionTimeStr || ''
    ).slice(0, 10)
    form.order_type = (consult.order_type ?? consult.orderType ?? 2) as number | ''
    form.send_address = String(consult.send_address || consult.sendAddress || '')
    form.reverso_context = flagOn(consult.reverso_context ?? consult.reversoContext)
    form.addressee_name = String(consult.addressee_name || consult.addresseeName || '')
    form.addressee_mobile = String(consult.addressee_mobile || consult.addresseeMobile || '')
    form.test_address_id = (consult.test_address_id ?? consult.testAddressId ?? '') as
      | string
      | number
      | ''
    form.company_account_id = (consult.company_account_id ?? consult.companyAccountId ?? '') as
      | string
      | number
      | ''
    form.invoiceType = flagOn(consult.invoiceType)
    form.is_video = flagOn(consult.is_video ?? consult.isVideo)
    form.is_arrive = flagOn(consult.is_arrive ?? consult.isArrive)
    form.is_on = flagOn(consult.is_on ?? consult.isOn)

    const rawChilds = Array.isArray(obj.childs) ? (obj.childs as ChildRow[]) : []
    childs.value = rawChilds.length
      ? rawChilds.map((c) => {
          const eg = (c.expGoods || c.exp_goods) as Record<string, unknown> | undefined
          return {
            ...emptyChild(),
            ...c,
            goods_id: c.goods_id ?? c.goodsId ?? '',
            goods_name: c.goods_name || c.goodsName || eg?.goods_name || eg?.goodsName || '',
            goods_model: String(
              c.goods_model || c.goodsModel || eg?.goods_model || eg?.goodsModel || ''
            ),
            goods_spec:
              c.goods_spec ||
              c.goodsSpec ||
              '',
            goods_brand_name:
              c.goods_brand_name || c.goodsBrandName || eg?.brand_name || eg?.brandName || '',
            goods_brand_id: c.goods_brand_id ?? c.goodsBrandId ?? eg?.goods_brand_id ?? '',
            goods_nums: c.goods_nums != null || c.goodsNums != null
              ? String(c.goods_nums ?? c.goodsNums)
              : '1',
            goods_price: c.goods_price != null || c.goodsPrice != null
              ? String(c.goods_price ?? c.goodsPrice)
              : '0',
            reference_price:
              c.reference_price != null || c.referencePrice != null
                ? String(c.reference_price ?? c.referencePrice)
                : '0',
            experiment_project_id: c.experiment_project_id ?? c.experimentProjectId ?? '',
            experiment_project_name:
              c.experiment_project_name || c.experimentProjectName || '',
            experiment_class_id: c.experiment_class_id ?? c.experimentClassId ?? '',
            experiment_class_name: c.experiment_class_name || c.experimentClassName || '',
            sample_id: c.sample_id ?? c.sampleId ?? '',
          }
        })
      : [emptyChild()]

    files.value = Array.isArray(obj.files) ? (obj.files as Record<string, unknown>[]) : []
    sampleInfos.value = Array.isArray(obj.childsyp)
      ? (obj.childsyp as Record<string, unknown>[])
      : []
    const samples = Array.isArray(obj.sampleList) ? (obj.sampleList as Record<string, unknown>[]) : []
    sampleOpts.value = samples.map((s) => ({
      value: (s.value ?? s.id ?? '') as string | number,
      label: String(s.label || `${s.sampleNum || s.sample_num || ''} ${s.sampleName || s.sample_name || ''}`.trim() || s.id || ''),
    })).filter((o) => o.value !== '' && o.value != null)

    if (!form.syUserName && obj.className) {
      /* keep className from obj if needed */
    }
    recalcTotals()
  } finally {
    loading.value = false
  }
}

async function onSave() {
  saving.value = true
  try {
    const res = await updateConsult(buildPayload())
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success(res.resMsg || '保存成功')
    await loadDetail()
  } finally {
    saving.value = false
  }
}

async function onSaveOrder() {
  if (!form.class_id) return ElMessage.warning('请选择实验测试分类')
  if (!form.supplier_name) return ElMessage.warning('请选择所属公司')
  if (!form.sale_manager) return ElMessage.warning('请选择销售主管')
  if (!form.delivery_time_str) return ElMessage.warning('请选择预计收货时间')
  if (!form.collection_time_str) return ElMessage.warning('请选择预计收款时间')
  if (!form.order_type) return ElMessage.warning('请选择生成订单类型')
  if (!form.test_address_id) return ElMessage.warning('请选择实验测试地址')
  if (!form.company_account_id) return ElMessage.warning('请选择公司汇款账号')
  if (!childs.value.some((c) => c.goods_id)) return ElMessage.warning('请至少选择一条产品信息')
  // 有样品时：每个样品须被至少一条产品选中；额外产品可不选样品
  const sampleIds = (
    sampleOpts.value.length
      ? sampleOpts.value.map((s) => s.value)
      : sampleInfos.value.map((s) => s.id ?? s.value)
  )
    .filter((id) => id !== '' && id != null)
    .map((id) => String(id))
  if (sampleIds.length) {
    const selected = new Set(
      childs.value
        .map((c) => c.sample_id)
        .filter((id) => id !== '' && id != null)
        .map((id) => String(id))
    )
    if (sampleIds.some((id) => !selected.has(id))) {
      return ElMessage.warning('请将所有样品关联到产品后再生成订单')
    }
  }

  ordering.value = true
  try {
    const res = await saveConsultOrder(buildPayload())
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '生成订单失败'))
      return
    }
    ElMessage.success('生成成功')
    const orderId = res.obj ?? res.resMsg
    if (orderId && String(orderId).match(/^\d+$/)) {
      router.push({
        name: 'ExperimentOrderDetail',
        params: { id: String(orderId) },
      })
      return
    }
    await loadDetail()
  } finally {
    ordering.value = false
  }
}

async function onCancel() {
  await ElMessageBox.confirm('确认取消该咨询？', '提示', { type: 'warning' })
  cancelling.value = true
  try {
    const res = await cancelConsult(form.id)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '取消失败'))
      return
    }
    ElMessage.success(res.resMsg || '取消成功')
    form.status = 3
    await loadDetail()
  } finally {
    cancelling.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadOptions(), loadDetail()])
})
</script>

<style scoped lang="scss">
.edit-page {
  padding: 8px 4px 24px;
}
.page-head {
  margin-bottom: 16px;
  h2 {
    margin: 8px 0 4px;
    font-size: 20px;
    font-weight: 600;
  }
  .sub {
    margin: 0;
    color: #64748b;
    font-size: 13px;
  }
}
.back-link {
  border: 0;
  background: transparent;
  color: #2563eb;
  cursor: pointer;
  padding: 0;
  font-size: 13px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.form-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px 20px 8px;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 8px 0 12px;
  h3 {
    margin: 0;
    font-size: 15px;
  }
}
.sample-table {
  margin-bottom: 16px;
}
.goods-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}
.file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.file-link {
  color: #e96302;
  text-decoration: none;
  &:hover {
    text-decoration: underline;
  }
}
.muted {
  color: #94a3b8;
}
.totals {
  display: flex;
  gap: 24px;
  justify-content: flex-end;
  margin: 12px 0 8px;
  font-weight: 600;
}
.actions {
  margin: 16px 0 8px;
  display: flex;
  gap: 8px;
}
</style>
