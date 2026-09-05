<template>
  <admin-page-card :title="pageTitle">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增</el-button>
    </template>

    <el-radio-group v-model="type" class="type-tabs" @change="onTypeChange">
      <el-radio-button :label="1">一级属性</el-radio-button>
      <el-radio-button :label="2">二级属性</el-radio-button>
      <el-radio-button :label="3">三级属性</el-radio-button>
    </el-radio-group>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item v-if="type >= 2" label="一级">
        <el-select
          v-model="filters.firstId"
          clearable
          filterable
          placeholder="全部"
          style="width: 150px"
          @change="onFirstFilterChange"
        >
          <el-option v-for="o in firstOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="type === 3" label="二级">
        <el-select v-model="filters.parentId" clearable filterable placeholder="全部" style="width: 150px">
          <el-option v-for="o in secOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
        </el-select>
      </el-form-item>
      <el-form-item label="名称">
        <el-input v-model="filters.name" clearable placeholder="属性名称" style="width: 160px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" label="#" align="center" />
      <el-table-column v-if="type === 1" prop="specialId" label="特殊字段编号" width="120" />
      <el-table-column prop="name" :label="type === 3 ? '分类名称' : '属性名称'" min-width="140" />
      <el-table-column v-if="type >= 2" prop="parentName" label="上级" min-width="120" />
      <el-table-column v-if="type >= 3" prop="firstName" label="一级" min-width="120" />
      <el-table-column v-if="type === 2" prop="selectionLabel" label="选择方式" width="100" />
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑属性' : '新增属性'" width="480px">
      <el-form label-width="110px">
        <el-form-item v-if="type === 1" label="特殊字段编号" required>
          <el-input
            v-model="form.specialId"
            placeholder="请输入 1-100 的数字"
            maxlength="3"
            @input="onSpecialIdInput"
          />
        </el-form-item>
        <el-form-item v-if="type === 2" label="上级属性" required>
          <el-select v-model="form.parentId" filterable style="width: 100%">
            <el-option
              v-for="o in firstOpts"
              :key="String(o.value)"
              :label="String(o.label)"
              :value="Number(o.value)"
            />
          </el-select>
        </el-form-item>
        <template v-if="type === 3">
          <el-form-item label="一级类型" required>
            <el-select v-model="form.firstId" filterable style="width: 100%" @change="onFormFirstChange">
              <el-option
                v-for="o in firstOpts"
                :key="String(o.value)"
                :label="String(o.label)"
                :value="Number(o.value)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="二级类型" required>
            <el-select v-model="form.parentId" filterable style="width: 100%" :disabled="!form.firstId">
              <el-option
                v-for="o in formSecOpts"
                :key="String(o.value)"
                :label="String(o.label)"
                :value="Number(o.value)"
              />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item :label="nameFieldLabel" required>
          <el-input v-model="form.name" :placeholder="type === 3 ? '请输入分类名称' : '请输入属性名称'" />
        </el-form-item>
        <el-form-item v-if="type === 2" label="选择方式">
          <el-select v-model="form.selection" style="width: 100%">
            <el-option :value="1" label="单选" />
            <el-option :value="2" label="多选" />
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  deleteSampleAttr,
  fetchSampleAttrList,
  fetchSampleAttrOptions,
  getSampleAttr,
  saveSampleAttr,
} from '@admin/api/experiment'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const route = useRoute()
const router = useRouter()
const type = ref(Number(route.query.type || 1) || 1)
const titles: Record<number, string> = {
  1: '样品属性一级',
  2: '样品属性二级',
  3: '样品属性三级',
}
const pageTitle = computed(() => titles[type.value] || '样品属性')
const nameFieldLabel = computed(() => {
  if (type.value !== 3) return '属性名称'
  return form.id ? '修改分类名称' : '分类名称'
})

const filters = reactive({ name: '', parentId: '', firstId: '' })
const firstOpts = ref<Record<string, unknown>[]>([])
const secOpts = ref<Record<string, unknown>[]>([])
const formSecOpts = ref<Record<string, unknown>[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  id: undefined as number | undefined,
  name: '',
  specialId: '' as string | number,
  firstId: undefined as number | undefined,
  parentId: undefined as number | undefined,
  selection: 1,
})

