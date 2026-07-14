<template>
  <admin-page-card title="税率管理">
    <el-form :inline="true" @submit.prevent="handleAdd">
      <el-form-item label="税率名称">
        <el-input v-model="form.name" placeholder="税率名称" clearable />
      </el-form-item>
      <el-form-item label="税率比例">
        <el-input v-model="form.taxValue" placeholder="如 13 或 0.13" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleAdd">添加</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="name" label="税率名称" min-width="160" />
      <el-table-column label="税率值" min-width="120">
        <template #default="{ row }">{{ formatTaxDisplay(row.taxValue) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.delStatus ? 'info' : 'success'">
            {{ row.delStatus ? '已禁用' : '启用中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            link
            :type="row.delStatus ? 'success' : 'danger'"
            @click="toggleStatus(row)"
          >
            {{ row.delStatus ? '开启' : '禁用' }}
          </el-button>
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

    <el-dialog v-model="editVisible" title="修改税率" width="420px">
      <el-form label-width="90px">
        <el-form-item label="税率名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="税率比例">
          <el-input v-model="editForm.taxValue" placeholder="0-1 之间小数" />
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
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  fetchTaxList,
  formatTaxDisplay,
  normalizeTaxInput,
  submitTax,
  updateTax,
  updateTaxStatus,
} from '@/api/order-settings'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const { loading, rows, total, pagination, load } = useDataTable(fetchTaxList)
const saving = ref(false)
const form = reactive({ name: '', taxValue: '' })
const editVisible = ref(false)
const editForm = reactive({ id: '', name: '', taxValue: '' })

onMounted(() => load())

async function handleAdd() {
  if (!form.name.trim() || !form.taxValue) {
    ElMessage.warning('请填写税率名称和税率值')
    return
  }
  saving.value = true
  try {
    const ok = await submitTax({
      name: form.name.trim(),
      taxValue: normalizeTaxInput(form.taxValue),
    })
    if (ok) {
      ElMessage.success('添加成功')
      form.name = ''
      form.taxValue = ''
      await load()
      return
    }
    ElMessage.error('税率名称已存在或保存失败')
  } finally {
    saving.value = false
  }
}

function openEdit(row: Record<string, unknown>) {
  editForm.id = String(row.id)
  editForm.name = String(row.name || '')
  editForm.taxValue = String(row.taxValue ?? '')
  editVisible.value = true
}

async function handleUpdate() {
  saving.value = true
  try {
    const res = await updateTax({
      id: editForm.id,
      name: editForm.name.trim(),
      taxValue: normalizeTaxInput(editForm.taxValue),
    })
    if (isAjaxOk(res) && !(res as { obj?: unknown }).obj) {
      ElMessage.success('修改成功')
      editVisible.value = false
      await load()
      return
    }
    ElMessage.error(String((res as { obj?: unknown }).obj || ajaxErrorMessage(res, '修改失败')))
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: Record<string, unknown>) {
  const status = row.delStatus ? '1' : '2'
  const ok = await updateTaxStatus(String(row.id), status as '1' | '2')
  if (ok) {
    ElMessage.success('操作成功')
    await load()
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
