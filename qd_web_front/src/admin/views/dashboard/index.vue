<template>
  <div class="dashboard">
    <section class="welcome-banner">
      <div>
        <p class="welcome-banner__hello">{{ greeting }}，{{ displayName }}</p>
        <h2 class="welcome-banner__title">欢迎回来</h2>
        <p class="welcome-banner__hint">查看近期交易与系统动态，或从下方快捷入口进入常用模块</p>
      </div>
      <div class="welcome-banner__meta">
        <span>{{ todayLabel }}</span>
      </div>
    </section>

    <div class="quick-row">
      <button type="button" class="quick-card quick-card--fund" @click="goFundAccount">
        <span class="quick-card__icon" aria-hidden="true">¥</span>
        <span class="quick-card__body">
          <strong>资金账户</strong>
          <em>账户余额 · 收支明细</em>
        </span>
        <span class="quick-card__arrow">→</span>
      </button>
      <button type="button" class="quick-card quick-card--digital" @click="goDigitalCenter">
        <span class="quick-card__icon" aria-hidden="true">◈</span>
        <span class="quick-card__body">
          <strong>数字化中心</strong>
          <em>运营看板 · 绩效统计</em>
        </span>
        <span class="quick-card__arrow">→</span>
      </button>
    </div>

    <div class="main-row">
      <el-card class="panel-card chart-card" shadow="never">
        <template #header>
          <div class="panel-head">
            <span class="panel-head__title">最近 6 个月交易记录</span>
            <span class="panel-head__sub">销售订单金额（万元）</span>
          </div>
        </template>
        <div ref="chartRef" class="chart-box" />
      </el-card>

      <el-card class="panel-card log-card" shadow="never">
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

const router = useRouter()
const userStore = useUserStore()
const chartRef = ref<HTMLDivElement>()
let chart: ECharts | null = null

const xdate = computed(() => userStore.welcome?.xdate || [])
const ydata = computed(() => (userStore.welcome?.ydata || []).map((v) => Number(v) || 0))
const logs = computed<WelcomeLogItem[]>(() => userStore.welcome?.newlogs || [])

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
  router.push('/admin/fund/account')
}

function goDigitalCenter() {
  router.push('/admin/fund/digital-center')
}

function goMoreLogs() {
  router.push('/admin/system/ops-logs')
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  const hasData = xdate.value.length > 0 && ydata.value.some((v) => v !== 0)
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
        name: '交易金额',
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
              text: '暂无交易数据',
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
  const hasChart = Array.isArray(userStore.welcome?.xdate) && Array.isArray(userStore.welcome?.ydata)
  const hasLogs = Array.isArray(userStore.welcome?.newlogs)
  if (hasChart && hasLogs) return
  const res = await fetchAdminWelcome({ silentError: true })
  if (isAjaxOk(res) && res.obj) {
    userStore.welcome = { ...(userStore.welcome || {}), ...(res.obj as object) }
  }
}

watch([xdate, ydata], async () => {
  await nextTick()
  renderChart()
})

onMounted(async () => {
  await ensureWelcomeData()
  await nextTick()
  renderChart()
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
  font-size: 13px;
  color: #9ca3af;
  padding-bottom: 2px;
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
  }

  em {
    font-style: normal;
    font-size: 12px;
    color: #9ca3af;
  }
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

  .quick-row,
  .main-row {
    grid-template-columns: 1fr;
  }
}
</style>
