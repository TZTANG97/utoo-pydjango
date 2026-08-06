<template>
  <div ref="rootRef" class="ops-console" :class="{ 'is-fullscreen': isFullscreen }">
    <aside class="ops-nav">
      <button type="button" :class="{ active: activeTab === 'overview' }" @click="switchTab('overview')">
        数据概览
      </button>
      <button type="button" :class="{ active: activeTab === 'orders' }" @click="switchTab('orders')">
        订单管理
      </button>
    </aside>

    <div class="ops-main">
    <header class="ops-toolbar">
      <div class="ops-brand">
        <span class="ops-brand__pulse" />
        <div>
          <h1>{{ activeTab === 'overview' ? '数字化中心 · 测试运营台' : '数字化中心 · 订单管理' }}</h1>
          <p>{{ activeTab === 'overview' ? '实时订单流 · 实验线状态 · 人员产出' : '完成趋势 · 类型分布 · 人员工作量' }}</p>
        </div>
      </div>

      <div class="ops-filters">
        <el-select
          v-model="periodType"
          class="ops-select"
          style="width: 110px"
          :append-to="selectAppendTo"
          @change="onPeriodChange"
        >
          <el-option label="月数据" value="2" />
          <el-option label="年数据" value="0" />
        </el-select>
        <el-select
          v-if="periodType === '2'"
          v-model="month"
          class="ops-select"
          style="width: 100px"
          :append-to="selectAppendTo"
          @change="reload"
        >
          <el-option v-for="m in 12" :key="m" :label="`${m}月`" :value="String(m).padStart(2, '0')" />
        </el-select>
        <el-select
          v-model="year"
          class="ops-select"
          style="width: 110px"
          :append-to="selectAppendTo"
          @change="reload"
        >
          <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="String(y)" />
        </el-select>
        <el-select
          v-model="deptId"
          clearable
          filterable
          placeholder="全部部门"
          class="ops-select"
          style="width: 160px"
          :append-to="selectAppendTo"
          @change="onDeptChange"
        >
          <el-option
            v-for="item in depts"
            :key="String(item.id)"
            :label="String(item.deptName || '')"
            :value="String(item.id)"
          />
        </el-select>
        <el-select
          v-model="userId"
          clearable
          filterable
          placeholder="全部人员"
          class="ops-select"
          style="width: 140px"
          :append-to="selectAppendTo"
          @change="reload"
        >
          <el-option
            v-for="u in users"
            :key="String(u.id)"
            :label="String(u.trueName || u.userName || '')"
            :value="String(u.id)"
          />
        </el-select>
        <el-button class="ops-btn" :loading="loading" @click="reload">刷新</el-button>
        <el-button class="ops-btn ops-btn--accent" @click="toggleFullscreen">
          {{ isFullscreen ? '退出全屏' : '全屏' }}
        </el-button>
      </div>
    </header>

    <div v-show="activeTab === 'overview'">
    <section class="ops-kpi" v-loading="loading">
      <button
        type="button"
        class="kpi-card kpi-card--cyan"
        @click="openHoverDrawer('done')"
      >
        <div class="kpi-card__icon">✓</div>
        <div class="kpi-card__body">
          <span class="kpi-card__label">完成测试订单</span>
          <span class="kpi-card__value">{{ anim.ywc }}</span>
          <span class="kpi-card__hint">点击打开明细</span>
        </div>
      </button>
      <button
        type="button"
        class="kpi-card kpi-card--amber"
        @click="openHoverDrawer('nostart')"
      >
        <div class="kpi-card__icon">◌</div>
        <div class="kpi-card__body">
          <span class="kpi-card__label">未开始订单</span>
          <span class="kpi-card__value">{{ anim.nostart }}</span>
          <span class="kpi-card__hint">点击打开明细</span>
        </div>
      </button>
      <button
        type="button"
        class="kpi-card kpi-card--teal"
        @click="openHoverDrawer('staff')"
      >
        <div class="kpi-card__icon">◎</div>
        <div class="kpi-card__body">
          <span class="kpi-card__label">测试人员总数</span>
          <span class="kpi-card__value">{{ anim.staff }}</span>
          <span class="kpi-card__hint">{{ deptLabel }} · 点击打开</span>
        </div>
      </button>
      <div class="kpi-card kpi-card--gold kpi-card--best">
        <div class="kpi-card__icon">★</div>
        <div class="kpi-card__body">
          <span class="kpi-card__label">本月最佳测试员</span>
          <span class="kpi-card__value kpi-card__value--name">{{ bestName }}</span>
          <span class="kpi-card__hint">{{ bestHint }}</span>
        </div>
      </div>
    </section>

    <section class="ops-mid">
      <div class="panel panel--chart">
        <div class="panel__head">
          <h3>订单状态分布</h3>
          <span class="panel__tag">实时</span>
        </div>
        <div ref="pieRef" class="chart-box" />
      </div>
      <div class="panel panel--trend">
        <div class="panel__head">
          <h3>{{ year }} 完成趋势</h3>
          <span class="panel__tag">月度</span>
        </div>
        <div ref="lineRef" class="chart-box" />
      </div>
      <div class="panel panel--best">
        <div class="panel__head">
          <h3>本月领跑榜</h3>
          <span class="panel__tag">Top 3</span>
        </div>
        <ul v-if="top3.length" class="podium">
          <li v-for="(item, idx) in top3" :key="String(item.test_user_id || idx)" :class="`rank-${idx + 1}`">
            <span class="podium__rank">{{ idx + 1 }}</span>
            <div class="podium__meta">
              <strong>{{ item.user_name || '—' }}</strong>
              <span>完成 {{ item.total_count ?? 0 }} · 准时率 {{ item.zsl ?? 0 }}%</span>
            </div>
          </li>
        </ul>
        <div v-else class="empty-soft">暂无排行数据</div>
      </div>
    </section>

    <section class="ops-lines panel">
      <div class="panel__head">
        <h3>实验线列表</h3>
        <span class="panel__tag">{{ linelist.length }} 条</span>
      </div>
      <div v-if="linelist.length" class="line-grid">
        <div
          v-for="(line, idx) in linelist"
          :key="String(line.id || idx)"
          class="line-chip"
          :class="{ 'is-busy': Number(line.line_status) === 1 }"
        >
          <span class="line-chip__status" />
          <div>
            <strong>{{ line.lab_name || '实验室' }}</strong>
            <span>{{ line.line_num || '—' }} · {{ line.lineStatusLabel || '—' }}</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-soft">暂无实验线</div>
    </section>

    <section class="ops-streams">
      <article class="stream stream--doing">
        <header>
          <h3>进行中</h3>
          <span class="badge">{{ jxzList.length }}</span>
        </header>
        <div class="stream__body">
          <div v-for="(row, i) in jxzList" :key="`j-${i}`" class="order-row">
            <div class="order-row__id">{{ row.orderNum || '—' }}</div>
            <div class="order-row__cols">
              <span>{{ row.user_name || '—' }}</span>
              <span>预计 {{ row.expect_finishtime || '—' }}</span>
              <span>开始 {{ row.start_time || '—' }}</span>
              <span>{{ row.experiment_project_name || '—' }}</span>
              <span>{{ row.line_num || '—' }}</span>
            </div>
          </div>
          <div v-if="!jxzList.length" class="empty-soft">暂无进行中订单</div>
        </div>
      </article>

      <article class="stream stream--overdue">
        <header>
          <h3>超时订单</h3>
          <span class="badge badge--danger">{{ wfpList.length }}</span>
        </header>
        <div class="stream__body">
          <div v-for="(row, i) in wfpList" :key="`w-${i}`" class="order-row order-row--alert">
            <div class="order-row__id">{{ row.orderNum || '—' }}</div>
            <div class="order-row__cols">
              <span>{{ row.user_name || '—' }}</span>
              <span class="text-danger">超时 {{ row.expect_finishtime || '—' }}</span>
              <span class="text-danger">超期 {{ row.timeout_days ?? '—' }} 天</span>
              <span>{{ row.experiment_project_name || '—' }}</span>
              <span>{{ row.line_num || '—' }}</span>
            </div>
          </div>
          <div v-if="!wfpList.length" class="empty-soft">暂无超时订单</div>
        </div>
      </article>

      <article class="stream stream--done">
        <header>
          <h3>完成订单</h3>
          <span class="badge badge--ok">{{ ywcList.length }}</span>
        </header>
        <div class="stream__body">
          <div v-for="(row, i) in ywcList" :key="`y-${i}`" class="order-row">
            <div class="order-row__id">{{ row.orderNum || '—' }}</div>
            <div class="order-row__cols">
              <span>{{ row.user_name || '—' }}</span>
              <span>完成 {{ row.end_time || row.finish_time || '—' }}</span>
              <span>{{ row.experiment_project_name || '—' }}</span>
              <span>{{ row.line_num || '—' }}</span>
            </div>
          </div>
          <div v-if="!ywcList.length" class="empty-soft">暂无完成订单</div>
        </div>
      </article>
    </section>
    </div>

    <div v-show="activeTab === 'orders'" v-loading="ordersLoading">
      <section class="ops-kpi ops-kpi--6">
        <div class="kpi-card kpi-card--cyan">
          <div class="kpi-card__icon">∑</div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">总订单数</span>
            <span class="kpi-card__value">{{ orderKpi.zongsl }}</span>
          </div>
        </div>
        <div class="kpi-card kpi-card--teal">
          <div class="kpi-card__icon">%</div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">测试准时率</span>
            <span class="kpi-card__value kpi-card__value--sm">{{ orderKpi.zsl }}%</span>
          </div>
        </div>
        <div class="kpi-card kpi-card--amber">
          <div class="kpi-card__icon">⏱</div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">平均测试时长</span>
            <span class="kpi-card__value kpi-card__value--sm">{{ orderKpi.pjsc }}h</span>
          </div>
        </div>
        <div class="kpi-card kpi-card--cyan">
          <div class="kpi-card__icon">↻</div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">进行中订单</span>
            <span class="kpi-card__value">{{ orderKpi.jxzsl }}</span>
          </div>
        </div>
        <div class="kpi-card kpi-card--gold">
          <div class="kpi-card__icon">!</div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">超时订单</span>
            <span class="kpi-card__value">{{ orderKpi.cssl }}</span>
          </div>
        </div>
        <div class="kpi-card kpi-card--teal">
          <div class="kpi-card__icon">✓</div>
          <div class="kpi-card__body">
            <span class="kpi-card__label">完成订单</span>
            <span class="kpi-card__value">{{ orderKpi.ywcsl }}</span>
          </div>
        </div>
      </section>

      <section class="ops-charts-grid">
        <div class="panel">
          <div class="panel__head">
            <h3>{{ orderDept }}测试任务完成趋势</h3>
          </div>
          <div ref="taskTrendRef" class="chart-box chart-box--lg" />
        </div>
        <div class="panel">
          <div class="panel__head">
            <h3>{{ orderDept }}测试类型分布</h3>
          </div>
          <div ref="testTypeRef" class="chart-box chart-box--lg" />
        </div>
        <div class="panel">
          <div class="panel__head">
            <h3>{{ orderDept }}测试人员工作量统计</h3>
          </div>
          <div ref="workloadRef" class="chart-box chart-box--lg" />
        </div>
        <div class="panel">
          <div class="panel__head">
            <h3>{{ orderDept }}测试人员年度测试数量统计</h3>
          </div>
          <div ref="annualRef" class="chart-box chart-box--lg" />
        </div>
      </section>
    </div>
    </div>

    <el-drawer
      :model-value="hoverDrawer === 'done'"
      title="完成测试明细"
      size="640px"
      class="ops-drawer"
      modal-class="ops-drawer-modal"
      :modal="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :append-to="selectAppendTo"
      @update:model-value="(v) => !v && closeHoverDrawer('done')"
    >
      <div class="drawer-row drawer-row--head">
        <span>订单号</span>
        <span>测试人员</span>
        <span>完成时间</span>
      </div>
      <div v-for="(row, i) in ywcList" :key="`d-${i}`" class="drawer-row">
        <strong>{{ row.orderNum || '—' }}</strong>
        <span>{{ row.user_name || '—' }}</span>
        <span>{{ row.end_time || row.finish_time || '—' }}</span>
      </div>
      <el-empty v-if="!ywcList.length" description="暂无数据" />
    </el-drawer>

    <el-drawer
      :model-value="hoverDrawer === 'nostart'"
      title="未开始订单明细"
      size="860px"
      class="ops-drawer"
      modal-class="ops-drawer-modal"
      :modal="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :append-to="selectAppendTo"
      @update:model-value="(v) => !v && closeHoverDrawer('nostart')"
    >
      <div class="drawer-row drawer-row--head drawer-row--5">
        <span>订单号</span>
        <span>测试人员</span>
        <span>预计完成</span>
        <span>测试分类</span>
        <span>实验线</span>
      </div>
      <div v-for="(row, i) in nostartList" :key="`n-${i}`" class="drawer-row drawer-row--5">
        <strong>{{ row.orderNum || '—' }}</strong>
        <span>{{ row.user_name || '—' }}</span>
        <span>{{ row.expect_finishtime || '—' }}</span>
        <span>{{ row.experiment_class_name || row.project_name || '—' }}</span>
        <span>{{ row.line_num || '—' }}</span>
      </div>
      <el-empty v-if="!nostartList.length" description="暂无数据" />
    </el-drawer>

    <el-drawer
      :model-value="hoverDrawer === 'staff'"
      title="测试人员明细"
      size="480px"
      class="ops-drawer"
      modal-class="ops-drawer-modal"
      :modal="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :append-to="selectAppendTo"
      @update:model-value="(v) => !v && closeHoverDrawer('staff')"
    >
      <el-table :data="testUserList" size="small" stripe>
        <el-table-column prop="userName" label="账号" min-width="100" />
        <el-table-column prop="trueName" label="姓名" min-width="90" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span :class="Number(row.test_num) > 0 ? 'text-busy' : 'text-idle'">
              {{ Number(row.test_num) > 0 ? '测试中' : '空闲中' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="deptName" label="部门" min-width="120" />
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onDeactivated, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import {
  fetchDigitalDepts,
  fetchStatsBoard1,
  fetchStatsBoardAnnual,
  fetchStatsDashboard,
  fetchStatsOrderManage,
  fetchStatsUsersByDept,
} from '@admin/api/digital'
import { useUserStore } from '@admin/stores/user'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type Row = Record<string, unknown>

const userStore = useUserStore()
const rootRef = ref<HTMLElement>()
/** 全屏时下拉必须挂到全屏根节点，挂 body 会不可见 */
const selectAppendTo = computed(() => rootRef.value || 'body')
const pieRef = ref<HTMLDivElement>()
const lineRef = ref<HTMLDivElement>()
const taskTrendRef = ref<HTMLDivElement>()
const testTypeRef = ref<HTMLDivElement>()
const workloadRef = ref<HTMLDivElement>()
const annualRef = ref<HTMLDivElement>()
let pieChart: ECharts | null = null
let lineChart: ECharts | null = null
let taskTrendChart: ECharts | null = null
let testTypeChart: ECharts | null = null
let workloadChart: ECharts | null = null
let annualChart: ECharts | null = null

const activeTab = ref<'overview' | 'orders'>('overview')
const loading = ref(false)
const ordersLoading = ref(false)
const isFullscreen = ref(false)
type HoverDrawer = 'done' | 'nostart' | 'staff'
const hoverDrawer = ref<HoverDrawer | null>(null)

/** 点击打开/切换明细；点关闭按钮或页面空白处关闭 */
function openHoverDrawer(kind: HoverDrawer) {
  hoverDrawer.value = kind
}

function closeHoverDrawer(kind: HoverDrawer) {
  if (hoverDrawer.value === kind) hoverDrawer.value = null
}

function closeAllHoverDrawers() {
  hoverDrawer.value = null
}

function onPageClickCloseDrawer(e: MouseEvent) {
  if (!hoverDrawer.value || e.button !== 0) return
  const el = e.target as HTMLElement | null
  if (!el?.closest) return
  // 点在抽屉内或三个 KPI 卡片上：不关（KPI 用于切换明细）
  if (el.closest('.el-drawer.ops-drawer')) return
  if (el.closest('.kpi-card--cyan, .kpi-card--amber, .kpi-card--teal')) return
  hoverDrawer.value = null
}

const now = new Date()
const periodType = ref('2')
const year = ref(String(now.getFullYear()))
const month = ref(String(now.getMonth() + 1).padStart(2, '0'))
const deptId = ref('')
const userId = ref('')

const depts = ref<Row[]>([])
const users = ref<Row[]>([])

const ywcList = ref<Row[]>([])
const jxzList = ref<Row[]>([])
const wfpList = ref<Row[]>([])
const nostartList = ref<Row[]>([])
const linelist = ref<Row[]>([])
const testUserList = ref<Row[]>([])
const trend = ref<Row[]>([])
const top3 = ref<Row[]>([])
const syUserMax = ref<Row | null>(null)
const syUsersNum = ref(0)
/** KPI / 环图用真实 COUNT，避免被列表截断影响 */
const counts = reactive({ ywc: 0, nostart: 0, doing: 0, timeout: 0 })
const orderKpi = reactive({
  zongsl: 0,
  zsl: 0,
  pjsc: 0,
  jxzsl: 0,
  cssl: 0,
  ywcsl: 0,
})
const orderDept = ref('所有部门')
const orderManageData = ref<Row>({})
const annualRows = ref<Row[]>([])

const anim = reactive({ ywc: 0, nostart: 0, staff: 0 })

const yearOptions = computed(() => {
  const y = now.getFullYear()
  return [y, y - 1, y - 2, y - 3]
})

const deptLabel = computed(() => {
  if (!deptId.value) return '全部部门测试人员'
  const d = depts.value.find((x) => String(x.id) === deptId.value)
  return `${d?.deptName || ''}测试人员`
})

const bestName = computed(() => String(syUserMax.value?.user_name || '—'))
const bestHint = computed(() => {
  if (!syUserMax.value) return '暂无数据'
  return `完成 ${syUserMax.value.total_count ?? 0} · 准时率 ${syUserMax.value.zsl ?? 0}%`
})

function filterParams() {
  return {
    type: periodType.value === '0' ? '4' : periodType.value,
    year: year.value,
    month: periodType.value === '2' ? month.value : '',
    test_lab: deptId.value,
    userId: userId.value,
    dept_id: deptId.value,
  }
}

function animateTo(key: 'ywc' | 'nostart' | 'staff', target: number) {
  const start = anim[key]
  const diff = target - start
  if (!diff) {
    anim[key] = target
    return
  }
  const steps = 18
  let i = 0
  const timer = window.setInterval(() => {
    i += 1
    anim[key] = Math.round(start + (diff * i) / steps)
    if (i >= steps) window.clearInterval(timer)
  }, 16)
}

function onPeriodChange() {
  reload()
}

async function switchTab(tab: 'overview' | 'orders') {
  closeAllHoverDrawers()
  activeTab.value = tab
  await reload()
  await nextTick()
  onResize()
}

async function loadDepts() {
  const res = await fetchDigitalDepts()
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    depts.value = res.obj as Row[]
  }
}

/** 首次进入：用当前登录账号部门预填筛选（如 admin → 总经理） */
function applyDefaultDeptFromLoginUser() {
  if (deptId.value) return
  const profile = (userStore.profile || {}) as Row
  const id = String(profile.deptId || profile.dept_id || '').trim()
  if (id && id !== '0' && depts.value.some((d) => String(d.id) === id)) {
    deptId.value = id
    return
  }
  const name = String(userStore.welcome?.deptName || profile.deptName || '').trim()
  if (!name) return
  const hit = depts.value.find((d) => String(d.deptName || '') === name)
  if (hit) deptId.value = String(hit.id)
}

async function loadUsers() {
  const res = await fetchStatsUsersByDept(deptId.value)
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    users.value = res.obj as Row[]
  } else {
    users.value = []
  }
}

