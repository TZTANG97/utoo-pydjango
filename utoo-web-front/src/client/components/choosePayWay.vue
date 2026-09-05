<script>
import Decimal from "decimal.js";
export default {
  name: "ChoosePayWay",
  data() {
    return {
      payWay: 0,
      payList: [
        // {
        //   id: 1,
        //   icon_name: 'alipay',
        //   icon_title: '支付宝'
        // },
        {
          id: 2,
          icon_name: "wxpay",
          icon_title: "微信",
        },
        {
          id: 3,
          icon_name: "transfer_money",
          icon_title: "线下",
        },
        {
          id: 4,
          icon_name: "balance",
          icon_title: "余额",
        },
      ],
      values: false,
      integral_num: 0,
      deleteMoney: 0,
      // 默认 2，避免接口未返回时除零（100 积分抵扣 2 元）
      integral_convert_ratio: 2,
      totalIntegral: 0,
    };
  },
  props: {
    modelValue: {
      default: false,
      type: Boolean,
    },
    value: {
      default: false,
      type: Boolean,
    },

    // 是不是充值
    isTopUp: {
      default: false,
      type: Boolean,
    },
    money: { type: Number, default: 0 },
  },
  computed: {
    dialogVisible: {
      get() {
        return this.modelValue || this.value;
      },
      set(val) {
        this.$emit("update:modelValue", val);
        this.$emit("input", val);
      },
    },
  },
  watch: {
    dialogVisible: {
      immediate: true,
      async handler(visible) {
        if (visible) {
          this.integral_num = 0;
          this.deleteMoney = 0;
          this.$store.dispatch("user/getIntegralApi");
          try {
            await this.$store.dispatch("user/getIntegralConvertRatio");
          } catch (_) {
            /* keep default */
          }
          const ratio = Number(this.$store.getters.IntegralConvertRatio);
          this.integral_convert_ratio =
            Number.isFinite(ratio) && ratio > 0 ? ratio : 2;
          this.totalIntegral = this.$store.getters.totalIntegral || 0;
        }
      },
    },
  },
  methods: {
    choosePay(id) {
      if (this.payWay === id) return;
      if (this.isTopUp && id === 4) return;
      this.payWay = id;
    },
    handleClose(done) {
      this.payWay = 0;
      this.values = false;
      this.dialogVisible = false;
      this.$emit("moneyFn", false);
      if (typeof done === "function") done();
    },
    confirmPayWay() {
      if (this.isTopUp) {
      }
      if (!this.payWay)
        return this.$notify({
          title: "提示",
          type: "warning",
          message: "请选择支付方式",
        });
      if (this.payWay == 3) this.values = false;
      // 校验输入的积分和实际积分
      if (this.values) {
        if (this.integral_num < 1)
          return this.$message.error("请输入正确的兑换积分");
        if (this.integral_num > this.totalIntegral)
          return this.$message.error("请输入正确的兑换积分");
        if (this.integral_num / 100 > this.money)
          return this.$message.error("请输入正确的兑换积分");
        if (this.deleteMoney > this.money)
          return this.$message.error("请输入正确的兑换积分");
      } else {
        this.integral_num = 0;
      }
      if (
        this.payWay == 2 &&
        this.moneyFn(this.money, this.deleteMoney) == 0.0
      ) {
        this.$emit("selected", this.payWay, this.integral_num, this.money);
      } else {
        this.$emit("selected", this.payWay, this.integral_num);
      }
      this.handleClose();
    },
    // 校验输入的积分和实际积分
    inputChange(val) {
      this.integral_num = String(val ?? "").replace(/[.]+/g, "");
      const ratio = Number(this.integral_convert_ratio);
      const safeRatio = Number.isFinite(ratio) && ratio > 0 ? ratio : 2;
      const points = this.integral_num === "" ? 0 : this.integral_num;
      // 100 积分可抵扣 safeRatio 元 → 抵扣额 = points * (safeRatio / 100)
      const data = new Decimal(points).mul(safeRatio).div(100);
      this.deleteMoney = data.toFixed(2);
    },
    moneyFn(num1, num2) {
      const data = new Decimal(num1).sub(num2);
      return data.toFixed(2);
    },
  },
};
</script>

<template>
  <div class="choose-pay-way">
    <el-dialog
      title="请选择支付方式"
      v-model="dialogVisible"
      align-center
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleClose"
    >
      <div class="pay-list">
        <div
          class="pay-item"
          v-for="item in payList"
          :key="item.id"
          :class="{
            'pay-item-active': payWay === item.id,
            dsa: isTopUp && item.id === 4,
          }"
          @click="choosePay(item.id)"
        >
          <svg-icon :icon-class="item.icon_name"></svg-icon>
          <span>{{ item.icon_title }}</span>
        </div>
        <span
          v-if="!isTopUp && (payWay == 2 || payWay == 4)"
          style="font-size: 20px; margin-left: 20px"
          >此单支付金额：{{ money }}元</span
        >
        <div
          class="integralBox"
          v-if="!isTopUp && (payWay == 2 || payWay == 4)"
        >
          <div class="imgBox">
            <div style="display: flex; align-items: center">
              <img src="../assets/图表.png" alt="" />
              <span>积分抵扣</span>
            </div>
            <el-switch
              v-model="values"
              active-color="#f59700"
              inactive-color="gray"
            >
            </el-switch>
          </div>
          <span style="font-size: 18px; font-weight: 700"
            >仅微信/余额支付有效，当前可用积分：{{ totalIntegral }}</span
          >
          <br />
          <div class="sy">
            <span>
              <span>使用</span
              ><el-input
                :disabled="!values"
                style="width: 200px; border-radius: 20px; margin: 0 10px"
                min="1"
                size="small"
                type="number"
                step="1"
                v-model="integral_num"
                @input="inputChange"
              ></el-input
              ><span>积分</span>
            </span>
            <span>-￥{{ deleteMoney }}</span>
          </div>
        </div>
      </div>
      <span
        style="
          display: inline-block;
          font-size: 20px;
          width: 100%;
          text-align: right;
          font-weight: 700;
        "
        v-if="!isTopUp && (payWay == 2 || payWay == 4)"
        >此单剩余支付金额￥ <span v-if="!values">{{ money }}</span>
        <span v-else>
          {{ moneyFn(money, deleteMoney) }}
        </span>
      </span>
      <span slot="footer" class="dialog-footer">
        <el-button @click="handleClose">取&nbsp;消</el-button>
        <el-button type="primary" @click="confirmPayWay">确&nbsp;定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<style scoped>
/deep/.el-dialog {
  width: 600px;
}
</style>

<style scoped lang="scss">
.dsa {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}
.pay-item-active {
  border: 3px solid var(--mainColor);
  border-radius: 5px;
  margin: 0px -3px;
}

.pay-list {
  font-size: 23px;
  margin-bottom: 20px;

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
.integralBox {
  border-top: 8px #e99c00 solid;
  margin-top: 15px;
  padding-left: 20px;
  .imgBox {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    margin-bottom: 20px;
    img {
      width: 40px;
      margin-right: 10px;
    }
    span {
      font-size: 20px;
      font-weight: 700;
    }
  }
  .sy {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 40px;
    font-size: 20px;
    font-weight: 700;
  }
}
</style>
