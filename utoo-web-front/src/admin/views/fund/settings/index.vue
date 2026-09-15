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
        <el-button :disabled="!dirty" @click="handleReset">取消/重置</el-button>
      </el-form-item>
    </el-form>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { fetchFundSetting, saveFundRates, isAjaxOk } from '@admin/api/fund'

const saving = ref(false)
const form = reactive({ rmbRate: 0, usRate: 0 })
const loaded = reactive({ rmbRate: 0, usRate: 0 })

const dirty = computed(
  () => Number(form.rmbRate) !== Number(loaded.rmbRate) || Number(form.usRate) !== Number(loaded.usRate)
)

function applyLoaded(obj: Record<string, unknown>) {
  const rmb = Number(obj.rmbRate || 0)
  const us = Number(obj.usRate || 0)
  form.rmbRate = rmb
  form.usRate = us
  loaded.rmbRate = rmb
  loaded.usRate = us
}

async function loadSetting() {
  const res = await fetchFundSetting()
  if (isAjaxOk(res) && res.obj) {
    applyLoaded(res.obj as Record<string, unknown>)
  }
}

onMounted(() => {
  void loadSetting()
})

function handleReset() {
  form.rmbRate = loaded.rmbRate
  form.usRate = loaded.usRate
  ElMessage.success('已恢复为当前已保存值')
}

async function handleSave() {
  saving.value = true
  try {
    const res = await saveFundRates({ ...form })
    if (!isAjaxOk(res)) {
      ElMessage.error(String(res.msg || '保存失败'))
      return
    }
    loaded.rmbRate = Number(form.rmbRate)
    loaded.usRate = Number(form.usRate)
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}
</script>
