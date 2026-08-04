<template>
  <div class="dashboard">
    <section class="welcome-banner">
      <div>
        <p class="welcome-banner__hello">{{ greeting }}，{{ displayName }}</p>
        <h2 class="welcome-banner__title">欢迎回来</h2>
        <p class="welcome-banner__hint">{{ bannerHint }}</p>
      </div>
      <div class="welcome-banner__meta">
        <span v-if="roleName" class="welcome-banner__role">{{ roleName }}</span>
        <span>{{ todayLabel }}</span>
      </div>
    </section>

    <!-- 销售主管：待审核 KPI（对齐图一） -->
    <div v-if="pendingKpis.length" class="kpi-row">
      <button
        v-for="item in pendingKpis"
        :key="item.key"
        type="button"
        class="kpi-card"
        @click="item.onClick"
      >
        <strong class="kpi-card__num">{{ item.count }}</strong>
        <span class="kpi-card__label">{{ item.label }}</span>
      </button>
    </div>

    <!-- 快捷入口 -->
    <div v-if="actionCards.length" class="action-row" :style="actionRowStyle">
      <button
        v-for="card in actionCards"
        :key="card.key"
        type="button"
        class="action-card"
        :class="card.tone"
        @click="card.onClick"
      >
        <span class="action-card__icon">{{ card.icon }}</span>
        <span class="action-card__body">
          <strong>
            <template v-if="card.count != null">{{ card.count }} </template>{{ card.title }}
          </strong>
          <em v-if="card.desc">{{ card.desc }}</em>
        </span>
      </button>
    </div>

    <!-- 未开始 / 进行中 / 通过或超时 -->
    <div v-if="opsKpis.length" class="kpi-row kpi-row--ops">
      <button
        v-for="item in opsKpis"
        :key="item.key"
        type="button"
        class="kpi-card kpi-card--ops"
        :class="item.tone"
        @click="item.onClick"
      >
        <strong class="kpi-card__num">{{ item.count }}</strong>
        <span class="kpi-card__label">{{ item.label }}</span>
      </button>
    </div>

    <!-- 销售人员：测试数量(年) + 测试人员测试数量(月) —— 对齐 Java 图一 -->
    <div v-if="showSaleTestCharts" class="main-row main-row--sale">
      <el-card class="panel-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">测试数量(年)</span>
            <span class="panel-head__sub">{{ testYearChart.year || '' }}</span>
          </div>
        </template>
        <div ref="testYearChartRef" class="chart-box" />
      </el-card>
      <el-card class="panel-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">测试人员测试数量(月)</span>
            <span class="panel-head__sub">{{ testerMonthChart.month || '' }}</span>
          </div>
        </template>
        <div ref="testerMonthChartRef" class="chart-box" />
      </el-card>
    </div>

    <el-alert
      v-if="!pendingKpis.length && !actionCards.length && !opsKpis.length && welcomeUserType !== 1"
      class="role-hint"
      type="info"
      :closable="false"
      show-icon
      title="当前账号类型在欢迎页无快捷入口，请从左侧菜单进入业务模块"
    />

    <!-- 主内容：资产饼图 + 销售额/测试数量/管理员交易 + 日志 -->
    <div v-if="showMainPanels" class="main-row" :class="mainRowClass">
      <el-card v-if="showAssets" class="panel-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">我的实际可用总资产</span>
          </div>
        </template>
        <div ref="assetChartRef" class="chart-box chart-box--asset" />
        <p class="chart-foot">
          我的实际可用总资产：人民币 {{ accountRMB }} 元 ；美元 {{ accountUS }} 元
        </p>
      </el-card>

      <el-card v-if="showSaleChart" class="panel-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">我的实际销售额</span>
            <span class="panel-head__sub">{{ saleYear }} 年</span>
          </div>
        </template>
        <div ref="saleChartRef" class="chart-box" />
        <p class="chart-foot">
          {{ saleYear }}全年销售总额：人民币 {{ qnxsrmb }} | 美元 {{ qnxsus }}
          <template v-if="Number(grml) > 0">
            | 毛利总额:{{ grml }} | 毛利率:{{ grmlRate }} %
          </template>
          <br />
          销售的订单数量：人民币订单总数:{{ ddslrmb }}，美元订单总数:{{ ddslus }}
        </p>
      </el-card>

      <el-card v-if="showTestChart" class="panel-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">我的测试数量</span>
          </div>
        </template>
        <div ref="testChartRef" class="chart-box" />
      </el-card>

      <el-card v-if="showAdminChart" class="panel-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">最近 6 个月交易记录</span>
            <span class="panel-head__sub">销售订单金额（万元）</span>
          </div>
        </template>
        <div ref="adminChartRef" class="chart-box" />
      </el-card>

      <el-card v-if="showLogs" class="panel-card log-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">平台系统操作记录</span>
            <el-button link type="primary" @click="goMoreLogs">更多</el-button>
          </div>
        </template>
        <ul v-if="logs.length" class="log-list">
          <li v-for="(item, idx) in logs" :key="String(item.id ?? idx)">
            <span class="log-dot" />
            <div class="log-body">
              <div class="log-meta">
                <time class="log-time">{{ item.addTime || '-' }}</time>
                <span v-if="item.userName" class="log-user">{{ item.userName }}</span>
              </div>
              <p class="log-content">{{ item.content || '-' }}</p>
            </div>
          </li>
        </ul>
        <el-empty v-else description="暂无操作记录" :image-size="72" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { fetchAdminWelcome } from '@admin/api/auth'
