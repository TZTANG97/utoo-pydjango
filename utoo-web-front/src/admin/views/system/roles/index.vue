<template>
  <admin-page-card title="角色管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">添加角色</el-button>
    </template>

    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="角色名称">
        <el-input v-model="keyword" placeholder="角色名称" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="roleName" label="角色名称" min-width="160" />
      <el-table-column prop="roleDesc" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="openPower(row)">菜单权限</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px">
      <el-form label-width="90px">
        <el-form-item label="角色名称">
          <el-input v-model="form.roleName" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.roleDesc" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="powerVisible" title="菜单权限" width="480px">
      <el-tree
        ref="treeRef"
        v-loading="powerLoading"
        :data="menuTree"
        show-checkbox
        node-key="id"
        default-expand-all
        :props="{ label: 'menuName', children: 'children' }"
      />
      <template #footer>
        <el-button @click="powerVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handlePowerSave">保存</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  addRole,
  deleteRole,
  fetchMenuTree,
  fetchRoleList,
  fetchRolePower,
  updateRole,
  updateRolePower,
} from '@admin/api/system'
import { useDataTable } from '@admin/composables/useDataTable'
import { isAjaxOk } from '@admin/utils/request'

const keyword = ref('')
const { loading, rows, total, pagination, load } = useDataTable(fetchRoleList)
const dialogVisible = ref(false)
const powerVisible = ref(false)
const powerLoading = ref(false)
const saving = ref(false)
const editingId = ref<string | null>(null)
const powerRoleId = ref('')
const menuTree = ref<Record<string, unknown>[]>([])
const treeRef = ref<{ setCheckedKeys: (keys: string[]) => void; getCheckedKeys: (leafOnly?: boolean) => string[]; getHalfCheckedKeys: () => string[] }>()
const form = reactive({ roleName: '', roleDesc: '' })

const dialogTitle = computed(() => (editingId.value ? '编辑角色' : '添加角色'))

onMounted(() => reload())

function reload() {
  return load({ roleName: keyword.value.trim() })
}

function resetForm() {
  editingId.value = null
  form.roleName = ''
  form.roleDesc = ''
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  form.roleName = String(row.roleName || '')
  form.roleDesc = String(row.roleDesc || '')
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.roleName.trim()) {
    ElMessage.warning('请填写角色名称')
    return
  }
  saving.value = true
  try {
    const payload = { roleName: form.roleName.trim(), roleDesc: form.roleDesc }
    const res = editingId.value
      ? await updateRole({ ...payload, id: editingId.value })
      : await addRole(payload)
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

async function openPower(row: Record<string, unknown>) {
  powerRoleId.value = String(row.id)
  powerVisible.value = true
  powerLoading.value = true
  try {
    const [tree, checked] = await Promise.all([
      fetchMenuTree(),
      fetchRolePower(powerRoleId.value),
    ])
    menuTree.value = tree
    await nextTick()
    treeRef.value?.setCheckedKeys(checked.map(String))
  } finally {
    powerLoading.value = false
  }
}

async function handlePowerSave() {
  const checked = treeRef.value?.getCheckedKeys(false) || []
  const half = treeRef.value?.getHalfCheckedKeys() || []
  const menuIds = [...checked, ...half]
  saving.value = true
  try {
    const res = await updateRolePower(powerRoleId.value, menuIds as (string | number)[])
    if (isAjaxOk(res)) {
      ElMessage.success('权限保存成功')
      powerVisible.value = false
      return
    }
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该角色吗？', '提示', { type: 'warning' })
  const res = await deleteRole(String(row.id))
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
