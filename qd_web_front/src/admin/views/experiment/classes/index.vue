<template>
  <admin-page-card :title="pageTitle">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增</el-button>
    </template>

    <el-radio-group v-model="type" class="type-tabs" @change="onTypeChange">
      <el-radio-button :label="1">一级类</el-radio-button>
      <el-radio-button :label="2">二级类</el-radio-button>
      <el-radio-button :label="3">三级类</el-radio-button>
    </el-radio-group>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item v-if="type >= 2" label="一级类">
        <el-select
          v-model="filters.firstId"
          clearable
          filterable
          placeholder="全部"
          style="width: 160px"
          @change="onFirstFilterChange"
        >
          <el-option v-for="o in firstOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="type === 3" label="二级类">
        <el-select v-model="filters.parentId" clearable filterable placeholder="全部" style="width: 160px">
          <el-option v-for="o in secOpts" :key="String(o.value)" :label="String(o.label)" :value="String(o.value)" />
        </el-select>
      </el-form-item>
      <el-form-item label="名称">
        <el-input v-model="filters.name" clearable placeholder="类目名称" style="width: 160px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" label="#" align="center" />
      <el-table-column prop="sequence" label="排序序号" width="90" align="center" />
      <el-table-column prop="name" :label="type === 1 ? '名称' : '分类名称'" min-width="140" show-overflow-tooltip />
      <el-table-column v-if="type === 1" prop="ptName" label="所属平台" min-width="120" />
      <el-table-column v-if="type === 2" prop="parentName" label="一级类型" min-width="120" />
      <el-table-column v-if="type === 3" prop="firstName" label="一级类型" min-width="120" />
      <el-table-column v-if="type === 3" prop="parentName" label="二级类型" min-width="120" />
      <el-table-column prop="enname" label="英文代码" width="100" />
      <el-table-column prop="addTime" label="创建时间" width="170" />
      <el-table-column label="操作" width="160" fixed="right">
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑类目' : '新增类目'" width="640px" destroy-on-close>
      <el-form label-width="130px">
        <el-form-item label="排序序号" required>
          <el-input-number v-model="form.sequence" :min="1" :controls="true" />
        </el-form-item>

        <el-form-item v-if="type === 2" label="一级类型" required>
          <el-select v-model="form.parentId" filterable placeholder="请选择" style="width: 100%">
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

        <el-form-item :label="nameLabel" required>
          <el-input v-model="form.name" maxlength="100" />
        </el-form-item>

        <el-form-item label="项目英文大写代码" required>
          <el-input
            v-model="form.enname"
            maxlength="4"
            placeholder="仅英文字母，最多4位"
            @input="onEnnameInput"
          />
        </el-form-item>

        <el-form-item v-if="type === 1" label="所属平台" required>
          <el-select v-model="form.ptType" filterable placeholder="请选择" style="width: 100%">
            <el-option
              v-for="o in ptTypeOpts"
              :key="String(o.value)"
              :label="String(o.label)"
              :value="Number(o.value)"
            />
          </el-select>
        </el-form-item>

        <el-form-item v-if="type === 1" label="特殊填写类型">
          <el-input
            v-model="form.specialType"
            maxlength="5"
            placeholder="1-100 数字，可空"
            @input="onSpecialTypeInput"
          />
        </el-form-item>

        <el-form-item v-if="type >= 2" label="关联账号">
          <el-select
            v-model="form.syuserId"
            clearable
            filterable
            :loading="userLoading"
            placeholder="无"
            style="width: 100%"
          >
            <el-option v-for="u in userOptions" :key="u.value" :label="u.label" :value="u.value" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="type === 3" label="负责人账号">
          <el-select
            v-model="form.headUserId"
            clearable
            filterable
            :loading="userLoading"
            placeholder="无"
            style="width: 100%"
          >
            <el-option v-for="u in userOptions" :key="`h-${u.value}`" :label="u.label" :value="u.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="简介">
          <el-input v-model="form.intro" type="textarea" :rows="2" :maxlength="introMaxLen" show-word-limit />
        </el-form-item>

        <el-form-item :label="type === 1 ? '实验室介绍' : '项目介绍'">
          <el-input v-model="form.projectDetails" type="textarea" :rows="4" placeholder="支持 HTML 内容" />
        </el-form-item>

        <el-form-item v-if="type === 3" label="项目介绍（小程序）">
          <el-input v-model="form.appProjectDetails" type="textarea" :rows="4" placeholder="支持 HTML 内容" />
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
  deleteManage,
  fetchManageList,
  fetchManageOptions,
  fetchManagePtTypes,
  getManage,
  saveManage,
} from '@admin/api/experiment'
import { fetchUserList } from '@admin/api/system'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const route = useRoute()
const router = useRouter()
const type = ref(Number(route.query.type || 1) || 1)
const titles: Record<number, string> = {
  1: '实验业务一级类',
  2: '实验业务二级类',
  3: '实验业务三级类',
}
const pageTitle = computed(() => titles[type.value] || '实验业务类目')
const nameLabel = computed(() => {
  if (type.value === 1) return '一级类型名称'
  if (type.value === 2) return '二级类型名称'
  return '三级类型名称'
})
const introMaxLen = computed(() => {
  if (type.value === 1) return 150
  if (type.value === 2) return 60
  return 50
})

const filters = reactive({ name: '', parentId: '', firstId: '' })
const firstOpts = ref<Record<string, unknown>[]>([])
const secOpts = ref<Record<string, unknown>[]>([])
const formSecOpts = ref<Record<string, unknown>[]>([])
const ptTypeOpts = ref<Record<string, unknown>[]>([])
const userOptions = ref<{ value: string; label: string }[]>([])
const userLoading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  id: undefined as number | undefined,
  name: '',
  sequence: 1,
  enname: '',
  intro: '',
  ptType: undefined as number | undefined,
  specialType: '' as string | number,
  firstId: undefined as number | undefined,
  parentId: undefined as number | undefined,
  syuserId: '',
  headUserId: '',
  projectDetails: '',
  appProjectDetails: '',
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
  fetchManageList({ ...p, ...listParams() })
)