async function onDeptChange() {
  userId.value = ''
  await loadUsers()
  await reload()
}

async function reloadOverview() {
  loading.value = true
  try {
    const params = filterParams()
    const [dashRes, boardRes] = await Promise.all([
      fetchStatsDashboard(params),
      fetchStatsBoard1({
        year: year.value,
        month: month.value,
        dept_id: deptId.value,
      }),
    ])
    if (!isAjaxOk(dashRes) || !dashRes.obj) {
      ElMessage.error(ajaxErrorMessage(dashRes, '加载统计失败'))
      return
    }
    const obj = dashRes.obj as Row
    ywcList.value = (obj.ywcList as Row[]) || []
    jxzList.value = (obj.jxzList as Row[]) || []
    wfpList.value = (obj.wfpList as Row[]) || []
    nostartList.value = (obj.nostartList as Row[]) || []
    linelist.value = (obj.linelist as Row[]) || []
    testUserList.value = (obj.testUserList as Row[]) || []
    trend.value = (obj.trend as Row[]) || []

    counts.ywc = Number(obj.ywcsl ?? ywcList.value.length) || 0
    counts.nostart = Number(obj.wfpsl ?? obj.nostartsl ?? nostartList.value.length) || 0
    counts.doing = Number(obj.jxzsl ?? jxzList.value.length) || 0
    counts.timeout = Number(obj.cssl ?? wfpList.value.length) || 0
    animateTo('ywc', counts.ywc)
    animateTo('nostart', counts.nostart)

    if (isAjaxOk(boardRes) && boardRes.obj) {
      const b = boardRes.obj as Row
      syUsersNum.value = Number(b.syUsersNum) || testUserList.value.length
      syUserMax.value = (b.syUserMax as Row) || null
      top3.value = (b.top3List as Row[]) || []
      animateTo('staff', syUsersNum.value)
    } else {
      animateTo('staff', testUserList.value.length)
    }

    await nextTick()
    renderOverviewCharts()
  } finally {
    loading.value = false
  }
}