import { useUserStore } from '@admin/stores/user'
import type { WelcomeLogItem } from '@admin/types/admin'
import { isAjaxOk } from '@admin/utils/request'

type Card = {
  key: string
  title: string
  desc?: string
  icon: string
  tone: string
  count?: number
  onClick: () => void
}

type Kpi = {
  key: string
  label: string
  count: number
  tone?: string
  onClick: () => void
}

const router = useRouter()
const userStore = useUserStore()

const assetChartRef = ref<HTMLDivElement>()
const saleChartRef = ref<HTMLDivElement>()
const testChartRef = ref<HTMLDivElement>()
const adminChartRef = ref<HTMLDivElement>()
const testYearChartRef = ref<HTMLDivElement>()
const testerMonthChartRef = ref<HTMLDivElement>()
let assetChart: ECharts | null = null
let saleChart: ECharts | null = null
let testChart: ECharts | null = null
let adminChart: ECharts | null = null
let testYearChartInst: ECharts | null = null
let testerMonthChartInst: ECharts | null = null

const welcome = computed(() => userStore.welcome)
const welcomeUserType = computed(() =>
  Number(welcome.value?.userType ?? userStore.userType ?? 0),
)
const welcomeUserType2 = computed(() => Number(welcome.value?.userType2 ?? 0))
const roleName = computed(() => String(welcome.value?.roleName || userStore.roleName || ''))
const currentUser = computed(
  () => welcome.value?.currentUser || welcome.value?.loginName || userStore.loginName || '',
)

const logs = computed<WelcomeLogItem[]>(() => welcome.value?.newlogs || [])
const showLogs = computed(() => welcomeUserType.value === 1)
const showAssets = computed(() => {
  if (welcome.value?.showAssets != null) return Boolean(welcome.value.showAssets)
  return [0, 2, 3, 4, 6, 7, 14].includes(welcomeUserType.value)
})
const showSaleChart = computed(() => welcomeUserType2.value === 2)
const showTestChart = computed(() => welcomeUserType2.value === 3)
const showAdminChart = computed(() => welcomeUserType2.value === 1)
const showMainPanels = computed(
  () => showAssets.value || showSaleChart.value || showTestChart.value || showAdminChart.value || showLogs.value,
)
const mainRowClass = computed(() => {
  if (showAdminChart.value && showLogs.value) return 'main-row--admin'
  if (showSaleChart.value && showAssets.value) return 'main-row--sale'
  if (showTestChart.value && showAssets.value) return 'main-row--sale'
  return 'main-row--single'
})

const accountRMB = computed(() => String(welcome.value?.accountRMB ?? '0.00'))
const accountUS = computed(() => String(welcome.value?.accountUS ?? '0.00'))
const saleYear = computed(() => String(welcome.value?.saleYear || new Date().getFullYear()))
const qnxsrmb = computed(() => String(welcome.value?.qnxsrmb ?? '0.00'))
const qnxsus = computed(() => String(welcome.value?.qnxsus ?? '0.00'))
const ddslrmb = computed(() => Number(welcome.value?.ddslrmb || 0))
const ddslus = computed(() => Number(welcome.value?.ddslus || 0))
const grml = computed(() => String(welcome.value?.grmlzhbigdecimal ?? '0.00'))
const grmlRate = computed(() => String(welcome.value?.grmlllbigdecimal ?? '0.00'))

