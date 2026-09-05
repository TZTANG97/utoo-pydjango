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

    <!-- C类等：入口+运营卡同一流式区域（对齐 Java welcome 混排） -->
    <div v-if="isLiteSalesRole && (actionCards.length || opsKpis.length)" class="java-home-strip">
      <button
        v-for="card in actionCards"
        :key="card.key"
        type="button"
        class="java-home-strip__action"
        @click="card.onClick"
      >
        {{ card.title }}
      </button>
      <button
        v-for="item in opsKpis"
        :key="item.key"
        type="button"
        class="java-home-strip__kpi"
        :class="item.tone"
        @click="item.onClick"
      >
        <strong>{{ item.count }}</strong>
        <span>{{ item.label }}</span>
      </button>
    </div>

    <!-- 其它角色：快捷入口 -->
    <div
      v-else-if="actionCards.length"
      class="action-row"
      :style="actionRowStyle"
    >
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

    <!-- 其它角色：未开始 / 进行中 / 通过或超时 -->
    <div v-if="!isLiteSalesRole && opsKpis.length" class="kpi-row kpi-row--ops">
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

    <!-- 主内容：测试数量(左) → 资产 → 销售额 / 管理员交易 + 日志（对齐 Java welcome.html） -->
    <div v-if="showMainPanels" class="main-row" :class="mainRowClass">
      <el-card v-if="showTestChart" class="panel-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">我的测试数量</span>
            <el-date-picker
              v-model="testYearPicked"
              type="year"
              placeholder="年份选择"
              value-format="YYYY"
              class="panel-head__year"
              :clearable="false"
              @change="onTestYearChange"
            />
          </div>
        </template>
        <div ref="testChartRef" class="chart-box" />
      </el-card>

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
            <span class="panel-head__title">我的实验销售额</span>
            <div class="panel-head__tools">
              <el-select v-model="saleOrderType" style="width: 120px" @change="reloadSaleChart">
                <el-option label="全部" value="" />
                <el-option label="实验" value="1" />
                <el-option label="实验分包" value="2" />
              </el-select>
              <el-date-picker
                v-model="saleYearPicked"
                type="year"
                placeholder="年份"
                value-format="YYYY"
                class="panel-head__year"
                :clearable="false"
                @change="reloadSaleChart"
              />
            </div>
          </div>
        </template>
        <div ref="saleChartRef" class="chart-box" />
        <p class="chart-foot">
          {{ saleYear }}全年销售总额：人民币 {{ qnxsrmb }} | 美元 {{ qnxsus }}
          <template v-if="Number(grml) !== 0">
            | 毛利总额:{{ grml }} | 毛利率:{{ grmlRate }} %
          </template>
          <br />
          销售的订单数量：人民币订单总数:{{ ddslrmb }}，美元订单总数:{{ ddslus }}
        </p>
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
/** Java userType3：2=销售额图；C类为 0 */
const welcomeUserType3 = computed(() => Number(welcome.value?.userType3 ?? 0))
const roleName = computed(() => String(welcome.value?.roleName || userStore.roleName || ''))
/** C类/原厂/R类/内勤：即使后端仍返回旧 ut2=2，也不展示销售额与测试年/月图 */
const isLiteSalesRole = computed(() => {
  const r = roleName.value
  return /C类|原厂|R类|内勤/.test(r)
})
const currentUser = computed(
  () => welcome.value?.currentUser || welcome.value?.loginName || userStore.loginName || '',
)
const currentUserId = computed(() => {
  const fromWelcome = String(welcome.value?.currentUserId || '').trim()
  if (fromWelcome) return fromWelcome
  const profile = (userStore.profile || {}) as Record<string, unknown>
  return String(profile.id || profile.userId || profile.user_id || '').trim()
})

function managerQuery(extra: Record<string, string> = {}): Record<string, string> {
  const q = { ...extra }
  if (currentUserId.value) q.saleManager = currentUserId.value
  return q
}

/** Java：测试主管点「待审核实验分包子订单」按 test_manager 筛，不按 sale_manager */
const isTestManager = computed(
  () => welcomeUserType2.value === 5 || String(roleName.value || '').includes('测试主管'),
)

function pendingSubcontractSubQuery(): Record<string, string> {
  if (isTestManager.value && currentUserId.value) {
    return { orderStatus: '20', testManager: currentUserId.value }
  }
  return managerQuery({ orderStatus: '20' })
}

