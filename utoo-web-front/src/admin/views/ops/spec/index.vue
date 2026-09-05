<template>
  <admin-page-card title="规格管理">
    <div class="tab-row">
      <el-button type="primary">管理</el-button>
      <el-button @click="openCreate">新增</el-button>
    </div>
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="规格名称">
        <el-input v-model="filters.name" clearable placeholder="规格名称" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload()">搜索</el-button>
      </el-form-item>
    </el-form>
    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="sequence" label="排序" width="90" align="center" />
      <el-table-column prop="name" label="规格名称" min-width="140" />
      <el-table-column prop="propertyValues" label="规格值" min-width="220" show-overflow-tooltip />
      <el-table-column label="操作" width="140" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="() => load({ name: filters.name })"
      />
    </div>
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑规格' : '新增规格'" width="560px">
      <el-form label-width="90px">
        <el-form-item label="规格名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sequence" :min="0" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type" style="width: 160px">
            <el-option label="文字" value="text" />
            <el-option label="图片" value="img" />
          </el-select>
        </el-form-item>
        <el-form-item label="规格值">
          <el-input
            v-model="form.propertyText"
            type="textarea"
            :rows="3"
            placeholder="多个规格值用英文逗号分隔，如：红色,蓝色,绿色"
          />
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { deleteSpec, fetchSpecList, getSpecDetail, saveSpec } from '@admin/api/ops'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const filters = reactive({ name: '' })
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  id: undefined as number | undefined,
  name: '',
  sequence: 0,
  type: 'text',
  propertyText: '',
})

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchSpecList({ ...params, name: filters.name })
)

function reload() {
  pagination.page = 1
  return load({ name: filters.name })
}

function openCreate() {
  Object.assign(form, { id: undefined, name: '', sequence: 0, type: 'text', propertyText: '' })
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getSpecDetail(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  const props = (obj.properties as Array<Record<string, unknown>>) || []
  Object.assign(form, {
    id: Number(obj.id),
    name: String(obj.name || ''),
    sequence: Number(obj.sequence || 0),
    type: String(obj.type || 'text'),
    propertyText: props.map((p) => p.value).filter(Boolean).join(','),
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入规格名称')
    return
  }
  saving.value = true
  try {
    const properties = form.propertyText
      .split(',')
      .map((v, i) => ({ value: v.trim(), sequence: i }))
      .filter((p) => p.value)
    const res = await saveSpec({
      id: form.id,
      name: form.name.trim(),
      sequence: form.sequence,
      type: form.type,
      properties,
    })
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await reload()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
    }
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认删除该规格？', '提示', { type: 'warning' })
  const res = await deleteSpec(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

onMounted(() => reload())
</script>

<style scoped lang="scss">
.tab-row { margin-bottom: 12px; }
.filter-form { margin-bottom: 12px; }
.pager { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