async function reloadOrders() {
  ordersLoading.value = true
  try {
    const params = filterParams()
    const [manageRes, annualRes] = await Promise.all([
      fetchStatsOrderManage(params),
      fetchStatsBoardAnnual({ year: year.value, dept_id: deptId.value }),
    ])
    if (!isAjaxOk(manageRes) || !manageRes.obj) {
      ElMessage.error(ajaxErrorMessage(manageRes, '加载订单管理失败'))
      return
    }
    const obj = manageRes.obj as Row
    orderManageData.value = obj
    orderDept.value = String(obj.dept || '所有部门')
    orderKpi.zongsl = Number(obj.zongsl) || 0
    orderKpi.zsl = Number(obj.zsl) || 0
    orderKpi.pjsc = Number(obj.pjsc) || 0
    orderKpi.jxzsl = Number(obj.jxzsl) || 0
    orderKpi.cssl = Number(obj.cssl) || 0
    orderKpi.ywcsl = Number(obj.ywcsl) || 0
    annualRows.value = isAjaxOk(annualRes) && Array.isArray(annualRes.obj) ? (annualRes.obj as Row[]) : []
    await nextTick()
    renderOrderCharts()
  } finally {
    ordersLoading.value = false
  }
}

async function reload() {
  if (activeTab.value === 'orders') {
    await reloadOrders()
  } else {
    await reloadOverview()
  }
}

