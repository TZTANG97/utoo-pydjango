<template>
  <admin-page-card title="类型管理">
    <div class="tab-row">
      <el-button type="primary">管理</el-button>
      <el-button @click="openCreate">新增</el-button>
    </div>
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="类型名称">
        <el-input v-model="filters.name" clearable placeholder="类型名称" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload()">搜索</el-button>
      </el-form-item>
    </el-form>
    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="sequence" label="排序" width="90" align="center" />
      <el-table-column prop="name" label="类型名称" min-width="180" />
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
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑类型' : '新增类型'" width="640px">
      <el-form label-width="90px">
        <el-form-item label="类型名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sequence" :min="0" />
        </el-form-item>
        <el-form-item label="关联规格">
          <el-select v-model="form.specIds" multiple filterable collapse-tags style="width: 100%">
            <el-option v-for="item in specOptions" :key="String(item.id)" :label="String(item.name)" :value="Number(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联品牌">
          <el-select v-model="form.brandIds" multiple filterable collapse-tags style="width: 100%">
            <el-option v-for="item in brandOptions" :key="String(item.id)" :label="String(item.name)" :value="Number(item.id)" />
          </el-select>
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
import {
  deleteGoodsType,
  fetchGoodsTypeList,
  fetchGoodsTypeOptions,
  getGoodsTypeDetail,
  saveGoodsType,
} from '@/api/ops'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const filters = reactive({ name: '' })
const dialogVisible = ref(false)
const saving = ref(false)
const specOptions = ref<Record<string, unknown>[]>([])
const brandOptions = ref<Record<string, unknown>[]>([])
const form = reactive({
  id: undefined as number | undefined,
  name: '',
  sequence: 0,
  specIds: [] as number[],
  brandIds: [] as number[],
})

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchGoodsTypeList({ ...params, name: filters.name })
)

function reload() {
  pagination.page = 1
  return load({ name: filters.name })
}

function openCreate() {
  Object.assign(form, { id: undefined, name: '', sequence: 0, specIds: [], brandIds: [] })
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getGoodsTypeDetail(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  Object.assign(form, {
    id: Number(obj.id),
    name: String(obj.name || ''),
    sequence: Number(obj.sequence || 0),
    specIds: ((obj.specIds as number[]) || []).map(Number),
    brandIds: ((obj.brandIds as number[]) || []).map(Number),
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入类型名称')
    return
  }
  saving.value = true
  try {
    const res = await saveGoodsType({
      id: form.id,
      name: form.name.trim(),
      sequence: form.sequence,
      specIds: form.specIds,
      brandIds: form.brandIds,
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
  await ElMessageBox.confirm('确认删除该类型？', '提示', { type: 'warning' })
  const res = await deleteGoodsType(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

onMounted(async () => {
  await reload()
  const res = await fetchGoodsTypeOptions()
  if (isAjaxOk(res) && res.obj) {
    const obj = res.obj as Record<string, unknown>
    specOptions.value = (obj.specs as Record<string, unknown>[]) || []
    brandOptions.value = (obj.brands as Record<string, unknown>[]) || []
  }
})
</script>

<style scoped lang="scss">
.tab-row { margin-bottom: 12px; }
.filter-form { margin-bottom: 12px; }
.pager { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
