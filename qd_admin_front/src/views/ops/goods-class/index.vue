<template>
  <admin-page-card title="分类管理">
    <div class="tab-row">
      <el-button type="primary" @click="openCreate()">新增</el-button>
      <el-button @click="loadRoot">刷新</el-button>
    </div>
    <el-table
      v-loading="loading"
      :data="rows"
      border
      stripe
      row-key="id"
      lazy
      :load="loadChildren"
      :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
    >
      <el-table-column prop="sequence" label="排序" width="90" align="center" />
      <el-table-column prop="className" label="分类名称" min-width="200" />
      <el-table-column prop="goodsTypeName" label="类型" width="140" show-overflow-tooltip />
      <el-table-column label="显示" width="90" align="center">
        <template #default="{ row }">{{ Number(row.display) === 1 ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="240" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openCreate(row)">新增下级</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑分类' : '新增分类'" width="520px">
      <el-form label-width="100px">
        <el-form-item label="分类名称" required>
          <el-input v-model="form.className" />
        </el-form-item>
        <el-form-item label="上级分类">
          <el-input :model-value="parentLabel" disabled />
        </el-form-item>
        <el-form-item label="商品类型">
          <el-select v-model="form.goodsTypeId" clearable filterable style="width: 100%">
            <el-option
              v-for="item in typeOptions"
              :key="String(item.id)"
              :label="String(item.name)"
              :value="Number(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sequence" :min="0" />
        </el-form-item>
        <el-form-item label="显示">
          <el-switch v-model="form.display" :active-value="1" :inactive-value="0" />
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
  deleteGoodsClass,
  fetchGoodsClassList,
  fetchGoodsTypeOptions,
  getGoodsClassDetail,
  saveGoodsClass,
} from '@/api/ops'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref<Record<string, unknown>[]>([])
const typeOptions = ref<Record<string, unknown>[]>([])
const dialogVisible = ref(false)
const parentLabel = ref('顶级分类')
const form = reactive({
  id: undefined as number | undefined,
  className: '',
  parentId: undefined as number | undefined,
  goodsTypeId: undefined as number | undefined,
  sequence: 0,
  display: 1,
})

async function loadRoot() {
  loading.value = true
  try {
    const res = await fetchGoodsClassList(null)
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      rows.value = res.obj as Record<string, unknown>[]
    } else {
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    }
  } finally {
    loading.value = false
  }
}

async function loadChildren(
  row: Record<string, unknown>,
  _treeNode: unknown,
  resolve: (data: Record<string, unknown>[]) => void
) {
  const res = await fetchGoodsClassList(row.id as string | number)
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    resolve(res.obj as Record<string, unknown>[])
  } else {
    resolve([])
  }
}

function openCreate(parent?: Record<string, unknown>) {
  Object.assign(form, {
    id: undefined,
    className: '',
    parentId: parent ? Number(parent.id) : undefined,
    goodsTypeId: undefined,
    sequence: 0,
    display: 1,
  })
  parentLabel.value = parent ? String(parent.className || parent.id) : '顶级分类'
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getGoodsClassDetail(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  Object.assign(form, {
    id: Number(obj.id),
    className: String(obj.className || ''),
    parentId: obj.parentId ? Number(obj.parentId) : obj.parent_id ? Number(obj.parent_id) : undefined,
    goodsTypeId: obj.goodsTypeId
      ? Number(obj.goodsTypeId)
      : obj.goodsType_id
        ? Number(obj.goodsType_id)
        : undefined,
    sequence: Number(obj.sequence || 0),
    display: Number(obj.display) === 1 ? 1 : 0,
  })
  parentLabel.value = form.parentId ? `ID: ${form.parentId}` : '顶级分类'
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.className.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  saving.value = true
  try {
    const res = await saveGoodsClass({
      id: form.id,
      className: form.className.trim(),
      parentId: form.parentId,
      goodsTypeId: form.goodsTypeId,
      sequence: form.sequence,
      display: form.display,
    })
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await loadRoot()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
    }
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认删除该分类及其下级？', '提示', { type: 'warning' })
  const res = await deleteGoodsClass(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await loadRoot()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

onMounted(async () => {
  await loadRoot()
  const res = await fetchGoodsTypeOptions()
  if (isAjaxOk(res) && res.obj) {
    typeOptions.value = ((res.obj as Record<string, unknown>).types as Record<string, unknown>[]) || []
  }
})
</script>

<style scoped lang="scss">
.tab-row {
  margin-bottom: 12px;
}
</style>