const logs = computed<WelcomeLogItem[]>(() => welcome.value?.newlogs || [])
const showLogs = computed(() => welcomeUserType.value === 1)
const showAssets = computed(() => {
  if (welcome.value?.showAssets != null) return Boolean(welcome.value.showAssets)
  // 2/3/4/5/6/7/14；不含 0（公共账号/外部合作空白页）；5=制单员
  return [2, 3, 4, 5, 6, 7, 14].includes(welcomeUserType.value)
})
/** Java userType3==2（仅销售主管/销售人员）；C类等强制关闭 */
const showSaleChart = computed(() => {
  if (isLiteSalesRole.value) return false
  return welcomeUserType3.value === 2 || welcomeUserType2.value === 2
})
/** Java：3=测试人员，5=测试主管 */
const showTestChart = computed(
  () => welcomeUserType2.value === 3 || welcomeUserType2.value === 5,
)
const showAdminChart = computed(() => welcomeUserType2.value === 1)
const testYearPicked = ref(String(new Date().getFullYear()))
const saleYearPicked = ref(String(new Date().getFullYear()))
const saleOrderType = ref('')
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
const testChartYear = computed(() =>
  String(welcome.value?.testChartYear || welcome.value?.saleYear || new Date().getFullYear()),
)
const qnxsrmb = computed(() => String(welcome.value?.qnxsrmb ?? '0.00'))
const qnxsus = computed(() => String(welcome.value?.qnxsus ?? '0.00'))
const ddslrmb = computed(() => Number(welcome.value?.ddslrmb || 0))
const ddslus = computed(() => Number(welcome.value?.ddslus || 0))
const grml = computed(() => String(welcome.value?.grmlzhbigdecimal ?? '0.00'))
const grmlRate = computed(() => String(welcome.value?.grmlllbigdecimal ?? '0.00'))

const pending = computed(() => welcome.value?.pendingCounts || {})
const ops = computed(() => welcome.value?.opsCounts || {})

const pendingKpis = computed<Kpi[]>(() => {
  // 对齐 Java welcome.html userType=3（销售主管 / 测试主管）
  if (welcomeUserType.value !== 3) return []
  return [
    {
      key: 'exp',
      label: '待审核实验订单',
      count: Number(pending.value.expOrder || 0),
      onClick: () => goOrders(managerQuery({ orderType: '6', orderStatus: '20' })),
    },
    {
      key: 'self',
      label: '待审核实验子订单',
      count: Number(pending.value.selfChildOrder || 0),
      onClick: () => goOrders(managerQuery({ orderType: '10', orderStatus: '20' })),
    },
    {
      key: 'sub',
      label: '待审核实验分包订单',
      count: Number(pending.value.subcontractOrder || 0),
      onClick: () =>
        router.push({
          name: 'ExperimentSubcontractOrders',
          query: managerQuery({ orderStatus: '20' }),
        }),
    },
    {
      key: 'sub-child',
      label: '待审核实验分包子订单',
      count: Number(pending.value.subcontractSubOrder || 0),
      onClick: () =>
        router.push({
          name: 'ExperimentSubcontractSubOrders',
          query: pendingSubcontractSubQuery(),
        }),
    },
    {
      key: 'pay',
      label: '待审核付款实验分包子订单',
      count: Number(pending.value.materialSubOrder || 0),
      onClick: () =>
        router.push({
          name: 'ExperimentSubcontractSubOrders',
          // 对齐 Java todoCheckListPagesub：付款审核仍按 sale_manager
          query: managerQuery({ payStatus: '32' }),
        }),
    },
  ]
})

const showSaleTestCharts = computed(() => {
  if (isLiteSalesRole.value) return false
  // Java userType2==4（销售人员）才有测试数量年/月图
  return Boolean(welcome.value?.showSaleTestCharts) || welcomeUserType2.value === 4
})
const testYearChart = computed(() => welcome.value?.testYearChart || {})
const testerMonthChart = computed(() => welcome.value?.testerMonthChart || {})

