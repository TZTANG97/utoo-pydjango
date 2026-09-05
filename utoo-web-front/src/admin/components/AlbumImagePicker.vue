<template>
  <el-dialog
    v-model="visible"
    title="从相册选择图片"
    width="780px"
    destroy-on-close
    append-to-body
    align-center
    :z-index="5200"
    @open="onOpen"
  >
    <div v-loading="loading" class="image-grid">
      <button
        v-for="img in images"
        :key="String(img.id)"
        type="button"
        class="image-item"
        :class="{ active: selectedId === Number(img.id) }"
        @click="selectImage(img)"
      >
        <img :src="imageUrl(img)" :alt="String(img.name || '')" referrerpolicy="no-referrer" />
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
      <el-button type="primary" :disabled="!selectedPick" @click="confirm">确认选择</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchGoodsAlbumImages } from '@admin/api/ops'

const OSS_BASE = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/'

type AlbumImagePick = { id: number; url: string }

const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ select: [pick: AlbumImagePick] }>()
const selectedPick = ref<AlbumImagePick | null>(null)

const images = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const total = ref(0)
const selectedId = ref<number | null>(null)
const pagination = reactive({ page: 1, pageSize: 16 })

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
  selectedPick.value = null
  pagination.page = 1
  await loadImages()
}

async function loadImages() {
  loading.value = true
  try {
    const start = (pagination.page - 1) * pagination.pageSize
    // 对齐 Java goods_img_album：列出 path=goods 的图片，不按相册 id 过滤
    const res = await fetchGoodsAlbumImages({
      draw: pagination.page,
      start,
      length: pagination.pageSize,
    })
    images.value = (Array.isArray(res?.data) ? res.data : []) as Record<string, unknown>[]
    total.value = Number(res?.recordsTotal || 0)
  } catch {
    images.value = []
    total.value = 0
    ElMessage.error('图片列表加载失败')
  } finally {
    loading.value = false
  }
}

function selectImage(img: Record<string, unknown>) {
  const id = Number(img.id)
  const url = imageUrl(img)
  selectedId.value = id
  selectedPick.value = Number.isFinite(id) && id > 0 && url ? { id, url } : null
}

function confirm() {
  if (!selectedPick.value) {
    ElMessage.warning('请选择图片')
    return
  }
  emit('select', selectedPick.value)
  visible.value = false
}
</script>

<style scoped lang="scss">
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
