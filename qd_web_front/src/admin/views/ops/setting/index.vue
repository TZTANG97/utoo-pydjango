<template>
  <admin-page-card :title="pageTitle">
    <!-- 二手 / 租赁：图片配置 -->
    <template v-if="isImageSetting">
      <el-form label-width="110px" class="setting-form">
        <el-form-item label="图片地址" required>
          <el-input
            v-model="content"
            placeholder="填写图片完整 URL，或相对路径（如 goods/xxx.jpg）"
          />
        </el-form-item>
        <el-form-item label="预览">
          <div class="img-preview">
            <el-image
              v-if="previewUrl"
              :src="previewUrl"
              fit="contain"
              :preview-src-list="[previewUrl]"
              preview-teleported
            />
            <span v-else class="placeholder">暂无图片</span>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </el-form-item>
      </el-form>
    </template>

    <!-- 设备服务 / 产品测试 / 商业支持：富文本 -->
    <template v-else>
      <div class="html-layout">
        <div class="editor-pane">
          <HtmlRichEditor :key="settingType" v-model="content">
            <template #actions>
              <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
            </template>
          </HtmlRichEditor>
        </div>
        <div class="preview-pane">
          <div class="preview-title">预览</div>
          <div class="phone-frame">
            <div class="phone-notch" />
            <div class="html-preview" v-html="previewHtml" />
          </div>
        </div>
      </div>
    </template>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import HtmlRichEditor from '@admin/components/HtmlRichEditor.vue'
import { getOpsSetting, saveOpsSetting } from '@admin/api/ops'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const OSS_BASE = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/'

const route = useRoute()
const pageTitle = computed(() => String(route.meta.title || '运营设置'))
const settingType = computed(() => String(route.meta.settingType || ''))
const isImageSetting = computed(
  () => settingType.value === 'rent' || settingType.value === 'secondhand'
)
const content = ref('')
const saving = ref(false)

const previewUrl = computed(() => {
  const raw = content.value.trim()
  if (!raw) return ''
  if (raw.startsWith('http://') || raw.startsWith('https://')) return raw
  if (raw.startsWith('<')) {
    const m = raw.match(/src=["']([^"']+)["']/i)
    return m?.[1] || ''
  }
  return `${OSS_BASE}${raw.replace(/^\//, '')}`
})

const previewHtml = computed(() => {
  const raw = content.value.trim()
  return raw || '<p class="empty-tip">暂无内容</p>'
})

async function fetchSetting() {
  const res = await getOpsSetting(settingType.value)
  if (isAjaxOk(res) && res.obj) {
    const data = res.obj as Record<string, unknown>
    content.value = String(data.imgsrc || data.content || '')
  } else {
    content.value = ''
  }
}

onMounted(fetchSetting)
watch(settingType, fetchSetting)

async function handleSave() {
  if (isImageSetting.value && !content.value.trim()) {
    ElMessage.warning('请填写图片地址')
    return
  }
  saving.value = true
  try {
    const res = await saveOpsSetting(settingType.value, content.value)
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.setting-form {
  max-width: 720px;
}

.img-preview {
  width: 600px;
  max-width: 100%;
  height: 300px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  overflow: hidden;

  .el-image {
    width: 100%;
    height: 100%;
  }

  .placeholder {
    color: var(--el-text-color-secondary);
  }
}

.html-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
  align-items: start;
}

.preview-pane {
  position: sticky;
  top: 12px;
}

.preview-title {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.phone-frame {
  width: 100%;
  max-width: 300px;
  margin: 0 auto;
  border: 1px solid #d8dde6;
  border-radius: 28px;
  background: #111827;
  padding: 12px 10px 18px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
}

.phone-notch {
  width: 88px;
  height: 8px;
  margin: 0 auto 10px;
  border-radius: 999px;
  background: #374151;
}

.html-preview {
  height: 520px;
  overflow: auto;
  border-radius: 16px;
  padding: 12px;
  background: #fff;
  font-size: 13px;
  line-height: 1.6;
  color: #1f2937;

  :deep(img) {
    max-width: 100%;
    height: auto;
  }

  :deep(.empty-tip) {
    margin: 0;
    color: #9ca3af;
    text-align: center;
    padding-top: 40px;
  }
}

@media (max-width: 1100px) {
  .html-layout {
    grid-template-columns: 1fr;
  }

  .preview-pane {
    position: static;
  }

  .phone-frame {
    max-width: 360px;
  }
}
</style>
