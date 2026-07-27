<template>
  <div class="dashboard">
    <div class="quick-row">
      <button type="button" class="quick-card" @click="goFundAccount">资金账户</button>
      <button type="button" class="quick-card" @click="goDigitalCenter">数字化中心</button>
    </div>

    <div class="main-row">
      <el-card class="chart-card" shadow="never">
        <template #header>
          <span>最近6个月交易记录</span>
        </template>
        <div ref="chartRef" class="chart-box" />
      </el-card>

      <el-card class="log-card" shadow="never">
        <template #header>
          <div class="log-head">
            <span>平台系统操作记录</span>
            <el-button link type="primary" @click="goMoreLogs">更多</el-button>
          </div>
        </template>
        <ul v-if="logs.length" class="log-list">
          <li v-for="(item, idx) in logs" :key="String(item.id ?? idx)">
            <span class="log-arrow">&gt;</span>
            <span class="log-body">
              <span class="log-time">[{{ item.addTime || '-' }}]</span>
              {{ item.userName ? `${item.userName} ` : '' }}{{ item.content || '-' }}
            </span>
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

function goFundAccount() {
  router.push('/fund/account')
}

function goDigitalCenter() {
  router.push('/fund/digital-center')
}

function goMoreLogs() {
  router.push('/system/ops-logs')
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  chart.setOption({
    title: {
      subtext: '销售订单',
      left: 8,
      top: 0,
    },
    tooltip: { trigger: 'axis' },
    toolbox: {
      right: 8,
      feature: {
        dataView: { readOnly: true },
        magicType: { type: ['line', 'bar'] },
        restore: {},
        saveAsImage: {},
      },
    },
    grid: { left: 48, right: 24, top: 56, bottom: 32 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xdate.value.length ? xdate.value : ['-'],
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '{value} 万元' },
    },
    series: [
      {
        name: '交易金额',
        type: 'line',
        smooth: false,
        data: ydata.value.length ? ydata.value : [0],
        itemStyle: { color: '#c23531' },
        lineStyle: { color: '#c23531' },
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
  gap: 16px;
}

.quick-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.quick-card {
  height: 88px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;

  &:hover {
    border-color: #409eff;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.12);
    color: #409eff;
  }
}

.main-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.8fr);
  gap: 16px;
}

.chart-box {
  width: 100%;
  height: 360px;
}

.log-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.log-list {
  margin: 0;
  padding: 0;
  list-style: none;
  max-height: 360px;
  overflow: auto;
}

.log-list li {
  display: flex;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px dashed #ebeef5;
  color: #606266;
  line-height: 1.5;
}

.log-arrow {
  color: #909399;
  flex-shrink: 0;
}

.log-body {
  min-width: 0;
  word-break: break-all;
}

.log-time {
  margin-right: 6px;
  color: #909399;
}

@media (max-width: 960px) {
  .quick-row,
  .main-row {
    grid-template-columns: 1fr;
  }
}
</style>
