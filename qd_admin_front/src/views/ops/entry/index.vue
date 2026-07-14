<template>
  <admin-page-card title="帖子列表管理">
    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column prop="addTime" label="创建时间" min-width="160" />
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="userName" label="用户名" width="140" />
      <el-table-column label="是否显示" width="100" align="center">
        <template #default="{ row }">
          {{ Number(row.isAudit) === 1 ? '上架' : '下架' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button link type="primary" @click="handleAudit(row)">
            {{ Number(row.isAudit) === 1 ? '下架' : '上架' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="() => load()"
      />
    </div>

    <el-dialog v-model="detailVisible" title="帖子详情" width="720px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="标题">{{ detail.title }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ detail.userName }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detail.addTime }}</el-descriptions-item>
        <el-descriptions-item label="内容">
          <div class="content" v-html="String(detail.content || '')" />
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { auditEntry, fetchEntryList, getEntryDetail } from '@/api/ops'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const { loading, rows, total, pagination, load } = useDataTable(fetchEntryList)
const detailVisible = ref(false)
const detail = reactive<Record<string, unknown>>({})

onMounted(() => load())

async function openDetail(row: Record<string, unknown>) {
  const res = await getEntryDetail(String(row.id))
  if (isAjaxOk(res) && res.obj) {
    Object.assign(detail, res.obj as Record<string, unknown>)
    detailVisible.value = true
  } else {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
  }
}

async function handleAudit(row: Record<string, unknown>) {
  const res = await auditEntry(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('操作成功')
    await load()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.content {
  max-height: 360px;
  overflow: auto;
  white-space: pre-wrap;
}
</style>
