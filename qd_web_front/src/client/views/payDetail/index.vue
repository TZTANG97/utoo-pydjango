<script>
import { fetchPayDetailApi, rechargeDetail } from "@client/api/index";
import { alterTime } from "@client/utils";
import { downloadOrderFileApi } from "@client/api";

export default {
  name: "PayDetail",
  data() {
    return {
      detail: null,
      payWayList: {
        1: "支付宝",
        2: "微信",
        3: "线下支付",
        4: "余额支付",
        5: "线下充值",
        6: "会员余额收款",
        7: "线下充值",
      },
      applyStatusList: {
        1: "审核中",
        2: "审核通过",
        3: "审核拒绝",
      },
      files: [],
      ofList:[],
      type:true,
      recharge_type:null
    };
  },
  mounted() {
    const id = this.$route.params.id.split("|")[0];
    const type = this.$route.params.id.split("|")[1];

    fetchPayDetailApi({ id: id, type }).then((res) => {
      if (res.res) {
        if(res.obj.eor) this.recharge_type = res.obj.eor.recharge_type
        this.detail = res.obj.obj;
        if (type == 1) {
          if (res.obj.ofList && res.obj.ofList.length > 0) {
            this.ofList = res.obj.ofList;
            this.type = true;
          } else {
            this.ofList = [
              {
                id: res.obj.eor.id,
                order_id: res.obj.eor.recharge_num,
              },
            ];
            this.type = false;
          }
        } else {
          this.ofList = res.obj.ofList;
        }
        if (res.obj.files && res.obj.files.length > 0) this.files = res.obj.files;
      }
    });
  },
  methods: {
    alterTime,
    downloadOrderFileApi,
  },
};
</script>

<template>
  <div class="container">
    <el-descriptions v-if="detail">
      <el-descriptions-item label="充值编号">{{
        detail.pa_num
      }}</el-descriptions-item>
      <el-descriptions-item label="充值时间">{{
        alterTime(detail.addTime)
      }}</el-descriptions-item>
      <el-descriptions-item label="充值方式">{{
        payWayList[detail.pay_way]
      }}</el-descriptions-item>
      <el-descriptions-item label="操作类型">
        {{
          detail.orderType != 1
            ? payWayList[detail.orderType]
            : detail.pay_way == 7
            ? "赠送"
            : "充值"
        }}
      </el-descriptions-item>
      <el-descriptions-item label="充值金额">{{
        detail.money ? detail.money.toFixed(2) : "0.00"
      }}</el-descriptions-item>
      <el-descriptions-item label="回执单" v-if="detail.hzdPath">
        <el-image
          class="hzd"
          :src="detail.hzdPath"
          :preview-src-list="[detail.hzdPath]"
        >
          <template #error class="err-text"> 暂无 </template>
        </el-image>
      </el-descriptions-item>
      <el-descriptions-item label="审核状态">{{
        detail.applyStatus
      }}</el-descriptions-item>
      <el-descriptions-item label="驳回原因" v-if="detail.mark">{{
        detail.mark
      }}</el-descriptions-item>
      <el-descriptions-item label="资料" v-if="files.length">
        <div class="order-data-list">
          <div v-for="(file, idx) in files" :key="idx">
            <a
              :href="`${file.path}/${file.name}`"
              target="_blank"
              :download="`${file.info}.${file.ext}`"
            >
              {{ file.info }}
            </a>
            <span @click="downloadOrderFileApi(file)">下载</span>
          </div>
        </div>
      </el-descriptions-item>
      <el-descriptions-item label="关联订单" v-if="ofList.length > 0">
        <div class="order-data-list">
          <div v-for="(order, idx) in ofList" :key="idx">
            <el-link>
              <router-link v-if="type" :to="`/b/order_detail/${order.id}`">
                <span style="font-size: 18px">{{ order.order_id }}</span>
              </router-link>
              <router-link v-else :to="`/b/order_detail/${order.id}|1`">
                <span style="font-size: 18px">{{ order.order_id }}</span>
              </router-link>
            </el-link>
          </div>
        </div>
      </el-descriptions-item>
    </el-descriptions>
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
    margin-bottom: 10px;
  }
}
.hzd {
  line-height: 100px;
  text-align: center;
  color: #999;
  width: 100px;
  height: 100px;
  border-radius: 5px;
  vertical-align: top;
}

.el-descriptions {
  font-size: 18px;
}
.container {
  padding: 20px;
}
</style>
