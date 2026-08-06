<template>
  <admin-page-card title="实验测试项目">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增项目</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="一级类">
        <el-select
          v-model="filters.firstId"
          clearable
          filterable
          placeholder="全部"
          style="width: 150px"
          @change="onFirstChange"
        >
          <el-option v-for="o in firstOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
        </el-select>
      </el-form-item>
      <el-form-item label="二级类">
        <el-select
          v-model="filters.secId"
          clearable
          filterable
          placeholder="全部"
          style="width: 150px"
          @change="onSecChange"
        >
          <el-option v-for="o in secOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
        </el-select>
      </el-form-item>
      <el-form-item label="三级类">
        <el-select v-model="filters.thirdId" clearable filterable placeholder="全部" style="width: 150px">
          <el-option v-for="o in thirdOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
        </el-select>
      </el-form-item>
      <el-form-item label="项目名称">
        <el-input v-model="filters.name" clearable placeholder="项目名称" style="width: 160px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" label="#" align="center" />
      <el-table-column prop="projectName" label="项目名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="firstName" label="一级类" min-width="110" />
      <el-table-column prop="secName" label="二级类" min-width="110" />
      <el-table-column prop="className" label="三级类" min-width="110" />
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑项目' : '新增项目'" width="520px">
      <el-form label-width="90px">
        <el-form-item label="一级类">
          <el-select v-model="form.firstId" filterable style="width: 100%" @change="onFormFirstChange">
            <el-option v-for="o in firstOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
          </el-select>
        </el-form-item>
        <el-form-item label="二级类">
          <el-select v-model="form.secId" filterable style="width: 100%" @change="onFormSecChange">
            <el-option v-for="o in formSecOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
          </el-select>
        </el-form-item>
        <el-form-item label="三级类" required>
          <el-select v-model="form.classId" filterable style="width: 100%">
            <el-option v-for="o in formThirdOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称" required>
          <el-input v-model="form.projectName" />
        </el-form-item>
        <el-form-item label="测试单价">
          <el-input v-model="form.testPrice" clearable placeholder="请输入测试单价" />
        </el-form-item>
        <el-form-item label="隶属国家">
          <el-input v-model="form.country" clearable placeholder="请输入国家名称" />
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
  deleteProject,
  fetchManageOptions,
  fetchProjectList,
  getProject,
  saveProject,
} from '@/api/experiment'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const filters = reactive({ name: '', firstId: '', secId: '', thirdId: '' })
const firstOpts = ref<Record<string, unknown>[]>([])
const secOpts = ref<Record<string, unknown>[]>([])
const thirdOpts = ref<Record<string, unknown>[]>([])
const formSecOpts = ref<Record<string, unknown>[]>([])
const formThirdOpts = ref<Record<string, unknown>[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  id: undefined as number | undefined,
  projectName: '',
  firstId: '',
  secId: '',
  classId: '',
  testPrice: '',
  country: '',
})

function listParams() {
  const p: Record<string, string> = {}
  if (filters.name) p.name = filters.name.trim()
  if (filters.firstId) p.firstId = filters.firstId
  if (filters.secId) p.secId = filters.secId
  if (filters.thirdId) p.thirdId = filters.thirdId
  return p
}

const { loading, rows, total, pagination, load } = useDataTable((p) =>
  fetchProjectList({ ...p, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

async function loadOpts(type: number, parentId?: string) {
  const res = await fetchManageOptions(type, parentId)
  return isAjaxOk(res) && Array.isArray(res.obj) ? (res.obj as Record<string, unknown>[]) : []
}

async function onFirstChange() {
  filters.secId = ''
  filters.thirdId = ''
  secOpts.value = filters.firstId ? await loadOpts(2, filters.firstId) : []
  thirdOpts.value = []
}

async function onSecChange() {
  filters.thirdId = ''
  thirdOpts.value = filters.secId ? await loadOpts(3, filters.secId) : []
}

async function onFormFirstChange() {
  form.secId = ''
  form.classId = ''
  formSecOpts.value = form.firstId ? await loadOpts(2, form.firstId) : []
  formThirdOpts.value = []
}

async function onFormSecChange() {
  form.classId = ''
  formThirdOpts.value = form.secId ? await loadOpts(3, form.secId) : []
}

function openCreate() {
  Object.assign(form, {
    id: undefined,
    projectName: '',
    firstId: '',
    secId: '',
    classId: '',
    testPrice: '',
    country: '',
  })
  formSecOpts.value = []
  formThirdOpts.value = []
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getProject(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  form.id = Number(obj.id)
  form.projectName = String(obj.projectName || '')
  form.firstId = obj.firstId != null ? String(obj.firstId) : ''
  form.secId = obj.secId != null ? String(obj.secId) : ''
  form.classId = obj.classId != null ? String(obj.classId) : ''
  form.testPrice =
    obj.testPrice != null && obj.testPrice !== '' ? String(obj.testPrice) : ''
  form.country = String(obj.country || '')
  formSecOpts.value = form.firstId ? await loadOpts(2, form.firstId) : []
  formThirdOpts.value = form.secId ? await loadOpts(3, form.secId) : []
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.projectName.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  if (!form.classId) {
    ElMessage.warning('请选择三级类目')
    return
  }
  const priceText = form.testPrice.trim()
  if (priceText) {
    const n = Number(priceText)
    if (!Number.isFinite(n) || n < 0) {
      ElMessage.warning('测试单价格式错误')
      return
    }
  }
  saving.value = true
  try {
    const res = await saveProject({
      id: form.id,
      projectName: form.projectName.trim(),
      classId: form.classId,
      testPrice: priceText || undefined,
      country: form.country.trim() || undefined,
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
  await ElMessageBox.confirm('确认删除该项目？', '提示', { type: 'warning' })
  const res = await deleteProject(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

onMounted(async () => {
  firstOpts.value = await loadOpts(1)
  reload()
})
</script>

<style scoped lang="scss">
.filter-form { margin-bottom: 12px; }
.pager { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