const opsKpis = computed<Kpi[]>(() => {
  if (
    !welcome.value?.showOpsCounts &&
    ![3, 4, 5, 6, 7].includes(welcomeUserType.value) &&
    welcomeUserType2.value !== 3 &&
    welcomeUserType2.value !== 5
  ) {
    return []
  }
  // 对齐 Java welcome.html：测试人员/主管/C类等第三卡均为「测试超时订单」
  return [
    {
      key: 'nostart',
      label: '未开始测试订单',
      count: Number(ops.value.notStarted || 0),
      tone: 'kpi-card--warn',
      onClick: () =>
        router.push({ name: 'ExperimentWelcomeOrders', query: { order_status_out: '0' } }),
    },
    {
      key: 'progress',
      label: '进行中测试订单',
      count: Number(ops.value.inProgress || 0),
      tone: 'kpi-card--info',
      onClick: () =>
        router.push({ name: 'ExperimentWelcomeOrders', query: { order_status_out: '1' } }),
    },
    {
      key: 'timeout',
      label: '测试超时订单',
      count: Number(ops.value.timeout || 0),
      tone: 'kpi-card--danger',
      onClick: () =>
        router.push({
          name: 'ExperimentWelcomeOrders',
          query: { order_status_out: 'null', is_timeout: '1' },
        }),
    },
  ]
})

