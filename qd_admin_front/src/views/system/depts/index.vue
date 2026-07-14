<template>
  <admin-page-card title="部门管理">
    <template #actions>
      <el-button type="primary" @click="openCreate('0')">添加根部门</el-button>
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
      <el-table-column prop="deptName" label="部门名称" min-width="200" />
      <el-table-column prop="deptSort" label="排序" width="80" />
      <el-table-column prop="deptPhone" label="电话" min-width="120" />
      <el-table-column prop="deptAddress" label="地址" min-width="180" show-overflow-tooltip />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openCreate(String(row.id))">添加子部门</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form label-width="90px">
        <el-form-item label="部门名称">
          <el-input v-model="form.deptName" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.deptSort" :min="0" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.deptPhone" />
        </el-form-item>
        <el-form-item label="传真">
          <el-input v-model="form.deptFax" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.deptAddress" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.deptDesc" type="textarea" :rows="2" />
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
import { addDept, deleteDept, fetchDeptTree, updateDept } from '@/api/system'
import { isAjaxOk } from '@/utils/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref<Record<string, unknown>[]>([])
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const parentId = ref('0')
const form = reactive({
  deptName: '',
  deptSort: 0,
  deptPhone: '',
  deptFax: '',
  deptAddress: '',
  deptDesc: '',
})

const dialogTitle = computed(() => (editingId.value ? '编辑部门' : '添加部门'))

async function load() {
  loading.value = true
  try {
    rows.value = await fetchDeptTree()
  } finally {
    loading.value = false
  }
}

onMounted(() => load())

function resetForm() {
  form.deptName = ''
  form.deptSort = 0
  form.deptPhone = ''
  form.deptFax = ''
  form.deptAddress = ''
  form.deptDesc = ''
}

function openCreate(superId: string) {
  editingId.value = null
  parentId.value = superId
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  parentId.value = String(row.superId || '0')
  form.deptName = String(row.deptName || '')
  form.deptSort = Number(row.deptSort || 0)
  form.deptPhone = String(row.deptPhone || '')
  form.deptFax = String(row.deptFax || '')
  form.deptAddress = String(row.deptAddress || '')
  form.deptDesc = String(row.deptDesc || '')
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.deptName.trim()) {
    ElMessage.warning('请填写部门名称')
    return
  }
  saving.value = true
  try {
    const payload = { ...form, deptName: form.deptName.trim(), superId: parentId.value }
    const res = editingId.value
      ? await updateDept({ ...payload, id: editingId.value })
      : await addDept(payload)
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
  await ElMessageBox.confirm('确定删除该部门吗？', '提示', { type: 'warning' })
  const res = await deleteDept(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await load()
  } else {
    ElMessage.error('删除失败')
  }
}
</script>