const chartText = { color: '#94a3b8' }
const chartAxis = { lineStyle: { color: '#334155' } }

function renderOverviewCharts() {
  if (pieRef.value) {
    if (!pieChart) pieChart = echarts.init(pieRef.value)
    const data = [
      { name: '未开始', value: counts.nostart, itemStyle: { color: '#d97706' } },
      { name: '进行中', value: counts.doing, itemStyle: { color: '#0ea5e9' } },
      { name: '超时', value: counts.timeout, itemStyle: { color: '#ef4444' } },
      { name: '已完成', value: counts.ywc, itemStyle: { color: '#10b981' } },
    ]
    pieChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#94a3b8', fontSize: 11 } },
      series: [
        {
          type: 'pie',
          radius: ['48%', '72%'],
          center: ['50%', '46%'],
          itemStyle: { borderRadius: 6, borderColor: '#0f172a', borderWidth: 2 },
          label: { color: '#cbd5e1', fontSize: 11 },
          data,
        },
      ],
    })
  }

  if (lineRef.value) {
    if (!lineChart) lineChart = echarts.init(lineRef.value)
    const map = new Map(trend.value.map((r) => [String(r.mon).padStart(2, '0'), Number(r.num || 0)]))
    const months = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'))
    const values = months.map((m) => map.get(m) || 0)
    lineChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: 36, right: 16, top: 24, bottom: 28 },
      xAxis: {
        type: 'category',
        data: months.map((m) => `${Number(m)}月`),
        axisLabel: { color: '#94a3b8', fontSize: 10 },
        axisLine: chartAxis,
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        splitLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: chartText,
      },
      series: [
        {
          type: 'line',
          smooth: true,
          data: values,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(20, 184, 166, 0.45)' },
              { offset: 1, color: 'rgba(20, 184, 166, 0.02)' },
            ]),
          },
          lineStyle: { color: '#14b8a6', width: 2.5 },
          itemStyle: { color: '#2dd4bf' },
          symbolSize: 6,
        },
      ],
    })
  }
}

