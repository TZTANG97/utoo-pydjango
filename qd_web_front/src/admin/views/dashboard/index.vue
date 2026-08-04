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

    <div v-if="quickCards.length" class="quick-row" :style="quickRowStyle">
      <button
        v-for="card in quickCards"
        :key="card.key"
        type="button"
        class="quick-card"
        :class="card.tone"
        @click="card.onClick"
      >
        <span class="quick-card__icon" aria-hidden="true">{{ card.icon }}</span>
        <span class="quick-card__body">
          <strong>
            {{ card.title }}
            <em v-if="card.badge != null" class="quick-card__badge">{{ card.badge }}</em>
          </strong>
          <em>{{ card.desc }}</em>
        </span>
        <span class="quick-card__arrow">→</span>
      </button>
    </div>
    <el-alert
      v-else-if="welcomeUserType !== 1"
      class="role-hint"
      type="info"
      :closable="false"
      show-icon
      title="当前账号类型在欢迎页无快捷入口，请从左侧菜单进入业务模块"
    />

    <div v-if="showMainPanels" class="main-row" :class="{ 'main-row--single': !showLogs }">
      <el-card v-if="showRoleChart" class="panel-card chart-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">{{ chartTitle }}</span>
            <span v-if="chartUnit" class="panel-head__sub">{{ chartUnit }}</span>
          </div>
        </template>
        <div ref="chartRef" class="chart-box" />
      </el-card>

      <el-card v-if="showAssets" class="panel-card asset-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">我的实际可用总资产</span>
          </div>
        </template>
        <div class="asset-body">
          <div class="asset-item">
            <span class="asset-item__label">人民币</span>
            <strong class="asset-item__value">{{ accountRMB }} <small>元</small></strong>
          </div>
          <div class="asset-item">
            <span class="asset-item__label">美元</span>
            <strong class="asset-item__value">{{ accountUS }} <small>元</small></strong>
          </div>
        </div>
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

type QuickCard = {
  key: string
  title: string
  desc: string
  icon: string
  tone: string
  badge?: number
  onClick: () => void
}

const router = useRouter()
const userStore = useUserStore()
const chartRef = ref<HTMLDivElement>()
let chart: ECharts | null = null

const welcome = computed(() => userStore.welcome)
const xdate = computed(() => welcome.value?.xdate || [])
const ydata = computed(() => (welcome.value?.ydata || []).map((v) => Number(v) || 0))
const logs = computed<WelcomeLogItem[]>(() => welcome.value?.newlogs || [])

/** 对齐 Java welcome.html：1管理员 2公司 3销售主管 4销售/测试人员 5制单 6投资 7仓库 14=H类 0=其它(测试主管等) */
const welcomeUserType = computed(() =>
  Number(welcome.value?.userType ?? userStore.userType ?? 0),
)
const welcomeUserType2 = computed(() => Number(welcome.value?.userType2 ?? 0))
const roleName = computed(() => String(welcome.value?.roleName || userStore.roleName || ''))

const showLogs = computed(() => welcomeUserType.value === 1)
const showRoleChart = computed(() => [1, 2, 3].includes(welcomeUserType2.value))
const showAssets = computed(() => {
  if (welcome.value?.showAssets != null) return Boolean(welcome.value.showAssets)
  return [0, 2, 3, 4, 6, 7, 14].includes(welcomeUserType.value)
})
const showMainPanels = computed(() => showRoleChart.value || showAssets.value || showLogs.value)

const chartTitle = computed(() => {
  if (welcome.value?.chartTitle) return welcome.value.chartTitle
  if (welcomeUserType2.value === 1) return '最近 6 个月交易记录'
  if (welcomeUserType2.value === 2) return '我的实验销售额'
  if (welcomeUserType2.value === 3) return '我的测试数量'
  return '数据概览'
})
const chartUnit = computed(() => {
  if (welcome.value?.chartUnit) return welcome.value.chartUnit
  if (welcomeUserType2.value === 3) return '测试数量（单）'
  return '金额（万元）'
})
const chartSeriesName = computed(() => {
  if (welcomeUserType2.value === 3) return '测试数量'
  if (welcomeUserType2.value === 2) return '销售额'
  return '交易金额'
})

const accountRMB = computed(() => String(welcome.value?.accountRMB ?? '0'))
const accountUS = computed(() => String(welcome.value?.accountUS ?? '0'))
const pending = computed(() => welcome.value?.pendingCounts || {})

const bannerHint = computed(() => {
  const t = welcomeUserType.value
  if (t === 1) return '查看近期交易与系统动态，或从下方快捷入口进入常用模块'
  if (t === 3) return '处理待审核订单，或查看个人业绩与资产'
  if (t === 4 && welcomeUserType2.value === 3) return '查看测试数量与账户资产'
  if ([2, 3, 4, 7, 14].includes(t)) return '查看个人业绩与资产，或从下方快捷入口进入常用模块'
  if (t === 0 || t === 6) return '查看账户可用资产，或从左侧菜单进入业务模块'
  return '从下方快捷入口或左侧菜单进入业务模块'
})