function listParams() {
  const p: Record<string, unknown> = { type: type.value }
  if (filters.name) p.name = filters.name.trim()
  // 二级：一级筛选项即上级 parentId（去掉重复的「上级」下拉）
  if (type.value === 2 && filters.firstId) p.parentId = filters.firstId
  if (type.value === 3) {
    if (filters.parentId) p.parentId = filters.parentId
    if (filters.firstId) p.firstId = filters.firstId
  }
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchSampleAttrList({ ...p, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

async function loadFirstOpts() {
  const res = await fetchSampleAttrOptions(1)
  if (isAjaxOk(res) && Array.isArray(res.obj)) firstOpts.value = res.obj as Record<string, unknown>[]
}

async function loadSecOpts(firstId?: string | number) {
  if (!firstId) {
    secOpts.value = []
    return
  }
  const res = await fetchSampleAttrOptions(2, String(firstId))
  if (isAjaxOk(res) && Array.isArray(res.obj)) secOpts.value = res.obj as Record<string, unknown>[]
}

async function loadFormSecOpts(firstId?: string | number) {
  if (!firstId) {
    formSecOpts.value = []
    return
  }
  const res = await fetchSampleAttrOptions(2, String(firstId))
  formSecOpts.value = isAjaxOk(res) && Array.isArray(res.obj) ? (res.obj as Record<string, unknown>[]) : []
}

function onFirstFilterChange() {
  filters.parentId = ''
  loadSecOpts(filters.firstId)
}

async function onFormFirstChange() {
  form.parentId = undefined
  await loadFormSecOpts(form.firstId)
}

function onSpecialIdInput(val: string) {
  form.specialId = String(val || '').replace(/\D/g, '').slice(0, 3)
}

function resetForm() {
  Object.assign(form, {
    id: undefined,
    name: '',
    specialId: '',
    firstId: undefined,
    parentId: undefined,
    selection: 1,
  })
  formSecOpts.value = []
}

async function onTypeChange() {
  filters.name = ''
  filters.parentId = ''
  filters.firstId = ''
  secOpts.value = []
  await router.replace({ query: { ...route.query, type: String(type.value) } })
  await loadFirstOpts()
  reload()
}

async function openCreate() {
  resetForm()
  await loadFirstOpts()
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getSampleAttr(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  await loadFirstOpts()
  Object.assign(form, {
    id: Number(obj.id),
    name: String(obj.name || ''),
    specialId: obj.specialId != null && obj.specialId !== '' ? String(obj.specialId) : '',
    firstId: obj.firstId != null ? Number(obj.firstId) : undefined,
    parentId: obj.parentId != null ? Number(obj.parentId) : undefined,
    selection: Number(obj.selection || 1),
  })
  if (type.value === 3 && form.firstId) {
    await loadFormSecOpts(form.firstId)
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (type.value === 1) {
    const sid = Number(form.specialId)
    if (!form.specialId || Number.isNaN(sid) || sid < 1 || sid > 100) {
      ElMessage.warning('请填写 1-100 的特殊字段编号')
      return
    }
  }
  if (!form.name.trim()) {
    ElMessage.warning(type.value === 3 ? '请输入分类名称' : '请输入属性名称')
    return
  }
  if (type.value === 2 && !form.parentId) {
    ElMessage.warning('请选择上级属性')
    return
  }
  if (type.value === 3) {
    if (!form.firstId) {
      ElMessage.warning('请选择一级类型')
      return
    }
    if (!form.parentId) {
      ElMessage.warning('请选择二级类型')
      return
    }
  }
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      id: form.id,
      name: form.name.trim(),
      type: type.value,
      parentId: form.parentId,
    }
    if (type.value === 1) payload.specialId = Number(form.specialId)
    if (type.value === 2) payload.selection = form.selection
    const res = await saveSampleAttr(payload)
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      // 刷新下拉选项，保证新增后可立即选到
      await loadFirstOpts()
      if (filters.firstId) await loadSecOpts(filters.firstId)
      await reload()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
    }
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认删除该属性？', '提示', { type: 'warning' })
  const res = await deleteSampleAttr(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await loadFirstOpts()
    if (filters.firstId) await loadSecOpts(filters.firstId)
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

watch(
  () => route.query.type,
  (v) => {
    const n = Number(v || 1) || 1
    if (n !== type.value) {
      type.value = n
      reload()
    }
  }
)

onMounted(async () => {
  await loadFirstOpts()
  reload()
})
</script>

<style scoped lang="scss">
.type-tabs { margin-bottom: 12px; }
.filter-form { margin-bottom: 12px; }
.pager { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
