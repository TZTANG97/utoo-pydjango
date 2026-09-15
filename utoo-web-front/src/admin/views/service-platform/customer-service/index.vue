<template>
  <admin-page-card title="客服显示设置">
    <el-form label-width="140px" style="max-width: 480px">
      <el-form-item label="显示客服入口">
        <el-switch v-model="form.is_show" :active-value="1" :inactive-value="0" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </el-form-item>
    </el-form>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onActivated, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { getIshowSetting, saveIshowSetting } from '@admin/api/service-platform'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const saving = ref(false)
const form = reactive({
  is_show: 0,
})

async function loadSetting() {
  const res = await getIshowSetting()
  if (isAjaxOk(res) && res.obj && typeof res.obj === 'object') {
    const data = res.obj as Record<string, unknown>
    form.is_show = Number(data.is_show ?? 0)
  }
}

onMounted(() => {
  void loadSetting()
})

onActivated(() => {
  void loadSetting()
})

async function handleSave() {
  saving.value = true
  try {
    const res = await saveIshowSetting({ is_show: form.is_show })
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
