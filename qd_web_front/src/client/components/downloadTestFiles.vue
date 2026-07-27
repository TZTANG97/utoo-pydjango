<template>
  <div class="download-test-files">
    <el-dialog
      title="测试资料"
      :visible.sync="value"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false">
      <div class="test-file-list">
          <a target="_blank" :href="`${item['path']}/${item['name']}`" v-for="(item, idx) in list" :key="idx">{{ item['info'] }}</a>
      </div>
      <span slot="footer" class="dialog-footer">
    <el-button @click="$emit('input', false)">取 消</el-button>
    <el-button type="primary" @click="$emit('input', false)">确 定</el-button>
  </span>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: "DownloadTestFiles",
  props: {
    value: {
      type: Boolean,
      default: false
    },
    list: {
      type: Array,
      default: () => []
    }
  }
}
</script>

<style>
.el-dialog {
  width: 500px !important;
}
</style>

<style scoped lang="scss">
.test-file-list {
  a {
    display: inline-block;
    color: var(--mainColor);
    font-size: 17px;

    &:nth-child(n+1) {
      margin: 0 15px 15px 0;
    }

    &:hover {
      border-bottom: 1px solid var(--mainColor);
      margin-bottom: 14px;
    }
  }
}
</style>
