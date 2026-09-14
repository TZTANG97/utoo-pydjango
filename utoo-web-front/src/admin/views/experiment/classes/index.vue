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
      <el-table-column prop="sequence" label="排序序号" width="90" align="center">
        <template #default="{ row }">
          {{ Number(row.sequence) > 0 ? row.sequence : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="name" :label="type === 1 ? '名称' : '分类名称'" min-width="140" show-overflow-tooltip />
      <el-table-column v-if="type === 1" prop="ptName" label="所属平台" min-width="120" />
      <el-table-column v-if="type === 2" prop="parentName" label="一级类型" min-width="120" />
      <el-table-column v-if="type === 3" prop="firstName" label="一级类型" min-width="120" />
      <el-table-column v-if="type === 3" prop="parentName" label="二级类型" min-width="120" />
      <el-table-column prop="enname" label="英文代码" width="100">
        <template #default="{ row }">{{ row.enname || '-' }}</template>
      </el-table-column>
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

    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑类目' : '新增类目'"
      width="860px"
      top="4vh"
      destroy-on-close
      append-to-body
    >
      <el-form label-width="140px">
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

        <el-form-item label="添加图片">
          <div class="photo-box">
            <div class="upload-row">
              <el-upload
                :show-file-list="false"
                accept="image/jpeg,image/png,image/gif,image/webp,.jpg,.jpeg,.png,.gif,.webp"
                :http-request="(opt) => onUploadImage(opt, 'main')"
              >
                <el-button type="primary" :loading="uploading">上传主图</el-button>
              </el-upload>
              <el-button @click="openAlbum('main')">从相册选择</el-button>
              <el-button v-if="form.photoUrl" link type="danger" @click="clearPhoto('main')">清除</el-button>
            </div>
            <el-image
              v-if="form.photoUrl"
              class="preview-img"
              :src="form.photoUrl"
              fit="contain"
              :preview-src-list="[form.photoUrl]"
              preview-teleported
            />
            <div v-else class="preview-empty">暂无主图</div>
          </div>
        </el-form-item>

        <el-form-item v-if="type === 3" label="小程序图片">
          <div class="photo-box">
            <div class="upload-row">
              <el-upload
                :show-file-list="false"
                accept="image/jpeg,image/png,image/gif,image/webp,.jpg,.jpeg,.png,.gif,.webp"
                :http-request="(opt) => onUploadImage(opt, 'app')"
              >
                <el-button type="primary" :loading="uploading">上传小程序图</el-button>
              </el-upload>
              <el-button @click="openAlbum('app')">从相册选择</el-button>
              <el-button v-if="form.appPhotoUrl" link type="danger" @click="clearPhoto('app')">清除</el-button>
            </div>
            <el-image
              v-if="form.appPhotoUrl"
              class="preview-img"
              :src="form.appPhotoUrl"
              fit="contain"
              :preview-src-list="[form.appPhotoUrl]"
              preview-teleported
            />
            <div v-else class="preview-empty">暂无小程序图</div>
          </div>
        </el-form-item>

        <el-form-item label="简介">
          <el-input v-model="form.intro" type="textarea" :rows="2" :maxlength="introMaxLen" show-word-limit />
        </el-form-item>

        <el-form-item :label="type === 1 ? '实验室介绍' : '项目介绍'">
          <HtmlRichEditor v-if="dialogVisible" v-model="form.projectDetails" />
        </el-form-item>

        <el-form-item v-if="type === 3" label="项目介绍（小程序）">
          <HtmlRichEditor v-if="dialogVisible" v-model="form.appProjectDetails" />
        </el-form-item>

        <template v-if="type === 3 && form.id">
          <el-form-item label="关联测试账号">
            <el-table :data="testUsers" border stripe size="small" empty-text="暂无关联测试账号" max-height="220">
              <el-table-column prop="userName" label="姓名" min-width="120" />
              <el-table-column prop="loginName" label="账号" min-width="120" />
            </el-table>
          </el-form-item>
          <el-form-item label="操作记录">
            <el-table :data="manageLogs" border stripe size="small" empty-text="暂无操作记录" max-height="220">
              <el-table-column prop="addTime" label="时间" width="170" />
              <el-table-column prop="addusername" label="操作人" width="120" />
              <el-table-column prop="content" label="内容" min-width="180" show-overflow-tooltip />
            </el-table>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
    <AlbumImagePicker v-model="albumVisible" @select="onAlbumPick" />
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import AlbumImagePicker from '@admin/components/AlbumImagePicker.vue'
import HtmlRichEditor from '@admin/components/HtmlRichEditor.vue'
import {
  deleteManage,
  fetchManageList,
  fetchManageOptions,
  fetchManagePtTypes,
  getManage,
  saveManage,
} from '@admin/api/experiment'
import { fetchUserList } from '@admin/api/system'
import { uploadSellerImage } from '@admin/api/ops'
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
const uploading = ref(false)
const albumVisible = ref(false)
const albumTarget = ref<'main' | 'app'>('main')
const testUsers = ref<Record<string, unknown>[]>([])
const manageLogs = ref<Record<string, unknown>[]>([])
const OSS_BASE = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/'
type AlbumImagePick = { id: number; url: string }
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
  photoId: '' as string,
  photoUrl: '',
  appPhotoId: '' as string,
  appPhotoUrl: '',
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

/** 关联/负责人账号可能不在 pt_type=2 的员工列表里，需用详情人名补进下拉，避免只显示 UUID */
function ensureUserOption(id: string, trueName: string, loginName: string) {
  const uid = String(id || '').trim()
  if (!uid) return
  const label =
    trueName && loginName
      ? `${loginName}（${trueName}）`
      : trueName || loginName || uid
  const idx = userOptions.value.findIndex((u) => u.value === uid)
  if (idx >= 0) {
    if (label !== uid) userOptions.value[idx] = { value: uid, label }
    return
  }
  userOptions.value = [...userOptions.value, { value: uid, label }]
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

function mediaUrl(path: unknown, name: unknown) {
  const p = String(path || '')
  const n = String(name || '')
  if (!p && !n) return ''
  if (p.includes('https') || p.startsWith('http://')) {
    return p.includes(n) ? p : `${p.replace(/\/?$/, '/')}${n}`
  }
  return `${OSS_BASE}${p.replace(/^\//, '')}/${n.replace(/^\//, '')}`
}

function openAlbum(target: 'main' | 'app') {
  albumTarget.value = target
  albumVisible.value = true
}

function applyPhoto(target: 'main' | 'app', id: string, url: string) {
  if (target === 'app') {
    form.appPhotoId = id
    form.appPhotoUrl = url
    return
  }
  form.photoId = id
  form.photoUrl = url
}

function clearPhoto(target: 'main' | 'app') {
  applyPhoto(target, '', '')
}

function onAlbumPick(pick: AlbumImagePick) {
  applyPhoto(albumTarget.value, String(pick.id), pick.url)
}

async function onUploadImage(options: { file: File }, target: 'main' | 'app') {
  uploading.value = true
  try {
    const res = await uploadSellerImage(options.file)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    const obj = (res.obj || res.data || res) as Record<string, unknown>
    const id = obj.id ?? (obj as { obj?: { id?: unknown } }).obj?.id
    const url = String(obj.url || '')
    if (!id) {
      ElMessage.error('上传成功但未返回图片ID')
      return
    }
    applyPhoto(target, String(id), url)
    ElMessage.success('上传成功')
  } finally {
    uploading.value = false
  }
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
    photoId: '',
    photoUrl: '',
    appPhotoId: '',
    appPhotoUrl: '',
  })
  testUsers.value = []
  manageLogs.value = []
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
    photoId: obj.photoId != null && String(obj.photoId) !== '0' ? String(obj.photoId) : '',
    photoUrl: mediaUrl(obj.photoPath, obj.photoName),
    appPhotoId: obj.appPhotoId != null && String(obj.appPhotoId) !== '0' ? String(obj.appPhotoId) : '',
    appPhotoUrl: mediaUrl(obj.appPhotoPath, obj.appPhotoName),
  })
  ensureUserOption(
    form.syuserId,
    String(obj.syuserName || ''),
    String(obj.syuserLoginName || '')
  )
  ensureUserOption(
    form.headUserId,
    String(obj.headUserName || ''),
    String(obj.headUserLoginName || '')
  )
  testUsers.value = Array.isArray(obj.testUsers) ? (obj.testUsers as Record<string, unknown>[]) : []
  manageLogs.value = Array.isArray(obj.logs) ? (obj.logs as Record<string, unknown>[]) : []
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
      photoId: form.photoId || undefined,
      appPhotoId: form.appPhotoId || undefined,
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
.photo-box { width: 100%; }
.upload-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.preview-img { width: 160px; height: 100px; border: 1px solid #ebeef5; border-radius: 4px; }
.preview-empty { color: #909399; font-size: 13px; }
</style>