function reload() {
  pagination.page = 1
  return load(listParams())
}

async function loadFirstOpts() {
  const res = await fetchManageOptions(1)
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    firstOpts.value = res.obj as Record<string, unknown>[]
  }
}

async function loadSecOpts(firstId?: string) {
  if (!firstId) {
    secOpts.value = []
    return
  }
  const res = await fetchManageOptions(2, firstId)
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    secOpts.value = res.obj as Record<string, unknown>[]
  }
}

async function loadFormSecOpts(firstId?: string | number) {
  if (!firstId) {
    formSecOpts.value = []
    return
  }
  const res = await fetchManageOptions(2, String(firstId))
  formSecOpts.value = isAjaxOk(res) && Array.isArray(res.obj) ? (res.obj as Record<string, unknown>[]) : []
}

async function loadPtTypes() {
  const res = await fetchManagePtTypes()
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    ptTypeOpts.value = (res.obj as Record<string, unknown>[]).map((o) => ({
      value: o.value ?? o.id,
      label: o.label ?? o.name,
    }))
  }
}

async function loadUserOptions() {
  userLoading.value = true
  try {
    const res = await fetchUserList(
      { start: 0, length: 1000, type: -1, draw: 1 },
      { silentError: true }
    )
    const list = Array.isArray(res.data) ? res.data : []
    userOptions.value = list
      .map((u) => {
        const id = String(u.id ?? u.userId ?? '')
        const name = String(u.userName || u.user_name || '')
        const trueName = String(u.trueName || u.true_name || '')
        const label = trueName ? `${name}（${trueName}）` : name || id
        return { value: id, label }
      })
      .filter((o) => o.value)
  } catch {
    userOptions.value = []
  } finally {
    userLoading.value = false
  }
}

function onFirstFilterChange() {
  filters.parentId = ''
  loadSecOpts(filters.firstId)
}

async function onFormFirstChange() {
  form.parentId = undefined
  await loadFormSecOpts(form.firstId)
}

function onEnnameInput(val: string) {
  form.enname = String(val || '')
    .replace(/[^a-zA-Z]/g, '')
    .toUpperCase()
    .slice(0, 4)
}

function onSpecialTypeInput(val: string) {
  form.specialType = String(val || '').replace(/\D/g, '').slice(0, 5)
}

function resetForm() {
  Object.assign(form, {
    id: undefined,
    name: '',
    sequence: 1,
    enname: '',
    intro: '',
    ptType: undefined,
    specialType: '',
    firstId: undefined,
    parentId: undefined,
    syuserId: '',
    headUserId: '',
    projectDetails: '',
    appProjectDetails: '',
  })
  formSecOpts.value = []
}

async function onTypeChange() {
  filters.name = ''
  filters.parentId = ''
  filters.firstId = ''
  await router.replace({ query: { ...route.query, type: String(type.value) } })
  await loadFirstOpts()
  reload()
}

async function openCreate() {
  resetForm()
  if (type.value >= 2) await loadUserOptions()
  if (type.value === 1) await loadPtTypes()
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getManage(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  if (type.value >= 2) await loadUserOptions()
  if (type.value === 1) await loadPtTypes()
  const firstId = obj.firstId != null ? Number(obj.firstId) : undefined
  if (type.value === 3 && firstId) await loadFormSecOpts(firstId)
  Object.assign(form, {
    id: Number(obj.id),
    name: String(obj.name || ''),
    sequence: Number(obj.sequence || 1),
    enname: String(obj.enname || ''),
    intro: String(obj.intro || ''),
    ptType: obj.ptType != null && Number(obj.ptType) > 0 ? Number(obj.ptType) : undefined,
    specialType: obj.specialType != null && String(obj.specialType) !== '0' ? String(obj.specialType) : '',
    firstId,
    parentId: obj.parentId != null ? Number(obj.parentId) : undefined,
    syuserId: String(obj.syuserId || ''),
    headUserId: String(obj.headUserId || ''),
    projectDetails: String(obj.projectDetails || ''),
    appProjectDetails: String(obj.appProjectDetails || ''),
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }
  if (!form.enname.trim()) {
    ElMessage.warning('请填写项目英文大写代码')
    return
  }
  if (type.value === 1 && !form.ptType) {
    ElMessage.warning('请选择所属平台')
    return
  }
  if (type.value === 2 && !form.parentId) {
    ElMessage.warning('请选择一级类型')
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
  if (!form.sequence || form.sequence < 1) {
    ElMessage.warning('请填写排序序号')
    return
  }
  saving.value = true
  try {
    const res = await saveManage({
      id: form.id,
      name: form.name.trim(),
      sequence: form.sequence,
      enname: form.enname.trim(),
      intro: form.intro,
      type: type.value,
      parentId: form.parentId,
      ptType: form.ptType,
      specialType: form.specialType === '' ? undefined : Number(form.specialType),
      syuserId: form.syuserId || undefined,
      headUserId: form.headUserId || undefined,
      projectDetails: form.projectDetails,
      appProjectDetails: form.appProjectDetails,
    })
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await loadFirstOpts()
      if (type.value === 3 && filters.firstId) await loadSecOpts(filters.firstId)
      await reload()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
    }
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认删除该类目？', '提示', { type: 'warning' })
  const res = await deleteManage(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await loadFirstOpts()
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
