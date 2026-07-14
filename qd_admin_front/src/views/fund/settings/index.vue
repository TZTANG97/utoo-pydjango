<template>
  <admin-page-card title="资金账户设置">
    <el-form label-width="160px" style="max-width: 480px">
      <el-form-item label="人民币年化利率(%)">
        <el-input-number v-model="form.rmbRate" :min="0" :max="100" />
      </el-form-item>
      <el-form-item label="美金年化利率(%)">
        <el-input-number v-model="form.usRate" :min="0" :max="100" />
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
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchFundSetting, saveFundRates, isAjaxOk } from '@/api/fund'

const saving = ref(false)
const form = reactive({ rmbRate: 0, usRate: 0 })

onMounted(async () => {
  const res = await fetchFundSetting()
  if (isAjaxOk(res) && res.obj) {
    const obj = res.obj as Record<string, unknown>
    form.rmbRate = Number(obj.rmbRate || 0)
    form.usRate = Number(obj.usRate || 0)
  }
})

async function handleSave() {
  saving.value = true
  try {
    const res = await saveFundRates({ ...form })
    if (!isAjaxOk(res)) {
      ElMessage.error(String(res.msg || '保存失败'))
      return
    }
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}
</script>
