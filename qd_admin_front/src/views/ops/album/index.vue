<template>
  <admin-page-card title="相册管理">
    <div class="tab-row">
      <el-button type="primary" @click="openCreate">创建相册</el-button>
    </div>
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="相册名称">
        <el-input v-model="filters.name" clearable placeholder="相册名称" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload()">搜索</el-button>
      </el-form-item>
    </el-form>
    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column label="封面" width="90" align="center">
        <template #default="{ row }">
          <el-image
            v-if="coverUrl(row)"
            class="cover"
            :src="coverUrl(row)"
            fit="cover"
            :preview-src-list="[coverUrl(row)]"
            preview-teleported
          />
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="albumName" label="相册名称" min-width="160" />
      <el-table-column prop="albumSequence" label="排序" width="90" align="center" />
      <el-table-column prop="photoCount" label="图片数" width="90" align="center" />
      <el-table-column label="默认" width="90" align="center">
        <template #default="{ row }">{{ Number(row.albumDefault) === 1 ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openImages(row)">图片</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-if="Number(row.albumDefault) !== 1"
            link
            type="primary"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑相册' : '创建相册'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="相册名称" required>
          <el-input v-model="form.albumName" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.albumSequence" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="imageDialogVisible" title="相册图片" width="760px">
      <el-table v-loading="imageLoading" :data="images" border stripe>
        <el-table-column label="图片" width="90" align="center">
          <template #default="{ row }">
            <el-image
              v-if="imageUrl(row)"
              class="cover"
              :src="imageUrl(row)"
              fit="cover"
              :preview-src-list="[imageUrl(row)]"
              preview-teleported
            />
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="addTime" label="上传时间" width="170" />
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleCover(row)">设为封面</el-button>
            <el-button link type="primary" @click="handleImageDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="imagePagination.page"
          v-model:page-size="imagePagination.pageSize"
          layout="total, prev, pager, next"
          :total="imageTotal"
          @current-change="loadImages"
        />
      </div>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  deleteAlbum,
  deleteAlbumImage,
  fetchAlbumImages,
  fetchAlbumList,
  getAlbumDetail,
  saveAlbum,
  setAlbumCover,
} from '@/api/ops'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const OSS_BASE = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/'
const filters = reactive({ name: '' })
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  id: undefined as number | undefined,
  albumName: '',
  albumSequence: 0,
})

const imageDialogVisible = ref(false)
const imageLoading = ref(false)
const images = ref<Record<string, unknown>[]>([])
const imageTotal = ref(0)
const currentAlbumId = ref<number | undefined>()
const imagePagination = reactive({ page: 1, pageSize: 10 })

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchAlbumList({ ...params, name: filters.name })
)

function mediaUrl(path: unknown, name: unknown) {
  const p = String(path || '')
  const n = String(name || '')
  if (!p && !n) return ''
  if (p.includes('https') || p.startsWith('http://')) {
    return p.includes(n) ? p : `${p.replace(/\/?$/, '/')}${n}`
  }
  return `${OSS_BASE}${p.replace(/^\//, '')}/${n.replace(/^\//, '')}`
}

function coverUrl(row: Record<string, unknown>) {
  return mediaUrl(row.coverPath, row.coverName)
}

function imageUrl(row: Record<string, unknown>) {
  return mediaUrl(row.path, row.name)
}

function reload() {
  pagination.page = 1
  return load({ name: filters.name })
}

function openCreate() {
  Object.assign(form, { id: undefined, albumName: '', albumSequence: 0 })
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getAlbumDetail(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  Object.assign(form, {
    id: Number(obj.id),
    albumName: String(obj.albumName || obj.album_name || ''),
    albumSequence: Number(obj.albumSequence || obj.album_sequence || 0),
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.albumName.trim()) {
    ElMessage.warning('请输入相册名称')
    return
  }
  saving.value = true
  try {
    const res = await saveAlbum({
      id: form.id,
      albumName: form.albumName.trim(),
      albumSequence: form.albumSequence,
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
  await ElMessageBox.confirm('确认删除该相册？', '提示', { type: 'warning' })
  const res = await deleteAlbum(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

async function openImages(row: Record<string, unknown>) {
  currentAlbumId.value = Number(row.id)
  imagePagination.page = 1
  imageDialogVisible.value = true
  await loadImages()
}

async function loadImages() {
  if (!currentAlbumId.value) return
  imageLoading.value = true
  try {
    const start = (imagePagination.page - 1) * imagePagination.pageSize
    const res = await fetchAlbumImages({
      id: currentAlbumId.value,
      draw: imagePagination.page,
      start,
      length: imagePagination.pageSize,
    })
    images.value = res.data || []
    imageTotal.value = Number(res.recordsTotal || 0)
  } finally {
    imageLoading.value = false
  }
}

async function handleCover(row: Record<string, unknown>) {
  if (!currentAlbumId.value) return
  const res = await setAlbumCover(currentAlbumId.value, String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('设置成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '设置失败'))
  }
}

async function handleImageDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认删除该图片？', '提示', { type: 'warning' })
  const res = await deleteAlbumImage(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await loadImages()
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}

onMounted(() => reload())
</script>

<style scoped lang="scss">
.tab-row {
  margin-bottom: 12px;
}
.filter-form {
  margin-bottom: 12px;
}
.cover {
  width: 40px;
  height: 40px;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
