<template>
  <el-card shadow="never" class="page-card">
    <template v-if="title" #header>
      <div class="card-header">
        <span>{{ title }}</span>
        <slot name="actions" />
      </div>
    </template>
    <slot />
  </el-card>
</template>

<script setup lang="ts">
defineProps<{ title?: string }>()
</script>

<style scoped lang="scss">
.page-card {
  min-height: calc(100vh - 120px);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
</style>
