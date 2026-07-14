<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面不存在或尚未迁移</p>
    <el-button type="primary" @click="$router.replace('/dashboard')">返回工作台</el-button>
  </div>
</template>

<style scoped lang="scss">
.not-found {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;

  h1 {
    margin: 0;
    font-size: 56px;
    color: #f97316;
  }

  p {
    margin: 0 0 8px;
    color: #909399;
  }
}
</style>
