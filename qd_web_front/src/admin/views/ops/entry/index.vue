<template>
  <admin-page-card title="帖子列表管理">
    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column prop="addTime" label="创建时间" min-width="160" />
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="userName" label="用户名" width="140" />
      <el-table-column label="是否显示" width="100" align="center">
        <template #default="{ row }">
          {{ Number(row.isAudit) === 1 ? '上架' : '下架' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button link type="primary" @click="handleAudit(row)">
            {{ Number(row.isAudit) === 1 ? '下架' : '上架' }}
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
        @current-change="() => load()"
      />
    </div>

    <el-dialog
      v-model="detailVisible"
      title="帖子详情"
      width="860px"
      top="4vh"
      destroy-on-close
      class="entry-detail-dialog"
    >
      <div v-loading="detailLoading" class="detail-body">
        <div class="meta">
          <h3 class="title">{{ detail.title || '-' }}</h3>
          <p class="sub">
            <span>{{ detail.userName || '-' }}</span>
            <span>·</span>
            <span>{{ detail.addTime || '-' }}</span>
          </p>
        </div>

        <div v-if="photos.length" class="photos">
          <el-image
            v-for="(url, i) in photos"
            :key="`${url}-${i}`"
            :src="url"
            :preview-src-list="photos"
            :initial-index="i"
            fit="cover"
            class="photo"
          />
        </div>

        <div class="section-label">内容</div>
        <div class="content" v-html="decodedContent" />

        <div class="section-label">评论区（{{ comments.length }}）</div>
        <div v-if="comments.length" class="comments">
          <div v-for="c in comments" :key="String(c.id)" class="comment-item">
            <div class="comment-head">
              <el-avatar :size="36" :src="String(c.avatar || '')" />
              <div>
                <div class="author">{{ c.userName || '-' }}</div>
                <div class="time">{{ c.addTimes || c.addTime || '' }}</div>
              </div>
            </div>
            <div class="comment-text">{{ c.content || '' }}</div>
            <div v-if="Array.isArray(c.replies) && c.replies.length" class="replies">
              <div v-for="r in c.replies as Record<string, unknown>[]" :key="String(r.id)" class="reply-item">
                <el-avatar :size="28" :src="String(r.avatar || '')" />
                <div class="reply-main">
                  <div class="reply-author">
                    <span>{{ r.userName || '-' }}</span>
                    <template v-if="r.puserName">
                      <span class="arrow">›</span>
                      <span>{{ r.puserName }}</span>
                    </template>
                  </div>
                  <div class="reply-text">{{ r.content || '' }}</div>
                  <div class="time">{{ r.addTimes || r.addTime || '' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无评论" :image-size="72" />
      </div>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { auditEntry, fetchEntryList, getEntryDetail } from '@admin/api/ops'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const { loading, rows, total, pagination, load } = useDataTable(fetchEntryList)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = reactive<Record<string, unknown>>({})
const comments = ref<Record<string, unknown>[]>([])
const photos = ref<string[]>([])

/** 对齐 Java commentSection.initContent：解码 URL 编码的富文本 */
function decodeEntryContent(raw: unknown): string {
  let text = String(raw ?? '')
  if (!text) return ''
  let prev = ''
  for (let i = 0; i < 3 && text !== prev; i += 1) {
    prev = text
    try {
      text = decodeURIComponent(text.replace(/\+/g, ' '))
    } catch {
      break
    }
  }
  return text.replace(
    /<img/gi,
    '<img style="max-width:100%;height:auto;display:block;margin:8px auto;"'
  )
}

const decodedContent = computed(() => decodeEntryContent(detail.content))

onMounted(() => load())

async function openDetail(row: Record<string, unknown>) {
  detailVisible.value = true
  detailLoading.value = true
  comments.value = []
  photos.value = []
  Object.keys(detail).forEach((k) => delete detail[k])
  try {
    const res = await getEntryDetail(String(row.id))
    if (!isAjaxOk(res) || !res.obj) {
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    Object.assign(detail, obj)
    const list = Array.isArray(obj.commentList)
      ? obj.commentList
      : Array.isArray(obj.comments)
        ? obj.comments
        : []
    comments.value = list as Record<string, unknown>[]
    const photoList = Array.isArray(obj.photos)
      ? obj.photos
      : Array.isArray(obj.stringList)
        ? obj.stringList
        : []
    photos.value = photoList.map((x) => String(x)).filter(Boolean)
  } finally {
    detailLoading.value = false
  }
}

async function handleAudit(row: Record<string, unknown>) {
  const res = await auditEntry(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('操作成功')
    await load()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.detail-body {
  max-height: calc(92vh - 120px);
  overflow: auto;
  padding-right: 4px;
}
.meta {
  margin-bottom: 12px;
  .title {
    margin: 0 0 6px;
    font-size: 18px;
    font-weight: 600;
    line-height: 1.4;
    word-break: break-word;
  }
  .sub {
    margin: 0;
    color: #64748b;
    font-size: 13px;
    display: flex;
    gap: 8px;
  }
}
.photos {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  .photo {
    width: 120px;
    height: 90px;
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
  }
}
.section-label {
  margin: 16px 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  border-bottom: 1px solid #eee;
  padding-bottom: 6px;
}
.content {
  line-height: 1.7;
  word-break: break-word;
  overflow-wrap: anywhere;
  :deep(img) {
    max-width: 100%;
    height: auto;
  }
  :deep(p) {
    margin: 0 0 8px;
  }
}
.comments {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.comment-item {
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}
.comment-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  .author {
    font-weight: 500;
    font-size: 14px;
  }
}
.time {
  font-size: 12px;
  color: #94a3b8;
}
.comment-text {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
.replies {
  margin: 10px 0 0 46px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.reply-item {
  display: flex;
  gap: 8px;
}
.reply-main {
  flex: 1;
  background: #f8fafc;
  border-radius: 8px;
  padding: 8px 10px;
}
.reply-author {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  .arrow {
    margin: 0 4px;
    color: #94a3b8;
  }
}
.reply-text {
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
