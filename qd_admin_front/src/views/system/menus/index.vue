<template>
  <admin-page-card title="菜单管理">
    <template #actions>
      <el-button type="primary" @click="openCreate('0')">添加根菜单</el-button>
    </template>

    <el-table
      v-loading="loading"
      :data="rows"
      row-key="id"
      border
      stripe
      default-expand-all
      :tree-props="{ children: 'children' }"
    >
      <el-table-column prop="menuName" label="菜单名称" min-width="180" />
      <el-table-column prop="menuSort" label="排序" width="70" />
      <el-table-column prop="menuUrl" label="URL" min-width="200" show-overflow-tooltip />
      <el-table-column prop="menuIcon" label="图标" width="100" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openCreate(String(row.id))">添加子菜单</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px">
      <el-form label-width="100px">
        <el-form-item label="菜单名称">
          <el-input v-model="form.menuName" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.menuSort" :min="0" />
        </el-form-item>
        <el-form-item label="URL">
          <el-input v-model="form.menuUrl" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.menuIcon" />
        </el-form-item>
        <el-form-item label="打开方式">
          <el-input v-model="form.menuTarget" placeholder="navTab" />
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
import AdminPageCard from '@/components/AdminPageCard.vue'
import { addMenu, deleteMenu, fetchMenuTree, updateMenu } from '@/api/system'
import { isAjaxOk } from '@/utils/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref<Record<string, unknown>[]>([])
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const parentId = ref('0')
const form = reactive({
  menuName: '',
  menuSort: 0,
  menuUrl: '',
  menuIcon: '',
  menuTarget: 'navTab',
})

const dialogTitle = computed(() => (editingId.value ? '编辑菜单' : '添加菜单'))

async function load() {
  loading.value = true
  try {
    rows.value = await fetchMenuTree()
  } finally {
    loading.value = false
  }
}

onMounted(() => load())

function resetForm() {
  form.menuName = ''
  form.menuSort = 0
  form.menuUrl = ''
  form.menuIcon = ''
  form.menuTarget = 'navTab'
}

function openCreate(superId: string) {
  editingId.value = null
  parentId.value = superId
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  parentId.value = String(row.menuSuperId || '0')
  form.menuName = String(row.menuName || '')
  form.menuSort = Number(row.menuSort || 0)
  form.menuUrl = String(row.menuUrl || '')
  form.menuIcon = String(row.menuIcon || '')
  form.menuTarget = String(row.menuTarget || 'navTab')
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.menuName.trim()) {
    ElMessage.warning('请填写菜单名称')
    return
  }
  saving.value = true
  try {
    const payload = { ...form, menuName: form.menuName.trim(), menuSuperId: parentId.value }
    const res = editingId.value
      ? await updateMenu({ ...payload, id: editingId.value })
      : await addMenu(payload)
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await load()
      return
    }
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该菜单吗？', '提示', { type: 'warning' })
  const res = await deleteMenu(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await load()
  } else {
    ElMessage.error('删除失败')
  }
}
</script>
