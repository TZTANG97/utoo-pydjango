<script>
export default {
  name: "Evaluate",
  data() {
    return {
      form: {
        star: 5,
        evaluate_content: ''
      },
    }
  },
  props: {
    value: {
      type: Boolean,
      default: false
    },
    evaluating: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    submitEval() {
      this.$emit('comfirmOK', this.form)
    },

    handleClose() {
      this.form.star = 5
      this.form.evaluate_content = ''
      this.$emit('update:evaluating', false)
    },
  }
}
</script>

<template>
  <el-dialog
    title="评价"
    :visible.sync="value"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    @close="handleClose">
    <el-form class="sub-form" :model="form" ref="sub-form" label-position="top">
      <el-form-item label="综合评价：" prop="star">
        <el-rate v-model="form.star"></el-rate>
      </el-form-item>
      <el-form-item label="评价内容" prop="evaluate_content">
        <el-input type="textarea" v-model="form.evaluate_content" maxlength="120"></el-input>
      </el-form-item>
    </el-form>
    <span slot="footer" class="dialog-footer">
        <el-button @click="$emit('input', false)">取 消</el-button>
        <el-button type="primary" :loading="evaluating" @click="submitEval">确 定</el-button>
      </span>
  </el-dialog>
</template>

<style scoped>
.el-dialog {
  width: 500px !important;
}

.el-textarea__inner {
  height: 150px !important;
  padding: 5px !important;
}

.el-rate__icon {
  font-size: 25px !important;
}

.el-input {
  width: 300px;
}

.el-dialog__body {
  padding: 0 20px;
}

.el-form-item__label {
  padding: 0 !important;
}
</style>
