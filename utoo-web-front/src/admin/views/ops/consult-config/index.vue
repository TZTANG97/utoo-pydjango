<template>
  <admin-page-card title="咨询方式设置">
    <el-form v-loading="loading" label-width="100px" class="consult-form" style="max-width: 560px">
      <el-form-item label="公司名称" required>
        <el-input v-model="form.qdName" />
      </el-form-item>
      <el-form-item label="服务热线">
        <el-input v-model="form.serviceMobile" />
      </el-form-item>
      <el-form-item label="传真">
        <el-input v-model="form.qdFax" />
      </el-form-item>
      <el-form-item label="地址" required>
        <el-input v-model="form.qdAddress" />
      </el-form-item>
      <el-form-item label="电子邮箱">
        <el-input v-model="form.qdEmail" />
      </el-form-item>
      <el-form-item>
        <el-button type="warning" :loading="saving" @click="handleSubmit">保存</el-button>
      </el-form-item>
    </el-form>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { getConsultConfig, saveConsultConfig } from '@admin/api/ops'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const loading = ref(false)
const saving = ref(false)
const form = reactive({
  id: undefined as number | undefined,
  qdName: '',
  serviceMobile: '',
  qdFax: '',
  qdAddress: '',
  qdEmail: '',
})

async function load() {
  loading.value = true
  try {
    const res = await getConsultConfig()
    if (isAjaxOk(res) && res.obj) {
      const obj = res.obj as Record<string, unknown>
      Object.assign(form, {
        id: obj.id ? Number(obj.id) : undefined,
        qdName: String(obj.qdName || ''),
        serviceMobile: String(obj.serviceMobile || ''),
        qdFax: String(obj.qdFax || ''),
        qdAddress: String(obj.qdAddress || ''),
        qdEmail: String(obj.qdEmail || ''),
      })
    } else {
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    }
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!form.qdName.trim()) {
    ElMessage.warning('请输入公司名称')
    return
  }
  if (!form.qdAddress.trim()) {
    ElMessage.warning('请输入地址')
    return
  }
  saving.value = true
  try {
    const res = await saveConsultConfig({ ...form })
    if (isAjaxOk(res)) {
      ElMessage.success('咨询方式设置成功')
      await load()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => load())
</script>

<style scoped lang="scss">
.consult-form {
  margin-top: 24px;
}
</style>
