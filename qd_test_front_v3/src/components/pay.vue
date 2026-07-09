<script>
import {UploadPermitApi, savePermitApi, payApi, balancePayApi, wxPayApi, wxTopUpApi} from '@/api/index'
import VueQr from 'vue-qr'
export default {
  name: "Pay",
  components: {VueQr},
  props: {
    payDialog: {
      default: false,
      type: Boolean
    },
    id: {
      default: '',
      type: String
    },
    collectionName: {
      type: String,
      default: ''
    },
    collectionAccount: {
      type: String,
      default: ''
    },
    money: {
      type: Number,
      default: 1
    },
    // 判断用户要执行哪个操作
    // 1订单支付
    // 2充值
    // 3还款
    type: {
      type: Number,
      default: 1
    }
  },
  data() {
    return {
      // 用户选择的支付方式
      pay_way: 0,
      pay_list: [
        // {
        //   id: 1,
        //   icon_name: 'alipay',
        //   icon_title: '支付宝支付'
        // },
        {
          id: 2,
          icon_name: 'wxpay',
          icon_title: '微信支付'
        },
        {
          id: 3,
          icon_name: 'transfer_money',
          icon_title: '线下支付'
        }],
      step: 1,
      path: '',
      uploadingReceipt: false,
      paying: false,
      code_url: '',
      loadingCodeUrl: false,
      localMoney: this.money,
    }
  },

  watch: {
    money(v) {
      this.localMoney = v
    },
    payDialog(n) {
      if (this.type !== 2) {
        if (n) {
          this.pay_list.push({
            id: 4,
            icon_name: 'balance',
            icon_title: '余额支付'
          })
        } else {
          this.pay_list.pop()
        }
      }
    }
  },
  methods: {

    resetInput() {
      this.$refs['file'].value = ''
    },

    // 复制收款账号
    copyAccount() {
      this.$message.success('复制成功')
    },

    // 上传回执单
    uploadFile(e) {
      this.uploadingReceipt = true
      const file = e.target.files[0],
        type = file.type;

      if (type !== 'image/jpeg' && type !== 'image/jpg' && type !== 'image/png') {
        this.resetInput()
        this.uploadingReceipt = false
        return this.$notify.warning({
          title: '提示',
          message: '上传头像图片只能是 JPG 格式!'
        })
      }

      // if (file.size / 1024 / 1024 > 3) {
      //   this.resetInput()
      //   this.uploadingReceipt = false
      //   return this.$notify.warning({
      //     title: '提示',
      //     message: '回执单大小不能超过 3MB!'
      //   })
      // }

      UploadPermitApi(file).then(res => {
        if (res.res) {
          const {path, name, id} = res.obj
          this.path = path + '/' + name
          this.file_id = id
          this.resetInput()
        } else {
          this.$notify.warning({
            title: '提示',
            message: res.errMsg
          })
        }
      }).finally(_ => {
        this.uploadingReceipt = false
      })
    },

    // 提交回执单
    submitReceipt() {
      if (!this.path) return this.$notify.warning({
        title: '提示',
        message: '请上传回执单！'
      })
      this.uploadingReceipt = true

      savePermitApi({
        id: this.id,
        file_id: this.file_id,
        type: this.type === 1 ? 3 : 2,
        pay_way: this.pay_way
      }).then(res => {
        this.$notify({
          type: res.res ? 'success' : 'warning',
          title: '提示',
          message: res.res ? '上传成功' : res.errMsg
        })
        if (res.res) {
          this.handleClose()
          this.$emit('refresh')
        }
      }).finally(_ => {
        this.uploadingReceipt = false
      })
    },

    // 确定充值
    confirmPay() {
      if (!this.path) return this.$notify.warning({
        title: '提示',
        message: '请上传回执单！'
      })
      this.uploadingReceipt = true
      payApi({
        money: this.localMoney,
        file_id: this.file_id,
        pay_way: this.pay_way
      }).then(res => {
        this.$notify({
          type: res.res ? 'success' : 'warning',
          title: '提示',
          message: res.res ? '审核已提交' : res.errMsg
        })
        if (res.res) {
          this.handleClose()
          this.$emit('refresh')
        }
      })
    },


    // 微信充值
    wxTopUp() {
      this.$prompt('请输入充值金额', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        // inputPattern: /[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?/,
        // inputErrorMessage: '邮箱格式不正确'
      }).then(({ value }) => {
        wxTopUpApi({
          money: value
        }).then(res => {
          if (res.res) {
            this.code_url = res.obj.codeUrl
          } else {
            this.$notify({
              type: 'warning',
              title: '提示',
              message: res.resMsg
            })
          }
        })
      })
    },

    // 下一步
    next() {
      if (!this.pay_way) return
      if(this.pay_way === 4) {
        this.paying = true
        this.$confirm('确认支付?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          balancePayApi({
            ofId: this.id,
          }).then(res => {
            this.$notify({
              type: res.res ? 'success' : 'warning',
              title: '提示',
              message: res.res ? '支付成功' : res.resMsg
            })
            if (res.res) {
              this.handleClose()
              this.$emit('refresh')
            }
          })
        }).finally(_ => {
          this.paying = false
        })
      } else if(this.pay_way === 2){
        this.loadingCodeUrl = true
        this.step = 2
        wxPayApi({
          ofId: this.id,
        }).then(res => {
          if(res.res){
            this.code_url = res.obj.codeUrl
          }
        }).finally(_=> this.loadingCodeUrl = false)
      } else {
        this.step = 2
      }
    },

    // 选择支付方式
    choosePay(id) {
      if (this.pay_way === id) return
      this.pay_way = id
    },

    opened() {
      // this.pay_way = 3
    },

    // 关闭之前
    handleClose() {
      this.path = ''
      this.step = 1
      this.pay_way  = 0
      this.code_url = ''
      this.loadingCodeUrl = false
      this.$emit('update:payDialog', false)
    },

    // 验证金额
    verifyMoney(e) {
      let num = parseFloat(e)

      if (num < 1) {
        num = 1
      }

      if (num > 999999) {
        num = 999999
      }

      this.localMoney = num
      this.$emit('update:money', num)
    },
  }
}
</script>

