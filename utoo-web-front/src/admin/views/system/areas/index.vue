<template>
  <admin-page-card title="区域管理">
    <el-form :inline="true" @submit.prevent="handleAdd">
      <el-form-item label="区域名称">
        <el-input v-model="form.areaName" placeholder="区域名称" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleAdd">添加</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="areaName" label="区域名称" min-width="200" />
      <el-table-column prop="addTime" label="添加时间" min-width="160" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="load()"
      />
    </div>

    <el-dialog v-model="editVisible" title="修改区域" width="420px">
      <el-form label-width="90px">
        <el-form-item label="区域名称">
          <el-input v-model="editForm.areaName" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleUpdate">保存</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { deleteArea, fetchAreaList, submitArea, updateArea } from '@admin/api/system'
import { useDataTable } from '@admin/composables/useDataTable'
import { isAjaxOk } from '@admin/utils/request'

const { loading, rows, total, pagination, load } = useDataTable(fetchAreaList)
const saving = ref(false)
const form = reactive({ areaName: '' })
const editVisible = ref(false)
const editForm = reactive({ id: '', areaName: '' })

onMounted(() => load())

async function handleAdd() {
  if (!form.areaName.trim()) {
    ElMessage.warning('请填写区域名称')
    return
  }
  saving.value = true
  try {
    const res = await submitArea({ areaName: form.areaName.trim() })
    if (isAjaxOk(res)) {
      ElMessage.success('添加成功')
      form.areaName = ''
      await load()
      return
    }
    ElMessage.error('名称已存在或保存失败')
  } finally {
    saving.value = false
  }
}

function openEdit(row: Record<string, unknown>) {
  editForm.id = String(row.id)
  editForm.areaName = String(row.areaName || '')
  editVisible.value = true
}

async function handleUpdate() {
  if (!editForm.areaName.trim()) {
    ElMessage.warning('请填写区域名称')
    return
  }
  saving.value = true
  try {
    const res = await updateArea({ id: editForm.id, areaName: editForm.areaName.trim() })
    if (isAjaxOk(res)) {
      ElMessage.success('修改成功')
      editVisible.value = false
      await load()
      return
    }
    ElMessage.error('修改失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该区域吗？', '提示', { type: 'warning' })
  const res = await deleteArea(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await load()
  } else {
    ElMessage.error('删除失败')
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