const actionCards = computed<Card[]>(() => {
  const t = welcomeUserType.value
  // C类等对齐 Java：入口卡仅标题、无副文案
  const lite = isLiteSalesRole.value
  const cards: Card[] = []
  if ([1, 2, 3, 4, 7, 14].includes(t)) {
    cards.push({
      key: 'fund',
      title: '资金账户',
      desc: lite ? undefined : '账户余额 · 收支明细',
      icon: '¥',
      tone: 'action-card--fund',
      onClick: () => router.push({ name: 'FundAccount' }),
    })
    cards.push({
      key: 'digital',
      title: '数字化中心',
      desc: lite ? undefined : '运营看板 · 绩效统计',
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
  // 制单员(userType=5)：新增商品 + 新增实验订单（对齐 Java welcome.html）
  if (t === 5) {
    cards.push({
      key: 'goods',
      title: '新增商品',
      desc: lite ? undefined : '录入商品资料',
      icon: '品',
      tone: 'action-card--order',
      onClick: () => router.push({ name: 'OpsGoods' }),
    })
  }
  if ([3, 4, 5, 7].includes(t)) {
    cards.push({
      key: 'create',
      title: '新增实验订单',
      desc: lite ? undefined : '创建实验销售订单',
      icon: '+',
      tone: 'action-card--order',
      onClick: () => router.push({ name: 'ExperimentOrderCreate' }),
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
  if (t === 0) return '当前账号类型在欢迎页无图表与快捷入口，请从左侧菜单进入业务模块'
  if (t === 1) return '查看近期交易与系统动态，或从下方快捷入口进入常用模块'
  if (t === 2) return '查看账户资产，或从下方快捷入口进入资金与数字化模块'
  if (t === 5) return '从下方快捷入口新增商品或实验订单，查看测试订单与账户资产'
  // 测试主管(ut2=5) / 测试人员(ut2=3)
  if (t === 3 && welcomeUserType2.value === 5) {
    return '处理待审核订单，查看测试数量与账户资产'
  }
  if (t === 3) return '处理待审核订单，查看个人业绩与资产'
  if (welcomeUserType2.value === 3 || welcomeUserType2.value === 5) {
    return '查看测试数量与账户资产'
  }
  // C类等：仅快捷入口 + 运营卡 + 资产
  if (t === 4 && welcomeUserType3.value !== 2) {
    return '从下方快捷入口进入业务模块，查看测试订单与账户资产'
  }
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
  // 双 0 时避免饼图对半假数据（对齐金额文案）
  const data =
    rmb === 0 && usd === 0
      ? [{ name: '暂无资产', value: 1, itemStyle: { color: '#e5e7eb' } }]
      : [
          { name: '人民币', value: rmb },
          { name: '美金(转人民币)', value: usd },
        ]
  assetChart.setOption({
    color: ['#e11d48', '#374151'],
    tooltip: {
      trigger: 'item',
      formatter: (p: { name?: string; value?: number; percent?: number }) => {
        if (p.name === '暂无资产') return '暂无资产'
        return `${p.name} : ${p.value} (${p.percent}%)`
      },
    },
    series: [
      {
        name: '可用资产',
        type: 'pie',
        radius: ['35%', '62%'],
        center: ['50%', '48%'],
        data,
        label: {
          formatter: (p: { name?: string; value?: number }) =>
            p.name === '暂无资产' ? '暂无资产' : `${p.name}\n${p.value}`,
        },
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
  saleChart.off('click')
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
  saleChart.on('click', (params: { name?: string; seriesIndex?: number }) => {
    const m = String(params.name || '')
    if (!m || m === '暂无') return
    const currencyType = params.seriesIndex === 1 ? '2' : '1'
    router.push({
      name: 'DigitalExpAmountList',
      query: {
        month: m,
        order_type: saleOrderType.value || '',
        currency_type: currencyType,
        userId: currentUserId.value || '',
      },
    })
  })
}

function renderTestBars() {
  if (!testChartRef.value || !showTestChart.value) return
  if (!testChart) testChart = echarts.init(testChartRef.value)
  const months = welcome.value?.expmonth || []
  const vals = (welcome.value?.expTestAry || []).map((v) => Number(v) || 0)
  testChart.off('click')
  testChart.setOption({
    color: ['#ea580c'],
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 24, bottom: 36 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
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
        areaStyle: { color: 'rgba(234,88,12,0.12)' },
        data: vals.length ? vals : [0],
      },
    ],
  })
  testChart.on('click', (params: { name?: string }) => {
    const m = String(params.name || '')
    if (!m || m === '暂无') return
    router.push({
      name: 'DigitalMyTestOrders',
      query: { userId: currentUserId.value || '', month: m },
    })
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
  const saleUid = String(
    (testYearChart.value as Record<string, unknown>).saleUserId || currentUserId.value || '',
  )
  testYearChartInst.off('click')
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
  testYearChartInst.on('click', (params: { name?: string }) => {
    const m = String(params.name || '')
    if (!m || m === '暂无') return
    router.push({
      name: 'DigitalMyTestOrders',
      query: { month: m, sale_user: saleUid, userId: '' },
    })
  })
}

function renderTesterMonth() {
  if (!testerMonthChartRef.value || !showSaleTestCharts.value) return
  if (!testerMonthChartInst) testerMonthChartInst = echarts.init(testerMonthChartRef.value)
  const names = testerMonthChart.value.names || []
  const vals = (testerMonthChart.value.values || []).map((v) => Number(v) || 0)
  const userIds = ((testerMonthChart.value as Record<string, unknown>).userIds || []) as string[]
  const month = String(testerMonthChart.value.month || '')
  const saleUid = String(
    (testerMonthChart.value as Record<string, unknown>).saleUserId || currentUserId.value || '',
  )
  testerMonthChartInst.off('click')
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
        data: vals.length
          ? vals.map((v, i) => ({
              value: v,
              userId: userIds[i] || '',
            }))
          : [0],
      },
    ],
  })
  testerMonthChartInst.on('click', (params: { dataIndex?: number; data?: { userId?: string } }) => {
    const idx = Number(params.dataIndex ?? -1)
    const uid = String(params.data?.userId || userIds[idx] || '')
    if (!uid && !month) return
    router.push({
      name: 'DigitalMyTestOrders',
      query: {
        userId: uid,
        month,
        sale_user: saleUid,
      },
    })
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

async function ensureWelcomeData(year?: string, orderType?: string) {
  const y = year || saleYearPicked.value || testYearPicked.value || String(new Date().getFullYear())
  const ot = orderType != null ? orderType : saleOrderType.value
  const res = await fetchAdminWelcome({
    silentError: true,
    params: { year: y, order_type: ot || undefined },
  })
  if (isAjaxOk(res) && res.obj) {
    const obj = res.obj as Record<string, unknown>
    userStore.welcome = { ...(userStore.welcome || {}), ...obj }
    if (obj.testChartYear) {
      testYearPicked.value = String(obj.testChartYear)
    }
    if (obj.saleYear) {
      saleYearPicked.value = String(obj.saleYear)
    }
  }
}

async function reloadSaleChart() {
  await ensureWelcomeData(saleYearPicked.value, saleOrderType.value)
  await nextTick()
  renderSaleBars()
}

async function onTestYearChange(val: string | null) {
  if (!val) return
  await ensureWelcomeData(val)
  await nextTick()
  renderTestBars()
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

.java-home-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.java-home-strip__action {
  flex: 1 1 160px;
  min-height: 88px;
  padding: 18px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: #fff;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  cursor: pointer;

  &:hover {
    border-color: #f5a623;
    color: #ea580c;
  }
}

.java-home-strip__kpi {
  flex: 1 1 160px;
  min-height: 88px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;

  strong {
    font-size: 28px;
    font-weight: 700;
    line-height: 1;
    color: #ea580c;
  }

  span {
    font-size: 13px;
    color: #666;
  }

  &.kpi-card--info strong {
    color: #2563eb;
  }

  &.kpi-card--danger strong {
    color: #dc2626;
  }

  &:hover {
    border-color: #f5a623;
  }
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

.panel-head__year {
  width: 120px;
}

.panel-head__tools {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.panel-head__year :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #e5e7eb inset;
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