function renderOrderCharts() {
  const obj = orderManageData.value
  const xdate = (obj.xdate as string[]) || []
  const wcvalues = ((obj.wcvalues as unknown[]) || []).map((v) => Number(v) || 0)
  const jhvalues = ((obj.jhvalues as unknown[]) || []).map((v) => Number(v) || 0)

  if (taskTrendRef.value) {
    if (!taskTrendChart) taskTrendChart = echarts.init(taskTrendRef.value)
    taskTrendChart.setOption({
      backgroundColor: 'transparent',
      legend: { data: ['完成测试数量', '计划测试数量'], textStyle: chartText, top: 0 },
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 40, bottom: 28 },
      xAxis: { type: 'category', data: xdate, axisLabel: { ...chartText, fontSize: 10 }, axisLine: chartAxis },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: chartText,
      },
      series: [
        { name: '完成测试数量', type: 'line', smooth: true, data: wcvalues, itemStyle: { color: '#14b8a6' } },
        { name: '计划测试数量', type: 'line', smooth: true, data: jhvalues, itemStyle: { color: '#64748b' } },
      ],
    })
  }

  if (testTypeRef.value) {
    if (!testTypeChart) testTypeChart = echarts.init(testTypeRef.value)
    const types = ((obj.testTypeAry as Row[]) || []).map((t) => ({
      name: String(t.project_name || t.test_type || '未命名'),
      value: Number(t.num) || 0,
    }))
    testTypeChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [
        {
          type: 'pie',
          radius: ['42%', '68%'],
          center: ['50%', '52%'],
          data: types,
          itemStyle: { borderRadius: 5, borderColor: '#0f172a', borderWidth: 2 },
          label: { color: '#cbd5e1', fontSize: 11 },
        },
      ],
    })
  }

  if (workloadRef.value) {
    if (!workloadChart) workloadChart = echarts.init(workloadRef.value)
    const ywcAry = (obj.testUserYwcAry as Row[]) || []
    const zsAry = (obj.testUserZsAry as Row[]) || []
    const names = ywcAry.map((r) => String(r.user_name || '—'))
    const finishNums = ywcAry.map((r) => Number(r.num) || 0)
    const rates = zsAry.map((r) => Number(r.value) || 0)
    workloadChart.setOption({
      backgroundColor: 'transparent',
      legend: { data: ['完成测试数量', '准时率(%)'], textStyle: chartText },
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 48, top: 40, bottom: 40, containLabel: true },
      xAxis: {
        type: 'category',
        data: names,
        axisLabel: { ...chartText, fontSize: 10, rotate: names.length > 6 ? 30 : 0 },
        axisLine: chartAxis,
      },
      yAxis: [
        {
          type: 'value',
          name: '完成数',
          nameTextStyle: chartText,
          splitLine: { lineStyle: { color: '#1e293b' } },
          axisLabel: chartText,
        },
        {
          type: 'value',
          name: '准时率%',
          nameTextStyle: chartText,
          splitLine: { show: false },
          axisLabel: chartText,
        },
      ],
      series: [
        { name: '完成测试数量', type: 'bar', data: finishNums, itemStyle: { color: '#14b8a6', borderRadius: [4, 4, 0, 0] } },
        { name: '准时率(%)', type: 'line', yAxisIndex: 1, data: rates, itemStyle: { color: '#f59e0b' } },
      ],
    })
  }

  if (annualRef.value) {
    if (!annualChart) annualChart = echarts.init(annualRef.value)
    const byUser = new Map<string, { name: string; data: number[] }>()
    const months = Array.from({ length: 12 }, (_, i) => `${year.value}-${String(i + 1).padStart(2, '0')}`)
    for (const row of annualRows.value) {
      const uid = String(row.test_user_id || '')
      const name = String(row.user_name || uid || '—')
      if (!byUser.has(uid)) {
        byUser.set(uid, { name, data: months.map(() => 0) })
      }
      const entry = byUser.get(uid)!
      const sm = String(row.stat_month || '')
      const idx = months.indexOf(sm)
      if (idx >= 0) entry.data[idx] = Number(row.total_count) || 0
    }
    // 只展示年内有完成量的人员，避免图例爆炸
    const series = Array.from(byUser.values())
      .filter((t) => t.data.some((n) => n > 0))
      .map((t, index) => {
        const palette = ['#14b8a6', '#0ea5e9', '#f59e0b', '#ef4444', '#8b5cf6', '#22d3ee', '#84cc16']
        return {
          name: t.name,
          type: 'bar' as const,
          data: t.data,
          itemStyle: { color: palette[index % palette.length] },
        }
      })
    annualChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { top: 0, textStyle: { ...chartText, fontSize: 11 }, type: 'scroll' },
      grid: { left: 40, right: 16, top: 48, bottom: 48, containLabel: true },
      xAxis: {
        type: 'category',
        data: months.map((m) => `${Number(m.slice(5))}月`),
        axisLabel: chartText,
        axisLine: chartAxis,
      },
      yAxis: {
        type: 'value',
        name: '测试数量',
        nameTextStyle: chartText,
        splitLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: chartText,
      },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { type: 'slider', start: 0, end: 100, height: 14, bottom: 8, borderColor: '#334155', fillerColor: 'rgba(20,184,166,0.25)', textStyle: chartText },
      ],
      series,
    }, true)
  }
}

