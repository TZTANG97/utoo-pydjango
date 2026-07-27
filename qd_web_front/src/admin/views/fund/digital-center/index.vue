<template>
  <admin-page-card title="数字化管理运营中心">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="年份">
        <el-date-picker v-model="year" type="year" value-format="YYYY" style="width: 140px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="load">查询</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="12" class="cards">
      <el-col :span="6" v-for="card in cards" :key="card.label">
        <div class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ formatMoney(card.value) }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <h4>账户余额汇总</h4>
        <el-table :data="balances" border size="small">
          <el-table-column label="币种" width="100">
            <template #default="{ row }">
              {{ Number(row.accountType) === 2 ? '美金' : '人民币' }}
            </template>
          </el-table-column>
          <el-table-column prop="availableBalance" label="可用余额" />
          <el-table-column prop="freezingBalance" label="冻结余额" />
        </el-table>
      </el-col>
      <el-col :span="12">
        <h4>公司支出月度趋势</h4>
        <el-table :data="monthly" border size="small">
          <el-table-column prop="month" label="月份" width="80" />
          <el-table-column prop="amount" label="支出合计" />
        </el-table>
      </el-col>
    </el-row>

    <p class="hint">流水笔数（当年）：{{ overview.logCount ?? 0 }}</p>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { fetchDigitalManageOverview, isAjaxOk } from '@admin/api/fund'

const loading = ref(false)
const year = ref(String(new Date().getFullYear()))
const overview = ref<Record<string, unknown>>({})

const cards = computed(() => [
  { label: '公司支出合计', value: overview.value.companyPayTotal },
  { label: '个人支出合计', value: overview.value.userPayTotal },
  { label: '借贷款还款', value: overview.value.loanPayTotal },
  { label: '项目支出合计', value: overview.value.projectPayTotal },
])

const balances = computed(
  () => (overview.value.balances as Record<string, unknown>[]) || []
)
const monthly = computed(() => {
  const list = (overview.value.monthlyCompanyPay as Record<string, unknown>[]) || []
  const map = new Map(list.map((r) => [String(r.month), Number(r.amount || 0)]))
  return Array.from({ length: 12 }, (_, i) => {
    const m = String(i + 1)
    return { month: m, amount: map.get(m) || map.get(m.padStart(2, '0')) || 0 }
  })
})

function formatMoney(v: unknown) {
  return Number(v || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

async function load() {
  loading.value = true
  try {
    const res = await fetchDigitalManageOverview({ year: year.value })
    if (isAjaxOk(res)) overview.value = (res.obj as Record<string, unknown>) || {}
  } finally {
    loading.value = false
  }
}

onMounted(() => load())
</script>

<style scoped>
.filter-form { margin-bottom: 12px; }
.cards { margin-bottom: 16px; }
.stat-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 14px 16px;
}
.stat-label { color: #909399; font-size: 13px; }
.stat-value { margin-top: 6px; font-size: 20px; font-weight: 600; }
.hint { margin-top: 16px; color: #909399; font-size: 13px; }
h4 { margin: 0 0 8px; }
</style>
