<template>
  <admin-page-card title="系统操作日志">
    <el-form :inline="true" class="filter-form" @submit.prevent="reload">
      <el-form-item label="关键词">
        <el-input
          v-model="filters.keyword"
          clearable
          placeholder="用户名 / 内容"
          style="width: 200px"
        />
      </el-form-item>
      <el-form-item label="起始时间">
        <el-date-picker
          v-model="filters.addTime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="起始日期"
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" label="#" align="center" />
      <el-table-column prop="addTime" label="操作时间" width="170" />
      <el-table-column prop="userName" label="操作人" width="120" />
      <el-table-column prop="loginName" label="账号" width="120" />
      <el-table-column prop="content" label="操作内容" min-width="220" show-overflow-tooltip />
      <el-table-column prop="ip" label="IP" width="130" />
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50]"
        layout="sizes, total, prev, pager, next"
        :total="total"
        @size-change="reload"
        @current-change="() => load(listParams())"
      />
    </div>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchSysLogs } from '@/api/auth'
import { useDataTable } from '@/composables/useDataTable'

const filters = reactive({
  keyword: '',
  addTime: '',
})

function listParams() {
  return {
    userName: filters.keyword.trim(),
    addTime: filters.addTime || '',
  }
}

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchSysLogs({ ...params, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

onMounted(() => reload())
</script>

<style scoped>
.filter-form {
  margin-bottom: 12px;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