const quickCards = computed<QuickCard[]>(() => {
  const t = welcomeUserType.value
  const cards: QuickCard[] = []

  // 销售主管：待审核入口（对齐 Java welcome.html userType==3）
  if (t === 3) {
    cards.push({
      key: 'audit-exp',
      title: '待审核实验订单',
      desc: '实验订单审核',
      icon: '审',
      tone: 'quick-card--audit',
      badge: Number(pending.value.expOrder || 0) || undefined,
      onClick: () => goExperimentOrders({ orderStatus: '20' }),
    })
    cards.push({
      key: 'audit-sub',
      title: '待审核实验分包订单',
      desc: '分包订单审核',
      icon: '包',
      tone: 'quick-card--audit',
      badge: Number(pending.value.subcontractOrder || 0) || undefined,
      onClick: () => router.push({ name: 'ExperimentSubcontractOrders', query: { orderStatus: '20' } }),
    })
    cards.push({
      key: 'audit-sub-child',
      title: '待审核实验分包子订单',
      desc: '分包子订单审核',
      icon: '子',
      tone: 'quick-card--audit',
      badge: Number(pending.value.subcontractSubOrder || 0) || undefined,
      onClick: () =>
        router.push({ name: 'ExperimentSubcontractSubOrders', query: { orderStatus: '20' } }),
    })
  }

  // 资金账户 + 数字化中心：管理员/公司/销售主管/销售·测试人员/仓库/H类
  if ([1, 2, 3, 4, 7, 14].includes(t)) {
    cards.push({
      key: 'fund',
      title: '资金账户',
      desc: '账户余额 · 收支明细',
      icon: '¥',
      tone: 'quick-card--fund',
      onClick: goFundAccount,
    })
    cards.push({
      key: 'digital',
      title: '数字化中心',
      desc: '运营看板 · 绩效统计',
      icon: '◈',
      tone: 'quick-card--digital',
      onClick: goDigitalCenter,
    })
  }

  if (t === 2) {
    cards.push({
      key: 'company-pay',
      title: '公司资金支出',
      desc: '各公司支出明细',
      icon: '企',
      tone: 'quick-card--company',
      onClick: goCompanyPay,
    })
    cards.push({
      key: 'personal-pay',
      title: '个人资金支出',
      desc: '个人支出明细',
      icon: '人',
      tone: 'quick-card--personal',
      onClick: goPersonalPay,
    })
  }

  // 新增实验订单：销售主管/销售·测试人员/仓库/制单
  if ([3, 4, 5, 7].includes(t)) {
    cards.push({
      key: 'create-order',
      title: '新增实验订单',
      desc: '创建实验销售订单',
      icon: '+',
      tone: 'quick-card--order',
      onClick: goCreateExpOrder,
    })
  }

  return cards
})

const quickRowStyle = computed(() => {
  const n = quickCards.value.length
  if (n <= 1) return { gridTemplateColumns: '1fr' }
  if (n === 3) return { gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }
  if (n >= 4) return { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }
  return { gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }
})

const displayName = computed(
  () => userStore.userName || userStore.loginName || '管理员',
)

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

function goFundAccount() {
  router.push({ name: 'FundAccount' })
}

function goDigitalCenter() {
  router.push({ name: 'FundDigitalCenter' })
}

function goCompanyPay() {
  router.push({ name: 'FundCompanyPay' })
}

function goPersonalPay() {
  router.push({ name: 'FundPersonalPay' })
}

function goCreateExpOrder() {
  router.push({ name: 'ExperimentOrders' })
}

function goExperimentOrders(query?: Record<string, string>) {
  router.push({ name: 'ExperimentOrders', query })
}

function goMoreLogs() {
  router.push({ name: 'SystemOpsLogs' })
}

function renderChart() {
  if (!chartRef.value || !showRoleChart.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  const hasData = xdate.value.length > 0 && ydata.value.some((v) => v !== 0)
  const emptyText =
    welcomeUserType2.value === 3 ? '暂无测试数据' : welcomeUserType2.value === 2 ? '暂无销售数据' : '暂无交易数据'
  chart.setOption({
    color: ['#ea580c'],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e5e7eb',
      textStyle: { color: '#374151', fontSize: 12 },
    },
    toolbox: {
      right: 4,
      top: 0,
      iconStyle: { borderColor: '#9ca3af' },
      feature: {
        dataView: { readOnly: true, title: '数据' },
        magicType: { type: ['line', 'bar'], title: { line: '折线', bar: '柱状' } },
        restore: { title: '还原' },
        saveAsImage: { title: '保存' },
      },
    },
    grid: { left: 52, right: 20, top: 48, bottom: 36 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xdate.value.length ? xdate.value : ['暂无数据'],
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
      axisLabel: { formatter: '{value}', color: '#6b7280' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        name: chartSeriesName.value,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: ydata.value.length ? ydata.value : [0],
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(234, 88, 12, 0.22)' },
            { offset: 1, color: 'rgba(234, 88, 12, 0.02)' },
          ]),
        },
        itemStyle: { color: '#ea580c' },
        lineStyle: { color: '#ea580c', width: 2.5 },
      },
    ],
    graphic: hasData
      ? []
      : [
          {
            type: 'text',
            left: 'center',
            top: 'middle',
            style: {
              text: emptyText,
              fill: '#9ca3af',
              fontSize: 14,
            },
          },
        ],
  })
}

