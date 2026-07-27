<template>
  <admin-page-card title="订单类型管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">添加订单类型</el-button>
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
      <el-table-column prop="type_sort" label="类型编号" width="120" />
      <el-table-column prop="type_name" label="类型名称" min-width="160" />
      <el-table-column prop="type_desc" label="备注" min-width="200" show-overflow-tooltip />
      <el-table-column label="操作" width="180" fixed="right">
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
      <el-form label-width="110px">
        <el-form-item label="类型编号">
          <el-input-number v-model="form.type_sort" :min="0" />
        </el-form-item>
        <el-form-item label="订单类型名称">
          <el-input v-model="form.type_name" placeholder="至少 3 个字符" />
        </el-form-item>
        <el-form-item label="订单类型">
          <el-select v-model="form.table_id" placeholder="请选择" filterable style="width: 100%">
            <el-option
              v-for="item in tableOptions"
              :key="String(item.id)"
              :label="String(item.table_name || item.name || item.id)"
              :value="Number(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.type_desc" type="textarea" :rows="3" />
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
  deleteOrderType,
  fetchOrderTypeList,
  fetchOrderTypeTables,
  submitOrderType,
  updateOrderType,
} from '@admin/api/order-settings'
import { useDataTable } from '@admin/composables/useDataTable'
import { isAjaxOk } from '@admin/utils/request'

const keyword = ref('')
const { loading, rows, total, pagination, load } = useDataTable(fetchOrderTypeList)
const tableOptions = ref<Record<string, unknown>[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  type_sort: 0,
  type_name: '',
  type_desc: '',
  table_id: undefined as number | undefined,
})

const dialogTitle = computed(() => (editingId.value ? '编辑订单类型' : '添加订单类型'))

onMounted(async () => {
  await reload()
  const res = await fetchOrderTypeTables()
  if (isAjaxOk(res)) {
    tableOptions.value = Array.isArray(res.obj) ? (res.obj as Record<string, unknown>[]) : []
  }
})

function reload() {
  return load({ type_name: keyword.value.trim() })
}

function resetForm() {
  editingId.value = null
  form.type_sort = 0
  form.type_name = ''
  form.type_desc = ''
  form.table_id = undefined
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = Number(row.id)
  form.type_sort = Number(row.type_sort || 0)
  form.type_name = String(row.type_name || '')
  form.type_desc = String(row.type_desc || '')
  form.table_id = row.table_id ? Number(row.table_id) : undefined
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.type_name.trim() || form.type_name.trim().length < 3) {
    ElMessage.warning('订单类型名称至少 3 个字符')
    return
  }
  if (!form.table_id) {
    ElMessage.warning('请选择订单类型')
    return
  }
  saving.value = true
  try {
    const payload = { ...form, type_name: form.type_name.trim() }
    const res = editingId.value
      ? await updateOrderType({ ...payload, id: editingId.value })
      : await submitOrderType(payload)
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
  await ElMessageBox.confirm('确定删除该订单类型吗？', '提示', { type: 'warning' })
  const res = await deleteOrderType(String(row.id))
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
