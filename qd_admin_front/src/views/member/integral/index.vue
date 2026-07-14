<template>
  <admin-page-card title="会员积分设置">
    <div class="section-bar">积分兑换比例</div>
    <div class="setting-body">
      <div class="label">会员积分兑换比例设置：</div>
      <div class="ratio-row">
        <span>100积分兑换</span>
        <el-input
          v-model="ratioText"
          class="ratio-input"
          clearable
          @keyup.enter="handleSubmit"
        />
        <span>元</span>
      </div>
      <el-button class="submit-btn" :loading="saving" @click="handleSubmit">提交</el-button>
    </div>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { getIntegralSetting, saveIntegralRatio } from '@/api/member'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const ratioText = ref('1.0')
const saving = ref(false)

onMounted(async () => {
  const res = await getIntegralSetting()
  if (isAjaxOk(res) && res.obj) {
    const data = res.obj as Record<string, unknown>
    const ratio = data.integralConvertRatio
    ratioText.value = ratio == null || ratio === '' ? '1.0' : String(ratio)
  }
})

async function handleSubmit() {
  const raw = ratioText.value.trim()
  if (!raw || Number.isNaN(Number(raw)) || Number(raw) < 0) {
    ElMessage.warning('金额不能为空或填写错误！')
    return
  }
  saving.value = true
  try {
    const res = await saveIntegralRatio(Number(raw))
    if (isAjaxOk(res)) {
      ElMessage.success('积分规则设置成功')
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.section-bar {
  margin: -4px 0 20px;
  padding: 8px 12px;
  background: #5a5a5a;
  color: #fff;
  font-size: 14px;
}

.setting-body {
  padding: 8px 4px 24px;
}

.label {
  margin-bottom: 16px;
  color: var(--el-text-color-regular);
}

.ratio-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 14px;
}

.ratio-input {
  width: 160px;
}

.submit-btn {
  min-width: 88px;
}
</style>
