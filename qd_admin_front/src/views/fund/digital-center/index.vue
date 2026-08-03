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
          <el-table-column prop="company_name" label="公司名称" min-width="280" show-overflow-tooltip />
          <el-table-column prop="syrmb" label="实验(RMB)" width="180" align="right">
            <template #default="{ row }">
              {{ formatMoney(row.syrmb) }}
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
  </admin-page-card>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  fetchCompanySaleByYear,
  fetchExpSaleByYear,
  isAjaxOk,
} from '@admin/api/fund'

type CompanyRow = {
  index?: number
  id?: number | string
  company_name?: string
  syrmb?: number
  isTotal?: boolean
}

const tableLoading = ref(false)
const chart6Loading = ref(false)
const chart8Loading = ref(false)

const nowYear = new Date().getFullYear()
/** 对齐 Java：自 2019 年起 */
const yearOptions = Array.from({ length: nowYear - 2019 + 1 }, (_, i) => nowYear - i)

const year = ref('')
const chartYear6 = ref('')
const chartYear8 = ref('')
const companyRows = ref<CompanyRow[]>([])
const total6 = ref(0)
const total8 = ref(0)

const chart6Ref = ref<HTMLDivElement | null>(null)
const chart8Ref = ref<HTMLDivElement | null>(null)
let chart6: ECharts | null = null
let chart8: ECharts | null = null

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

function ensureChart(kind: 6 | 8) {
  if (kind === 6) {
    if (!chart6Ref.value) return null
    if (!chart6) chart6 = echarts.init(chart6Ref.value)
    return chart6
  }
  if (!chart8Ref.value) return null
  if (!chart8) chart8 = echarts.init(chart8Ref.value)
  return chart8
}

function renderBar(kind: 6 | 8, months: string[], values: number[]) {
  const inst = ensureChart(kind)
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

/** 顶部年份只刷新公司表（与 Java #year1 一致）；图表年份各自独立。 */
async function reloadCompany() {
  await loadCompany()
}

async function reloadAll() {
  await Promise.all([loadCompany(), loadChart(6), loadChart(8)])
}

function onResize() {
  chart6?.resize()
  chart8?.resize()
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
  chart6 = null
  chart8 = null
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
.chart-total {
  margin: 8px 0 0;
  font-size: 13px;
  color: #606266;
}
.company-table :deep(.is-total-row) {
  font-weight: 600;
  background: #fafafa;
}
</style>
