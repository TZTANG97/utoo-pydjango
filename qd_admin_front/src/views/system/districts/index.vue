<template>
  <admin-page-card title="行政区划管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">添加区划</el-button>
    </template>

    <el-breadcrumb separator="/" class="breadcrumb">
      <el-breadcrumb-item>
        <a href="#" @click.prevent="navigateTo('0')">根目录</a>
      </el-breadcrumb-item>
      <el-breadcrumb-item v-for="(item, index) in breadcrumbs" :key="item.id">
        <a
          v-if="index < breadcrumbs.length - 1"
          href="#"
          @click.prevent="navigateTo(item.id, index)"
        >
          {{ item.name }}
        </a>
        <span v-else>{{ item.name }}</span>
      </el-breadcrumb-item>
    </el-breadcrumb>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="disName" label="名称" min-width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="drillDown(row)">{{ row.disName }}</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="disSort" label="排序" width="80" />
      <el-table-column prop="disDesc" label="描述" min-width="180" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px">
      <el-form label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.disName" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.disSort" :min="0" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.disDesc" type="textarea" :rows="2" />
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
import { addDistrict, deleteDistrict, fetchDistrictList, updateDistrict } from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { isAjaxOk } from '@/utils/request'

interface Crumb {
  id: string
  name: string
}

const superId = ref('0')
const breadcrumbs = ref<Crumb[]>([])
const { loading, rows, total, pagination, load } = useDataTable(fetchDistrictList)
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const form = reactive({ disName: '', disSort: 0, disDesc: '' })

const dialogTitle = computed(() => (editingId.value ? '编辑区划' : '添加区划'))

onMounted(() => reload())

function reload() {
  return load({ superId: superId.value === '0' ? '' : superId.value })
}

function navigateTo(id: string, index?: number) {
  superId.value = id
  if (index != null) {
    breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
  } else {
    breadcrumbs.value = []
  }
  pagination.page = 1
  reload()
}

function drillDown(row: Record<string, unknown>) {
  const id = String(row.id)
  const name = String(row.disName || '')
  superId.value = id
  breadcrumbs.value.push({ id, name })
  pagination.page = 1
  reload()
}

function resetForm() {
  form.disName = ''
  form.disSort = 0
  form.disDesc = ''
}

function openCreate() {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  form.disName = String(row.disName || '')
  form.disSort = Number(row.disSort || 0)
  form.disDesc = String(row.disDesc || '')
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.disName.trim()) {
    ElMessage.warning('请填写名称')
    return
  }
  saving.value = true
  try {
    const payload = {
      disName: form.disName.trim(),
      disSort: form.disSort,
      disDesc: form.disDesc,
      superId: superId.value,
    }
    const res = editingId.value
      ? await updateDistrict({ ...payload, id: editingId.value })
      : await addDistrict(payload)
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
  await ElMessageBox.confirm('确定删除该区划吗？', '提示', { type: 'warning' })
  const res = await deleteDistrict(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
  } else {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped lang="scss">
.breadcrumb {
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
