<template>
  <el-card shadow="never" class="pending-card">
    <template #header>
      <span>{{ title }}</span>
    </template>
    <el-result icon="info" title="功能迁移中">
      <template #sub-title>
        <p>该功能页面正在建设中，请稍后再试。</p>
        <p v-if="legacyUrl" class="legacy-url">关联路径：{{ legacyUrl }}</p>
      </template>
      <template #extra>
        <el-button type="primary" @click="$router.replace('/admin/dashboard')">返回欢迎页</el-button>
      </template>
    </el-result>
    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="说明"
      description="目前已迁移：发票申请管理、支付记录管理、用户还款/付款申请管理、用户复测管理。其余模块会按业务优先级逐步迁移。"
    />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@admin/stores/user'

const route = useRoute()
const userStore = useUserStore()
const menuId = computed(() => String(route.params.menuId || ''))
const meta = computed(() => userStore.pendingMenus[menuId.value])
const title = computed(() => meta.value?.title || '功能迁移中')
const legacyUrl = computed(() => meta.value?.url || '')
</script>

<style scoped lang="scss">
.pending-card {
  max-width: 760px;
}

.legacy-url {
  margin: 8px 0 0;
  color: #909399;
  word-break: break-all;
}
</style>
