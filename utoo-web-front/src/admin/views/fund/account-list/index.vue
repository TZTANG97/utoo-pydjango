<template>
  <admin-page-card title="资金账户一览">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="用户名">
        <el-input v-model="filters.userName" clearable style="width: 160px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="userName" label="用户名" min-width="120" />
      <el-table-column prop="trueName" label="姓名" min-width="100" />
      <el-table-column prop="rmbAvailable" label="人民币可用" min-width="110" />
      <el-table-column prop="usdAvailable" label="美金可用" min-width="110" />
      <el-table-column prop="rmbFreezing" label="人民币冻结" min-width="110" />
      <el-table-column prop="usdFreezing" label="美金冻结" min-width="110" />
      <el-table-column prop="rmbIncome" label="人民币收益" min-width="110" />
      <el-table-column prop="usdIncome" label="美金收益" min-width="110" />
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">明细</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="load(filters)"
      />
    </div>

    <el-drawer v-model="drawerVisible" title="账户明细" size="480px">
      <el-table :data="detailRows" border size="small">
        <el-table-column label="币种" width="90">
          <template #default="{ row }">
            {{ Number(row.accountType) === 2 ? '美金' : '人民币' }}
          </template>
        </el-table-column>
        <el-table-column prop="availableBalance" label="可用余额" />
        <el-table-column prop="freezingBalance" label="冻结余额" />
        <el-table-column prop="incomeTotal" label="累计收益" />
      </el-table>
    </el-drawer>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { fetchAccountOverviewList, fetchUserAccountDetail, isAjaxOk } from '@admin/api/fund'
import { useDataTable } from '@admin/composables/useDataTable'

const filters = reactive({ userName: '' })
const drawerVisible = ref(false)
const detailRows = ref<Record<string, unknown>[]>([])

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchAccountOverviewList({ ...p, ...filters })
)

function reload() {
  pagination.page = 1
  load(filters)
}

onMounted(() => load(filters))

async function openDetail(row: Record<string, unknown>) {
  const res = await fetchUserAccountDetail(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(String(res.msg || '加载失败'))
    return
  }
  const obj = (res.obj as Record<string, unknown>) || {}
  detailRows.value = (obj.accounts as Record<string, unknown>[]) || []
  drawerVisible.value = true
}
</script>

<style scoped>
.filter-form { margin-bottom: 12px; }
.pager { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