const pending = computed(() => welcome.value?.pendingCounts || {})
const ops = computed(() => welcome.value?.opsCounts || {})

const pendingKpis = computed<Kpi[]>(() => {
  if (welcomeUserType.value !== 3) return []
  return [
    {
      key: 'exp',
      label: '待审核实验订单',
      count: Number(pending.value.expOrder || 0),
      onClick: () => goOrders({ orderType: '6', orderStatus: '20' }),
    },
    {
      key: 'self',
      label: '待审核自制子订单',
      count: Number(pending.value.selfChildOrder || 0),
      onClick: () => goOrders({ orderType: '10', orderStatus: '20' }),
    },
    {
      key: 'sub',
      label: '待审核外协分包订单',
      count: Number(pending.value.subcontractOrder || 0),
      onClick: () =>
        router.push({ name: 'ExperimentSubcontractOrders', query: { orderStatus: '20' } }),
    },
    {
      key: 'sub-child',
      label: '待审核外协子订单',
      count: Number(pending.value.subcontractSubOrder || 0),
      onClick: () =>
        router.push({ name: 'ExperimentSubcontractSubOrders', query: { orderStatus: '20' } }),
    },
    {
      key: 'material',
      label: '待审核物资分包子订单',
      count: Number(pending.value.materialSubOrder || 0),
      onClick: () =>
        router.push({ name: 'ExperimentSubcontractSubOrders', query: { orderStatus: '20' } }),
    },
  ]
})

const opsMode = computed(() => String(ops.value.opsMode || ''))
const showSaleTestCharts = computed(() => Boolean(welcome.value?.showSaleTestCharts))
const testYearChart = computed(() => welcome.value?.testYearChart || {})
const testerMonthChart = computed(() => welcome.value?.testerMonthChart || {})

const opsKpis = computed<Kpi[]>(() => {
  if (!welcome.value?.showOpsCounts && welcomeUserType.value !== 3 && welcomeUserType.value !== 4) {
    return []
  }
  if (!(welcome.value?.showOpsCounts || welcomeUserType.value === 3 || welcomeUserType2.value === 3)) {
    return []
  }
  const mode = opsMode.value
  // 销售人员 / 测试人员：未开始测试、进行中、测试通过（对齐 Java 图一）
  if (mode === 'salesperson' || mode === 'tester' || (welcomeUserType.value === 4 && welcomeUserType2.value === 2)) {
    return [
      {
        key: 'nostart',
        label: '未开始测试订单',
        count: Number(ops.value.notStarted || 0),
        tone: 'kpi-card--warn',
        onClick: () => router.push({ name: 'DigitalStats' }),
      },
      {
        key: 'progress',
        label: '进行中测试订单',
        count: Number(ops.value.inProgress || 0),
        tone: 'kpi-card--info',
        onClick: () => router.push({ name: 'DigitalStats' }),
      },
      {
        key: 'passed',
        label: '测试通过订单',
        count: Number(ops.value.passed || 0),
        tone: 'kpi-card--ok',
        onClick: () => router.push({ name: 'DigitalStats' }),
      },
    ]
  }
  // 销售主管等：未开始实验、进行中、超时
  return [
    {
      key: 'nostart',
      label: '未开始实验订单',
      count: Number(ops.value.notStarted || 0),
      tone: 'kpi-card--warn',
      onClick: () => router.push({ name: 'DigitalStats' }),
    },
    {
      key: 'progress',
      label: '进行中测试订单',
      count: Number(ops.value.inProgress || 0),
      tone: 'kpi-card--info',
      onClick: () => router.push({ name: 'DigitalStats' }),
    },
    {
      key: 'timeout',
      label: '测试超时订单',
      count: Number(ops.value.timeout || 0),
      tone: 'kpi-card--danger',
      onClick: () => router.push({ name: 'DigitalStats' }),
    },
  ]
})

