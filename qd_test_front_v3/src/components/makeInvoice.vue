<script>
import {billingApi} from "@/api/order";
import {getUserInvoiceInfoApi} from "@/api/user";
import {fetchAddressListApi, fetchInvoiceListApi} from "@/api";

export default {
  name: "MakeInvoice",
  props: {
    money: {
      default: 0,
      type: Number
    },
    dialogVisible: {
      default: false,
      type: Boolean
    },
    // 如果是1，则ids是发票订单的订单编号，2：测试实验订单的订单号
    orderType: {
      default: 1,
      type: Number
    },
    ids: {
      default: '',
      type: String
    }
  },
  data() {
    return {
      bill_form: {
        rise: '',
        // 电子发票和纸质发票
        invoice_type: '',
        // 1专用和2普用
        type: 2,
        email: '',
        address_info: '',
        // 信用代码
        credit_code: '',
        bank_name: '',
        bank_account: '',
        reg_address: '',
        reg_mobile: '',
      },
      bill_form_rule: {
        rise: [
          {
            validator: (rules, value, callback) => {
              let val = value.replace(/\s/g, '')
              this.bill_form.rise = val
              if (!val) {
                callback(new Error('发票抬头不能为空'))
              } else {
                callback()
              }
            }, trigger: 'blur'
          },
        ],
        invoice_type: [
          {required: true, trigger: 'change', message: '请选择发票类型'}
        ],
        credit_code: [
          {
            validator: (rules, value, callback) => {
              let val = value.replace(/\s/g, '')
              this.bill_form.credit_code = val
              if (!val) {
                callback(new Error('信用代码不能为空'))
              } else {
                callback()
              }
            }, trigger: 'blur'
          },
        ],
      },
      addressList: [],
      invoiceList: [],
      default_invoice: ''
    }
  },
  methods: {

    // 千分位
    format_with_Intl(num = 0) {
      let str = parseFloat(num).toFixed(2);
      let parts = str.split(".");
      let integerPart = parts[0];
      integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      return `${integerPart}.${parts[1]}`;
    },

    //   确认开票
    configBill() {
      this.$refs['bill-form'].validate((valid) => {
        if (valid) {
          // 电子发票 && 电子邮箱不能为空
          // if (this.bill_form.invoice_type === 1 && !this.bill_form.email) {
          //   return this.$notify.warning({
          //     title: '提示',
          //     message: '请填写电子邮箱'
          //   })
          // }
          if (!this.bill_form.email) {
            return this.$notify.warning({
              title: '提示',
              message: '请填写电子邮箱'
            })
          }

          // 纸质发票 && 收件地址不能为空
          // if (this.bill_form.invoice_type === 2 && !this.bill_form.address_info) {
          //   return this.$notify.warning({
          //     title: '提示',
          //     message: '请填写收件地址'
          //   })
          // }


          billingApi({
            invoiceTitle: this.bill_form['rise'],
            ids: this.ids,
            type: this.bill_form['type'],
            email: this.bill_form['email'],
            address_info: this.bill_form['address_info'],
            credit_code: this.bill_form['credit_code'],
            order_type: this.orderType,
            invoice_type: this.bill_form['invoice_type'],
            bank_name: this.bill_form['bank_name'],
            bank_account: this.bill_form['bank_account'],
            reg_address: this.bill_form['reg_address'],
            reg_mobile: this.bill_form['reg_mobile']
          }).then(res => {
            this.$notify({
              type: res.res ? 'success' : 'error',
              title: '提示',
              message: res.resMsg ? res.resMsg : '开票申请成功'
            })
            if (res.res) {
              this.closeDialog()
            }
          })
        } else {
          return false;
        }
      });
    },

    // 监听dialog打开
    async monitorOpen() {
      const res = await fetchInvoiceListApi()
      if (!res.res) {
        this.$notify.warning({
          title: '提示',
          message: res.resMsg || '获取发票信息失败',
        })
        return
      }
      const list = res.obj?.invoiceInfs || []
      this.invoiceList = list
      if (!list.length) {
        this.$notify.warning({
          title: '提示',
          message: '请先在个人中心添加开票信息',
        })
        return
      }
      const obj = list.find((item) => item.is_default) || list[0]
      this.default_invoice = obj.id
      this.bill_form.rise = obj.invoice_title
      this.bill_form.email = obj.email
      this.bill_form.credit_code = obj.taxNum
      this.bill_form.bank_name = obj.bank
      this.bill_form.bank_account = obj.bankCardNum
      this.bill_form.reg_address = obj.address
      this.bill_form.reg_mobile = obj.mobile

      // 获取收件地址
      // fetchAddressListApi().then(res => {
      //   if (res.res) {
      //     this.addressList = []
      //     res.obj.expUserDeliveryAddresses.forEach(item => {
      //       item.value = item.delivery_address + item.detail_address
      //       this.addressList.push(item)
      //       if (item.is_default) {
      //         this.bill_form.address_info = item.value
      //       }
      //     })
      //   }
      // })
    },

    //   监听关闭dialog
    closeDialog() {
      this.$emit('update:dialogVisible', false)
    },

    querySearch(queryString, cb) {
      var results = queryString ? this.addressList.filter(item => item.value.indexOf(queryString) !== -1) : this.addressList;
      cb(results);
    },

    // 更换发票信息
    changeInvoiceInfo(id) {
      let obj = this.invoiceList.find(item => item.id === id)
      // 发票抬头
      this.bill_form['rise'] = obj.invoice_title
      this.bill_form['email'] = obj.email
      // 税号
      this.bill_form['credit_code'] = obj.taxNum
      this.bill_form['bank_name'] = obj.bank
      this.bill_form['bank_account'] = obj.bankCardNum
      this.bill_form['reg_address'] = obj.address
      this.bill_form['reg_mobile'] = obj.mobile
    },
  }
}
</script>

