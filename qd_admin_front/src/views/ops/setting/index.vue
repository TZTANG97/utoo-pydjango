<template>
  <admin-page-card :title="pageTitle">
    <!-- 二手 / 租赁：按 Java 为图片配置 -->
    <template v-if="isImageSetting">
      <el-form label-width="110px">
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

    <!-- 设备服务 / 产品测试 / 商业支持：富文本 HTML -->
    <template v-else>
      <el-form label-width="100px">
        <el-form-item label="页面内容">
          <el-input
            v-model="content"
            type="textarea"
            :rows="18"
            placeholder="支持 HTML 富文本（对应 Java KindEditor 字段 imgsrc）"
          />
        </el-form-item>
        <el-form-item label="预览">
          <div class="html-preview" v-html="content || '<p>暂无内容</p>'" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </el-form-item>
      </el-form>
    </template>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { getOpsSetting, saveOpsSetting } from '@/api/ops'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

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
.img-preview {
  width: 600px;
  max-width: 100%;
  height: 300px;
  border: 1px solid var(--el-border-color);
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

.html-preview {
  width: 100%;
  min-height: 160px;
  max-height: 360px;
  overflow: auto;
  border: 1px solid var(--el-border-color);
  padding: 12px;
  background: #fff;
}
</style>