const actionCards = computed<Card[]>(() => {
  const t = welcomeUserType.value
  const cards: Card[] = []
  if ([1, 2, 3, 4, 7, 14].includes(t)) {
    cards.push({
      key: 'fund',
      title: '资金账户',
      desc: '账户余额 · 收支明细',
      icon: '¥',
      tone: 'action-card--fund',
      onClick: () => router.push({ name: 'FundAccount' }),
    })
    cards.push({
      key: 'digital',
      title: '数字化中心',
      desc: '运营看板 · 绩效统计',
      icon: '◈',
      tone: 'action-card--digital',
      onClick: () => router.push({ name: 'FundDigitalCenter' }),
    })
  }
  if (t === 2) {
    cards.push({
      key: 'company-pay',
      title: '公司资金支出',
      icon: '企',
      tone: 'action-card--company',
      onClick: () => router.push({ name: 'FundCompanyPay' }),
    })
    cards.push({
      key: 'personal-pay',
      title: '个人资金支出',
      icon: '人',
      tone: 'action-card--personal',
      onClick: () => router.push({ name: 'FundPersonalPay' }),
    })
  }
  if ([3, 4, 5, 7].includes(t)) {
    cards.push({
      key: 'create',
      title: '新增实验订单',
      desc: '创建实验销售订单',
      icon: '+',
      tone: 'action-card--order',
      onClick: () => router.push({ name: 'ExperimentOrders' }),
    })
  }
  return cards
})

const actionRowStyle = computed(() => {
  const n = actionCards.value.length
  if (n <= 1) return { gridTemplateColumns: '1fr' }
  if (n === 3) return { gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }
  return { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }
})

