<template>
  <el-dialog
    v-model="visible"
    title="从相册选择图片"
    width="780px"
    destroy-on-close
    @open="onOpen"
  >
    <el-form :inline="true" class="picker-filter" @submit.prevent>
      <el-form-item label="相册">
        <el-select
          v-model="albumId"
          placeholder="选择相册"
          filterable
          style="width: 220px"
          @change="onAlbumChange"
        >
          <el-option
            v-for="item in albums"
            :key="String(item.id)"
            :label="String(item.albumName || item.album_name || item.id)"
            :value="Number(item.id)"
          />
        </el-select>
      </el-form-item>
    </el-form>

    <div v-loading="loading" class="image-grid">
      <button
        v-for="img in images"
        :key="String(img.id)"
        type="button"
        class="image-item"
        :class="{ active: selectedId === Number(img.id) }"
        @click="selectImage(img)"
      >
        <img :src="imageUrl(img)" :alt="String(img.name || '')" />
      </button>
      <div v-if="!loading && !images.length" class="empty">暂无图片</div>
    </div>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="loadImages"
      />
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :disabled="!selectedUrl" @click="confirm">插入图片</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchAlbumImages, fetchAlbumList } from '@admin/api/ops'

const OSS_BASE = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/'

const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ select: [url: string] }>()

const albums = ref<Record<string, unknown>[]>([])
const images = ref<Record<string, unknown>[]>([])
const albumId = ref<number | undefined>()
const loading = ref(false)
const total = ref(0)
const selectedId = ref<number | null>(null)
const selectedUrl = ref('')
const pagination = reactive({ page: 1, pageSize: 12 })

function mediaUrl(path: unknown, name: unknown) {
  const p = String(path || '')
  const n = String(name || '')
  if (!p && !n) return ''
  if (p.includes('https') || p.startsWith('http://')) {
    return p.includes(n) ? p : `${p.replace(/\/?$/, '/')}${n}`
  }
  return `${OSS_BASE}${p.replace(/^\//, '')}/${n.replace(/^\//, '')}`
}

function imageUrl(row: Record<string, unknown>) {
  return mediaUrl(row.path, row.name)
}

async function onOpen() {
  selectedId.value = null
  selectedUrl.value = ''
  pagination.page = 1
  await loadAlbums()
}

async function loadAlbums() {
  const res = await fetchAlbumList({ draw: 1, start: 0, length: 200 })
  albums.value = (Array.isArray(res?.data) ? res.data : []) as Record<string, unknown>[]
  if (!albums.value.length) {
    albumId.value = undefined
    images.value = []
    total.value = 0
    return
  }
  const preferred =
    albums.value.find((a) => Number(a.albumDefault) === 1) || albums.value[0]
  albumId.value = Number(preferred.id)
  await loadImages()
}

function onAlbumChange() {
  pagination.page = 1
  selectedId.value = null
  selectedUrl.value = ''
  return loadImages()
}

async function loadImages() {
  if (!albumId.value) return
  loading.value = true
  try {
    const start = (pagination.page - 1) * pagination.pageSize
    const res = await fetchAlbumImages({
      id: albumId.value,
      draw: pagination.page,
      start,
      length: pagination.pageSize,
    })
    images.value = (Array.isArray(res?.data) ? res.data : []) as Record<string, unknown>[]
    total.value = Number(res?.recordsTotal || 0)
  } finally {
    loading.value = false
  }
}

function selectImage(img: Record<string, unknown>) {
  selectedId.value = Number(img.id)
  selectedUrl.value = imageUrl(img)
}

function confirm() {
  if (!selectedUrl.value) {
    ElMessage.warning('请选择图片')
    return
  }
  emit('select', selectedUrl.value)
  visible.value = false
}
</script>

<style scoped lang="scss">
.picker-filter {
  margin-bottom: 8px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 10px;
  min-height: 220px;
  max-height: 360px;
  overflow: auto;
  padding: 4px;
}

.image-item {
  padding: 0;
  border: 2px solid transparent;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f7fa;
  cursor: pointer;
  aspect-ratio: 1;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  &:hover {
    border-color: var(--el-color-primary-light-5);
  }

  &.active {
    border-color: var(--el-color-primary);
    box-shadow: 0 0 0 1px var(--el-color-primary-light-7);
  }
}

.empty {
  grid-column: 1 / -1;
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 48px 0;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
