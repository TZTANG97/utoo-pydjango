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
      <el-table-column prop="title" label="标题" min-width="140" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px">
      <el-form label-width="110px">
        <el-form-item label="图片附件ID" required>
          <el-input v-model="form.manage_main_photo_id" placeholder="accessory.id" />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="副标题">
          <el-input v-model="form.subheading" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.badescribe" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="排序编号">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
        <el-form-item label="链接">
          <el-input v-model="form.website" />
        </el-form-item>
        <el-form-item v-if="showPlatformColumn" label="所属平台">
          <el-select v-model="form.platformType" style="width: 200px">
            <el-option label="大平台" :value="1" />
            <el-option label="utoo" :value="2" />
            <el-option label="爱沵库" :value="3" />
            <el-option label="途哲" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否显示">
          <el-switch v-model="form.is_show" :active-value="1" :inactive-value="0" />
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
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  createBanner,
  createXcxfmBanner,
  deleteBanner,
  fetchBannerList,
  fetchXcxfmBannerList,
  toggleBannerShow,
  updateBanner,
  updateXcxfmBanner,
} from '@admin/api/ops'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const OSS_BASE = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/'

const route = useRoute()
const bannerType = computed(() => Number(route.meta.bannerType ?? 0))
const pageTitle = computed(() => String(route.meta.title || '轮播图管理'))
const showPlatformColumn = computed(() => bannerType.value === 1 || bannerType.value === 2)
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
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = reactive({
  bid: '',
  manage_main_photo_id: '',
  title: '',
  subheading: '',
  badescribe: '',
  sort: 0,
  website: '',
  platformType: 1,
  is_show: 1,
})

function bannerImageUrl(row: Record<string, unknown>) {
  const path = String(row.path || '')
  const name = String(row.name || '')
  if (!path && !name) return ''
  if (path.includes('https') || path.startsWith('http://')) {
    return `${path}${name}`
  }
  return `${OSS_BASE}${path.replace(/^\//, '')}/${name.replace(/^\//, '')}`
}

function formatTime(val: unknown) {
  if (!val) return '-'
  const s = String(val)
  return s.length >= 16 ? s.slice(0, 16) : s
}

function canDelete(row: Record<string, unknown>) {
  // 与 Java 小程序加载页一致：已显示的不可删
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
  form.sort = 0
  form.website = ''
  form.platformType = 1
  form.is_show = 1
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
  form.sort = Number(row.sort || 0)
  form.website = String(row.website || '')
  form.platformType = Number(row.platformType || 1)
  form.is_show = Number(row.isShow ?? 1)
  isEdit.value = true
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.manage_main_photo_id.trim()) {
    ElMessage.warning('请填写图片附件ID')
    return
  }
  saving.value = true
  try {
    const payload = {
      bid: form.bid,
      manage_main_photo_id: form.manage_main_photo_id.trim(),
      title: form.title,
      subheading: form.subheading,
      badescribe: form.badescribe,
      sort: form.sort,
      website: form.website,
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
</style>
