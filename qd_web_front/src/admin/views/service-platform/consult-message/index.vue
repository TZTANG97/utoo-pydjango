<template>
  <admin-page-card title="咨询消息设置">
    <el-form label-width="140px" style="max-width: 560px">
      <el-form-item label="公众号用户ID">
        <el-input v-model="form.gzh_userId" placeholder="gzh_userId" />
      </el-form-item>
      <el-form-item label="公众号消息推送">
        <el-switch v-model="form.gzh_issend" :active-value="1" :inactive-value="0" />
      </el-form-item>
      <el-form-item label="服务邮箱">
        <el-input v-model="form.service_mail" placeholder="service_mail" />
      </el-form-item>
      <el-form-item label="邮件通知">
        <el-switch v-model="form.mail_issend" :active-value="1" :inactive-value="0" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </el-form-item>
    </el-form>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { getConsultSetting, saveConsultSetting } from '@admin/api/service-platform'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const saving = ref(false)
const form = reactive({
  gzh_userId: '',
  gzh_issend: 0,
  service_mail: '',
  mail_issend: 0,
})

onMounted(async () => {
  const res = await getConsultSetting()
  if (isAjaxOk(res) && res.obj && typeof res.obj === 'object') {
    const data = res.obj as Record<string, unknown>
    form.gzh_userId = String(data.gzh_userId || '')
    form.gzh_issend = Number(data.gzh_issend ?? 0)
    form.service_mail = String(data.service_mail || '')
    form.mail_issend = Number(data.mail_issend ?? 0)
  }
})

async function handleSave() {
  saving.value = true
  try {
    const res = await saveConsultSetting({ ...form })
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
