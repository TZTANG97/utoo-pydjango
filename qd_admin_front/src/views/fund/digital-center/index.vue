<template>
  <admin-page-card title="数字化管理运营中心">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="年份选择">
        <el-select v-model="year" clearable placeholder="全部" style="width: 140px">
          <el-option label="全部" value="" />
          <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="String(y)" />
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
          <el-table-column prop="rmb" label="销售(RMB)" width="130" align="right">
            <template #default="{ row }">{{ formatMoney(row.rmb) }}</template>
          </el-table-column>
          <el-table-column prop="us" label="销售(US)" width="120" align="right">
            <template #default="{ row }">{{ formatMoney(row.us) }}</template>
          </el-table-column>
          <el-table-column prop="syrmb" label="实验(RMB)" width="130" align="right">
            <template #default="{ row }">{{ formatMoney(row.syrmb) }}</template>
          </el-table-column>
          <el-table-column prop="rentrmb" label="租赁(RMB)" width="130" align="right">
            <template #default="{ row }">{{ formatMoney(row.rentrmb) }}</template>
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
  </admin-page-card>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  fetchCompanySaleByYear,
  fetchExpReceivePie,
  fetchExpSaleByYear,
  isAjaxOk,
} from '@admin/api/fund'

type CompanyRow = {
  index?: number
  id?: number | string
  company_name?: string
  rmb?: number
  us?: number
  syrmb?: number
  rentrmb?: number
  isTotal?: boolean
}

type PieSlice = { name?: string; value?: number; company_name?: string; total?: number }

const tableLoading = ref(false)
const chart6Loading = ref(false)
const chart8Loading = ref(false)
const pie6Loading = ref(false)
const pie8Loading = ref(false)

const nowYear = new Date().getFullYear()
/** 对齐 Java：自 2019 年起 */
const yearOptions = Array.from({ length: nowYear - 2019 + 1 }, (_, i) => nowYear - i)

const year = ref('')
const chartYear6 = ref('')
const chartYear8 = ref('')
const companyRows = ref<CompanyRow[]>([])
const total6 = ref(0)
const total8 = ref(0)
const pie6 = reactive({ received: 0, receivable: 0, total: 0 })
const pie8 = reactive({ received: 0, receivable: 0, total: 0 })

const chart6Ref = ref<HTMLDivElement | null>(null)
const chart8Ref = ref<HTMLDivElement | null>(null)
const pie6Ref = ref<HTMLDivElement | null>(null)
const pie8Ref = ref<HTMLDivElement | null>(null)
let chart6: ECharts | null = null
let chart8: ECharts | null = null
let pie6Chart: ECharts | null = null
let pie8Chart: ECharts | null = null

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

function toPieData(list: PieSlice[] | undefined) {
  if (!Array.isArray(list)) return []
  return list
    .map((item) => ({
      name: String(item.name || item.company_name || ''),
      value: Number(item.value ?? item.total ?? 0),
    }))
    .filter((item) => item.value !== 0)
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
}

async function loadCompany() {
  tableLoading.value = true
  try {
    const res = await fetchCompanySaleByYear({ year: year.value, type: '1' })
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

/** 顶部年份只刷新公司表（与 Java #year1 一致） */
async function reloadCompany() {
  await loadCompany()
}

async function reloadAll() {
  await Promise.all([loadCompany(), loadChart(6), loadChart(8), loadPie(6), loadPie(8)])
}

function onResize() {
  chart6?.resize()
  chart8?.resize()
  pie6Chart?.resize()
  pie8Chart?.resize()
}

onMounted(async () => {
  await nextTick()
  await reloadAll()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart6?.dispose()
  chart8?.dispose()
  pie6Chart?.dispose()
  pie8Chart?.dispose()
  chart6 = null
  chart8 = null
  pie6Chart = null
  pie8Chart = null
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
