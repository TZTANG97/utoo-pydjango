<template>
  <admin-page-card title="自动评价设置">
    <div class="section-title">已验收订单自动评价时间设置</div>
    <el-form label-width="120px" style="max-width: 520px">
      <el-form-item label="时间">
        <el-input-number v-model="form.evaluate_time" :min="1" :max="999" />
      </el-form-item>
      <el-form-item label="单位">
        <el-select v-model="form.evaluate_time_type" style="width: 160px">
          <el-option
            v-for="item in unitOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
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
import { fetchEvaluateSetting, saveEvaluateSetting } from '@/api/order-settings'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const saving = ref(false)
const form = reactive({
  evaluate_time: 7,
  evaluate_time_type: 0,
})

const unitOptions = [
  { label: '天', value: 0 },
  { label: '时', value: 1 },
  { label: '分', value: 2 },
  { label: '秒', value: 3 },
]

onMounted(async () => {
  const res = await fetchEvaluateSetting()
  if (isAjaxOk(res) && res.obj) {
    const data = res.obj as Record<string, unknown>
    form.evaluate_time = Number(data.evaluate_time || 7)
    form.evaluate_time_type = Number(data.evaluate_time_type || 0)
  }
})

async function handleSave() {
  saving.value = true
  try {
    const res = await saveEvaluateSetting({ ...form })
    if (isAjaxOk(res)) {
      ElMessage.success('设置成功')
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '设置失败'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.section-title {
  margin-bottom: 24px;
  font-size: 16px;
  font-weight: 600;
}
</style>
