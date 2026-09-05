<template>
  <admin-page-card title="数字化管理运营中心">
    <!-- 管理员：公司列表 + 全局实验看板（对齐 Java userType==1） -->
    <template v-if="isAdminDigital">
      <el-form :inline="true" class="filter-form" @submit.prevent>
        <el-form-item label="年份选择">
          <el-select v-model="year" clearable placeholder="全部" style="width: 140px" @change="reloadCompany">
            <el-option label="全部" value="" />
            <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="String(y)" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="orderStatusType" style="width: 160px" @change="reloadCompany">
            <el-option label="全部" value="1" />
            <el-option label="订单未发起审核" value="2" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="tableLoading" @click="reloadCompany">查询</el-button>
        </el-form-item>
      </el-form>

      <el-row :gutter="16">
        <el-col :span="24">
          <el-table
            v-loading="tableLoading"
            :data="companyRows"
            border
            size="small"
            max-height="420"
            class="company-table"
            :row-class-name="rowClassName"
          >
            <el-table-column prop="index" label="#" width="56" />
            <el-table-column prop="company_name" label="公司名称" min-width="220" show-overflow-tooltip />
            <el-table-column prop="syrmb" label="实验(RMB)" width="160" align="right">
              <template #default="{ row }">
                <el-button
                  v-if="!row.isTotal && row.company_id"
                  link
                  type="primary"
                  @click="openCompanyOrders(row)"
                >
                  {{ formatMoney(row.syrmb) }}
                </el-button>
                <span v-else>{{ formatMoney(row.syrmb) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="charts-row">
        <el-col :span="12">
          <div class="chart-panel">
            <div class="chart-head">
              <h4>实验订单金额</h4>
              <el-select
                v-model="chartYear6"
                clearable
                placeholder="全部"
                style="width: 120px"
                @change="loadChart(6)"
              >
                <el-option label="全部" value="" />
                <el-option v-for="y in yearOptions" :key="`6-${y}`" :label="`${y}年`" :value="String(y)" />
              </el-select>
            </div>
            <div ref="chart6Ref" class="chart-box" v-loading="chart6Loading" />
            <p class="chart-total">
              {{ chartFooter(chartYear6) }}人民币 {{ formatMoney(total6) }}
            </p>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-panel">
            <div class="chart-head">
              <h4>实验分包订单金额</h4>
              <el-select
                v-model="chartYear8"
                clearable
                placeholder="全部"
                style="width: 120px"
                @change="loadChart(8)"
              >
                <el-option label="全部" value="" />
                <el-option v-for="y in yearOptions" :key="`8-${y}`" :label="`${y}年`" :value="String(y)" />
              </el-select>
            </div>
            <div ref="chart8Ref" class="chart-box" v-loading="chart8Loading" />
            <p class="chart-total">
              {{ chartFooter(chartYear8) }}人民币 {{ formatMoney(total8) }}
            </p>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="charts-row">
        <el-col :span="12">
          <div class="chart-panel pie-panel">
            <div class="chart-head">
              <h4>实验已收/应收</h4>
            </div>
            <div ref="pie6Ref" class="chart-box pie-box" v-loading="pie6Loading" />
            <p class="chart-total">
              总额(实际总额/减去异常订单)：{{ formatMoney(pie6.total) }} ，已收总额(包含未分配金额)：
              {{ formatMoney(pie6.received) }}，应收总额：{{ formatMoney(pie6.receivable) }}
            </p>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-panel pie-panel">
            <div class="chart-head">
              <h4>实验分包已收/应收</h4>
            </div>
            <div ref="pie8Ref" class="chart-box pie-box" v-loading="pie8Loading" />
            <p class="chart-total">
              总额：{{ formatMoney(pie8.total) }}， 已收总额： {{ formatMoney(pie8.received) }}，应收总额：{{
                formatMoney(pie8.receivable)
              }}
            </p>
          </div>
        </el-col>
      </el-row>
    </template>

    <!-- 公司基金等：个人实验/分包双币种柱图 + 应收应付饼图（对齐 Java manage_center #else） -->
    <template v-else>
      <el-row :gutter="16">
        <el-col :span="12">
          <div class="chart-panel">
            <div class="chart-head">
              <h4>个人实验总额{{ personalYear6 ? ` ${personalYear6} 年` : '' }}</h4>
              <el-select
                v-model="personalYear6"
                placeholder="年份选择"
                style="width: 120px"
                @change="loadPersonal(6)"
              >
                <el-option v-for="y in yearOptions" :key="`p6-${y}`" :label="`${y}年`" :value="String(y)" />
              </el-select>
            </div>
            <div ref="personal6Ref" class="chart-box" v-loading="personal6Loading" />
            <p class="chart-total">
              全年实验总额：人民币 {{ formatMoney(personal6.qnxsrmb) }} |美元
              {{ formatMoney(personal6.qnxsus) }} | 实验的订单数量：人民币订单总数:{{ personal6.ddslrmb }}，美元订单总数:{{
                personal6.ddslus
              }}
            </p>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-panel">
            <div class="chart-head">
              <h4>个人实验分包总额{{ personalYear8 ? ` ${personalYear8} 年` : '' }}</h4>
              <el-select
                v-model="personalYear8"
                placeholder="年份选择"
                style="width: 120px"
                @change="loadPersonal(8)"
              >
                <el-option v-for="y in yearOptions" :key="`p8-${y}`" :label="`${y}年`" :value="String(y)" />
              </el-select>
            </div>
            <div ref="personal8Ref" class="chart-box" v-loading="personal8Loading" />
            <p class="chart-total">
              全年实验分包总额：人民币 {{ formatMoney(personal8.qnxsrmb) }} |美元
              {{ formatMoney(personal8.qnxsus) }} | 实验分包的订单数量：人民币订单总数:{{ personal8.ddslrmb }}，美元订单总数:{{
                personal8.ddslus
              }}
            </p>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="charts-row">
        <el-col :span="12">
          <div class="chart-panel pie-panel">
            <div class="chart-head">
              <h4>个人实验应付款</h4>
            </div>
            <div ref="payExpRef" class="chart-box pie-box" v-loading="personalPieLoading" />
            <p class="chart-total">
              应付总额：美元 {{ formatMoney(personalPie.payExp.us) }}，人民币
              {{ formatMoney(personalPie.payExp.rmb) }} 元
            </p>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-panel pie-panel">
            <div class="chart-head">
              <h4>个人实验应收款</h4>
            </div>
            <div ref="recvExpRef" class="chart-box pie-box" v-loading="personalPieLoading" />
            <p class="chart-total">
              应收总额：美元 {{ formatMoney(personalPie.recvExp.us) }}，人民币
              {{ formatMoney(personalPie.recvExp.rmb) }} 元
            </p>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="charts-row">
        <el-col :span="12">
          <div class="chart-panel pie-panel">
            <div class="chart-head">
              <h4>个人实验分包应付款</h4>
            </div>
            <div ref="paySubRef" class="chart-box pie-box" v-loading="personalPieLoading" />
            <p class="chart-total">
              应付总额：美元 {{ formatMoney(personalPie.paySub.us) }}，人民币
              {{ formatMoney(personalPie.paySub.rmb) }} 元
            </p>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-panel pie-panel">
            <div class="chart-head">
              <h4>个人实验分包应收款</h4>
            </div>
            <div ref="recvSubRef" class="chart-box pie-box" v-loading="personalPieLoading" />
            <p class="chart-total">
              应收总额：美元 {{ formatMoney(personalPie.recvSub.us) }}，人民币
              {{ formatMoney(personalPie.recvSub.rmb) }} 元
            </p>
          </div>
        </el-col>
      </el-row>
    </template>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { useUserStore } from '@admin/stores/user'
import {
  fetchCompanySaleByYear,
  fetchExpReceivePie,
  fetchExpSaleByYear,
  fetchUserAmountByYearSyfbgr,
  fetchUserAmountByYearSygr,
  fetchUserOverduePie,
  isAjaxOk,
} from '@admin/api/fund'

type CompanyRow = {
  index?: number
  id?: number | string
  company_id?: number | string
  company_name?: string
  syrmb?: number
  isTotal?: boolean
}

type PieSlice = {
  name?: string
  value?: number
  company_name?: string
  company_id?: number | string
  total?: number
}

const router = useRouter()
const userStore = useUserStore()
/** Java：userType=="1" 管理员看板，否则个人看板（公司基金 CS04 等） */
const isAdminDigital = computed(() => {
  const t = Number(userStore.welcome?.userType ?? userStore.userType ?? 0)
  return t === 1
})

const tableLoading = ref(false)
const chart6Loading = ref(false)
const chart8Loading = ref(false)
const pie6Loading = ref(false)
const pie8Loading = ref(false)
const personal6Loading = ref(false)
const personal8Loading = ref(false)
const personalPieLoading = ref(false)

const nowYear = new Date().getFullYear()
/** 对齐 Java：自 2019 年起 */
const yearOptions = Array.from({ length: nowYear - 2019 + 1 }, (_, i) => nowYear - i)

const year = ref('')
const orderStatusType = ref('1')
const chartYear6 = ref('')
const chartYear8 = ref('')
const personalYear6 = ref(String(nowYear))
const personalYear8 = ref(String(nowYear))
const companyRows = ref<CompanyRow[]>([])
const total6 = ref(0)
const total8 = ref(0)
const pie6 = reactive({ received: 0, receivable: 0, total: 0 })
const pie8 = reactive({ received: 0, receivable: 0, total: 0 })
const personal6 = reactive({ qnxsrmb: 0, qnxsus: 0, ddslrmb: 0, ddslus: 0 })
const personal8 = reactive({ qnxsrmb: 0, qnxsus: 0, ddslrmb: 0, ddslus: 0 })
const personalPie = reactive({
  payExp: { rmb: 0, us: 0 },
  recvExp: { rmb: 0, us: 0 },
  paySub: { rmb: 0, us: 0 },
  recvSub: { rmb: 0, us: 0 },
})
const currentUserLabel = ref('')

const chart6Ref = ref<HTMLDivElement | null>(null)
const chart8Ref = ref<HTMLDivElement | null>(null)
const pie6Ref = ref<HTMLDivElement | null>(null)
const pie8Ref = ref<HTMLDivElement | null>(null)
const personal6Ref = ref<HTMLDivElement | null>(null)
const personal8Ref = ref<HTMLDivElement | null>(null)
const payExpRef = ref<HTMLDivElement | null>(null)
const recvExpRef = ref<HTMLDivElement | null>(null)
const paySubRef = ref<HTMLDivElement | null>(null)
const recvSubRef = ref<HTMLDivElement | null>(null)
let chart6: ECharts | null = null
let chart8: ECharts | null = null
let pie6Chart: ECharts | null = null
let pie8Chart: ECharts | null = null
let personal6Chart: ECharts | null = null
let personal8Chart: ECharts | null = null
let payExpChart: ECharts | null = null
let recvExpChart: ECharts | null = null
let paySubChart: ECharts | null = null
let recvSubChart: ECharts | null = null

function formatMoney(v: unknown) {
  return Number(v || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

/** 对齐 Java：`{year}全年销售总额(包含未审核订单)：` */
function chartFooter(y: string) {
  const prefix = y ? `${y}` : ''
  return `${prefix}全年销售总额(包含未审核订单)：`
}

function rowClassName({ row }: { row: CompanyRow }) {
  return row.isTotal ? 'is-total-row' : ''
}

function ensureBar(kind: 6 | 8) {
  if (kind === 6) {
    if (!chart6Ref.value) return null
    if (!chart6) chart6 = echarts.init(chart6Ref.value)
    return chart6
  }
  if (!chart8Ref.value) return null
  if (!chart8) chart8 = echarts.init(chart8Ref.value)
  return chart8
}

function ensurePie(kind: 6 | 8) {
  if (kind === 6) {
    if (!pie6Ref.value) return null
    if (!pie6Chart) pie6Chart = echarts.init(pie6Ref.value)
    return pie6Chart
  }
  if (!pie8Ref.value) return null
  if (!pie8Chart) pie8Chart = echarts.init(pie8Ref.value)
  return pie8Chart
}

function ensurePersonal(kind: 6 | 8) {
  if (kind === 6) {
    if (!personal6Ref.value) return null
    if (!personal6Chart) personal6Chart = echarts.init(personal6Ref.value)
    return personal6Chart
  }
  if (!personal8Ref.value) return null
  if (!personal8Chart) personal8Chart = echarts.init(personal8Ref.value)
  return personal8Chart
}

function toPieData(list: PieSlice[] | undefined) {
  if (!Array.isArray(list)) return []
  return list
    .map((item) => ({
      name: String(item.name || item.company_name || ''),
      value: Number(item.value ?? item.total ?? 0),
      company_id: item.company_id ?? '',
    }))
    .filter((item) => item.value !== 0)
}

function openCompanyOrders(row: CompanyRow) {
  const companyId = row.company_id ?? row.id
  if (companyId == null || companyId === '' || row.isTotal) return
  router.push({
    name: 'FundDigitalOrders',
    query: {
      mode: 'company',
      title: '实验订单',
      company_id: String(companyId),
      type: orderStatusType.value,
      year: year.value,
      order_type: '3',
      account_type: '1',
    },
  })
}

function openExpOrders(query: Record<string, string>, title: string) {
  router.push({
    name: 'FundDigitalOrders',
    query: {
      mode: 'exp',
      title,
      ...query,
    },
  })
}

function bindBarClick(kind: 6 | 8) {
  const inst = kind === 6 ? chart6 : chart8
  if (!inst) return
  inst.off('click')
  inst.on('click', (params: { name?: string }) => {
    const axisName = String(params?.name || '')
    openExpOrders(
      {
        type: '0',
        currency_type: '1',
        year: axisName,
        test_type: '',
        order_type: String(kind),
      },
      kind === 6 ? '实验订单' : '实验分包订单'
    )
  })
}

function bindPieClick(kind: 6 | 8) {
  const inst = kind === 6 ? pie6Chart : pie8Chart
  if (!inst) return
  inst.off('click')
  inst.on('click', (params: { data?: { company_id?: string | number }; seriesIndex?: number }) => {
    const cid = params?.data?.company_id
    if (cid == null || cid === '') return
    const receiveType = params?.seriesIndex === 1 ? '2' : '1'
    openExpOrders(
      {
        type: receiveType,
        currency_type: '1',
        company_id: String(cid),
        order_type: String(kind),
      },
      kind === 6 ? '实验订单收款' : '实验分包订单收款'
    )
  })
}

function renderBar(kind: 6 | 8, months: string[], values: number[]) {
  const inst = ensureBar(kind)
  if (!inst) return
  inst.setOption({
    color: ['#e74c3c'],
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 16, top: 24, bottom: 36 },
    xAxis: {
      type: 'category',
      data: months.length ? months : Array.from({ length: 12 }, (_, i) => `${i + 1}月`),
      axisLabel: { color: '#606266' },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#606266' },
      splitLine: { lineStyle: { type: 'dashed', color: '#ebeef5' } },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 36,
        data: values.length ? values : Array(12).fill(0),
        itemStyle: { borderRadius: [2, 2, 0, 0] },
      },
    ],
  })
  bindBarClick(kind)
}

/** 对齐 Java option583：人民币 + 美金双柱 */
function renderPersonalDualBar(
  kind: 6 | 8,
  months: string[],
  rmb: number[],
  usd: number[],
  labelPrefix: string
) {
  const inst = ensurePersonal(kind)
  if (!inst) return
  const nameRmb = `${labelPrefix}${kind === 6 ? '实验人民币' : '实验分包人民币'}`
  const nameUsd = `${labelPrefix}${kind === 6 ? '实验美金' : '实验分包美金'}`
  inst.setOption({
    color: ['#e74c3c', '#3498db'],
    legend: { data: [nameRmb, nameUsd], top: 0 },
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 16, top: 40, bottom: 36 },
    xAxis: {
      type: 'category',
      data: months.length ? months : Array.from({ length: 12 }, (_, i) => `${i + 1}月`),
    },
    yAxis: { type: 'value', position: 'right' },
    series: [
      { name: nameRmb, type: 'bar', stack: '人民币', data: rmb.length ? rmb : Array(12).fill(0) },
      { name: nameUsd, type: 'bar', data: usd.length ? usd : Array(12).fill(0) },
    ],
  })
}

/** 对齐 Java option42：左右双饼（已收 / 应收） */
function renderDualPie(kind: 6 | 8, received: PieSlice[], receivable: PieSlice[]) {
  const inst = ensurePie(kind)
  if (!inst) return
  const left = toPieData(received)
  const right = toPieData(receivable)
  inst.setOption({
    title: [
      { subtext: '已收', left: '22.67%', top: '82%', textAlign: 'center', subtextStyle: { fontSize: 13 } },
      { subtext: '应收', left: '75%', top: '82%', textAlign: 'center', subtextStyle: { fontSize: 13 } },
    ],
    tooltip: {
      trigger: 'item',
      formatter: '{b} : {c} ({d}%)',
    },
    series: [
      {
        type: 'pie',
        radius: '55%',
        center: ['25%', '48%'],
        data: left.length ? left : [{ name: '暂无', value: 0 }],
        label: { show: false },
        minAngle: 1,
      },
      {
        type: 'pie',
        radius: '55%',
        center: ['75%', '48%'],
        data: right.length ? right : [{ name: '暂无', value: 0 }],
        label: { show: false },
        minAngle: 1,
      },
    ],
  })
  bindPieClick(kind)
}

type CurrencyPieKey = 'payExp' | 'recvExp' | 'paySub' | 'recvSub'

function ensureCurrencyPie(key: CurrencyPieKey): ECharts | null {
  if (key === 'payExp') {
    if (!payExpRef.value) return null
    if (!payExpChart) payExpChart = echarts.init(payExpRef.value)
    return payExpChart
  }
  if (key === 'recvExp') {
    if (!recvExpRef.value) return null
    if (!recvExpChart) recvExpChart = echarts.init(recvExpRef.value)
    return recvExpChart
  }
  if (key === 'paySub') {
    if (!paySubRef.value) return null
    if (!paySubChart) paySubChart = echarts.init(paySubRef.value)
    return paySubChart
  }
  if (!recvSubRef.value) return null
  if (!recvSubChart) recvSubChart = echarts.init(recvSubRef.value)
  return recvSubChart
}

/** 对齐 Java option105：人民币 / 美金双饼（单侧为 0 时只显示一侧） */
function renderCurrencyDualPie(key: CurrencyPieKey, rmb: PieSlice[], usd: PieSlice[]) {
  const inst = ensureCurrencyPie(key)
  if (!inst) return
  const left = toPieData(rmb)
  const right = toPieData(usd)
  if (!left.length && !right.length) {
    inst.clear()
    return
  }
  if (!left.length) {
    inst.setOption(
      {
        title: [
          { subtext: '美金', left: '50%', top: '85%', textAlign: 'center', subtextStyle: { fontSize: 13 } },
        ],
        tooltip: { trigger: 'item', formatter: '{b} : {c} ({d}%)' },
        series: [
          {
            type: 'pie',
            radius: '55%',
            center: ['50%', '50%'],
            data: right,
            label: { show: false },
            minAngle: 1,
          },
        ],
      },
      true
    )
    return
  }
  if (!right.length) {
    inst.setOption(
      {
        title: [
          {
            subtext: '人民币',
            left: '50%',
            top: '85%',
            textAlign: 'center',
            subtextStyle: { fontSize: 13 },
          },
        ],
        tooltip: { trigger: 'item', formatter: '{b} : {c} ({d}%)' },
        series: [
          {
            type: 'pie',
            radius: '55%',
            center: ['50%', '50%'],
            data: left,
            label: { show: false },
            minAngle: 1,
          },
        ],
      },
      true
    )
    return
  }
  inst.setOption(
    {
      title: [
        {
          subtext: '人民币',
          left: '22.67%',
          top: '80%',
          textAlign: 'center',
          subtextStyle: { fontSize: 13 },
        },
        { subtext: '美金', left: '75%', top: '80%', textAlign: 'center', subtextStyle: { fontSize: 13 } },
      ],
      tooltip: { trigger: 'item', formatter: '{b} : {c} ({d}%)' },
      series: [
        {
          type: 'pie',
          radius: '55%',
          center: ['25%', '50%'],
          data: left,
          label: { show: false },
          minAngle: 1,
        },
        {
          type: 'pie',
          radius: '55%',
          center: ['75%', '50%'],
          data: right,
          label: { show: false },
          minAngle: 1,
        },
      ],
    },
    true
  )
}

async function loadCompany() {
  tableLoading.value = true
  try {
    const res = await fetchCompanySaleByYear({ year: year.value, type: orderStatusType.value })
    if (!isAjaxOk(res)) {
      companyRows.value = []
      return
    }
    const obj = (res.obj || {}) as { companyInfo?: CompanyRow[] }
    companyRows.value = Array.isArray(obj.companyInfo) ? obj.companyInfo : []
  } finally {
    tableLoading.value = false
  }
}

async function loadChart(orderType: 6 | 8) {
  const loadingRef = orderType === 6 ? chart6Loading : chart8Loading
  const y = orderType === 6 ? chartYear6.value : chartYear8.value
  loadingRef.value = true
  try {
    const res = await fetchExpSaleByYear({
      year: y,
      order_type: orderType,
      test_type: '',
    })
    const obj = (isAjaxOk(res) ? res.obj : {}) as {
      expmonth?: string[]
      expSaleAryrmb?: number[]
      expqnxsrmb?: number
    }
    const months = Array.isArray(obj.expmonth) ? obj.expmonth.map(String) : []
    const values = Array.isArray(obj.expSaleAryrmb) ? obj.expSaleAryrmb.map((n) => Number(n || 0)) : []
    if (orderType === 6) total6.value = Number(obj.expqnxsrmb || 0)
    else total8.value = Number(obj.expqnxsrmb || 0)
    await nextTick()
    renderBar(orderType, months, values)
  } finally {
    loadingRef.value = false
  }
}

async function loadPie(orderType: 6 | 8) {
  const loadingRef = orderType === 6 ? pie6Loading : pie8Loading
  const totals = orderType === 6 ? pie6 : pie8
  loadingRef.value = true
  try {
    const res = await fetchExpReceivePie({ order_type: orderType })
    const obj = (isAjaxOk(res) ? res.obj : {}) as {
      expysAryrmball?: PieSlice[]
      expoverdueAryrmball?: PieSlice[]
      ysallamount?: number
      overdueallamount?: number
      totalamount?: number
    }
    totals.received = Number(obj.ysallamount || 0)
    totals.receivable = Number(obj.overdueallamount || 0)
    totals.total = Number(obj.totalamount || totals.received + totals.receivable)
    await nextTick()
    renderDualPie(orderType, obj.expysAryrmball || [], obj.expoverdueAryrmball || [])
  } finally {
    loadingRef.value = false
  }
}

async function loadPersonal(kind: 6 | 8) {
  const loadingRef = kind === 6 ? personal6Loading : personal8Loading
  const totals = kind === 6 ? personal6 : personal8
  const y = kind === 6 ? personalYear6.value : personalYear8.value
  loadingRef.value = true
  try {
    const res =
      kind === 6
        ? await fetchUserAmountByYearSygr({ year: y })
        : await fetchUserAmountByYearSyfbgr({ year: y })
    const obj = (isAjaxOk(res) ? res.obj : {}) as Record<string, unknown>
    if (obj.currentUser) currentUserLabel.value = String(obj.currentUser)
    const months = Array.isArray(obj.xmonths) ? obj.xmonths.map(String) : []
    let rmb: number[] = []
    let usd: number[] = []
    if (kind === 6) {
      rmb = Array.isArray(obj.userSaleAryrmbExp)
        ? (obj.userSaleAryrmbExp as unknown[]).map((n) => Number(n || 0))
        : []
      usd = Array.isArray(obj.userSaleAryusExp)
        ? (obj.userSaleAryusExp as unknown[]).map((n) => Number(n || 0))
        : []
      totals.qnxsrmb = Number(obj.qnxsrmbExp || 0)
      totals.qnxsus = Number(obj.qnxsusExp || 0)
      totals.ddslrmb = Number(obj.ddslrmbExp || 0)
      totals.ddslus = Number(obj.ddslusExp || 0)
    } else {
      rmb = Array.isArray(obj.userSaleAryrmbExpSub)
        ? (obj.userSaleAryrmbExpSub as unknown[]).map((n) => Number(n || 0))
        : []
      usd = Array.isArray(obj.userSaleAryusExpSub)
        ? (obj.userSaleAryusExpSub as unknown[]).map((n) => Number(n || 0))
        : []
      totals.qnxsrmb = Number(obj.qnxsrmbExpSub || 0)
      totals.qnxsus = Number(obj.qnxsusExpSub || 0)
      totals.ddslrmb = Number(obj.ddslrmbExpSub || 0)
      totals.ddslus = Number(obj.ddslusExpSub || 0)
    }
    const label =
      currentUserLabel.value ||
      String(userStore.welcome?.userName || userStore.userName || '')
    await nextTick()
    renderPersonalDualBar(kind, months, rmb, usd, label)
    await nextTick()
    ensurePersonal(kind)?.resize()
  } finally {
    loadingRef.value = false
  }
}

/** 顶部年份只刷新公司表（与 Java #year1 一致） */
async function reloadCompany() {
  await loadCompany()
}

async function reloadAdmin() {
  await Promise.all([loadCompany(), loadChart(6), loadChart(8), loadPie(6), loadPie(8)])
}

async function loadPersonalPies() {
  personalPieLoading.value = true
  try {
    const res = await fetchUserOverduePie()
    const obj = (isAjaxOk(res) ? res.obj : {}) as Record<string, unknown>
    personalPie.payExp.rmb = Number(obj.overduermbPaysy || 0)
    personalPie.payExp.us = Number(obj.overdueusPaysy || 0)
    personalPie.recvExp.rmb = Number(obj.overduermbsy || 0)
    personalPie.recvExp.us = Number(obj.overdueussy || 0)
    personalPie.paySub.rmb = Number(obj.overduermbPaysyfb || 0)
    personalPie.paySub.us = Number(obj.overdueusPaysyfb || 0)
    personalPie.recvSub.rmb = Number(obj.overduermbsyfb || 0)
    personalPie.recvSub.us = Number(obj.overdueussyfb || 0)
    await nextTick()
    renderCurrencyDualPie(
      'payExp',
      (obj.overdueAryrmbPaysy as PieSlice[]) || [],
      (obj.overdueAryusPaysy as PieSlice[]) || []
    )
    renderCurrencyDualPie(
      'recvExp',
      (obj.overdueAryrmbsy as PieSlice[]) || [],
      (obj.overdueAryussy as PieSlice[]) || []
    )
    renderCurrencyDualPie(
      'paySub',
      (obj.overdueAryrmbPaysyfb as PieSlice[]) || [],
      (obj.overdueAryusPaysyfb as PieSlice[]) || []
    )
    renderCurrencyDualPie(
      'recvSub',
      (obj.overdueAryrmbsyfb as PieSlice[]) || [],
      (obj.overdueAryussyfb as PieSlice[]) || []
    )
    await nextTick()
    payExpChart?.resize()
    recvExpChart?.resize()
    paySubChart?.resize()
    recvSubChart?.resize()
  } finally {
    personalPieLoading.value = false
  }
}

async function reloadPersonal() {
  await Promise.all([loadPersonal(6), loadPersonal(8), loadPersonalPies()])
}

function onResize() {
  chart6?.resize()
  chart8?.resize()
  pie6Chart?.resize()
  pie8Chart?.resize()
  personal6Chart?.resize()
  personal8Chart?.resize()
  payExpChart?.resize()
  recvExpChart?.resize()
  paySubChart?.resize()
  recvSubChart?.resize()
}

onMounted(async () => {
  await nextTick()
  if (isAdminDigital.value) await reloadAdmin()
  else await reloadPersonal()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart6?.dispose()
  chart8?.dispose()
  pie6Chart?.dispose()
  pie8Chart?.dispose()
  personal6Chart?.dispose()
  personal8Chart?.dispose()
  payExpChart?.dispose()
  recvExpChart?.dispose()
  paySubChart?.dispose()
  recvSubChart?.dispose()
  chart6 = null
  chart8 = null
  pie6Chart = null
  pie8Chart = null
  personal6Chart = null
  personal8Chart = null
  payExpChart = null
  recvExpChart = null
  paySubChart = null
  recvSubChart = null
})
</script>

<style scoped>
.filter-form {
  margin-bottom: 12px;
}
.company-table {
  margin-bottom: 8px;
}
.charts-row {
  margin-top: 16px;
}
.chart-panel {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px 12px 8px;
  min-height: 360px;
}
.pie-panel {
  min-height: 400px;
}
.chart-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.chart-head h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.chart-box {
  width: 100%;
  height: 280px;
}
.pie-box {
  height: 320px;
}
.chart-total {
  margin: 8px 0 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}
.company-table :deep(.is-total-row) {
  font-weight: 600;
  background: #fafafa;
}
</style>
