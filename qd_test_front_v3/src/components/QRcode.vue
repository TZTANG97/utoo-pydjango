<script>
import QRCode from 'qrcode'
import { fetchTpPayStatusApi } from '@/api'

export default {
  name: 'QRcode',
  emits: ['update:modelValue', 'input', 'reload'],
  props: {
    modelValue: {
      default: false,
      type: Boolean,
    },
    value: {
      default: false,
      type: Boolean,
    },
    content: {
      default: '',
      type: String,
    },
    title: {
      default: '微信',
      type: String,
    },
    searchFlag: {
      default: '',
      type: String,
    },
  },
  data() {
    return {
      searching: false,
      timer: null,
      qrDataUrl: '',
      qrError: false,
    }
  },
  computed: {
    visible: {
      get() {
        return !!(this.modelValue || this.value)
      },
      set(val) {
        this.$emit('update:modelValue', val)
        this.$emit('input', val)
      },
    },
  },
  watch: {
    content: {
      immediate: true,
      handler(text) {
        this.renderQr(text)
      },
    },
    visible(val) {
      if (val) {
        this.renderQr(this.content)
        this.startPoll()
      } else {
        this.stopPoll()
      }
    },
  },
  beforeUnmount() {
    this.stopPoll()
  },
  methods: {
    stopPoll() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    },
    startPoll() {
      this.stopPoll()
      if (!this.searchFlag) return
      this.timer = setInterval(() => {
        this.paied()
      }, 1500)
    },
    async renderQr(text) {
      const val = (text || '').trim()
      if (!val) {
        this.qrDataUrl = ''
        this.qrError = false
        return
      }
      try {
        this.qrDataUrl = await QRCode.toDataURL(val, { width: 220, margin: 1 })
        this.qrError = false
      } catch (e) {
        console.error('[QRcode] render failed', e)
        this.qrDataUrl = ''
        this.qrError = true
      }
    },
    onBeforeClose(done) {
      this.stopPoll()
      this.visible = false
      done()
    },
    cancelPay() {
      this.stopPoll()
      this.visible = false
      this.$emit('reload')
    },
    paied() {
      if (!this.searchFlag) return
      fetchTpPayStatusApi({
        outTradeNo: this.searchFlag,
      })
        .then((res) => {
          if (res.res) {
            this.$notify({
              type: 'success',
              message: '支付完成',
              title: '提示',
            })
            this.visible = false
            this.$emit('reload')
          }
        })
        .finally(() => {})
    },
  },
}
</script>

<template>
  <div class="QR-code">
    <el-dialog
      :title="`${title}扫码支付`"
      v-model="visible"
      align-center
      append-to-body
      :z-index="3000"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="onBeforeClose"
    >
      <div class="container">
        <div v-if="!content" class="loading">
          <img src="@/static/loading.gif" alt="" />
        </div>
        <div v-else-if="qrError" class="loading">
          <span>二维码生成失败，请刷新后重试</span>
        </div>
        <div v-else-if="!qrDataUrl" class="loading">
          <img src="@/static/loading.gif" alt="" />
        </div>
        <template v-else>
          <img class="qr-img" :src="qrDataUrl" alt="支付二维码" />
          <br />
          <span>请打开{{ title }}扫一扫进行支付</span>
        </template>
      </div>
      <template #footer>
        <div style="text-align: center">
          <el-button @click="cancelPay">不支付了</el-button>
          <el-button
            style="margin-left: 50px"
            @click="paied"
            :loading="searching"
          >
            我已支付
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.container {
  text-align: center;

  img {
    width: 200px;
    height: 200px;
    vertical-align: middle;
  }

  .qr-img {
    display: inline-block;
  }
}
</style>

<style lang="scss">
.QR-code {
  .el-dialog {
    width: 400px !important;
  }
}
</style>
