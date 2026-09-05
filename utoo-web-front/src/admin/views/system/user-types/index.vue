<template>
  <admin-page-card title="用户类型管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">添加类型</el-button>
    </template>

    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="类型名称">
        <el-input v-model="keyword" placeholder="类型名称" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="typeName" label="类型名称" min-width="140" />
      <el-table-column prop="typeSort" label="排序" width="80" />
      <el-table-column prop="typeDesc" label="描述" min-width="180" show-overflow-tooltip />
      <el-table-column prop="roleName" label="关联角色" min-width="120" />
      <el-table-column label="操作" width="160" fixed="right">
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
        @current-change="reload"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form label-width="100px">
        <el-form-item label="类型名称">
          <el-input v-model="form.typeName" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input v-model="form.typeSort" />
        </el-form-item>
        <el-form-item label="关联角色">
          <el-select v-model="form.roleId" clearable filterable style="width: 100%">
            <el-option
              v-for="item in roleOptions"
              :key="String(item.id)"
              :label="String(item.name || item.id)"
              :value="Number(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.typeDesc" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  addUserType,
  deleteUserType,
  fetchTypeRoleOptions,
  fetchUserTypeList,
  updateUserType,
} from '@admin/api/system'
import { useDataTable } from '@admin/composables/useDataTable'
import { isAjaxOk } from '@admin/utils/request'

const keyword = ref('')
const roleOptions = ref<Record<string, unknown>[]>([])
const { loading, rows, total, pagination, load } = useDataTable(fetchUserTypeList)
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const form = reactive({
  typeName: '',
  typeSort: '0',
  typeDesc: '',
  roleId: undefined as number | undefined,
})

const dialogTitle = computed(() => (editingId.value ? '编辑用户类型' : '添加用户类型'))

onMounted(async () => {
  roleOptions.value = await fetchTypeRoleOptions()
  await reload()
})

function reload() {
  return load({ typeName: keyword.value.trim() })
}

function resetForm() {
  editingId.value = null
  form.typeName = ''
  form.typeSort = '0'
  form.typeDesc = ''
  form.roleId = undefined
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  form.typeName = String(row.typeName || '')
  form.typeSort = String(row.typeSort ?? '0')
  form.typeDesc = String(row.typeDesc || '')
  form.roleId = row.roleId ? Number(row.roleId) : undefined
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.typeName.trim()) {
    ElMessage.warning('请填写类型名称')
    return
  }
  saving.value = true
  try {
    const payload = {
      typeName: form.typeName.trim(),
      typeSort: form.typeSort,
      typeDesc: form.typeDesc,
      roleId: form.roleId || undefined,
    }
    const res = editingId.value
      ? await updateUserType({ ...payload, id: editingId.value })
      : await addUserType(payload)
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await reload()
      return
    }
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该类型吗？', '提示', { type: 'warning' })
  const res = await deleteUserType(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
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
