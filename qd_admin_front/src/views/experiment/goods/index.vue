<template>
  <admin-page-card title="实验产品名称">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增产品</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="品牌">
        <el-select
          v-model="filters.brandId"
          clearable
          filterable
          placeholder="全部"
          style="width: 160px"
          @visible-change="(open: boolean) => open && loadBrandOptions()"
        >
          <el-option v-for="o in brandOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
        </el-select>
      </el-form-item>
      <el-form-item label="产品名称">
        <el-input v-model="filters.name" clearable placeholder="产品名称" style="width: 160px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" label="#" align="center" />
      <el-table-column prop="goodsName" label="产品名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="brandName" label="品牌" min-width="120" />
      <el-table-column prop="goodsModel" label="型号" min-width="160" show-overflow-tooltip />
      <el-table-column prop="addTime" label="创建时间" width="170" />
      <el-table-column label="操作" width="140" fixed="right">
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
        :page-sizes="[10, 20, 50]"
        layout="sizes, total, prev, pager, next"
        :total="total"
        @size-change="reload"
        @current-change="() => load(listParams())"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑产品' : '新增产品'" width="620px">
      <el-form label-width="90px">
        <el-form-item label="品牌">
          <el-select
            v-model="form.brandId"
            clearable
            filterable
            style="width: 100%"
            @visible-change="(open: boolean) => open && loadBrandOptions()"
          >
            <el-option v-for="o in brandOpts" :key="String(o.value)" :label="String(o.label)" :value="Number(o.value)" />
          </el-select>
        </el-form-item>
        <el-form-item label="产品名称" required>
          <el-input v-model="form.goodsName" />
        </el-form-item>
        <el-form-item label="产品型号">
          <div class="model-list">
            <div v-for="(m, idx) in form.models" :key="m.key" class="model-row">
              <el-input v-model="m.value" placeholder="请输入产品型号" />
              <el-button type="primary" plain @click="addModel">添加</el-button>
              <el-button type="danger" plain @click="removeModel(idx)">删除</el-button>
            </div>
          </div>
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
import { onActivated, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  deleteExpGoods,
  fetchExpBrandOptions,
  fetchExpGoodsList,
  getExpGoods,
  saveExpGoods,
} from '@/api/experiment'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

type ModelRow = { key: number; value: string }

let modelKeySeq = 1
function newModelRow(value = ''): ModelRow {
  return { key: modelKeySeq++, value }
}

/** 对齐 Java：goods_model 逗号分隔多型号 */
function splitModels(raw: unknown): ModelRow[] {
  const parts = String(raw || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  return parts.length ? parts.map((v) => newModelRow(v)) : [newModelRow()]
}

const filters = reactive({ name: '', brandId: '' })
const brandOpts = ref<Record<string, unknown>[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  id: undefined as number | undefined,
  goodsName: '',
  brandId: undefined as number | undefined,
  models: [newModelRow()] as ModelRow[],
})

async function loadBrandOptions() {
  try {
    const res = await fetchExpBrandOptions()
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      brandOpts.value = res.obj as Record<string, unknown>[]
    }
  } catch {
    /* ignore */
  }
}

function listParams() {
  const p: Record<string, string> = {}
  if (filters.name) p.name = filters.name.trim()
  if (filters.brandId) p.brandId = filters.brandId
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchExpGoodsList({ ...p, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

function addModel() {
  form.models.push(newModelRow())
}

function removeModel(idx: number) {
  if (form.models.length <= 1) {
    ElMessage.warning('不可删除最后一个哦！')
    return
  }
  form.models.splice(idx, 1)
}

async function openCreate() {
  await loadBrandOptions()
  Object.assign(form, {
    id: undefined,
    goodsName: '',
    brandId: undefined,
    models: [newModelRow()],
  })
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  await loadBrandOptions()
  const res = await getExpGoods(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  Object.assign(form, {
    id: Number(obj.id),
    goodsName: String(obj.goodsName || ''),
    brandId: obj.brandId != null ? Number(obj.brandId) : undefined,
    models: splitModels(obj.goodsModel),
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.goodsName.trim()) {
    ElMessage.warning('请输入产品名称')
    return
  }
  const models = form.models.map((m) => m.value.trim()).filter(Boolean)
  if (new Set(models).size !== models.length) {
    ElMessage.warning('产品型号不能重复!')
    return
  }
  saving.value = true
  try {
    const res = await saveExpGoods({
      id: form.id,
      goodsName: form.goodsName.trim(),
      goodsModel: models.join(','),
      brandId: form.brandId,
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
  await ElMessageBox.confirm('确认删除该产品？', '提示', { type: 'warning' })
  const res = await deleteExpGoods(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

onMounted(async () => {
  await loadBrandOptions()
  reload()
  if (String(useRoute().query.create || '') === '1') {
    openCreate()
  }
})

// keep-alive：从品牌管理返回时刷新下拉，避免搜不到刚新增的品牌
onActivated(() => {
  loadBrandOptions()
})
</script>

<style scoped lang="scss">
.filter-form { margin-bottom: 12px; }
.pager { display: flex; justify-content: flex-end; margin-top: 16px; }
.model-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.model-row {
  display: flex;
  align-items: center;
  gap: 8px;
  .el-input { flex: 1; }
}
</style>
