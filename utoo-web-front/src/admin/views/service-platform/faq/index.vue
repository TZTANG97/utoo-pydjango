<template>
  <admin-page-card title="常见问题管理">
    <el-form :inline="true" class="filter-form" @submit.prevent="reload">
      <el-form-item label="常见问题">
        <el-input
          v-model="filters.problem_description"
          clearable
          placeholder="常见问题"
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item label="关键字">
        <el-input
          v-model="filters.keywords"
          clearable
          placeholder="关键字"
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item label="点击量">
        <el-select v-model="filters.hits" style="width: 120px">
          <el-option label="正序" value="" />
          <el-option label="倒序" value="2" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <div class="toolbar">
      <el-button type="primary" @click="openCreate">新增</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column
        prop="problemDescription"
        label="常见问题"
        min-width="220"
        show-overflow-tooltip
      />
      <el-table-column prop="keywords" label="关键字" min-width="160" show-overflow-tooltip />
      <el-table-column prop="hits" label="点击量" width="100" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="() => load({ ...filters })"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑常见问题' : '创建常见问题'"
      width="640px"
      append-to-body
      destroy-on-close
    >
      <el-form label-width="100px">
        <el-form-item label="常见问题" required>
          <el-input v-model="form.problemDescription" placeholder="请输入常见问题" />
        </el-form-item>
        <el-form-item label="关键字" required>
          <el-input v-model="form.keywords" placeholder="请输入关键字" />
        </el-form-item>
        <el-form-item label="点击量" required>
          <el-input-number v-model="form.hits" :min="0" :controls="true" />
        </el-form-item>
        <el-form-item label="问题答案">
          <el-input
            v-model="form.problemAnswer"
            type="textarea"
            :rows="8"
            placeholder="请输入问题答案"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">
          {{ isEdit ? '编辑' : '保存' }}
        </el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onActivated, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { deleteFaq, editFaq, fetchFaqList, submitFaq } from '@admin/api/service-platform'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const filters = reactive({
  problem_description: '',
  keywords: '',
  hits: '',
})

const { loading, rows, total, pagination, load } = useDataTable(fetchFaqList)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = reactive({
  id: '',
  problemDescription: '',
  keywords: '',
  hits: 0,
  problemAnswer: '',
})

function reload() {
  pagination.page = 1
  return load({ ...filters })
}

onMounted(() => load({ ...filters }))

function resetForm() {
  form.id = ''
  form.problemDescription = ''
  form.keywords = ''
  form.hits = 0
  form.problemAnswer = ''
}

function openCreate() {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  form.id = String(row.id)
  form.problemDescription = String(row.problemDescription || '')
  form.keywords = String(row.keywords || '')
  form.hits = Number(row.hits || 0)
  form.problemAnswer = String(row.problemAnswer || '')
  isEdit.value = true
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.problemDescription.trim()) {
    ElMessage.warning('问题不能为空')
    return
  }
  if (!form.keywords.trim()) {
    ElMessage.warning('关键字不能为空')
    return
  }
  if (form.hits === null || form.hits === undefined || Number.isNaN(Number(form.hits))) {
    ElMessage.warning('点击量不能为空或填写错误')
    return
  }
  saving.value = true
  try {
    // 对齐 Java 表单字段名 + 新站 camelCase，确保网关 form/JSON 都能取到
    const payload = {
      name: form.problemDescription.trim(),
      enname: form.keywords.trim(),
      sequence: form.hits,
      project_details: form.problemAnswer || '',
      problemDescription: form.problemDescription.trim(),
      keywords: form.keywords.trim(),
      hits: form.hits,
      problemAnswer: form.problemAnswer || '',
    }
    const res = isEdit.value
      ? await editFaq({ id: form.id, ...payload })
      : await submitFaq(payload)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    dialogVisible.value = false
    ElMessage.success(isEdit.value ? '修改成功' : '保存成功')
    pagination.page = 1
    await load({ ...filters })
  } catch {
    // 网络异常由 request 拦截器提示
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('请确认是否删除？', '提示', { type: 'warning' })
  try {
    const res = await deleteFaq(String(row.id))
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '删除失败'))
      return
    }
    ElMessage.success('删除成功')
    await load({ ...filters })
  } catch {
    // 网络异常由 request 拦截器提示
  }
}

onActivated(() => {
  load({ ...filters })
})
</script>

<style scoped lang="scss">
.filter-form {
  margin-bottom: 8px;
}

.toolbar {
  margin-bottom: 12px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
