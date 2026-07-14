<template>
  <admin-page-card title="实验室销售人员绩效">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="请选择人员">
        <el-select
          v-model="userId"
          filterable
          placeholder="请选择"
          style="width: 240px"
          @change="load"
        >
          <el-option
            v-for="item in users"
            :key="String(item.id)"
            :label="userLabel(item)"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="请选择年份">
        <el-date-picker
          v-model="year"
          type="year"
          value-format="YYYY"
          style="width: 140px"
          @change="load"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="load">查询</el-button>
      </el-form-item>
    </el-form>

    <div v-loading="loading" class="tables">
      <el-table :data="orderRows" border stripe>
        <el-table-column prop="monthLabel" :label="`${displayName}订单`" min-width="120" />
        <el-table-column prop="mbyj" label="目标业绩" min-width="120" />
        <el-table-column prop="sjyj" label="实际业绩" min-width="120" />
        <el-table-column prop="dclText" label="达成率" min-width="120" />
      </el-table>

      <el-table :data="invoiceRows" border stripe>
        <el-table-column prop="monthLabel" :label="`${displayName}开票`" min-width="120" />
        <el-table-column prop="mbyj" label="目标业绩" min-width="120" />
        <el-table-column prop="sjyj" label="实际业绩" min-width="120" />
        <el-table-column prop="dclText" label="达成率" min-width="120" />
      </el-table>

      <el-table :data="receiptRows" border stripe>
        <el-table-column prop="monthLabel" :label="`${displayName}收款`" min-width="120" />
        <el-table-column prop="mbyj" label="目标业绩" min-width="120" />
        <el-table-column prop="sjyj" label="实际业绩" min-width="120" />
        <el-table-column prop="dclText" label="达成率" min-width="120" />
      </el-table>
    </div>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchLabSalePerf, fetchLabSaleUsers } from '@/api/digital'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const MONTH_CN = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']

const loading = ref(false)
const year = ref(String(new Date().getFullYear()))
const userId = ref('')
const users = ref<Record<string, unknown>[]>([])
const displayName = ref('')
const orderRows = ref<Record<string, unknown>[]>([])
const invoiceRows = ref<Record<string, unknown>[]>([])
const receiptRows = ref<Record<string, unknown>[]>([])

function userLabel(item: Record<string, unknown>) {
  const name = String(item.userName || '')
  const trueName = String(item.trueName || '')
  return trueName ? `${name} ${trueName}` : name
}

function normalizeRows(list: Record<string, unknown>[]) {
  return MONTH_CN.map((label, idx) => {
    const row = list[idx] || {}
    return {
      monthLabel: label,
      mbyj: Number(row.mbyj ?? 0),
      sjyj: Number(row.sjyj ?? 0),
      dclText: `${Number(row.dcl ?? 0)}%`,
    }
  })
}

async function loadUsers() {
  const res = await fetchLabSaleUsers()
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    users.value = res.obj as Record<string, unknown>[]
    if (!userId.value && users.value.length) {
      userId.value = String(users.value[0].id)
      displayName.value = String(users.value[0].trueName || users.value[0].userName || '')
    }
  }
}

async function load() {
  if (!userId.value) {
    ElMessage.warning('请选择人员')
    return
  }
  loading.value = true
  try {
    const res = await fetchLabSalePerf({ year: year.value, user_id: userId.value })
    if (!isAjaxOk(res) || !res.obj) {
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    displayName.value = String(obj.trueName || obj.userName || '')
    if (!displayName.value) {
      const hit = users.value.find((u) => String(u.id) === userId.value)
      displayName.value = hit ? String(hit.trueName || hit.userName || '') : ''
    }
    orderRows.value = normalizeRows(
      Array.isArray(obj.resultList) ? (obj.resultList as Record<string, unknown>[]) : []
    )
    invoiceRows.value = normalizeRows(
      Array.isArray(obj.resultListkp) ? (obj.resultListkp as Record<string, unknown>[]) : []
    )
    receiptRows.value = normalizeRows(
      Array.isArray(obj.resultListsk) ? (obj.resultListsk as Record<string, unknown>[]) : []
    )
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadUsers()
  if (userId.value) await load()
})
</script>

<style scoped lang="scss">
.filter-form {
  margin-bottom: 12px;
}
.tables {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
