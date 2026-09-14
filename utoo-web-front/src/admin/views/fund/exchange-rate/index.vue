<template>
  <admin-page-card title="美金汇率设置">
    <el-form label-width="140px" style="max-width: 480px">
      <el-form-item label="美金汇率">
        <el-input-number v-model="rate" :min="0" :precision="4" :step="0.01" style="width: 200px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        <el-button :disabled="!dirty" @click="handleReset">取消/重置</el-button>
      </el-form-item>
    </el-form>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { fetchFundSetting, saveExchangeRate, isAjaxOk } from '@admin/api/fund'

const saving = ref(false)
const rate = ref(1)
const loadedRate = ref(1)

const dirty = computed(() => Number(rate.value) !== Number(loadedRate.value))

async function loadSetting() {
  const res = await fetchFundSetting()
  if (isAjaxOk(res) && res.obj) {
    const v = Number((res.obj as Record<string, unknown>).usExchangeRate || 1)
    rate.value = v
    loadedRate.value = v
  }
}

onMounted(() => {
  void loadSetting()
})

function handleReset() {
  rate.value = loadedRate.value
  ElMessage.success('已恢复为当前已保存值')
}

async function handleSave() {
  saving.value = true
  try {
    const res = await saveExchangeRate({ usExchangeRate: rate.value })
    if (!isAjaxOk(res)) {
      ElMessage.error(String(res.msg || '保存失败'))
      return
    }
    loadedRate.value = Number(rate.value)
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}
</script>