const displayName = computed(() => userStore.userName || userStore.loginName || '管理员')
const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '上午好'
  if (h < 18) return '下午好'
  return '晚上好'
})
const todayLabel = computed(() => {
  const d = new Date()
  const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 星期${week}`
})
const bannerHint = computed(() => {
  const t = welcomeUserType.value
  if (t === 1) return '查看近期交易与系统动态，或从下方快捷入口进入常用模块'
  if (t === 3) return '处理待审核订单，查看个人业绩与资产'
  if (welcomeUserType2.value === 3) return '查看测试数量与账户资产'
  if ([2, 3, 4, 7, 14].includes(t)) return '查看个人业绩与资产，或从下方快捷入口进入常用模块'
  return '从下方快捷入口或左侧菜单进入业务模块'
})

function goOrders(query: Record<string, string>) {
  if (query.orderType === '10') {
    router.push({ name: 'ExperimentSubOrders', query })
    return
  }
  router.push({ name: 'ExperimentOrders', query })
}

function goMoreLogs() {
  router.push({ name: 'SystemOpsLogs' })
}

function renderAssetPie() {
  if (!assetChartRef.value || !showAssets.value) return
  if (!assetChart) assetChart = echarts.init(assetChartRef.value)
  const rmb = Number(accountRMB.value) || 0
  const usd = Number(accountUS.value) || 0
  assetChart.setOption({
    color: ['#e11d48', '#374151'],
    tooltip: { trigger: 'item', formatter: '{b} : {c} ({d}%)' },
    series: [
      {
        name: '可用资产',
        type: 'pie',
        radius: ['35%', '62%'],
        center: ['50%', '48%'],
        data: [
          { name: '人民币', value: rmb },
          { name: '美金', value: usd },
        ],
        label: { formatter: '{b}\n{c}' },
      },
    ],
  })
}

function renderSaleBars() {
  if (!saleChartRef.value || !showSaleChart.value) return
  if (!saleChart) saleChart = echarts.init(saleChartRef.value)
  const months = welcome.value?.xmonths || []
  const rmb = (welcome.value?.userSaleAryrmb || []).map((v) => Number(v) || 0)
  const usd = (welcome.value?.userSaleAryus || []).map((v) => Number(v) || 0)
  const name = currentUser.value || '我'
  saleChart.setOption({
    color: ['#e11d48', '#374151'],
    legend: {
      data: [`${name}销售人民币`, `${name}销售美金`],
      top: 0,
    },
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 40, bottom: 36 },
    xAxis: {
      type: 'category',
      data: months.length ? months : ['暂无'],
      axisLabel: { rotate: months.length > 8 ? 30 : 0, color: '#6b7280' },
    },
    yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } } },
    series: [
      {
        name: `${name}销售人民币`,
        type: 'bar',
        stack: 'rmb',
        data: rmb.length ? rmb : [0],
      },
      {
        name: `${name}销售美金`,
        type: 'bar',
        data: usd.length ? usd : [0],
      },
    ],
  })
}

function renderTestBars() {
  if (!testChartRef.value || !showTestChart.value) return
  if (!testChart) testChart = echarts.init(testChartRef.value)
  const months = welcome.value?.expmonth || []
  const vals = (welcome.value?.expTestAry || []).map((v) => Number(v) || 0)
  testChart.setOption({
    color: ['#ea580c'],
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 24, bottom: 36 },
    xAxis: { type: 'category', data: months.length ? months : ['暂无'] },
    yAxis: { type: 'value' },
    series: [{ name: '测试数量', type: 'bar', data: vals.length ? vals : [0] }],
  })
}

function renderAdminLine() {
  if (!adminChartRef.value || !showAdminChart.value) return
  if (!adminChart) adminChart = echarts.init(adminChartRef.value)
  const x = welcome.value?.xdate || []
  const y = (welcome.value?.ydata || []).map((v) => Number(v) || 0)
  adminChart.setOption({
    color: ['#ea580c'],
    tooltip: { trigger: 'axis' },
    grid: { left: 52, right: 20, top: 32, bottom: 36 },
    xAxis: { type: 'category', boundaryGap: false, data: x.length ? x : ['暂无'] },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}' } },
    series: [
      {
        name: '交易金额',
        type: 'line',
        smooth: true,
        areaStyle: { color: 'rgba(234,88,12,0.15)' },
        data: y.length ? y : [0],
      },
    ],
  })
}

function renderSaleTestYear() {
  if (!testYearChartRef.value || !showSaleTestCharts.value) return
  if (!testYearChartInst) testYearChartInst = echarts.init(testYearChartRef.value)
  const months = testYearChart.value.months || []
  const vals = (testYearChart.value.values || []).map((v) => Number(v) || 0)
  testYearChartInst.setOption({
    color: ['#e11d48'],
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 20, top: 28, bottom: 36 },
    xAxis: {
      type: 'category',
      data: months.length ? months : ['暂无'],
      axisLabel: { rotate: months.length > 8 ? 30 : 0, color: '#6b7280' },
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        name: '测试数量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: { color: 'rgba(225,29,72,0.12)' },
        data: vals.length ? vals : [0],
      },
    ],
  })
}

function renderTesterMonth() {
  if (!testerMonthChartRef.value || !showSaleTestCharts.value) return
  if (!testerMonthChartInst) testerMonthChartInst = echarts.init(testerMonthChartRef.value)
  const names = testerMonthChart.value.names || []
  const vals = (testerMonthChart.value.values || []).map((v) => Number(v) || 0)
  testerMonthChartInst.setOption({
    color: ['#374151'],
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 20, top: 28, bottom: names.length > 6 ? 64 : 36 },
    xAxis: {
      type: 'category',
      data: names.length ? names : ['暂无'],
      axisLabel: { rotate: names.length > 5 ? 35 : 0, color: '#6b7280', interval: 0 },
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        name: '测试数量',
        type: 'bar',
        barMaxWidth: 36,
        data: vals.length ? vals : [0],
      },
    ],
  })
}

function renderAllCharts() {
  renderAssetPie()
  renderSaleBars()
  renderTestBars()
  renderAdminLine()
  renderSaleTestYear()
  renderTesterMonth()
}

function onResize() {
  assetChart?.resize()
  saleChart?.resize()
  testChart?.resize()
  adminChart?.resize()
  testYearChartInst?.resize()
  testerMonthChartInst?.resize()
}

async function ensureWelcomeData() {
  const res = await fetchAdminWelcome({ silentError: true })
  if (isAjaxOk(res) && res.obj) {
    userStore.welcome = { ...(userStore.welcome || {}), ...(res.obj as object) }
  }
}

watch(
  () => [
    welcome.value?.accountRMB,
    welcome.value?.userSaleAryrmb,
    welcome.value?.expTestAry,
    welcome.value?.ydata,
    welcome.value?.testYearChart,
    welcome.value?.testerMonthChart,
    showAssets.value,
    showSaleChart.value,
    showTestChart.value,
    showAdminChart.value,
    showSaleTestCharts.value,
  ],
  async () => {
    await nextTick()
    renderAllCharts()
  },
)

onMounted(async () => {
  await ensureWelcomeData()
  await nextTick()
  renderAllCharts()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  assetChart?.dispose()
  saleChart?.dispose()
  testChart?.dispose()
  adminChart?.dispose()
  testYearChartInst?.dispose()
  testerMonthChartInst?.dispose()
  assetChart = saleChart = testChart = adminChart = null
  testYearChartInst = testerMonthChartInst = null
})
</script>

<style scoped lang="scss">
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-banner {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border-radius: 12px;
  background:
    linear-gradient(135deg, rgba(249, 115, 22, 0.12), rgba(249, 115, 22, 0.02) 42%, #fff 70%),
    #fff;
  border: 1px solid #f3e8d8;
}

.welcome-banner__hello {
  margin: 0;
  font-size: 13px;
  color: #9a3412;
}

.welcome-banner__title {
  margin: 4px 0 0;
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
}

.welcome-banner__hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.welcome-banner__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  font-size: 13px;
  color: #9ca3af;
}

.welcome-banner__role {
  font-size: 12px;
  color: #ea580c;
  background: rgba(249, 115, 22, 0.08);
  padding: 2px 10px;
  border-radius: 999px;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.kpi-row--ops {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.kpi-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 92px;
  padding: 14px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  transition: box-shadow 0.15s, border-color 0.15s;

  &:hover {
    border-color: #fdba74;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
  }
}

.kpi-card__num {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.kpi-card__label {
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

.kpi-card--warn .kpi-card__num {
  color: #d97706;
}

.kpi-card--info .kpi-card__num {
  color: #2563eb;
}

.kpi-card--danger .kpi-card__num {
  color: #dc2626;
}

.kpi-card--ok .kpi-card__num {
  color: #16a34a;
}

.action-row {
  display: grid;
  gap: 12px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 84px;
  padding: 16px 18px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  text-align: left;
  cursor: pointer;

  &:hover {
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
  }
}

.action-card__icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-weight: 700;
  background: rgba(249, 115, 22, 0.12);
  color: #ea580c;
}

.action-card--digital .action-card__icon {
  background: rgba(20, 184, 166, 0.12);
  color: #0f766e;
}

.action-card--order .action-card__icon {
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}

.action-card--company .action-card__icon {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}

.action-card--personal .action-card__icon {
  background: rgba(139, 92, 246, 0.12);
  color: #7c3aed;
}

.action-card__body {
  display: flex;
  flex-direction: column;
  gap: 4px;

  strong {
    font-size: 15px;
    color: #1f2937;
  }

  em {
    font-style: normal;
    font-size: 12px;
    color: #9ca3af;
  }
}

.role-hint {
  border-radius: 12px;
}

.main-row {
  display: grid;
  gap: 16px;
  align-items: stretch;

  &--sale {
    grid-template-columns: minmax(280px, 0.9fr) minmax(0, 1.3fr);
  }

  &--admin {
    grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.9fr);
  }

  &--single {
    grid-template-columns: 1fr;
  }
}

.panel-card {
  border-radius: 12px;
  border: 1px solid #e5e7eb;

  :deep(.el-card__header) {
    padding: 14px 18px;
    border-bottom: 1px solid #f3f4f6;
  }

  :deep(.el-card__body) {
    padding: 12px 16px 16px;
  }
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-head__title {
  font-size: 15px;
  font-weight: 650;
  color: #1f2937;
}

.panel-head__sub {
  font-size: 12px;
  color: #9ca3af;
}

.chart-box {
  width: 100%;
  height: 320px;
}

.chart-box--asset {
  height: 280px;
}

.chart-foot {
  margin: 8px 4px 0;
  font-size: 12px;
  line-height: 1.6;
  color: #6b7280;
}

.log-list {
  margin: 0;
  padding: 4px 0;
  list-style: none;
  max-height: 360px;
  overflow: auto;
}

.log-list li {
  display: flex;
  gap: 12px;
  padding: 12px 4px;
  border-bottom: 1px solid #f3f4f6;
}

.log-dot {
  width: 8px;
  height: 8px;
  margin-top: 7px;
  border-radius: 50%;
  background: #fdba74;
  flex-shrink: 0;
}

.log-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.log-time {
  font-size: 12px;
  color: #9ca3af;
}

.log-user {
  font-size: 12px;
  color: #ea580c;
  background: rgba(249, 115, 22, 0.08);
  padding: 1px 8px;
  border-radius: 999px;
}

.log-content {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
}

@media (max-width: 1100px) {
  .kpi-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .kpi-row--ops,
  .main-row--sale,
  .main-row--admin,
  .action-row {
    grid-template-columns: 1fr;
  }
}
</style>
