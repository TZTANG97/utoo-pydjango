<template>
  <admin-page-card title="评论审核管理">
    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column prop="addTime" label="创建时间" min-width="160" />
      <el-table-column label="评论内容" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">{{ truncate(row.content, 15) }}</template>
      </el-table-column>
      <el-table-column prop="userName" label="用户名" width="140" />
      <el-table-column label="操作" width="200" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleAudit(row)">通过</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
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

    <el-dialog v-model="detailVisible" title="评论详情" width="560px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="评论日期">{{ detail.addTime }}</el-descriptions-item>
        <el-descriptions-item label="评论人">{{ detail.userName }}</el-descriptions-item>
        <el-descriptions-item label="用户评论内容">{{ detail.content }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { auditComment, deleteComment, fetchCommentList, getCommentDetail } from '@admin/api/ops'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const { loading, rows, total, pagination, load } = useDataTable(fetchCommentList)
const detailVisible = ref(false)
const detail = reactive<Record<string, unknown>>({})

function truncate(val: unknown, max: number) {
  const s = String(val || '')
  return s.length > max ? `${s.slice(0, max)}...` : s
}

onMounted(() => load())

async function openDetail(row: Record<string, unknown>) {
  const res = await getCommentDetail(String(row.id))
  if (isAjaxOk(res) && res.obj) {
    Object.assign(detail, res.obj as Record<string, unknown>)
    detailVisible.value = true
  } else {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
  }
}

async function handleAudit(row: Record<string, unknown>) {
  const res = await auditComment(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('审核通过')
    await load()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '审核失败'))
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该评论吗？', '提示', { type: 'warning' })
  const res = await deleteComment(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await load()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
