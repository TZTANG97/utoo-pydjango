<script>
import { getOrderListApi } from "@/api/order";
import { alterTime } from "@/utils/index";
import pay from "@/components/pay.vue";
import {
  balancePayApi,
  fetchDefaultAccountApi,
  savePermitApi,
  wxRepaymentApi,
} from "@/api/index";
import offlinePay from "@/components/offlinePay.vue";
import QRcode from "@/components/QRcode.vue";
import choosePayWay from "@/components/choosePayWay.vue";
import { mapMutations } from "vuex";
import Decimal from "decimal.js";
import { ElMessageBox } from "element-plus";

export default {
  name: "repayment",
  data() {
    return {
      searchVal: "",
      searching: false,
      tableData: [],
      total: 0,
      page: 1,
      limit: 10,
      showPay: false,
      collection_account: "",
      collection_name: "",
      repaymentList: [],
      arrearsMoney: 0,
      openChooseTool: false,

      // 线下支付组件
      openOfflinePay: false,

      openQRcode: false,
      codeUrl: "",
      outTradeNo: "",
      money: 0,
      paying: false,
      store: {},
    };
  },
  computed: {
    payMoney() {
      return Number(this.money || 0);
    },
    arrearsMoneyNum() {
      return Number(this.arrearsMoney || 0);
    },
  },
  components: { choosePayWay, QRcode, offlinePay, pay },
  mounted() {
    this.getList();
    this.store = this.$store;

    // 获取默认的收款地址
    fetchDefaultAccountApi().then((res) => {
      if (res.res) {
        const { bankCardNum, company_name } = res.obj;
        this.collection_name = company_name;
        this.collection_account = bankCardNum;
      }
    });
  },
  methods: {
    ...mapMutations({ CHANGE_LOADING: "app/CHANGE_LOADING" }),

    // 选择/取消选择
    handleSelectionChange(val) {
      this.money = 0;
      this.arrearsMoney = 0;
      this.repaymentList = [];
      val.forEach((item) => {
        this.arrearsMoney += item["totalPrice"]
          ? item["totalPrice"] - item["xsskje"]
          : 0;
        let xsskje = item.xsskje ? item.xsskje : 0;
        let totalPrice = item.totalPrice ? item.totalPrice : 0;

        let data = new Decimal(totalPrice).sub(xsskje)

        this.money = new Decimal(this.money).add(data)
        // this.money += totalPrice- xsskje
        this.repaymentList.push(item.id);
      });
    },

    // 支付
    repayment() {
      if (!this.repaymentList.length)
        return this.$notify.warning({
          title: "提示",
          message: "请选择订单",
        });
      console.log(this.money, "money");
      this.openChooseTool = true;
    },

    // 提交成功后刷新页面
    refreshPage() {
      this.page = 1;
      this.$refs.multipleTable.clearSelection();
      this.repaymentList = [];
      this.arrearsMoney = 0;
      this.getList();
    },

    // 条数改变
    handleSizeChange(e) {
      this.limit = e;
      this.getList();
    },

    // 页数改变
    handleCurrentChange(e) {
      this.page = e;
      this.getList();
    },

    // 检索
    searchOrder() {
      this.page = 1;
      this.getList();
    },

    alterTime,

    //   获取列表
    getList() {
      this.$refs.multipleTable?.clearSelection?.();
      this.repaymentList = [];
      this.arrearsMoney = 0;
      this.money = 0;
      this.searching = true;
      getOrderListApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        keywords: this.searchVal,
        type: 1,
      })
        .then((res) => {
          if (res.res) {
            const payload = res.obj || res.data || {};
            this.tableData = payload.data || [];
            this.total = payload.recordsTotal || 0;
          } else {
            this.$notify({
              type: "warning",
              message: res.resMsg || res.message || res.msg || "加载失败",
              title: "提示",
            });
          }
        })
        .catch((err) => {
          this.$notify({
            type: "error",
            message: err?.message || "加载超时，请稍后重试",
            title: "提示",
          });
        })
        .finally(() => {
          this.searching = false;
        });
    },

    confirmSubmit(e) {
      this.CHANGE_LOADING(1);
      savePermitApi({
        id: this.repaymentList.join(),
        file_id: e.fileId,
        type: 2,
        pay_way: 3,
      })
        .then((res) => {
          this.$notify({
            type: res.res ? "success" : "warning",
            title: "提示",
            message: res.res ? "支付申请已提交" : res.errMsg,
          });
          if (res.res) {
            this.openOfflinePay = false;
            this.getList();
          }
        })
        .finally((_) => {
          this.CHANGE_LOADING();
        });
    },

    runBalancePay(integral_num, pay_way) {
      this.paying = true;
      return balancePayApi({
        ofId: this.repaymentList.join(),
        useIntegral: integral_num,
        pay_way,
      })
        .then((res) => {
          this.$notify({
            type: res.res ? "success" : "warning",
            title: "提示",
            message: res.res ? "支付成功" : res.resMsg,
          });
          if (res.res) {
            this.money = 0;
            this.getList();
            this.store.dispatch("user/getIntegralApi");
          }
        })
        .finally(() => {
          this.paying = false;
        });
    },

    runWxRepayment(integral_num) {
      this.paying = true;
      return wxRepaymentApi({
        ofId: this.repaymentList.join(),
        useIntegral: integral_num,
      })
        .then((res) => {
          const payload = res?.obj ?? res?.data ?? (res?.codeUrl ? res : null);
          const codeUrl = payload?.codeUrl;
          const ok =
            codeUrl &&
            (res?.res === true || res?.code === 0 || res?.res === undefined);
          if (ok) {
            this.codeUrl = codeUrl;
            this.outTradeNo = payload.outTradeNo || "";
            ElMessageBox.close();
            this.$nextTick(() => {
              this.openQRcode = true;
            });
          } else {
            this.$notify({
              type: "warning",
              title: "提示",
              message: res?.resMsg || res?.message || "获取支付二维码失败",
            });
          }
        })
        .finally(() => {
          this.paying = false;
        });
    },

    confirmPayWay(payWayId, integral_num, useBalancePay) {
      const ofIds = this.repaymentList.join();
      if (!ofIds) {
        return this.$notify.warning({
          title: "提示",
          message: "请选择订单",
        });
      }
      switch (payWayId) {
        case 1:
          break;
        case 2:
          if (useBalancePay) {
            this.$confirm("确认使用余额支付?", "提示", {
              confirmButtonText: "确定",
              cancelButtonText: "取消",
              type: "warning",
            })
              .then(() => this.runBalancePay(integral_num, 2))
              .catch(() => {});
          } else {
            this.runWxRepayment(integral_num);
          }
          break;
        case 3:
          this.openOfflinePay = true;
          break;
        default:
          this.$confirm("确认使用余额支付?", "提示", {
            confirmButtonText: "确定",
            cancelButtonText: "取消",
            type: "warning",
          })
            .then(() => this.runBalancePay(integral_num, 4))
            .catch(() => {});
      }
    },
  },
};
</script>

