<template>
  <admin-page-card title="实验产品品牌">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="品牌名称">
        <el-input v-model="filters.name" clearable placeholder="品牌名称" style="width: 180px" />
      </el-form-item>
      <el-form-item label="创建时间">
        <el-date-picker
          v-model="filters.addTime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="创建时间"
          clearable
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">搜索</el-button>
      </el-form-item>
    </el-form>

    <el-alert
      class="tip-box"
      type="warning"
      show-icon
      :closable="false"
      title="友情提示"
    >
      <p>通过实验产品品牌管理，你可以进行查看、编辑、删除系统实验产品品牌</p>
      <p>设置品牌首字母，在品牌列表页通过首字母搜索品牌</p>
    </el-alert>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="sequence" label="排序" width="90" align="center" />
      <el-table-column prop="firstWord" label="首字母" width="90" align="center" />
      <el-table-column prop="name" label="品牌名称" min-width="220" show-overflow-tooltip />
      <el-table-column prop="addTime" label="创建时间" width="170" align="center" />
      <el-table-column label="操作" width="140" fixed="right" align="center">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <span class="op-sep">|</span>
          <el-button link type="primary" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50]"
        layout="sizes, total, prev, pager, next"
        :total="total"
        @size-change="reload"
        @current-change="() => load(listParams())"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑品牌' : '新增品牌'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="品牌名称" required>
          <el-input v-model="form.name" maxlength="40" placeholder="品牌名称" />
        </el-form-item>
        <el-form-item label="首字母">
          <el-input
            v-model="form.firstWord"
            maxlength="1"
            style="width: 120px"
            placeholder="A-Z"
            @input="onFirstWordInput"
          />
          <div class="form-tip">输入品牌首字母，在品牌列表页通过首字母查询</div>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sequence" :min="0" :controls="true" />
          <div class="form-tip">序号越小显示越靠前</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { deleteExpBrand, fetchExpBrandList, getExpBrand, saveExpBrand } from '@/api/experiment'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const filters = reactive({ name: '', addTime: '' })
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  id: undefined as number | undefined,
  name: '',
  firstWord: '',
  sequence: 0,
})

function listParams() {
  const p: Record<string, unknown> = {}
  if (filters.name) p.name = filters.name.trim()
  if (filters.addTime) p.addTime = filters.addTime
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchExpBrandList({ ...params, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

function onFirstWordInput(val: string) {
  form.firstWord = String(val || '')
    .replace(/[^a-zA-Z]/g, '')
    .slice(0, 1)
    .toUpperCase()
}

function openCreate() {
  Object.assign(form, { id: undefined, name: '', firstWord: '', sequence: 0 })
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getExpBrand(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  Object.assign(form, {
    id: Number(obj.id),
    name: String(obj.name || ''),
    firstWord: String(obj.firstWord || ''),
    sequence: Number(obj.sequence || 0),
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('品牌名称不能为空')
    return
  }
  saving.value = true
  try {
    const res = await saveExpBrand({
      id: form.id,
      name: form.name.trim(),
      firstWord: form.firstWord.trim(),
      sequence: form.sequence,
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
  const res = await deleteExpBrand(String(row.id))
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
.filter-form {
  margin-bottom: 12px;
}
.tip-box {
  margin-bottom: 16px;
  :deep(.el-alert__content) {
    p {
      margin: 2px 0;
      line-height: 1.5;
      color: var(--el-text-color-regular);
    }
  }
}
.op-sep {
  margin: 0 4px;
  color: var(--el-border-color);
}
.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
