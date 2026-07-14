<template>
  <admin-page-card title="美金汇率设置">
    <el-form label-width="140px" style="max-width: 480px">
      <el-form-item label="美金汇率">
        <el-input-number v-model="rate" :min="0" :precision="4" :step="0.01" style="width: 200px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </el-form-item>
    </el-form>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchFundSetting, saveExchangeRate, isAjaxOk } from '@/api/fund'

const saving = ref(false)
const rate = ref(1)

onMounted(async () => {
  const res = await fetchFundSetting()
  if (isAjaxOk(res) && res.obj) {
    rate.value = Number((res.obj as Record<string, unknown>).usExchangeRate || 1)
  }
})

async function handleSave() {
  saving.value = true
  try {
    const res = await saveExchangeRate({ usExchangeRate: rate.value })
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
