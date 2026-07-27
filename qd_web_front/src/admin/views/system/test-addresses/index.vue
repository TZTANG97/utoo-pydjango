<template>
  <admin-page-card title="测试地址管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">添加地址</el-button>
    </template>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="trueName" label="收件人" min-width="120" />
      <el-table-column prop="mobile" label="手机" min-width="120" />
      <el-table-column prop="address" label="地址" min-width="240" show-overflow-tooltip />
      <el-table-column prop="addTime" label="添加时间" min-width="160" />
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
        @current-change="load()"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form label-width="80px">
        <el-form-item label="收件人">
          <el-input v-model="form.trueName" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.mobile" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" type="textarea" :rows="3" />
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
  createTestAddress,
  deleteTestAddress,
  fetchTestAddressList,
  updateTestAddress,
} from '@admin/api/system'
import { useDataTable } from '@admin/composables/useDataTable'
import { isAjaxOk } from '@admin/utils/request'

const { loading, rows, total, pagination, load } = useDataTable(fetchTestAddressList)
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const form = reactive({ trueName: '', mobile: '', address: '' })

const dialogTitle = computed(() => (editingId.value ? '编辑地址' : '添加地址'))

onMounted(() => load())

function resetForm() {
  editingId.value = null
  form.trueName = ''
  form.mobile = ''
  form.address = ''
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  form.trueName = String(row.trueName || '')
  form.mobile = String(row.mobile || '')
  form.address = String(row.address || '')
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.trueName.trim() || !form.address.trim()) {
    ElMessage.warning('请填写收件人和地址')
    return
  }
  saving.value = true
  try {
    const payload = {
      trueName: form.trueName.trim(),
      mobile: form.mobile.trim(),
      address: form.address.trim(),
    }
    const res = editingId.value
      ? await updateTestAddress({ ...payload, id: editingId.value })
      : await createTestAddress(payload)
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
  await ElMessageBox.confirm('确定删除该地址吗？', '提示', { type: 'warning' })
  const res = await deleteTestAddress(String(row.id))
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