function onResize() {
  pieChart?.resize()
  lineChart?.resize()
  taskTrendChart?.resize()
  testTypeChart?.resize()
  workloadChart?.resize()
  annualChart?.resize()
}

function toggleFullscreen() {
  const el = rootRef.value
  if (!el) return
  if (!document.fullscreenElement) {
    el.requestFullscreen?.().then(() => {
      isFullscreen.value = true
      nextTick(onResize)
    })
  } else {
    document.exitFullscreen?.().then(() => {
      isFullscreen.value = false
      nextTick(onResize)
    })
  }
}

function onFsChange() {
  isFullscreen.value = !!document.fullscreenElement
  nextTick(onResize)
}

onMounted(async () => {
  window.addEventListener('resize', onResize)
  document.addEventListener('fullscreenchange', onFsChange)
  try {
    await userStore.ensureProfile()
  } catch {
    /* 未登录信息时仍加载看板，部门保持全部 */
  }
  await loadDepts()
  applyDefaultDeptFromLoginUser()
  await loadUsers()
  await reload()
})

/** keep-alive：进入时挂空白处关闭；切走时关掉明细并卸监听 */
onActivated(() => {
  document.addEventListener('mousedown', onPageClickCloseDrawer)
})

onDeactivated(() => {
  closeAllHoverDrawers()
  document.removeEventListener('mousedown', onPageClickCloseDrawer)
})

onBeforeUnmount(() => {
  closeAllHoverDrawers()
  window.removeEventListener('resize', onResize)
  document.removeEventListener('fullscreenchange', onFsChange)
  document.removeEventListener('mousedown', onPageClickCloseDrawer)
  pieChart?.dispose()
  lineChart?.dispose()
  taskTrendChart?.dispose()
  testTypeChart?.dispose()
  workloadChart?.dispose()
  annualChart?.dispose()
})
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

