<script>
import {
  getOrderListApi,
  submitEvaluateApi,
  againTestApi,
  confirmCompleteApi,
} from "@/api/order";
import { alterTime } from "@/utils/index";
import pay from "@/components/pay.vue";
import MakeInvoice from "@/components/makeInvoice.vue";
import DownloadDialog from "@/components/downloadTestFiles.vue";
import evaluate from "@/components/evaluate.vue";
import choosePayWay from "@/components/choosePayWay.vue";
import offlinePay from "@/components/offlinePay.vue";
import QRcode from "@/components/QRcode.vue";
import {
  balancePayApi,
  fetchAgainAndFinishChildOrderListApi,
  fetchyydApi,
  savePermitApi,
  wxPayApi,
  isServiceConsult,
  saveServiceConsult,
} from "@/api";
import { mapMutations } from "vuex";

export default {
  data() {
    return {
      searchVal: "",
      searching: false,
      tableData: [],
      total: 0,
      page: 1,
      limit: 10,
      // 订单状态
      status_list: {
        0: "取消",
        1: "待支付",
        2: "待实验",
        3: "实验中",
        4: "已完成",
      },
      activeName: "0",
      // 订单分类状态
      order_status_list: {
        全部: "0",
        待支付: "1",
        待实验: "2",
        实验中: "3",
        已完成: "4",
        // '待开票': '5',
        // '实验完成': '6',
        售后: "7",
      },
      dialogVisible: false,
      money: 0,
      ids: "",
      showPay: false,
      id: "",
      collection_account: "",
      collection_name: "",
      payMoney: 0,
      showDownLoadDialog: false,
      testFiles: [],
      showEvaluate: false,
      evaluating: false,
      currentId: "",
      openChooseTool: false,

      // 线下支付组件
      openOfflinePay: false,

      openQRcode: false,
      codeUrl: "",
      outTradeNo: "",

      againTestDialog: false,
      selectedChild: "",
      children: [],
      childInfo: null,
      type: 1,
      mark: "",
      kpStatus: {
        0: "未完成",
        1: "已完成",
        2: "无需开票",
      },
      totalPrice: 0,
      store: {},
      loading: false,
      listRequestId: 0,
    };
  },
  name: "Order",
  components: {
    pay,
    MakeInvoice,
    DownloadDialog,
    evaluate,
    choosePayWay,
    offlinePay,
    QRcode,
  },
  mounted() {
    this.getList();
  },
  activated() {
    this.getList();
  },
  watch: {
    // 监听dialog关闭
    dialogVisible(n) {
      if (!n) {
        this.limit = 10;
        this.page = 1;
        this.getList();
      }
    },
  },
  created() {
    this.store = this.$store;
  },
  methods: {
    goyuyue(item) {
      isServiceConsult({ id: item.id }).then((res) => {
        if (res.res) {
          this.$confirm("是否确定再来一单？", "提示", {
            confirmButtonText: "确定",
            cancelButtonText: "取消",
            type: "warning",
          }).then(() => {
            saveServiceConsult({ id: item.id }).then((res) => {
              if (res.res) {
                this.$message({
                  type: "success",
                  message: "成功！可在「我的预约」中查看新预约",
                });
                this.getList();
              } else {
                this.$message({ type: "error", message: res.resMsg });
              }
            });
          });
        } else {
          this.$message({
            type: "error",
            message: "当前订单无业务咨询，请到测试预约详情重新预约！",
          });
          // setTimeout(() => {
          //   window.open(location.origin + `/#/test_detail/${item.class_id}`);
          // }, 3000);
        }
      });
    },
    ...mapMutations({ CHANGE_LOADING: "app/CHANGE_LOADING" }),

    downLoadTestFiles(testFiles) {
      this.testFiles = testFiles;
      this.showDownLoadDialog = true;
    },

    // 提交成功后刷新页面
    refreshPage() {
      this.getList();
    },

    // 去支付
    goPay(row, company_account = " ", payMoney = 0) {
      let xsskje = row.xsskje ? row.xsskje : 0;
      let totalPrice = row.totalPrice ? row.totalPrice : 0;
      this.totalPrice = (totalPrice * 100 - xsskje * 100) / 100;

      // this.totalPrice = row.totalPrice ? row.totalPrice : 0;
      const new_company_account = company_account.split(" ");
      this.collection_name = new_company_account[0];
      this.collection_account = new_company_account[1];
      this.payMoney = payMoney;
      this.id = row.id;
      this.openChooseTool = true;
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

    formatMoney(val) {
      const n = Number(val);
      return Number.isFinite(n) ? n.toFixed(2) : "0.00";
    },

    //   获取列表
    getList() {
      const reqId = ++this.listRequestId;
      this.searching = true;
      this.loading = true;
      getOrderListApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        keywords: this.searchVal,
        type: this.activeName,
      })
        .then((res) => {
          if (reqId !== this.listRequestId) return;
          if (res.res) {
            const payload = res.obj || res.data || {};
            this.tableData = payload.data || [];
            this.total = payload.recordsTotal || 0;
          } else {
            const msg = res.resMsg || res.message || "获取订单列表失败";
            this.tableData = [];
            this.total = 0;
            this.$notify({
              type: "warning",
              message: msg,
              title: "提示",
            });
            if (res.code === 401) {
              this.$store.dispatch("user/resetToken").then(() => {
                this.$router.push(`/login?redirect=${this.$route.fullPath}`);
              });
            }
          }
        })
        .catch((err) => {
          this.tableData = [];
          this.total = 0;
          console.error("[order] getList failed", err);
        })
        .finally(() => {
          if (reqId !== this.listRequestId) return;
          this.loading = false;
          this.searching = false;
        });
    },

    handleClick() {
      this.page = 1;
      this.limit = 10;
      this.tableData = [];
      this.getList();
    },

    // 开票
    billing(money, ids) {
      this.money = money || 0;
      this.ids = ids + "";
      this.dialogVisible = true;
    },

    // 打印预约单
    printPDF(id) {
      this.CHANGE_LOADING(1);
      fetchyydApi(id)
        .then((res) => {
          if (res.res) {
            window.open(res.obj.url);
          }
        })
        .finally((_) => {
          this.CHANGE_LOADING();
        });
    },

    submitEvaluate(e) {
      this.evaluating = true;
      submitEvaluateApi({
        id: this.currentId,
        star: e.star,
        content: e.evaluate_content,
      })
        .then((res) => {
          this.$notify({
            type: res.res ? "success" : "warning",
            title: "提示",
            message: res.resMsg,
          });

          if (res.res) {
            this.showEvaluate = false;
            const idx = this.tableData.findIndex(
              (item) => item.id === this.currentId
            );
            this.$set(this.tableData[idx], "ispjqx", false);
          }
        })
        .finally((_) => (this.evaluating = false));
    },

    confirmSubmit(e) {
      this.CHANGE_LOADING(1);
      savePermitApi({
        id: this.id,
        file_id: e.fileId,
        type: 3,
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

    confirmPayWay(payWayId, integral_num, money) {
      const that = this;
      console.log(payWayId, "payWayId");
      switch (payWayId) {
        case 1:
          break;
        case 2:
          if (money) {
            this.$confirm("确认支付?", "提示", {
              confirmButtonText: "确定",
              cancelButtonText: "取消",
              type: "warning",
              beforeClose(action, instance, done) {
                if (action === "confirm") {
                  that.CHANGE_LOADING(1);
                  balancePayApi({
                    ofId: that.id,
                    useIntegral: integral_num,
                    pay_way: 2,
                  })
                    .then((res) => {
                      console.log(that.store, "this.$store");
                      that.store.dispatch("user/getIntegralApi");
                      that.$notify({
                        type: res.res ? "success" : "warning",
                        title: "提示",
                        message: res.res ? "支付成功" : res.resMsg,
                      });
                      if (res.res) {
                        that.getList();
                      }
                    })
                    .finally((_) => {
                      that.CHANGE_LOADING();
                    });
                }
                done();
              },
            });
          } else {
            this.CHANGE_LOADING(1);
            wxPayApi({
              ofId: this.id,
              useIntegral: integral_num,
            })
              .then((res) => {
                if (res.res) {
                  this.codeUrl = res.obj.codeUrl;
                  this.outTradeNo = res.obj.outTradeNo;
                  this.openQRcode = true;
                  this.store.dispatch("user/getIntegralApi");
                } else {
                  this.$notify({
                    type: "warning",
                    title: "提示",
                    message: res.resMsg,
                  });
                }
              })
              .finally((_) => this.CHANGE_LOADING());
          }
          break;
        case 3:
          this.openOfflinePay = true;
          break;
        default:
          this.$confirm("确认支付?", "提示", {
            confirmButtonText: "确定",
            cancelButtonText: "取消",
            type: "warning",
            beforeClose(action, instance, done) {
              if (action === "confirm") {
                that.CHANGE_LOADING(1);
                balancePayApi({
                  ofId: that.id,
                  useIntegral: integral_num,
                  pay_way: 4,
                })
                  .then((res) => {
                    console.log(that.store, "this.$store");
                    that.store.dispatch("user/getIntegralApi");
                    that.$notify({
                      type: res.res ? "success" : "warning",
                      title: "提示",
                      message: res.res ? "支付成功" : res.resMsg,
                    });
                    if (res.res) {
                      that.getList();
                    }
                  })
                  .finally((_) => {
                    that.CHANGE_LOADING();
                  });
              }
              done();
            },
          });
      }
    },

    handleClose() {
      this.selectedChild = "";
      this.children = [];
      this.childInfo = "";
      this.mark = "";
    },

    getChildrenList(id, type) {
      this.CHANGE_LOADING(true);
      fetchAgainAndFinishChildOrderListApi({
        id,
        type,
      })
        .then((res) => {
          const { obj } = res;
          if (obj.length) {
            this.type = type;
            this.children = obj;
            this.againTestDialog = true;
          } else {
            this.$notify({
              title: "提示",
              type: "warning",
              message: "没有可操作的子订单",
            });
          }
        })
        .finally((_) => {
          this.CHANGE_LOADING();
        });
    },

    chooseChild(id) {
      this.childInfo = this.children.find((item) => item.id === id);
    },

    // 确认操作子订单
    confirmChild() {
      if (!this.selectedChild)
        return this.$notify({
          title: "提示",
          type: "warning",
          message: "请选择子订单",
        });

      this.CHANGE_LOADING(true);
      let fun;
      if (this.type === 1) {
        fun = againTestApi({
          mark: this.mark,
          orderId: this.selectedChild,
        });
      } else {
        fun = confirmCompleteApi({
          id: this.selectedChild,
        });
      }

      fun
        .then((res) => {
          this.$notify({
            title: "提示",
            type: res.res ? "success" : "warning",
            message: res.resMsg,
          });
          if (res.res) {
            this.handleClose();
            this.againTestDialog = false;
            this.getList();
          }
        })
        .finally((_) => {
          this.CHANGE_LOADING();
        });
    },
  },
};
</script>

<template>
  <div class="container">
    <make-invoice
      :dialog-visible.sync="dialogVisible"
      :money="money"
      :ids="ids"
      :order-type="2"
    />
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
    </header>
    <main>
      <el-tabs
        v-model="activeName"
        @tab-click="handleClick"
        v-loading="loading"
      >
        <el-tab-pane
          :label="k"
          :name="val"
          v-for="(val, k) in order_status_list"
          :key="k"
        >
          <el-table :data="tableData" style="width: 100%" border stripe>
            <el-table-column align="center" label="订单编号">
              <template #default="{ row }">
                <el-link>
                  <router-link :to="`/b/order_detail/${row.id}`">
                    {{ row["order_id"] }}
                  </router-link>
                </el-link>
              </template>
            </el-table-column>
            <el-table-column align="center" label="客户名称">
              <template #default="{ row }">
                {{ row.orderChildForms?.[0]?.goodsBrandName || row.orderChildForms?.[0]?.goods_brand_name || "—" }}
              </template>
            </el-table-column>
            <el-table-column align="center" label="样品名称">
              <template #default="{ row }">
                {{ row.orderChildForms?.[0]?.goodsName || row.orderChildForms?.[0]?.goods_name || "暂无" }}
              </template>
            </el-table-column>
            <el-table-column align="center" label="样品型号">
              <template #default="{ row }">
                {{ row.orderChildForms?.[0]?.goodsSpec || row.orderChildForms?.[0]?.goods_spec || "暂无" }}
              </template>
            </el-table-column>
            <el-table-column align="center" label="实验项目">
              <template #default="{ row }">
                {{ row.orderChildForms?.[0]?.experiment_project_name || "—" }}
              </template>
            </el-table-column>
            <el-table-column align="center" label="实验分类">
              <template #default="{ row }">
                {{ row.orderChildForms?.[0]?.experiment_class_name || "—" }}
              </template>
            </el-table-column>

            <el-table-column align="center" label="实付款金额">
              <template #default="{ row }">
                {{ row["xsskje"] }}
              </template>
            </el-table-column>
            <!--            <el-table-column-->
            <!--              align="center"-->
            <!--              label="下单时间"-->
            <!--            >-->
            <!--              <template #default="{ row }">-->
            <!--                {{ alterTime(row['order_time'], false) }}-->
            <!--              </template>-->
            <!--            </el-table-column>-->
            <el-table-column align="center" label="下单金额">
              <template #default="{ row }">
                {{ formatMoney(row.totalPrice ?? row.total_price) }}
              </template>
            </el-table-column>
            <el-table-column align="center" prop="" label="订单状态">
              <template #default="{ row }">
                <span :class="{ blue: row['order_statusstr'] === '已完成' }">{{
                  row["order_statusstr"]
                }}</span>
              </template>
            </el-table-column>
            <el-table-column align="center" label="开票状态">
              <template #default="{ row }">
                <span :class="{ blue: row['iskp'] == 1 }">{{
                  kpStatus[row["iskp"]]
                }}</span>
              </template>
            </el-table-column>
            <el-table-column align="center" label="付款状态">
              <template #default="{ row }">
                <span :class="{ blue: row['isfk'] - 0 }">{{
                  row["isfk"] - 0 ? "付款完成" : "待付款"
                }}</span>
              </template>
            </el-table-column>
            <el-table-column align="center" label="操作">
              <template #default="{ row }">
                <el-button
                  type="text"
                  v-if="row.order_statusstr == '已完成'"
                  @click="goyuyue(row)"
                  >再来一单</el-button
                >
                <el-button
                  type="text"
                  v-if="!(row['isfk'] - 0) && row.isUploadReceipt !== 1"
                  @click="
                    goPay(row, row.company_account, row.totalPrice - row.xsskje)
                  "
                  >支付
                </el-button>
                <el-button
                  type="text"
                  v-if="row.kpShow - 0 && row.invoiceType === 1"
                  @click="billing(row.dkpje, row.id)"
                  >申请开票
                </el-button>
                <!-- 线上订单 && 完成之前-->
                <el-button
                  type="text"
                  v-if="row['printYydShow']"
                  @click="printPDF(row.id)"
                  >打印预约单
                </el-button>
                <el-button
                  type="text"
                  v-if="row['testFiles']['length']"
                  @click="downLoadTestFiles(row['testFiles'])"
                >
                  测试数据
                </el-button>
                <el-button
                  v-if="row.ispjqx"
                  type="text"
                  @click="(currentId = row.id), (showEvaluate = true)"
                >
                  评价
                </el-button>
                <el-button
                  v-if="row.fcShow"
                  type="text"
                  @click="getChildrenList(row.id, 1)"
                  >再次测试</el-button
                >
                <el-button
                  v-if="row.wcShow"
                  type="text"
                  @click="getChildrenList(row.id, 2)"
                  >确认完成</el-button
                >
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
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
      :id="id + ''"
      :money="payMoney"
      :collection-name="collection_name"
      :collection-account="collection_account"
      @refresh="refreshPage"
      :type="1"
    ></pay>

    <download-dialog v-model="showDownLoadDialog" :list="testFiles" />

    <evaluate
      v-model="showEvaluate"
      @comfirmOK="submitEvaluate"
      :evaluating.sync="evaluating"
    ></evaluate>

    <!--    选择支付方式-->
    <choose-pay-way
      v-model="openChooseTool"
      @selected="confirmPayWay"
      :money="totalPrice"
    ></choose-pay-way>

    <!--    支付二维码-->
    <QRcode
      @reload="getList"
      :search-flag="outTradeNo"
      v-model="openQRcode"
      :content="codeUrl"
    ></QRcode>

    <!--    离线支付-->
    <offline-pay
      :pay-money="payMoney"
      @confirmSubmit="confirmSubmit"
      v-model="openOfflinePay"
      title="支付"
      :clt-account="collection_account"
      :clt-name="collection_name"
    ></offline-pay>

    <!--    复测-->
    <el-dialog
      title="选择子订单"
      :visible.sync="againTestDialog"
      :close-on-press-escape="false"
      :close-on-click-modal="false"
      @close="handleClose"
    >
      <el-select
        style="width: 100%"
        v-model="selectedChild"
        clearable
        @change="chooseChild"
        filterable
        placeholder="请选择子订单"
      >
        <el-option
          v-for="item in children"
          :key="item.id"
          :label="item.orderId"
          :value="item.id"
        >
        </el-option>
      </el-select>
      <div class="child-info" v-if="childInfo">
        <div class="info-item">
          <span>客户名称：</span>
          <span>{{ childInfo["goodsBrandName"] }}</span>
        </div>
        <div class="info-item">
          <span>样品名称：</span>
          <span>{{ childInfo["goodsName"] }}</span>
        </div>
        <div class="info-item">
          <span>样品型号：</span>
          <span>{{ childInfo["goodsSpec"] }}</span>
        </div>
        <div class="info-item" v-if="type === 1">
          <span>复测备注：</span>
          <el-input type="textarea" v-model="mark" maxlength="120"></el-input>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="againTestDialog = false">取 消</el-button>
          <el-button type="primary" @click="confirmChild">确 定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>


<style scoped>
/deep/.el-textarea__inner {
  max-height: 200px;
  padding: 5px;
  margin-top: 20px;
}

.el-dialog {
  width: 500px !important;
}
</style>
<style scoped lang="scss">
.blue {
  color: #20a0ff;
}

.child-info {
  margin-top: 20px;
  .info-item:nth-child(n + 1) {
    margin-top: 20px;
  }
}

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
