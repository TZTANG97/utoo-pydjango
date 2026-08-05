<template>
  <admin-page-card :title="pageTitle">
    <template #actions>
      <el-button type="primary" @click="openCreate">{{ createButtonText }}</el-button>
    </template>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column label="商品图片" width="100" align="center">
        <template #default="{ row }">
          <el-image
            v-if="bannerImageUrl(row)"
            class="banner-thumb"
            :src="bannerImageUrl(row)"
            fit="cover"
            :preview-src-list="[bannerImageUrl(row)]"
            preview-teleported
          />
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column
        v-if="showTitleColumn"
        prop="title"
        label="标题"
        min-width="140"
        show-overflow-tooltip
      />
      <el-table-column label="添加时间" min-width="160" align="center">
        <template #default="{ row }">{{ formatTime(row.time) }}</template>
      </el-table-column>
      <el-table-column prop="sort" label="排序编号" width="100" align="center" />
      <el-table-column label="是否显示" width="100" align="center">
        <template #default="{ row }">
          {{ Number(row.isShow) === 1 ? '显示' : '不显示' }}
        </template>
      </el-table-column>
      <el-table-column
        v-if="showPlatformColumn"
        label="所属平台"
        min-width="120"
        align="center"
        show-overflow-tooltip
      >
        <template #default="{ row }">{{ row.ptName || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" :width="showPlatformColumn ? 240 : 220" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-if="canDelete(row)"
            link
            type="primary"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
          <el-button link type="primary" @click="handleToggle(row)">是否显示</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="() => load()"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="680px" destroy-on-close>
      <el-form label-width="120px" class="banner-form">
        <el-form-item label="排序序号" required>
          <el-input-number v-model="form.sort" :min="1" :controls="true" />
        </el-form-item>

        <template v-if="showTextFields">
          <el-form-item label="标题" :required="bannerType !== 0">
            <el-input v-model="form.title" clearable placeholder="标题" />
          </el-form-item>
          <el-form-item v-if="bannerType === 1" label="小标题">
            <el-input v-model="form.subheading" clearable placeholder="小标题" />
          </el-form-item>
          <el-form-item label="描述" :required="bannerType !== 0">
            <el-input v-model="form.badescribe" clearable placeholder="描述" />
          </el-form-item>
        </template>

        <el-form-item label="是否显示" required>
          <el-select v-model="form.is_show" style="width: 200px">
            <el-option label="显示" :value="1" />
            <el-option label="不显示" :value="0" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="showPlatformColumn" label="所属平台" required>
          <el-select v-model="form.platformType" style="width: 200px">
            <el-option label="大平台" :value="1" />
            <el-option label="utoo" :value="2" />
            <el-option label="爱沵库" :value="3" />
            <el-option label="途哲" :value="4" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="showWebsiteField" label="点击跳转网址">
          <el-input v-model="form.website" clearable placeholder="点击跳转网址" />
        </el-form-item>

        <el-form-item label="添加图片" required>
          <div class="photo-box">
            <el-tabs v-model="photoTab" type="card" class="photo-tabs">
              <el-tab-pane label="上传图片" name="upload">
                <div class="upload-row">
                  <el-upload
                    :show-file-list="false"
                    accept="image/jpeg,image/png,image/gif,image/webp,.jpg,.jpeg,.png,.gif,.webp"
                    :http-request="onUploadImage"
                  >
                    <el-button type="primary" :loading="uploading">点击上传轮播图片</el-button>
                  </el-upload>
                  <el-button v-if="previewUrl" link type="danger" @click="clearPhoto">清除</el-button>
                </div>
              </el-tab-pane>
              <el-tab-pane label="从相册选取" name="album">
                <el-button @click="albumVisible = true">从相册选择</el-button>
              </el-tab-pane>
            </el-tabs>
            <div class="preview-wrap">
              <el-image
                v-if="previewUrl"
                class="preview-img"
                :src="previewUrl"
                fit="contain"
                :preview-src-list="[previewUrl]"
                preview-teleported
              />
              <div v-else class="preview-empty">暂无图片</div>
            </div>
          </div>
        </el-form-item>
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
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import AlbumImagePicker from '@/components/AlbumImagePicker.vue'
import {
  createBanner,
  createXcxfmBanner,
  deleteBanner,
  fetchBannerList,
  fetchXcxfmBannerList,
  toggleBannerShow,
  updateBanner,
  updateXcxfmBanner,
  uploadSellerImage,
} from '@/api/ops'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

type AlbumImagePick = { id: number; url: string }

const OSS_BASE = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/'

const route = useRoute()
const bannerType = computed(() => Number(route.meta.bannerType ?? 0))
const pageTitle = computed(() => String(route.meta.title || '轮播图管理'))
/** PC 轮播图 Java 已隐藏标题等文案字段；小程序 / 封面图仍保留 */
const showTextFields = computed(() => bannerType.value === 1 || bannerType.value === 2)
const showTitleColumn = computed(() => true)
const showPlatformColumn = computed(() => bannerType.value === 1 || bannerType.value === 2)
const showWebsiteField = computed(() => bannerType.value !== 2)
const createButtonText = computed(() =>
  bannerType.value === 2 ? '新增加载页面图' : '新增轮播图'
)
const dialogTitle = computed(() => {
  if (bannerType.value === 2) {
    return isEdit.value ? '编辑加载页面图' : '新增加载页面图'
  }
  return isEdit.value ? '编辑轮播图' : '新增轮播图'
})

