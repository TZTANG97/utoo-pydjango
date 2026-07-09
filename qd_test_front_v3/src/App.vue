<template>
  <router-view />
</template>

<script>
export default {
  name: 'App',
}
</script>

<style lang="scss">
.app-wrapper {
  min-width: 1240px;
}

:root {
  --mainColor: #f39800;
  --mainHoverColor: #e58f00;
  --menusColor: #ffffff;
}

.test-app {
  overflow-y: scroll;

  &::-webkit-scrollbar {
    display: none;
  }
}

.body-bg {
  background-color: #f5f5f5 !important;
}

#nprogress .bar {
  background: var(--mainColor) !important;
}

.required-label {
  .el-form-item__label::before {
    content: '*';
    color: #f56c6c;
    margin-right: 5px;
  }
}

.btf-roll {
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(233, 99, 2, 0.3);
    border-radius: 10px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: var(--mainColor);
  }
}
</style>
