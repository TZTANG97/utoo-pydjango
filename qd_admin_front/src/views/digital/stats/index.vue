<template>
  <admin-page-card title="统计">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="年份">
        <el-date-picker v-model="year" type="year" value-format="YYYY" style="width: 140px" />
      </el-form-item>
      <el-form-item label="部门">
        <el-select v-model="deptId" clearable filterable placeholder="全部" style="width: 200px">
          <el-option
            v-for="item in depts"
            :key="String(item.id)"
            :label="String(item.deptName || '')"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="load">查询</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="12" class="cards">
      <el-col :span="4" v-for="card in cards" :key="card.label">
        <div class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="section">
      <el-col :span="12">
        <h4>月度完成趋势</h4>
        <el-table :data="trendRows" border size="small">
          <el-table-column prop="mon" label="月份" width="100" />
          <el-table-column prop="num" label="完成数" />
        </el-table>
      </el-col>
      <el-col :span="12">
        <h4>测试人员工作量 Top</h4>
        <el-table :data="workload" border size="small" max-height="360">
          <el-table-column prop="trueName" label="姓名" min-width="120" />
          <el-table-column prop="finishNum" label="完成数" width="100" />
          <el-table-column prop="amount" label="金额" width="120" />
        </el-table>
      </el-col>
    </el-row>

    <div class="section">
      <h4>最近完成记录</h4>
      <el-table v-loading="loading" :data="recent" border>
        <el-table-column prop="orderId" label="订单号" min-width="140" />
        <el-table-column prop="trueName" label="测试人员" width="120" />
        <el-table-column prop="amount" label="金额" width="100" />
        <el-table-column prop="endTime" label="完成时间" min-width="160" />
        <el-table-column prop="expectFinishTime" label="期望完成" min-width="160" />
        <el-table-column label="超时" width="80">
          <template #default="{ row }">
            {{ Number(row.isTimeout) === 1 ? '是' : '否' }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchDigitalDepts, fetchStatsOverview } from '@/api/digital'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const loading = ref(false)
const year = ref(String(new Date().getFullYear()))
const deptId = ref('')
const depts = ref<Record<string, unknown>[]>([])
const overview = ref<Record<string, unknown>>({})
const trend = ref<Record<string, unknown>[]>([])
const workload = ref<Record<string, unknown>[]>([])
const recent = ref<Record<string, unknown>[]>([])

const cards = computed(() => [
  { label: '已完成', value: overview.value.finished ?? 0 },
  { label: '进行中', value: overview.value.doing ?? 0 },
  { label: '未开始', value: overview.value.waiting ?? 0 },
  { label: '超时', value: overview.value.timeout ?? 0 },
  { label: '准时完成', value: overview.value.ontime ?? 0 },
  { label: '准时率%', value: overview.value.ontimeRate ?? 0 },
])

const trendRows = computed(() => {
  const map = new Map(trend.value.map((r) => [String(r.mon), Number(r.num || 0)]))
  return Array.from({ length: 12 }, (_, i) => {
    const mon = String(i + 1).padStart(2, '0')
    return { mon, num: map.get(mon) || 0 }
  })
})

async function loadDepts() {
  const res = await fetchDigitalDepts()
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    depts.value = res.obj as Record<string, unknown>[]
  }
}

async function load() {
  loading.value = true
  try {
    const res = await fetchStatsOverview({ year: year.value, deptId: deptId.value })
    if (!isAjaxOk(res) || !res.obj) {
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    overview.value = (obj.overview as Record<string, unknown>) || {}
    trend.value = Array.isArray(obj.trend) ? (obj.trend as Record<string, unknown>[]) : []
    workload.value = Array.isArray(obj.workload) ? (obj.workload as Record<string, unknown>[]) : []
    recent.value = Array.isArray(obj.recent) ? (obj.recent as Record<string, unknown>[]) : []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadDepts()
  await load()
})
</script>

<style scoped lang="scss">
.filter-form {
  margin-bottom: 12px;
}
.cards {
  margin-bottom: 16px;
}
.stat-card {
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 14px 12px;
  text-align: center;
}
.stat-label {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.stat-value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 600;
}
.section {
  margin-top: 16px;
  h4 {
    margin: 0 0 10px;
  }
}
</style>
