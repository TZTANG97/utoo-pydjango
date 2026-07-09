<script>
import {
  redeemGoodsDetail,
} from "@/api/order";
import { alterTime } from "@/utils/index";
export default {
  name: "OrderDetail2",
  data() {
    return {
      id: "",
      detail: null,
    };
  },
  mounted() {
    this.store = this.$store;
    this.id = this.$route.params.id;
    this.getDetail();
  },
  methods: {
    alterTime,
    //   获取详情
    getDetail() {
      redeemGoodsDetail({ id: this.id }).then((res) => {
        console.log(res,'res')
          if (res.res) {
            this.detail = res.obj.obj;
          } else {
            this.$notify({
              type: "error",
              title: "提示",
              message: res.resMsg,
            });
          }
        });
    },
  },
};
</script>

<template>
  <div class="container">
    <el-card class="box-card" v-if="detail">
      <div slot="header" class="clearfix">
        <span>订单详情</span>
      </div>
      <div class="row">
        <div class="text item">
          <span>订单编号：</span>
          <span>{{ detail["orderId"] }}</span>
        </div>
        <div class="text item">
          <span>用户名：</span>
          <span>{{ detail["userName"] }}</span>
        </div>
        <div class="text item">
          <span>手机号：</span>
          <span>{{
            detail["mobile"]
          }}</span>
        </div>
        <div class="text item">
          <span>地址：</span>
          <span>{{ detail["address"] }}</span>
        </div>
      </div>
      <div class="row">
        <div class="text item">
          <span>兑换时间：</span>
          <span>{{ alterTime(detail["redeemTime"]) }}</span>
        </div>
        <div class="text item">
          <span>商品名称：</span>
          <span>{{ detail.goodsName }}</span>
        </div>
        <div class="text item">
          <span>商品数量：</span>
          <span>{{ detail.redeemNum }}</span>
        </div>
        <div class="text item">
          <span>消费积分：</span>
          <span>{{ detail.integralsum }}</span>
        </div>
      </div>
      <div class="row">
        <div class="text item">
          <span>发货状态：</span>
          <span>{{ detail["fhstatus"] == 1 ? "待发货" : "已发货" }}</span>
        </div>
        <div class="text item" v-if="detail.fhstatus == 2">
          <span>快递公司：</span>
          <span>{{ detail["expressCompany"] }}</span>
        </div>
        <div class="text item" v-if="detail.fhstatus == 2">
          <span>快递单号：</span>
          <span>{{ detail["expressNum"] }}</span>
        </div>
        <div class="text item" v-if="detail.fhstatus == 2">
          <span>发货时间：</span>
          <span>{{ alterTime(detail["fhTime"]) }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.order-data-list {
  a {
    color: var(--mainColor);
  }

  span {
    color: var(--mainColor);
    cursor: pointer;
  }

  div {
    margin-top: 10px;
  }
}

.progress {
  position: absolute;
  right: 80px;
  top: 80px;
  width: 120px;
  height: 120px;
}

.a-bill {
  margin-top: 20px;

  .row {
    margin-top: 0 !important;

    &:nth-child(n + 2) {
      color: var(--mainColor);
    }
  }
}

.clearfix {
  position: relative;
}


.row {
  display: flex;

  &:nth-child(n + 2) {
    margin-top: 30px;
  }
}

.el-timeline {
  padding: 0;
}

.item {
  width: 33%;

  .hzd {
    width: 100px;
    height: 100px;
    border-radius: 5px;
    vertical-align: top;
  }
}

.container {
  padding: 20px;
}
</style>
