<template>
  <admin-page-card title="实验室测试人员绩效">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="请选择年份">
        <el-date-picker
          v-model="year"
          type="year"
          value-format="YYYY"
          style="width: 160px"
          @change="load"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="load">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="trueName" label="姓名" width="110" fixed />
      <el-table-column prop="grccmb" label="个人产出目标" width="120" />
      <el-table-column label="月份" align="center">
        <el-table-column
          v-for="(m, idx) in months"
          :key="m"
          :label="m"
          width="86"
          align="right"
        >
          <template #default="{ row }">
            {{ Array.isArray(row.monthvalues) ? row.monthvalues[idx] : 0 }}
          </template>
        </el-table-column>
      </el-table-column>
      <el-table-column prop="sjcc" label="实际产出" width="110" align="right" />
      <el-table-column label="达成率" width="100" align="center">
        <template #default="{ row }">{{ Number(row.dcl ?? 0) }}%</template>
      </el-table-column>
      <el-table-column prop="pm" label="达成率排名" width="110" align="center" />
    </el-table>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchLabTestPerf } from '@/api/digital'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const loading = ref(false)
const year = ref(String(new Date().getFullYear()))
const rows = ref<Record<string, unknown>[]>([])
const months = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']

async function load() {
  loading.value = true
  try {
    const res = await fetchLabTestPerf(year.value)
    if (!isAjaxOk(res) || !res.obj) {
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    rows.value = Array.isArray(obj.resultList) ? (obj.resultList as Record<string, unknown>[]) : []
  } finally {
    loading.value = false
  }
}

onMounted(() => load())
</script>

<style scoped lang="scss">
.filter-form {
  margin-bottom: 12px;
}
</style>