<template>
  <div class="make-invoice">
    <el-dialog
      title="确认开票信息"
      :visible.sync="dialogVisible"
      :close-on-click-modal="false"
      @open="monitorOpen"
      :before-close="closeDialog"
      @close="closeDialog">
      <el-form :model="bill_form" :rules="bill_form_rule" ref="bill-form">
        <el-form-item label="可开票金额：">
          <br>
          <span class="money">{{ format_with_Intl(money) }}</span>元
        </el-form-item>
        <el-form-item label="发票信息：">
          <el-select v-model="default_invoice" filterable placeholder="请选择发票信息" @change="changeInvoiceInfo">
            <el-option
              v-for="item in invoiceList"
              :key="item.id"
              :label="item.invoice_title"
              :value="item.id">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="发票抬头：" prop="rise" class="required-label" label-width="100">
          <el-input placeholder="请输入发票抬头" v-model="bill_form.rise"></el-input>
        </el-form-item>
        <el-form-item label="企业税号：" prop="credit_code" class="required-label">
          <el-input placeholder="请输入企业税号" v-model="bill_form.credit_code"></el-input>
        </el-form-item>
        <el-form-item label="开户行名称：" prop="bank_name">
          <el-input placeholder="请输入开户行名称" v-model="bill_form.bank_name"></el-input>
        </el-form-item>
        <el-form-item label="开户行账号：" prop="bank_account">
          <el-input placeholder="请输入开户行账号" v-model="bill_form.bank_account"></el-input>
        </el-form-item>
        <el-form-item label="注册地址：" prop="reg_address">
          <el-input placeholder="请输入注册地址" v-model="bill_form.reg_address"></el-input>
        </el-form-item>
        <el-form-item label="注册电话：" prop="reg_mobile">
          <el-input placeholder="请输入注册电话" v-model="bill_form.reg_mobile"></el-input>
        </el-form-item>
        <el-form-item label="发票类型：" prop="invoice_type">
          <el-select v-model="bill_form.invoice_type" placeholder="请选择发票类型">
            <el-option
              label="电子普通发票"
              :value="1">
            </el-option>
            <el-option
              label="电子增值税专票"
              :value="3">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item required label="电子邮箱：" class="required-label">
          <el-input placeholder="请输入电子邮箱" v-model="bill_form.email"></el-input>
        </el-form-item>
<!--        <el-form-item label="收件地址：" v-if="bill_form.invoice_type === 3" class="required-label">-->
<!--          <el-autocomplete-->
<!--            class="inline-input"-->
<!--            v-model="bill_form.address_info"-->
<!--            :fetch-suggestions="querySearch"-->
<!--            placeholder="请输入收件地址"-->
<!--          ></el-autocomplete>-->
<!--        </el-form-item>-->



        <!--        <el-form-item label="发票：" prop="type">-->
        <!--          <el-select v-model="bill_form.type" placeholder="请选择发票">-->
        <!--            <el-option-->
        <!--              label="专用发票"-->
        <!--              :value="1">-->
        <!--            </el-option>-->
        <!--            <el-option-->
        <!--              label="普通发票"-->
        <!--              :value="2">-->
        <!--            </el-option>-->
        <!--          </el-select>-->
        <!--        </el-form-item>-->
      </el-form>
      <span slot="footer" class="dialog-footer">
    <el-button @click="closeDialog">取 消</el-button>
    <el-button type="primary" @click="configBill">确 定</el-button>
  </span>
    </el-dialog>
  </div>
</template>

<style scoped>

.el-autocomplete {
  width: 100%;
}

/deep/ .el-dialog {
  width: 600px !important;
  height: 700px !important;


  .el-dialog__body {
    height: 82% !important;
    overflow-y: scroll;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-thumb {
      background: rgba(233, 99, 2, .3);
      border-radius: 10px;
    }

    &::-webkit-scrollbar-thumb:hover {
      background: var(--mainColor);
    }

  }
}

.el-select {
  width: 100%;
}

</style>

<style scoped lang="scss">
.money {
  font-size: 34px;
  font-weight: bold;
  color: var(--mainColor);
  margin-right: 4px;
}
</style>
