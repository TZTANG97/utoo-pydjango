<template>
  <div class="page-wrap">
    <section class="table-panel">
      <div class="table-toolbar">
        <div class="toolbar-title">
          <span class="title-text">部门管理</span>
          <span class="title-meta">共 {{ nodeCount }} 个部门</span>
        </div>
        <el-button type="primary" @click="openCreate('0')">添加根部门</el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="rows"
        row-key="id"
        class="data-table"
        stripe
        default-expand-all
        :tree-props="{ children: 'children' }"
        :header-cell-style="{
          background: '#f3f6fb',
          color: '#3a4660',
          fontWeight: 600,
          borderBottom: '1px solid #e4ebf5',
        }"
      >
        <el-table-column label="部门名称" min-width="220">
          <template #default="{ row }">
            <span class="dept-name">{{ row.deptName || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="排序" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" round class="sort-tag">
              {{ row.deptSort ?? 0 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="电话" min-width="130">
          <template #default="{ row }">
            <span class="cell-muted">{{ row.deptPhone || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="地址" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="cell-muted">{{ row.deptAddress || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <div class="op-group">
              <el-button link type="primary" @click="openCreate(String(row.id))">
                添加子部门
              </el-button>
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="540px"
      destroy-on-close
      class="dept-dialog"
    >
      <div class="dialog-tip">
        {{ editingId ? '修改当前部门信息' : parentId === '0' ? '将创建一级根部门' : '将在所选部门下新增子部门' }}
      </div>
      <el-form label-width="90px" class="dept-form">
        <el-form-item label="部门名称" required>
          <el-input v-model="form.deptName" placeholder="请输入部门名称" maxlength="50" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.deptSort" :min="0" controls-position="right" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.deptPhone" placeholder="选填" />
        </el-form-item>
        <el-form-item label="传真">
          <el-input v-model="form.deptFax" placeholder="选填" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.deptAddress" placeholder="选填" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.deptDesc" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { addDept, deleteDept, fetchDeptTree, updateDept } from '@admin/api/system'
import { isAjaxOk } from '@admin/utils/request'

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

function countNodes(list: Record<string, unknown>[]): number {
  let n = 0
  for (const item of list) {
    n += 1
    const children = item.children
    if (Array.isArray(children) && children.length) {
      n += countNodes(children as Record<string, unknown>[])
    }
  }
  return n
}

const nodeCount = computed(() => countNodes(rows.value))

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

<style scoped lang="scss">
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.table-panel {
  background: #fff;
  border: 1px solid #e8eef6;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(31, 45, 61, 0.04);
  padding: 14px 16px 16px;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eef2f8;
}

.toolbar-title {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.title-text {
  font-size: 15px;
  font-weight: 600;
  color: #24324a;
}

.title-meta {
  font-size: 12px;
  color: #8a95a8;
}

.data-table {
  --el-table-border-color: #eef2f8;
  --el-table-row-hover-bg-color: #f5f9ff;

  :deep(.el-table__inner-wrapper::before) {
    display: none;
  }

  :deep(.el-table__expand-icon) {
    color: #5b7cba;
  }

  :deep(.el-table__indent) {
    padding-left: 14px;
  }
}

.dept-name {
  color: #24324a;
  font-weight: 600;
}

.cell-muted {
  color: #6b768a;
  font-size: 13px;
}

.sort-tag {
  --el-tag-bg-color: #f0f4fa;
  --el-tag-border-color: #dce5f2;
  --el-tag-text-color: #4d5d78;
  min-width: 36px;
  justify-content: center;
}

.op-group {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 2px;
}

.dialog-tip {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 8px;
  background: linear-gradient(120deg, #f4f8ff 0%, #fff8ef 100%);
  border: 1px solid #e8eef6;
  color: #5b6780;
  font-size: 13px;
}

.dept-form {
  :deep(.el-form-item__label) {
    color: #5b6780;
    font-weight: 500;
  }

  :deep(.el-input-number) {
    width: 160px;
  }
}
</style>