const loader = (params: Record<string, unknown>) => {
  if (bannerType.value === 2) return fetchXcxfmBannerList(params)
  return fetchBannerList({ ...params, banner_type: bannerType.value })
}

const { loading, rows, total, pagination, load } = useDataTable(loader)
const saving = ref(false)
const uploading = ref(false)
const dialogVisible = ref(false)
const albumVisible = ref(false)
const isEdit = ref(false)
const photoTab = ref('upload')
const previewUrl = ref('')
const form = reactive({
  bid: '',
  manage_main_photo_id: '',
  title: '',
  subheading: '',
  badescribe: '',
  sort: 1,
  website: '',
  platformType: 1,
  is_show: 1,
})

function bannerImageUrl(row: Record<string, unknown>) {
  const path = String(row.path || '')
  const name = String(row.name || '')
  if (!path && !name) return ''
  if (path.includes('https') || path.startsWith('http://')) {
    return path.includes(name) ? path : `${path.replace(/\/?$/, '/')}${name}`
  }
  return `${OSS_BASE}${path.replace(/^\//, '')}/${name.replace(/^\//, '')}`
}

function formatTime(val: unknown) {
  if (!val) return '-'
  const s = String(val)
  return s.length >= 16 ? s.slice(0, 16) : s
}

function canDelete(row: Record<string, unknown>) {
  if (bannerType.value === 2 && Number(row.isShow) === 1) return false
  return true
}

function reload() {
  return load()
}

function resetAndReload() {
  pagination.page = 1
  return load()
}

onMounted(() => resetAndReload())

watch(bannerType, () => {
  dialogVisible.value = false
  resetAndReload()
})

function resetForm() {
  form.bid = ''
  form.manage_main_photo_id = ''
  form.title = ''
  form.subheading = ''
  form.badescribe = ''
  form.sort = 1
  form.website = ''
  form.platformType = 1
  form.is_show = 1
  previewUrl.value = ''
  photoTab.value = 'upload'
}

function openCreate() {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  form.bid = String(row.bid || row.id || '')
  form.manage_main_photo_id = String(row.bannerId || row.accessoryId || '')
  form.title = String(row.title || '')
  form.subheading = String(row.subheading || '')
  form.badescribe = String(row.badescribe || '')
  form.sort = Number(row.sort || 1) || 1
  form.website = String(row.website || '')
  form.platformType = Number(row.platformType || 1)
  form.is_show = Number(row.isShow ?? 1)
  previewUrl.value = bannerImageUrl(row)
  photoTab.value = 'upload'
  isEdit.value = true
  dialogVisible.value = true
}

function clearPhoto() {
  form.manage_main_photo_id = ''
  previewUrl.value = ''
}

function onAlbumPick(pick: AlbumImagePick) {
  form.manage_main_photo_id = String(pick.id)
  previewUrl.value = pick.url
  photoTab.value = 'album'
}

async function onUploadImage(options: { file: File }) {
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
    form.manage_main_photo_id = String(id)
    previewUrl.value = url
    ElMessage.success('上传成功')
  } finally {
    uploading.value = false
  }
}

async function handleSubmit() {
  if (!form.sort || form.sort < 1) {
    ElMessage.warning('排序序号须为大于 0 的整数')
    return
  }
  if (!form.manage_main_photo_id.trim()) {
    ElMessage.warning('请上传图片')
    return
  }
  if (showTextFields.value) {
    if (!form.title.trim()) {
      ElMessage.warning('请填写标题')
      return
    }
    if (!form.badescribe.trim()) {
      ElMessage.warning('请填写描述')
      return
    }
  }
  saving.value = true
  try {
    const payload = {
      bid: form.bid,
      manage_main_photo_id: form.manage_main_photo_id.trim(),
      title: showTextFields.value ? form.title : '',
      subheading: bannerType.value === 1 ? form.subheading : '',
      badescribe: showTextFields.value ? form.badescribe : '',
      sort: form.sort,
      website: showWebsiteField.value ? form.website : '',
      platformType: form.platformType,
      is_show: form.is_show,
      banner_type: bannerType.value,
    }
    let res
    if (bannerType.value === 2) {
      res = isEdit.value ? await updateXcxfmBanner(payload) : await createXcxfmBanner(payload)
    } else {
      res = isEdit.value ? await updateBanner(payload) : await createBanner(payload)
    }
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await resetAndReload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function handleToggle(row: Record<string, unknown>) {
  const res = await toggleBannerShow(String(row.bid || row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('操作成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该轮播吗？', '提示', { type: 'warning' })
  const res = await deleteBanner(String(row.bid || row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}
</script>

<style scoped lang="scss">
.banner-thumb {
  width: 60px;
  height: 66px;
  border-radius: 2px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.banner-form {
  padding-right: 8px;
}

.photo-box {
  width: 100%;
}

.photo-tabs {
  width: 100%;
}

.upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.preview-wrap {
  width: 220px;
  height: 160px;
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  background: #fafafa;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-img {
  width: 100%;
  height: 100%;
}

.preview-empty {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>
