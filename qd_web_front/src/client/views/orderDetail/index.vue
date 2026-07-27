<script>
import {
  getOrderDetailApi,
  getProductOrderListApi,
  fetchTestChildOrderApi,
  submitEvaluateApi,
  getRechargeDetailApi,
} from "@client/api/order";
import { rechargeDetail } from "@client/api/index";
import { alterTime } from "@client/utils/index";
import MakeInvoice from "@client/components/makeInvoice.vue";
import pay from "@client/components/pay.vue";
import downloadDialog from "@client/components/downloadTestFiles.vue";
import evaluate from "@client/components/evaluate.vue";
import offlinePay from "@client/components/offlinePay.vue";
import QRcode from "@client/components/QRcode.vue";
import choosePayWay from "@client/components/choosePayWay.vue";
import {
  balancePayApi,
  downloadOrderFileApi,
  fetchyydApi,
  savePermitApi,
  wxPayApi,
} from "@client/api";
import { mapMutations } from "vuex";

export default {
  name: "OrderDetail",
  components: {
    choosePayWay,
    QRcode,
    offlinePay,
    evaluate,
    pay,
    MakeInvoice,
    downloadDialog,
  },
  data() {
    return {
      id: "",
      detail: null,
      jdshow: 0,
      logs: [],
      status_list: {
        0: "已取消",
        5: "采购成本未确认",
        10: "已驳回",
        20: "待审核",
        30: "已审核",
        40: "已确认",
        49: "所有成本未结清",
        50: "已完成",
        35: "已下单",
        45: "已发货",
        46: "已入库",
        55: "已评价",
        66: "待平台确认",
        67: "已和客户沟通确认",
      },
      childOrderList: [],
      page: 1,
      limit: 5,
      total: 0,
      searching: false,
      searchVal: "",
      collectionTimes: [],
      openBills: [],
      dialogVisible: false,
      money: 0,
      ids: "",
      tcoList: [],
      tcoPage: 1,
      tcoLimit: 5,
      tcoTotal: 0,
      tcoSearching: false,
      showPay: false,
      // 回执单
      hzdpath: "",
      isUploadReceipt: 0,
      hzdStatusList: ["未上传", "待审核", "审核通过", "审核驳回"],
      bhyy: "",
      collection_account: "",
      collection_name: "",
      testFiles: [],
      showDownLoadDialog: false,
      showEvaluate: false,
      evaluating: false,
      ispjqx: false,

      // 打开支付方式
      openChooseTool: false,

      // 二维码组件
      openQRcode: false,
      codeUrl: "",

      // 线下支付组件
      openOfflinePay: false,
      outTradeNo: "",
      yydUrl: "",
      totalPrice: 0,
      store: {},
      hzdFiles: [],
      showType: true,
      objData: null,
      payWayList: {
        0: "线下充值/充值",
        1: "线下充值/赠送",
      },
      yspAndDhList:[],
      recharge_type:null,
      detailLoading: false,
    };
  },
  watch: {
    // 监听dialog关闭
    dialogVisible(n) {
      if (!n) {
        if (this.id.split("|").length == 1) {
          this.showType = true;
        } else {
          this.showType = false;
        }
        this.getDetail();
      }
    },
  },
  mounted() {
    this.store = this.$store;
    this.initPage(this.$route.params.id);
  },
  methods: {
    downloadOrderFileApi,

    initPage(id) {
      this.id = id || "";
      this.detail = null;
      this.childOrderList = [];
      this.tcoList = [];
      this.logs = [];
      this.collectionTimes = [];
      this.openBills = [];
      this.yspAndDhList = [];
      if (!this.id) return;
      if (this.id.split("|").length === 1) {
        this.showType = true;
        this.getProductOrderList();
        this.getTestChildOrderList();
      } else {
        this.showType = false;
      }
      this.getDetail();
    },

    newTab() {
      window.open(this.yydUrl);
    },

    ...mapMutations({ CHANGE_LOADING: "app/CHANGE_LOADING" }),

    // 刷新页面
    refreshPage() {
      this.getDetail();
    },

    // 获取实验子订单
    getTestChildOrderList() {
      this.tcoSearching = true;
      fetchTestChildOrderApi({
        draw: 1,
        start: (this.tcoPage - 1) * this.tcoLimit,
        length: this.tcoLimit,
        ofId: this.id,
      })
        .then((res) => {
          if (res.res) {
            const payload = res.obj || res.data || {};
            this.tcoList = payload.data || [];
            this.tcoTotal = payload.recordsTotal || 0;
          } else {
            this.tcoList = [];
            this.tcoTotal = 0;
          }
        })
        .finally((_) => {
          this.tcoSearching = false;
        });
    },
    // 查看预约单
    checkMake() {
      window.open(location.origin + `/#/make/${this.id}`);
    },

    // 去支付
    goPay() {
      let xsskje = this.detail.xsskje ? this.detail.xsskje : 0;
      let totalPrice = this.detail.totalPrice ? this.detail.totalPrice : 0;
      this.totalPrice = (totalPrice * 100 - xsskje * 100) / 100;

      // this.totalPrice = this.detail.totalPrice
      this.openChooseTool = true;
    },

    // 开票
    billing() {
      this.money = this.detail.dkpje || 0;
      this.ids = this.detail.id + "";
      this.dialogVisible = true;
    },

    // 条数改变
    handleSizeChange(e, t) {
      if (t === 1) {
        this.limit = e;
        this.getProductOrderList();
      } else {
        this.tcoLimit = e;
        this.getTestChildOrderList();
      }
    },

    // 页数改变
    handleCurrentChange(e, t) {
      if (t === 1) {
        this.page = e;
        this.getProductOrderList();
      } else {
        this.tcoPage = e;
        this.getTestChildOrderList();
      }
    },

    // 检索
    searchOrder() {
      this.page = 1;
      this.getProductOrderList();
    },

    // 获取产品子订单
    getProductOrderList() {
      this.searching = true;
      getProductOrderListApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        ofId: this.id,
        order_id: this.searchVal,
      })
        .then((res) => {
          if (res.res) {
            const payload = res.obj || res.data || {};
            this.childOrderList = payload.data || [];
            this.total = payload.recordsTotal || 0;
          } else {
            this.childOrderList = [];
            this.total = 0;
            this.$notify({
              type: "warning",
              title: "提示",
              message: res.resMsg || res.message || "获取子订单失败",
            });
          }
        })
        .finally((_) => {
          this.searching = false;
        });
    },

    alterTime,
    //   获取详情
    getDetail() {
      if (this.showType) {
        this.detailLoading = true;
        getOrderDetailApi({ id: this.id })
          .then((res) => {
            const payload = res.obj || res.data || {};
            if (res.res && payload.of) {
              const {
                files,
                logs,
                collectionTimes,
                openBills,
                hzdpath,
                hzdFiles,
                bhyy,
                testFiles,
                ispjqx,
                jdshow,
                yydUrl,
                yspAndDhList,
              } = payload;
              if (payload.eor) this.recharge_type = payload.eor.recharge_type;

              this.jdshow = jdshow;
              this.detail = payload.of;
              this.logs = logs || [];
              this.collectionTimes = collectionTimes || [];
              this.openBills = openBills || [];
              this.hzdpath = hzdpath || "";
              this.isUploadReceipt = payload.of.isUploadReceipt || 0;
              this.bhyy = bhyy || "";
              this.ispjqx = ispjqx;
              this.hzdFiles = hzdFiles || [];
              this.testFiles = testFiles || [];
              this.yydUrl = yydUrl || "";
              this.files = files || [];
              this.yspAndDhList = yspAndDhList || [];
              if (payload.of.company_account) {
                const parts = String(payload.of.company_account).split(" ");
                this.collection_name = parts[0] || "";
                this.collection_account = parts[1] || "";
              }
            } else {
              this.detail = null;
              this.$notify({
                type: "warning",
                title: "提示",
                message: res.resMsg || res.message || "订单详情加载失败",
              });
            }
          })
          .catch(() => {
            this.detail = null;
          })
          .finally(() => {
            this.detailLoading = false;
          });
      } else {
        console.log('666')
        getRechargeDetailApi({ id: this.id.split("|")[0] }).then((res) => {
          const { files, logs, openBills, obj,yspAndDhList } = res.obj;
          if(res.obj.obj) this.recharge_type = res.obj.obj.recharge_type
          this.logs = logs;
          this.openBills = openBills ? openBills : [];
          this.files = files;
          this.objData = obj;
        });
      }
    },

    // 打印预约单
    printPDF() {
      return window.open(this.yydUrl);
      this.CHANGE_LOADING(1);
      fetchyydApi(id)
        .then((res) => {
          if (res.res) {
            window.open(res.obj.url);
          } else {
            this.$notify({
              type: res.res ? "success" : "warning",
              title: "提示",
              message: res.resMsg,
            });
          }
        })
        .finally((_) => {
          this.CHANGE_LOADING();
        });
    },

    submitEvaluate(e) {
      this.evaluating = true;
      submitEvaluateApi({
        id: this.id,
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
            this.ispjqx = false;
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
            this.getDetail();
          }
        })
        .finally((_) => {
          this.CHANGE_LOADING();
        });
    },

    confirmPayWay(payWayId, integral_num, money) {
      const that = this;
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
                      that.$notify({
                        type: res.res ? "success" : "warning",
                        title: "提示",
                        message: res.res ? "支付成功" : res.resMsg,
                      });
                      if (res.res) {
                        that.getDetail();
                        that.store.dispatch("user/getIntegralApi");
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
                    that.$notify({
                      type: res.res ? "success" : "warning",
                      title: "提示",
                      message: res.res ? "支付成功" : res.resMsg,
                    });
                    if (res.res) {
                      that.getDetail();
                      that.store.dispatch("user/getIntegralApi");
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
    <el-card class="box-card" v-loading="detailLoading">
    <template v-if="detail">
      <div slot="header" class="clearfix">
        <span>订单详情</span>
        <!--      进度展示-->
        <template v-if="jdshow">
          <img
            class="progress"
            v-if="jdshow === 1"
            src="@client/static/25.png"
            alt=""
          />
          <img
            class="progress"
            v-else-if="jdshow === 2"
            src="@client/static/50.png"
            alt=""
          />
          <img
            class="progress"
            v-else-if="jdshow === 3"
            src="@client/static/75.png"
            alt=""
          />
          <img class="progress" v-else src="@client/static/100.png" alt="" />
        </template>
      </div>
      <div class="row">
        <div class="text item">
          <span>订单编号：</span>
          <span>{{ detail["order_id"] }}</span>
        </div>
        <div class="text item">
          <span>订单类型：</span>
          <span>{{ detail.testClass?.name || "—" }}</span>
        </div>
        <div class="text item">
          <span>总价：</span>
          <span>{{
            Number(detail.totalPrice) ? Number(detail.totalPrice).toFixed(2) : "0.00"
          }}</span>
        </div>
      </div>
      <div class="row">
        <div class="text item">
          <span>下单时间：</span>
          <span>{{ alterTime(detail["order_time"], false) }}</span>
        </div>
        <div class="text item">
          <span>预计收货时间：</span>
          <span>{{ alterTime(detail["delivery_time"], false) }}</span>
        </div>
        <div class="text item">
          <span>是否开票：</span>
          <span>{{ detail.invoiceType === 1 ? "是" : "否" }}</span>
        </div>
      </div>
      <div class="row">
        <span>云视频：</span>
        <span>{{ detail.is_video ? "是" : "否" }}</span>
      </div>
      <div class="row">
        <div class="text item" v-if="detail.invoiceType && detail.isfk - 0">
          <span>开票状态：</span>
          <span>{{ detail["iskp"] - 0 ? "完成" : "未完成" }}</span>
        </div>
        <div class="text item">
          <span>订单状态：</span>
          <span>{{ detail["order_statusstr"] }}</span>
        </div>
        <div class="text item">
          <span>付款状态：</span>
          <span>{{ detail["isfk"] - 0 ? "付款完成" : "待付款" }}</span>
        </div>
      </div>
      <div
        class="row"
        v-for="(item, idx) in openBills"
        :key="'openBills_' + idx"
      >
        <div class="text item">
          <span>开票时间：</span>
          <span>{{ alterTime(item.billDate) }}</span>
        </div>
        <div class="text item">
          <span>开票金额：</span>
              <span>{{ Number(item.money || 0).toFixed(2) }}元</span>
        </div>
      </div>

      <template v-if="collectionTimes.length">
        <div
          class="a-bill"
          v-for="(item, idx) in collectionTimes"
          :key="'collectionTimes_' + idx"
        >
          <div class="row">
            <div class="text item">
              <span>预计付款时间：</span>
              <span>{{ alterTime(item.time, false) }}</span>
            </div>
            <div class="text item">
              <span>预计付款金额：</span>
              <span>{{ (item.price * 1).toFixed(2) }}元</span>
            </div>
          </div>
          <div class="row" v-if="item.onlinebill">
            <div class="text item">
              <span>实际付款时间：</span>
              <span>{{ alterTime(item.onlinebill.billDate) }}</span>
            </div>
            <div class="text item">
              <span>实际付款金额：</span>
              <span>{{ (item.onlinebill.money * 1).toFixed(2) }}元</span>
            </div>
          </div>
          <div class="row" v-if="item.bill&&!item.onlinebill">
            <div class="text item">
              <span>实际付款时间：</span>
              <span>{{ alterTime(item.bill.billDate) }}</span>
            </div>
            <div class="text item">
              <span>实际付款金额：</span>
              <span>{{ (item.bill.money * 1).toFixed(2) }}元</span>
            </div>
          </div>
        </div>
      </template>

      <!-- <div class="row" v-if="hzdpath">
        <div class="text item">
          <span>回执单：</span>
          <el-image
            class="hzd"
            :src="hzdpath"
            :preview-src-list="[hzdpath]">

          </el-image>
        </div>
        <div class="text item">
          <span>回执单状态：</span>
          <span>{{ hzdStatusList[isUploadReceipt] }}</span>
        </div>
        <div class="text item" v-if="isUploadReceipt === 3">
          <span>驳回原因：</span>
          <span>{{ bhyy }}</span>
        </div>
      </div> -->
      <div class="row" v-if="yydUrl">
        <div class="text item" style="width: 100%">
          <span>预约单：</span>
          <span>
            <el-link @click="newTab">{{ detail.order_id }}</el-link>
          </span>
        </div>
      </div>

      <!-- hzdFiles -->
      <div class="row" v-if="hzdFiles.length > 0">
        <!-- <div class="text item">
          <span>回执单：</span>
          <el-image
            class="hzd"
            :src="hzdpath"
            :preview-src-list="[hzdpath]">

          </el-image>
        </div> -->
        <div class="text item">
          <span>回执单：</span>
          <div class="order-data-list">
            <div v-for="(file, idx) in hzdFiles" :key="idx">
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
        </div>
        <div class="text item">
          <span>回执单状态：</span>
          <span>{{ hzdStatusList[isUploadReceipt] }}</span>
        </div>
        <div class="text item" v-if="isUploadReceipt === 3">
          <span>驳回原因：</span>
          <span>{{ bhyy }}</span>
        </div>
        <!-- <div class="text item">
          <span>回执单状态：</span>
          <span>{{ hzdStatusList[isUploadReceipt] }}</span>
        </div>
        <div class="text item" v-if="isUploadReceipt === 3">
          <span>驳回原因：</span>
          <span>{{ bhyy }}</span>
        </div> -->
      </div>
      <!-- <div class="row" v-if="yspAndDhList.length">
        <div class="text item">
          <span>订单资料：</span>
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
        </div>
      </div> -->
      <template v-if="yspAndDhList.length">
        <div
          class="a-bill"
          v-for="(item, idx) in yspAndDhList"
          :key="'yspAndDhList_' + idx"
        >
          <div class="row">
            <div class="text item" v-if="item.hyh">
              <span>云视频会议号：</span>
              <span>{{ item.hyh }}</span>
            </div>
            <div class="text item" v-if="item.jhdh">
              <span>样品寄回单号：</span>
              <span>{{ item.jhdh }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- <div class="row" v-if="files.length">
        <div class="text item">
          <span>订单资料：</span>
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
        </div>
      </div> -->
    </template>
    <div v-else-if="!detailLoading" class="empty-tip">暂无订单详情，请从列表重新进入或刷新页面</div>
    </el-card>
    <el-card class="box-card" v-if="objData">
      <div class="row">
        <div class="text item">
          <span>线下充值单号：</span>
          <span>{{ objData["recharge_num"] }}</span>
        </div>
        <div class="text item">
          <span>充值时间：</span>
          <span>{{ alterTime(objData["addTime"]) }}</span>
        </div>
        <div class="text item">
          <span>用户名：</span>
          <span>{{ objData.expUser["company_name"] }}</span>
        </div>
      </div>
      <div class="row">
        <div class="text item">
          <span>电话：</span>
          <span>{{ objData.expUser["mobile"] }}</span>
        </div>
        <div class="text item">
          <span>金额：</span>
          <span>{{ objData["money"] ? objData["money"].toFixed(2) : '0.00' }}</span>
        </div>
        <div class="text item">
          <span>申请类型：</span>
          <!-- <span>{{ payWayList[objData.recharge_type] }}</span> -->
           <span>线下充值</span>
        </div>
      </div>
      <div class="row">
        <div class="text item">
          <span>操作类型：</span>
          <span>{{ recharge_type == 0 ? '充值' : '赠送' }}</span>
        </div>
      </div>

      <div
        class="row"
        v-for="(item, idx) in openBills"
        :key="'openBills_' + idx"
      >
        <div class="text item">
          <span>开票时间：</span>
          <span>{{ alterTime(item.billDate) }}</span>
        </div>
        <div class="text item">
          <span>开票金额：</span>
          <span>{{ item.money ? item.money.toFixed(2) : '0.00' }}元</span>
        </div>
      </div>
      <div class="row">
        <div class="text item">
          <span>备注：</span>
          <span>{{ objData["mark"]}}</span>
        </div>
      </div>
      <!-- <div class="row">
        <div class="text item">
          <span>云视频会议号：</span>
          <span>{{ objData["mark"]}}</span>
        </div>
      </div>
      <div class="row">
        <div class="text item">
          <span>样品寄回单号：</span>
          <span>{{ objData["mark"]}}</span>
        </div>
      </div> -->
      <!-- <div class="row" v-if="files.length">
        <div class="text item">
          <span>订单资料：</span>
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
        </div>
      </div> -->
    </el-card>

    <div class="handle-btns" v-if="detail">
      <el-button
        type="primary"
        v-if="!(detail['isfk'] - 0) && isUploadReceipt !== 1"
        @click="goPay"
        >支付
      </el-button>
      <el-button
        type="primary"
        v-if="detail.kpShow - 0 && detail.invoiceType === 1"
        @click="billing"
        >申请开票
      </el-button>
      <!-- 线上订单 && 完成之前-->
      <el-button type="primary" v-if="detail['printYydShow']" @click="printPDF">
        打印预约单
      </el-button>
      <el-button
        type="primary"
        v-if="testFiles.length"
        @click="showDownLoadDialog = true"
        >测试数据</el-button
      >
      <el-button v-if="ispjqx" type="primary" @click="showEvaluate = true"
        >评价</el-button
      >

      <!--      <el-button type="primary" v-if="detail.order_status === 30" @click="goPay">去支付</el-button>-->
      <!--      <template v-if="detail.order_status === 48">-->
      <!--        <el-button type="primary" @click="checkMake">打印预约单</el-button>-->
      <!--        <el-button type="primary" @click="billing">申请开票</el-button>-->
      <!--      </template>-->
    </div>

    <header v-if="showType">
      <el-input
        size="mini"
        v-model="searchVal"
        placeholder="请输入产品订单编号"
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
    <main v-if="showType">
      <el-table :data="childOrderList" style="width: 100%" border stripe>
        <el-table-column align="center" prop="orderId" label="子订单编号" />
        <el-table-column
          align="center"
          label="客户名称"
          prop="goodsBrandName"
        />
        <el-table-column align="center" label="样品名称" prop="goodsName" />
        <el-table-column align="center" label="样品型号" prop="goodsSpec" />
        <el-table-column align="center" prop="goodsNums" label="样品数量" />
        <el-table-column align="center" label="实验项目">
          <template #default="{ row }">
            {{ row["experiment_project_name"] }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="实验分类">
          <template #default="{ row }">
            {{ row["experiment_class_name"] }}
          </template>
        </el-table-column>
        <el-table-column
          align="center"
          prop="orderStautsStr"
          label="订单状态"
        />
        <el-table-column align="center" label="总价">
          <template #default="{ row }">
            {{ (row["goodsNums"] * row["goodsPrice"]).toFixed(2) }}
          </template>
        </el-table-column>
      </el-table>
    </main>
    <footer v-if="showType">
      <el-pagination
        background
        @size-change="handleSizeChange($event, 1)"
        @current-change="handleCurrentChange($event, 1)"
        :page-sizes="[5, 10]"
        :page-size="limit"
        :current-page="page"
        layout="total, prev, pager, next, sizes"
        :total="total"
        :disabled="searching"
      />
    </footer>

    <!--    实验子订单-->
    <div class="test-child-order-table" v-if="showType">
      <el-table :data="tcoList" style="width: 100%" border stripe>
        <el-table-column align="center" label="子订单编号">
          <template #default="{ row }">
            <el-link>
              <router-link :to="`/b/child_order_detail/${row.id}`">
                {{ row["order_id"] }}
              </router-link>
            </el-link>
          </template>
        </el-table-column>
        <el-table-column align="center" label="创建时间">
          <template #default="{ row }">
            {{ alterTime(row.addTime) }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="订单状态">
          <template #default="{ row }">
            {{ row["order_statusstr"] }}
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="test-child-order-footer" v-if="showType">
      <el-pagination
        background
        @size-change="handleSizeChange($event, 2)"
        @current-change="handleCurrentChange($event, 2)"
        :page-sizes="[5, 10]"
        :page-size="tcoLimit"
        :current-page="tcoPage"
        layout="total, prev, pager, next, sizes"
        :total="tcoTotal"
        :disabled="tcoSearching"
      />
    </div>
    <div style="margin: 40px 0 20px 0;color: #f39800;font-weight: 700;padding-left: 28px;font-size: 15px">{{ showType ? '测试进度请点击子订单进入查看' : '' }}</div>
    <el-timeline>
      <el-timeline-item
        v-for="(activity, index) in logs"
        :key="'logs_' + index"
        :timestamp="alterTime(activity.addTime)"
      >
        <span>{{ activity.log_info }}</span>
      </el-timeline-item>
    </el-timeline>

    <!--    <pay :pay-dialog.sync="showPay" :id="id + ''" :collection-name="collection_name"-->
    <!--         :collection-account="collection_account"-->
    <!--         :money="detail && detail.totalPrice? (detail.totalPrice - detail.xsskje) : 0"-->
    <!--         @refresh="refreshPage" :type="1"></pay>-->

    <download-dialog v-model="showDownLoadDialog" :list="testFiles" />

    <evaluate
      v-model="showEvaluate"
      @comfirmOK="submitEvaluate"
      :evaluating.sync="evaluating"
    ></evaluate>

    <choose-pay-way
      :money="totalPrice"
      v-model="openChooseTool"
      @selected="confirmPayWay"
    ></choose-pay-way>
    <QRcode
      @reload="getDetail"
      :search-flag="outTradeNo"
      v-model="openQRcode"
      :content="codeUrl"
    ></QRcode>
    <offline-pay
      :pay-money="
        detail && detail.totalPrice ? detail.totalPrice - detail.xsskje : 0
      "
      @confirmSubmit="confirmSubmit"
      v-model="openOfflinePay"
      title="支付"
      :clt-account="collection_account"
      :clt-name="collection_name"
    ></offline-pay>
  </div>
</template>

<style scoped>
/deep/.el-link--inner {
  font-size: 16px;
}

/deep/.el-link.el-link--default {
  color: #303133;
}

/deep/.el-link.el-link--default:hover {
  color: var(--mainColor);
}
</style>

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

.handle-btns {
  margin: 30px 0 30px;

  .el-button {
    &:nth-child(n + 2) {
      margin-left: 20px !important;
    }
  }
}

.test-child-order-table {
  margin-top: 20px;
}

footer,
.test-child-order-footer {
  margin-top: 20px;
}

.clearfix {
  position: relative;
}

header {
  margin: 20px 0;

  .el-input {
    width: 200px;
  }

  .el-button {
    margin-left: 10px;
  }
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