.ops-console {
  --bg0: #0b1220;
  --bg1: #111827;
  --bg2: #1a2332;
  --line: rgba(148, 163, 184, 0.16);
  --text: #e2e8f0;
  --muted: #94a3b8;
  --cyan: #22d3ee;
  --teal: #14b8a6;
  --amber: #f59e0b;
  --gold: #eab308;
  --danger: #ef4444;
  --ok: #10b981;
  --font: 'IBM Plex Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, monospace;

  display: flex;
  gap: 14px;
  min-height: calc(100vh - 120px);
  margin: -4px;
  padding: 18px 18px 28px;
  color: var(--text);
  font-family: var(--font);
  background:
    radial-gradient(1200px 500px at 10% -10%, rgba(20, 184, 166, 0.18), transparent 55%),
    radial-gradient(900px 420px at 90% 0%, rgba(14, 165, 233, 0.14), transparent 50%),
    linear-gradient(165deg, var(--bg0), #0f172a 40%, #0b1324);
  border-radius: 12px;
  animation: fadeIn 0.45s ease both;
}

.ops-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
  width: 108px;
  padding-top: 6px;

  button {
    border: 1px solid var(--line);
    border-radius: 12px;
    background: rgba(15, 23, 42, 0.7);
    color: var(--muted);
    padding: 14px 10px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s ease;
    writing-mode: horizontal-tb;

    &:hover {
      color: var(--teal);
      border-color: rgba(20, 184, 166, 0.4);
    }
    &.active {
      color: #ecfeff;
      background: linear-gradient(160deg, rgba(13, 148, 136, 0.45), rgba(8, 145, 178, 0.25));
      border-color: rgba(45, 212, 191, 0.5);
      box-shadow: 0 0 18px rgba(20, 184, 166, 0.2);
    }
  }
}

.ops-main {
  flex: 1;
  min-width: 0;
}

.ops-console.is-fullscreen {
  min-height: 100vh;
  margin: 0;
  border-radius: 0;
  padding: 24px;
  overflow: auto;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.ops-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  margin-bottom: 16px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(12px);
  animation: fadeIn 0.5s ease 0.05s both;
  overflow: visible;
  position: relative;
  z-index: 20;
}

.ops-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  overflow: visible;
  position: relative;
  z-index: 21;
}

.ops-brand {
  display: flex;
  gap: 12px;
  align-items: center;

  h1 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  p {
    margin: 2px 0 0;
    font-size: 12px;
    color: var(--muted);
  }
}

.ops-brand__pulse {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--teal);
  box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.6);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.55);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(20, 184, 166, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(20, 184, 166, 0);
  }
}

.ops-select {
  :deep(.el-input__wrapper) {
    background: #0f172a;
    box-shadow: 0 0 0 1px #334155 inset;
  }
  :deep(.el-input__inner) {
    color: var(--text);
  }
  /* 全屏时下拉挂在容器内，避免被 Fullscreen 裁切 */
  :deep(.el-select__popper),
  :deep(.el-popper) {
    z-index: 4000 !important;
  }
}

.ops-btn {
  border: 1px solid #334155;
  background: #0f172a;
  color: var(--text);
  &:hover {
    border-color: var(--teal);
    color: var(--teal);
    background: rgba(20, 184, 166, 0.08);
  }
}
.ops-btn--accent {
  background: linear-gradient(120deg, #0d9488, #0891b2);
  border-color: transparent;
  color: #fff;
  &:hover {
    filter: brightness(1.08);
    color: #fff;
  }
}

.ops-kpi {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.ops-kpi--6 {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.ops-charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 14px;
}

.chart-box--lg {
  height: 280px;
}

.kpi-card__value--sm {
  font-size: 26px;
}

.kpi-card {
  position: relative;
  display: flex;
  gap: 14px;
  align-items: stretch;
  padding: 16px 18px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95));
  overflow: hidden;
  text-align: left;
  cursor: default;
  color: inherit;
  animation: fadeIn 0.55s ease both;

  &::before {
    content: '';
    position: absolute;
    inset: 0 auto 0 0;
    width: 4px;
  }

  &:nth-child(1) {
    animation-delay: 0.08s;
  }
  &:nth-child(2) {
    animation-delay: 0.12s;
  }
  &:nth-child(3) {
    animation-delay: 0.16s;
  }
  &:nth-child(4) {
    animation-delay: 0.2s;
  }
}

button.kpi-card {
  width: 100%;
  cursor: default;
  &:hover {
    border-color: rgba(45, 212, 191, 0.45);
    transform: translateY(-1px);
  }
}

.drawer-row {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr 1fr;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line, rgba(148, 163, 184, 0.16));
  font-size: 13px;
  color: var(--text, #e2e8f0);

  strong {
    color: #e2e8f0;
    word-break: break-all;
  }
  span {
    color: var(--muted, #94a3b8);
  }

  &--4 {
    grid-template-columns: 1.2fr 0.7fr 1fr 1fr;
  }

  &--5 {
    grid-template-columns: 1.4fr 0.7fr 1fr 1fr 0.8fr;
  }

  &--head {
    position: sticky;
    top: 0;
    z-index: 1;
    margin-top: -4px;
    padding-top: 4px;
    background: #0f172a;
    border-bottom: 1px solid rgba(148, 163, 184, 0.32);
    font-size: 12px;
    font-weight: 600;
    color: var(--muted, #94a3b8);

    span {
      color: var(--muted, #94a3b8);
    }
  }
}

.kpi-card--cyan::before {
  background: var(--cyan);
}
.kpi-card--amber::before {
  background: var(--amber);
}
.kpi-card--teal::before {
  background: var(--teal);
}
.kpi-card--gold::before {
  background: var(--gold);
}

.kpi-card__icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 18px;
  background: rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.kpi-card__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.kpi-card__label {
  font-size: 12px;
  color: var(--muted);
}
.kpi-card__value {
  margin-top: 4px;
  font-family: var(--mono);
  font-size: 32px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.03em;
}
.kpi-card__value--name {
  font-size: 22px;
  font-family: var(--font);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-card__hint {
  margin-top: 6px;
  font-size: 11px;
  color: #64748b;
}

.ops-mid {
  display: grid;
  grid-template-columns: 1.1fr 1.4fr 1fr;
  gap: 12px;
  margin-bottom: 14px;
}

.panel {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.72);
  padding: 12px 14px 14px;
  animation: fadeIn 0.6s ease 0.15s both;
}

.panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;

  h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
  }
}

.panel__tag {
  font-size: 11px;
  color: var(--teal);
  border: 1px solid rgba(20, 184, 166, 0.35);
  border-radius: 999px;
  padding: 2px 8px;
}

.chart-box {
  height: 220px;
}

.podium {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.podium li {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--line);
}

.podium__rank {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-family: var(--mono);
  font-weight: 700;
  background: #334155;
}
.rank-1 .podium__rank {
  background: linear-gradient(135deg, #fbbf24, #d97706);
  color: #111;
}
.rank-2 .podium__rank {
  background: linear-gradient(135deg, #94a3b8, #64748b);
}
.rank-3 .podium__rank {
  background: linear-gradient(135deg, #b45309, #78350f);
}

.podium__meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  strong {
    font-size: 14px;
  }
  span {
    font-size: 11px;
    color: var(--muted);
  }
}

.ops-lines {
  margin-bottom: 14px;
}

.line-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}

.line-chip {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.03);

  strong {
    display: block;
    font-size: 13px;
  }
  span {
    font-size: 11px;
    color: var(--muted);
  }
}

.line-chip__status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
  flex-shrink: 0;
}
.line-chip.is-busy .line-chip__status {
  background: var(--teal);
  box-shadow: 0 0 8px rgba(20, 184, 166, 0.7);
}

