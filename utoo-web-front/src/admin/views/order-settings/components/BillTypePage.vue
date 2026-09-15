<template>
  <admin-page-card :title="title">
    <el-form :inline="true" @submit.prevent="handleAdd">
      <el-form-item label="名称">
        <el-input v-model="form.name" placeholder="请输入名称" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleAdd">添加</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="name" label="名称" min-width="220" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.deleteStatus ? 'info' : 'success'">
            {{ row.deleteStatus ? '已禁用' : '启用中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            link
            :type="row.deleteStatus ? 'success' : 'warning'"
            @click="toggleStatus(row)"
          >
            {{ row.deleteStatus ? '开启' : '禁用' }}
          </el-button>
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
        @current-change="reload"
      />
    </div>

    <el-dialog v-model="editVisible" title="修改名称" width="420px">
      <el-input v-model="editName" placeholder="名称" />
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleUpdate">保存</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  deleteBillType,
  fetchBillTypeList,
  submitBillType,
  updateBillType,
  updateBillTypeStatus,
} from '@admin/api/order-settings'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const props = defineProps<{ billType: number; title: string }>()

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchBillTypeList({ ...params, type: props.billType })
)
const saving = ref(false)
const form = reactive({ name: '' })
const editVisible = ref(false)
const editId = ref('')
const editName = ref('')

function reload() {
  return load({ type: props.billType })
}

onMounted(() => reload())
watch(() => props.billType, () => reload())

async function handleAdd() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写名称')
    return
  }
  saving.value = true
  try {
    const res = await submitBillType({ name: form.name.trim(), type: props.billType })
    if (isAjaxOk(res)) {
      ElMessage.success(res.resMsg || '添加成功')
      form.name = ''
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '名称已存在或保存失败'))
  } catch {
    // 网络异常由 request 拦截器提示
  } finally {
    saving.value = false
  }
}

function openEdit(row: Record<string, unknown>) {
  editId.value = String(row.id)
  editName.value = String(row.name || '')
  editVisible.value = true
}

async function handleUpdate() {
  saving.value = true
  try {
    const res = await updateBillType({ id: editId.value, name: editName.value.trim() })
    if (isAjaxOk(res) && !(res as { obj?: unknown }).obj) {
      ElMessage.success('修改成功')
      editVisible.value = false
      await reload()
      return
    }
    ElMessage.error(String((res as { obj?: unknown }).obj || ajaxErrorMessage(res, '修改失败')))
  } finally {
    saving.value = false
  }
}


async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该发票类型吗？删除后不可恢复。', '提示', { type: 'warning' })
  try {
    const res = await deleteBillType(String(row.id))
    if (isAjaxOk(res)) {
      ElMessage.success(res.resMsg || '删除成功')
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  } catch {
    // 取消确认或网络异常
  }
}

async function toggleStatus(row: Record<string, unknown>) {
  const status = row.deleteStatus ? '1' : '2'
  const ok = await updateBillTypeStatus(String(row.id), status as '1' | '2')
  if (ok) {
    ElMessage.success('操作成功')
    await reload()
  } else {
    ElMessage.error('操作失败')
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
