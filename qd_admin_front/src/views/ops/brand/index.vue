<template>
  <admin-page-card title="品牌管理">
    <div class="tab-row">
      <el-button type="primary">管理</el-button>
      <el-button @click="openCreate">新增</el-button>
    </div>
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="品牌名称">
        <el-input v-model="filters.name" clearable placeholder="品牌名称" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload()">搜索</el-button>
      </el-form-item>
    </el-form>
    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="sequence" label="排序" width="90" align="center" />
      <el-table-column prop="firstWord" label="首字母" width="90" align="center" />
      <el-table-column prop="name" label="品牌名称" min-width="160" />
      <el-table-column prop="addTime" label="创建时间" width="170" />
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
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑品牌' : '新增品牌'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="品牌名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="首字母">
          <el-input v-model="form.firstWord" maxlength="1" style="width: 120px" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sequence" :min="0" />
        </el-form-item>
        <el-form-item label="英文名">
          <el-input v-model="form.enName" />
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
import AdminPageCard from '@/components/AdminPageCard.vue'
import { deleteBrand, fetchBrandList, getBrandDetail, saveBrand } from '@/api/ops'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const filters = reactive({ name: '' })
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  id: undefined as number | undefined,
  name: '',
  firstWord: '',
  sequence: 0,
  enName: '',
})

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchBrandList({ ...params, name: filters.name })
)

function reload() {
  pagination.page = 1
  return load({ name: filters.name })
}

function openCreate() {
  Object.assign(form, { id: undefined, name: '', firstWord: '', sequence: 0, enName: '' })
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getBrandDetail(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  Object.assign(form, {
    id: Number(obj.id),
    name: String(obj.name || ''),
    firstWord: String(obj.firstWord || obj.first_word || ''),
    sequence: Number(obj.sequence || 0),
    enName: String(obj.enName || obj.en_name || ''),
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入品牌名称')
    return
  }
  saving.value = true
  try {
    const res = await saveBrand({
      id: form.id,
      name: form.name.trim(),
      firstWord: form.firstWord.trim(),
      sequence: form.sequence,
      enName: form.enName.trim(),
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
  await ElMessageBox.confirm('是否要删除该品牌？', '提示', { type: 'warning' })
  const res = await deleteBrand(String(row.id))
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