.ops-streams {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.stream {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.78);
  min-height: 280px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: fadeIn 0.65s ease 0.2s both;

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-bottom: 1px solid var(--line);
    h3 {
      margin: 0;
      font-size: 14px;
    }
  }
}

.stream--overdue {
  border-color: rgba(239, 68, 68, 0.35);
  box-shadow: inset 0 0 0 1px rgba(239, 68, 68, 0.08), 0 0 24px rgba(239, 68, 68, 0.08);
  header {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.16), transparent);
  }
}

.stream--done header {
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.12), transparent);
}
.stream--doing header {
  background: linear-gradient(90deg, rgba(14, 165, 233, 0.12), transparent);
}

.badge {
  min-width: 24px;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  font-family: var(--mono);
  font-size: 12px;
  background: rgba(14, 165, 233, 0.2);
  color: #7dd3fc;
}
.badge--danger {
  background: rgba(239, 68, 68, 0.22);
  color: #fca5a5;
}
.badge--ok {
  background: rgba(16, 185, 129, 0.2);
  color: #6ee7b7;
}

.stream__body {
  flex: 1;
  overflow: auto;
  max-height: 420px;
  padding: 8px;
}

.order-row {
  padding: 10px 10px;
  border-radius: 10px;
  margin-bottom: 6px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid transparent;
  transition: border-color 0.15s ease;

  &:hover {
    border-color: var(--line);
  }
}

.order-row--alert {
  background: rgba(239, 68, 68, 0.06);
}

.order-row__id {
  font-family: var(--mono);
  font-size: 12px;
  color: #cbd5e1;
  margin-bottom: 6px;
  word-break: break-all;
}

.order-row__cols {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  font-size: 11px;
  color: var(--muted);
}

.text-danger {
  color: #f87171 !important;
  font-weight: 600;
}
.text-busy {
  color: #fb923c;
}
.text-idle {
  color: #34d399;
}

.empty-soft {
  padding: 36px 12px;
  text-align: center;
  color: #64748b;
  font-size: 13px;
  background: repeating-linear-gradient(
    -45deg,
    transparent,
    transparent 6px,
    rgba(148, 163, 184, 0.04) 6px,
    rgba(148, 163, 184, 0.04) 12px
  );
  border-radius: 10px;
}

@media (max-width: 1200px) {
  .ops-kpi,
  .ops-kpi--6,
  .ops-mid,
  .ops-streams,
  .ops-charts-grid {
    grid-template-columns: 1fr 1fr;
  }
  .ops-mid .panel--best {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .ops-console {
    flex-direction: column;
  }
  .ops-nav {
    width: 100%;
    flex-direction: row;
  }
  .ops-kpi,
  .ops-kpi--6,
  .ops-mid,
  .ops-streams,
  .ops-charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<!-- 抽屉 teleport 后需非 scoped -->
<style lang="scss">
.ops-drawer-modal {
  background-color: transparent !important;
  pointer-events: none;
}

.el-drawer.ops-drawer {
  background: #111827 !important;
  color: #e2e8f0;
  pointer-events: auto;

  .el-drawer__header {
    margin-bottom: 16px;
    color: #e2e8f0;
  }

  .el-drawer__title {
    color: #e2e8f0;
    font-weight: 600;
  }

  .el-drawer__close-btn {
    color: #94a3b8;

    &:hover {
      color: #e2e8f0;
    }
  }

  .el-drawer__body {
    color: #e2e8f0;
    background: #0f172a;
  }

  .el-empty__description p {
    color: #64748b;
  }

  .el-table {
    --el-table-bg-color: #0f172a;
    --el-table-tr-bg-color: #0f172a;
    --el-table-header-bg-color: #1a2332;
    --el-table-row-hover-bg-color: #1e293b;
    --el-table-border-color: rgba(148, 163, 184, 0.16);
    --el-table-text-color: #e2e8f0;
    --el-table-header-text-color: #94a3b8;
    --el-fill-color-lighter: #1a2332;
    background: transparent;
  }
}
</style>