<template>
  <div class="pay">
    <el-dialog
      @open="opened"
      :title="step === 1? '请选择支付方式' : pay_list.find(i => i.id === pay_way)['icon_title']"
      :visible.sync="payDialog"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      class="pay-dialog"
      v-loading="uploadingReceipt"
      :before-close="handleClose">
      <div class="pay-list" v-if="step === 1">
        <div class="pay-item" v-for="(item, idx) in pay_list" :key="'pay_' + idx"
             :class="pay_way === item.id? 'pay-item-active' : ''" @click="choosePay(item.id)"
             v-if="type !== 2 || item.id !== 4">
          <svg-icon :icon-class="item.icon_name"></svg-icon>
          <span>{{ item.icon_title }}</span>
        </div>
      </div>
      <div class="collection-info" v-else-if="step === 2 && pay_way === 3">
        <div class="collection-item">
          <div class="label">收款账号：</div>
          <div class="value">
            <span>{{ collectionAccount ? collectionAccount : '暂无' }}</span>
            <el-button type="text" size="mini" v-if="collectionAccount" style="margin-left: 10px"
                       @click="copyAccount">复制
            </el-button>
          </div>
        </div>
        <div class="collection-item">
          <div class="label">收款公司名称：</div>
          <div class="value">{{ collectionName ? collectionName : '暂无' }}</div>
        </div>
        <div class="collection-item" v-if="type === 2">
          <div class="label">充值金额：</div>
          <div class="value">
            <el-input :maxlength="6" placeholder="请输入充值金额" v-model="localMoney" type="number"
                      @change="verifyMoney"></el-input>
          </div>
        </div>
        <div class="collection-item" v-if="type !== 2">
          <div class="label">{{ type === 1 ? '支付' : '欠款' }}金额：</div>
          <div class="value">
            <el-input :disabled="true" :maxlength="6" placeholder="请输入充值金额" v-model="localMoney"
                      type="number"></el-input>
          </div>
        </div>

        <div class="collection-item">
          <div class="label">付款回执单：</div>
          <div class="value">
            <div class="receipt" @click="$refs['file'].click()" v-if="!path">
              <i class="el-icon-plus"/>
            </div>
            <img v-else :src="path" alt="" @click="$refs['file'].click()">
          </div>
        </div>
        <input type="file" @change="uploadFile" ref="file" v-show="false">
      </div>
      <div v-else-if="step === 2 && pay_way === 2" style="text-align: center">
        <div v-if="loadingCodeUrl" class="loading">
          <img src="@/static/loading.gif" alt="">
        </div>
        <template v-else>
          <vue-qr :text="code_url" qid="testid"/>
          <div v-if="!loadingCodeUrl">请打开微信扫一扫进行支付</div>
        </template>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="next" v-if="step === 1" :loading="paying">下一步</el-button>
        <template v-if="step === 2 && pay_way === 3">
          <el-button type="primary" @click="submitReceipt" v-if="type !== 2">提&nbsp;交</el-button>
          <el-button type="primary" @click="confirmPay" v-if="type === 2">确&nbsp;定</el-button>
        </template>
      </span>
    </el-dialog>
  </div>
</template>

<style>
.pay-dialog > .el-dialog {
  width: 32% !important;
  min-width: 380px !important;
}

.value {
  .el-input {
    input::-webkit-outer-spin-button,
    input::-webkit-inner-spin-button {
      -webkit-appearance: none;
    }

    .el-input__inner {
      line-height: 1px !important;
    }
  }
}
</style>

<style scoped lang="scss">

.loading {
  width: 200px;
  height: 200px;
  margin: auto;
  img {
    margin: 50px;
    width: 100px;
    height: 100px;
  }
}

.receipt {
  display: flex;
  box-sizing: border-box;
  justify-content: center;
  align-items: center;
  width: 100px;
  height: 100px;
  border-radius: 5px;
  border: 2px dotted #999;
  cursor: pointer;
  margin-top: 10px;

  i {
    font-size: 25px;
  }
}

.collection-info {
  font-size: 16px;

  .collection-item {
    margin-top: 20px;
  }

  .label {
    font-weight: bold;
  }

  .value {
    margin-top: 5px;
    font-size: 15px;

    .el-input {
      input::-webkit-outer-spin-button,
      input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        height: 100px;
      }
    }

    img {
      width: 100px;
      height: 100px;
      border-radius: 5px;
      cursor: pointer;
      border: 2px dotted #999;
    }
  }
}

.pay-item-active {
  border: 3px solid var(--mainColor);
  border-radius: 5px;
  margin: 0px -3px;
}


.pay-list {
  font-size: 23px;

  .pay-item {
    display: flex;
    align-items: center;
    height: 80px;
    padding: 0 20px;
    cursor: pointer;
  }

  svg {
    font-size: 40px;
    margin-right: 30px;
  }
}
</style>