function onResize() {
  chart?.resize()
}

async function ensureWelcomeData() {
  const res = await fetchAdminWelcome({ silentError: true })
  if (isAjaxOk(res) && res.obj) {
    userStore.welcome = { ...(userStore.welcome || {}), ...(res.obj as object) }
  }
}

watch([xdate, ydata, showRoleChart, chartTitle], async () => {
  if (!showRoleChart.value) {
    chart?.dispose()
    chart = null
    return
  }
  await nextTick()
  renderChart()
})

onMounted(async () => {
  await ensureWelcomeData()
  await nextTick()
  if (showRoleChart.value) {
    renderChart()
  }
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped lang="scss">
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 18px;
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
  letter-spacing: 0.02em;
}

.welcome-banner__hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.welcome-banner__meta {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  font-size: 13px;
  color: #9ca3af;
  padding-bottom: 2px;
}

.welcome-banner__role {
  font-size: 12px;
  color: #ea580c;
  background: rgba(249, 115, 22, 0.08);
  padding: 2px 10px;
  border-radius: 999px;
}

.quick-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 92px;
  padding: 18px 20px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);

    .quick-card__arrow {
      opacity: 1;
      transform: translateX(2px);
    }
  }

  &--fund:hover {
    border-color: #fdba74;
  }

  &--digital:hover {
    border-color: #5eead4;
  }

  &--company:hover {
    border-color: #93c5fd;
  }

  &--personal:hover {
    border-color: #c4b5fd;
  }

  &--order:hover {
    border-color: #86efac;
  }

  &--audit:hover {
    border-color: #fcd34d;
  }
}

.quick-card__icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}

.quick-card--fund .quick-card__icon {
  background: rgba(249, 115, 22, 0.12);
  color: #ea580c;
}

.quick-card--digital .quick-card__icon {
  background: rgba(20, 184, 166, 0.12);
  color: #0f766e;
}

.quick-card--company .quick-card__icon {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}

.quick-card--personal .quick-card__icon {
  background: rgba(139, 92, 246, 0.12);
  color: #7c3aed;
}

.quick-card--order .quick-card__icon {
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}

.quick-card--audit .quick-card__icon {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.role-hint {
  border-radius: 12px;
}

.quick-card__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;

  strong {
    font-size: 16px;
    font-weight: 650;
    color: #1f2937;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  em {
    font-style: normal;
    font-size: 12px;
    color: #9ca3af;
  }
}

.quick-card__badge {
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: #ea580c;
  color: #fff !important;
  font-size: 11px !important;
  font-style: normal !important;
  line-height: 18px;
  text-align: center;
}

.quick-card__arrow {
  color: #9ca3af;
  opacity: 0.45;
  transition: opacity 0.2s, transform 0.2s;
}

.main-row {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.85fr);
  gap: 16px;
  align-items: stretch;

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
  height: 360px;
}

.asset-body {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  padding: 12px 4px 8px;
}

.asset-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px 16px;
  border-radius: 12px;
  background: #fff7ed;
  border: 1px solid #ffedd5;
}

.asset-item__label {
  font-size: 13px;
  color: #9a3412;
}

.asset-item__value {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  font-variant-numeric: tabular-nums;

  small {
    font-size: 13px;
    font-weight: 500;
    color: #6b7280;
  }
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

  &:last-child {
    border-bottom: none;
  }
}

.log-dot {
  width: 8px;
  height: 8px;
  margin-top: 7px;
  border-radius: 50%;
  background: #fdba74;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.12);
  flex-shrink: 0;
}

.log-body {
  min-width: 0;
  flex: 1;
}

.log-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.log-time {
  font-size: 12px;
  color: #9ca3af;
  font-variant-numeric: tabular-nums;
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
  line-height: 1.55;
  color: #4b5563;
  word-break: break-word;
}

@media (max-width: 960px) {
  .welcome-banner {
    flex-direction: column;
    align-items: flex-start;
  }

  .welcome-banner__meta {
    align-items: flex-start;
  }

  .quick-row,
  .main-row,
  .asset-body {
    grid-template-columns: 1fr;
  }
}
</style>