<template>
  <div class="container">
    <header>
      <el-input
        size="mini"
        v-model="searchVal"
        placeholder="请输入订单编号"
        maxlength="30"
      ></el-input>
      <el-button
        :loading="searching"
        type="primary"
        size="mini"
        @click="searchOrder"
        >检索</el-button
      >
      <el-button
        type="primary"
        size="mini"
        @click="repayment"
        :loading="paying"
        :disabled="searching"
        >支付</el-button
      >
    </header>
    <main>
      <el-table
        :data="tableData"
        style="width: 100%"
        ref="multipleTable"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column
          type="selection"
          width="55"
          :selectable="(row) => !searching && row.isUploadReceipt !== 1"
        >
        </el-table-column>
        <el-table-column align="center" label="订单编号">
          <template #default="{ row }">
            <el-link>
              <router-link :to="`/b/order_detail/${row.id}`">
                {{ row["order_id"] }}
              </router-link>
            </el-link>
          </template>
        </el-table-column>

        <el-table-column align="center" label="产品名称">
          <template #default="{ row: { orderChildForms } }">
            {{ orderChildForms[0]["goodsName"] }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="产品型号">
          <template #default="{ row: { orderChildForms } }">
            {{ orderChildForms[0]["goodsSpec"] }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="产品品牌">
          <template #default="{ row: { orderChildForms } }">
            {{ orderChildForms[0]["goodsBrandName"] }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="实验项目">
          <template #default="{ row: { orderChildForms } }">
            {{ orderChildForms[0]["experiment_project_name"] }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="实验分类">
          <template #default="{ row: { orderChildForms } }">
            {{ orderChildForms[0]["experiment_class_name"] }}
          </template>
        </el-table-column>

        <el-table-column align="center" label="实付款金额">
          <template #default="{ row }">
            {{ row["xsskje"] }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="下单金额">
          <template #default="{ row }">
            {{ row["totalPrice"] ? row["totalPrice"].toFixed(2) : "0.00" }}
          </template>
        </el-table-column>
        <el-table-column align="center" prop="order_statusstr" label="订单状态">
        </el-table-column>
        <el-table-column align="center" label="开票状态">
          <template #default="{ row }">
            {{ row["iskp"] - 0 ? "完成" : "未完成" }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="支付状态">
          <template #default="{ row }">
            {{ row["isfk"] - 0 ? "支付完成" : "待支付" }}
          </template>
        </el-table-column>
      </el-table>
    </main>
    <footer>
      <el-pagination
        background
        :page-sizes="[10, 20, 30, 50, 100]"
        :page-size="limit"
        :current-page="page"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        layout="total, prev, pager, next, sizes"
        :total="total"
        :disabled="searching"
      >
      </el-pagination>
    </footer>
    <pay
      :pay-dialog.sync="showPay"
      :id="repaymentList.join()"
      :collection-name="collection_name"
      :collection-account="collection_account"
      @refresh="refreshPage"
      :type="3"
      :money="arrearsMoneyNum"
    ></pay>

    <choose-pay-way
      v-model="openChooseTool"
      @selected="confirmPayWay"
      :money="payMoney"
    ></choose-pay-way>
    <QRcode
      :search-flag="outTradeNo"
      @reload="getList"
      v-model="openQRcode"
      :content="codeUrl"
    ></QRcode>
    <offline-pay
      :pay-money="arrearsMoneyNum"
      @confirmSubmit="confirmSubmit"
      v-model="openOfflinePay"
      title="支付"
      :clt-account="collection_account"
      :clt-name="collection_name"
    ></offline-pay>
  </div>
</template>

<style scoped lang="scss">
.container {
  padding: 20px;
}

header {
  .el-input {
    width: 200px;
  }

  .el-button {
    margin-left: 10px;
  }
}

main,
footer {
  margin-top: 20px;
}
</style>
