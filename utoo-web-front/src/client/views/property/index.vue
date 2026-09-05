<script>
import { getMyAssetInfoApi } from "@client/api/user";
import {
  getOrderListForTypeApi,
  cancelInvoiceApi,
  getMyOrderListForTypeApi,
} from "@client/api/order";
import { alterTime } from "@client/utils/index";
import {
  checkPayStatusApi,
  fetchAccountDetailApi,
  fetchDefaultAccountApi,
  fetchInvoiceRecordListApi,
  payApi,
  submitFormApi,
  wxTopUpApi,
  wxContinueTopUpApi,
} from "@client/api/index";
import choosePayWay from "@client/components/choosePayWay.vue";
import { ElMessageBox } from "element-plus";
import QRcode from "@client/components/QRcode.vue";
import offlinePay from "@client/components/offlinePay.vue";
import { mapMutations } from "vuex";
import PersonalPageShell from "@client/components/personal/PersonalPageShell.vue";

export default {
  name: "Property",
  components: { choosePayWay, QRcode, offlinePay, PersonalPageShell },
  data() {
    var validatePass = (rule, value, callback) => {
      const reg = /^\d{16,19}$/;
      if (!value) {
        callback(new Error("银行卡号不能为空"));
      } else if (!reg.test(value)) {
        callback(new Error("银行卡号输入有误"));
      } else {
        callback();
      }
    };
    return {
      activeName: "0",
      /** 列表请求序号，防止 mounted 流水请求晚返回覆盖「待支付订单」等 Tab */
      listRequestSeq: 0,
      tableData: [],
      total: 0,
      page: 1,
      limit: 5,
      moneyInfo: "",
      // status_list: ['全部记录', '充值记录', '支付记录', '提现记录', '开票记录', '待处理订单', '待申请发票', '待支付订单'],
      status_list: [
        {
          value: 0,
          label: "全部记录",
        },
        {
          value: 1,
          label: "充值记录",
        },
        {
          value: 2,
          label: "支付记录",
        },
        // {
        //   value: 3,
        //   label: '提现记录'
        // },
        {
          value: 4,
          label: "开票记录",
        },
        {
          value: 5,
          label: "待处理订单",
        },
        {
          value: 6,
          label: "待申请发票",
        },
        {
          value: 7,
          label: "待支付订单",
        },
      ],
      searchVal: "",
      searching: false,
      order_status_list: {
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
        66: "待平台确认",
        67: "已和客户沟通确认",
      },
      // 是否有待审核的充值记录
      showPayBtn: false,
      defaultBankAccount: "",
      defaultBankName: "",

      //   提现
      openDialog: false,
      subForm: {
        name: "",
        money: "",
        card_num: "",
      },
      subFormRules: {
        name: [
          {
            required: true,
            message: "姓名不能为空",
            trigger: "blur",
          },
        ],
        money: [
          {
            required: true,
            message: "金额不能为空",
            trigger: "blur",
          },
        ],
        card_num: [
          {
            required: true,
            validator: validatePass,
            trigger: "blur",
          },
        ],
      },
      withdrawing: false,

      pay_time: "",
      payWayList: {
        1: "支付宝",
        2: "微信",
        3: "线下支付",
        4: "余额支付",
        5: "线下充值",
        6: "会员余额收款",
        7: "线下充值",
      },
      pickerOptions: {
        shortcuts: [
          {
            text: "最近一周",
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
              picker.$emit("pick", [start, end]);
            },
          },
          {
            text: "最近一个月",
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
              picker.$emit("pick", [start, end]);
            },
          },
          {
            text: "最近三个月",
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
              picker.$emit("pick", [start, end]);
            },
          },
        ],
      },
      handleList: {
        2: "支付",
        3: "支付",
        4: "提现",
      },
      invoice_status: {
        1: "开票中",
        2: "退票中",
        3: "已作废",
        4: "已开票",
        5: "已取消",
      },
      // 打开支付方式
      openChooseTool: false,

      // 二维码组件
      openQRcode: false,
      codeUrl: "",

      // 线下支付组件
      openOfflinePay: false,
      outTradeNo: "",
      countdownTimer: null,
    };
  },
  mounted() {
    this.getMoney();

    this.reloadCurrentTab();
    this.startCountdownTimer();

    checkPayStatusApi().then((res) => {
      this.showPayBtn = res.res ? false : true;
    });

    fetchDefaultAccountApi().then((res) => {
      if (res.res) {
        const { bankCardNum, company_name } = res.obj;
        this.defaultBankAccount = bankCardNum;
        this.defaultBankName = company_name;
      }
    });
  },
  beforeUnmount() {
    this.stopCountdownTimer();
  },
  methods: {
    checkInvoiceData(url) {
      window.open(url);
    },

    ...mapMutations({ CHANGE_LOADING: "app/CHANGE_LOADING" }),

    bumpListRequestSeq() {
      this.listRequestSeq += 1;
      return this.listRequestSeq;
    },

    isRunWaterTab() {
      return [0, 1, 2, 3].includes(this.activeName - 0);
    },

    isPendingOrderTab() {
      return [6, 7].includes(this.activeName - 0);
    },

    listPayload(res) {
      const payload = res?.obj ?? res?.data ?? {};
      return {
        data: payload.data ?? [],
        recordsTotal: payload.recordsTotal ?? 0,
      };
    },

    formatOrderMoney(val) {
      const n = Number(val);
      return Number.isFinite(n) ? n.toFixed(2) : "0.00";
    },

    /** 按当前 Tab 拉列表（分页/检索/切换 Tab 共用） */
    reloadCurrentTab() {
      const tab = this.activeName - 0;
      if ([0, 1, 2, 3].includes(tab)) {
        this.getRunWaterList();
      } else if (tab === 4) {
        this.getInvoiceList();
      } else if (tab === 5) {
        this.getOrderList();
      } else if (tab === 6 || tab === 7) {
        this.getOrderList2();
      }
    },

    // 千分位
    format_with_Intl(num = 0) {
      let str = parseFloat(num).toFixed(2);
      let parts = str.split(".");
      let integerPart = parts[0];
      integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      return `${integerPart}.${parts[1]}`;
    },

    //   获取发票列表
    getInvoiceList() {
      this.searching = true;
      fetchInvoiceRecordListApi({
        start: (this.page - 1) * this.limit,
        length: this.limit,
        orderId: this.searchVal,
        draw: 1,
        //   1专票 2普票
        // 目前只有普票
        type: 2,
      })
        .then((res) => {
          if (res.res) {
            this.tableData = res.obj.data;
            this.total = res.obj.recordsTotal;
            console.log(this.tableData);
            // this.invoice_money = res.obj.stayApplyMoney.toFixed(2)
          } else {
            this.$notify.error({
              title: "提示",
              message: res.resMsg,
            });
          }
        })
        .finally((_) => {
          this.searching = false;
        });
    },

    // 流水相关的订单
    getRunWaterList() {
      const seq = this.bumpListRequestSeq();
      this.searching = true;
      fetchAccountDetailApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        startTime: this.pay_time
          ? this.alterTime(+new Date(this.pay_time[0]))
          : "",
        endTime: this.pay_time
          ? this.alterTime(+new Date(this.pay_time[1]))
          : "",
        type: this.activeName,
      })
        .then((res) => {
          if (seq !== this.listRequestSeq || !this.isRunWaterTab()) return;
          if (res.res) {
            const { data, recordsTotal } = this.listPayload(res);
            this.tableData = data;
            this.total = recordsTotal;
          } else {
            this.$notify.error(res.errMsg ? res.errMsg : "获取失败");
          }
        })
        .finally(() => {
          if (seq === this.listRequestSeq) this.searching = false;
        });
    },

    /** 充值二维码关闭或支付成功：刷新余额与当前 Tab 流水 */
    onRechargeQrClosed() {
      this.getMoney();
      this.reloadCurrentTab();
      this.startCountdownTimer();
    },

    stopCountdownTimer() {
      if (this.countdownTimer) {
        clearInterval(this.countdownTimer);
        this.countdownTimer = null;
      }
    },

    startCountdownTimer() {
      this.stopCountdownTimer();
      if (![0, 1, 2, 3].includes(this.activeName - 0)) return;
      this.countdownTimer = setInterval(() => {
        const now = Date.now();
        let needReload = false;
        this.tableData = (this.tableData || []).map((row) => {
          if (String(row.payStatusRaw) !== "1" || !row.closeAt) return row;
          const rem = Math.max(
            0,
            Math.floor((new Date(row.closeAt).getTime() - now) / 1000)
          );
          if (rem === 0 && row.canContinuePay) needReload = true;
          return {
            ...row,
            remainingSeconds: rem,
            canContinuePay: rem > 0 && Number(row.pay_way) === 2,
          };
        });
        if (needReload) this.reloadCurrentTab();
      }, 1000);
    },

    formatPendingCountdown(sec) {
      const s = Math.max(0, Number(sec) || 0);
      const m = Math.floor(s / 60);
      const r = s % 60;
      return `${m}分${String(r).padStart(2, "0")}秒`;
    },

    continueRechargePay(row) {
      if (!row?.id) return;
      wxContinueTopUpApi({ id: row.id })
        .then((res) => {
          const payload = res?.obj ?? res?.data ?? {};
          const codeUrl = payload?.codeUrl;
          const ok =
            codeUrl &&
            (res?.res === true || res?.code === 0 || res?.res === undefined);
          if (ok) {
            this.codeUrl = codeUrl;
            this.outTradeNo = payload.outTradeNo || row.outTradeNo || "";
            this.openQRcode = true;
          } else {
            this.$notify({
              type: "warning",
              title: "提示",
              message: res?.resMsg || res?.message || "无法继续支付",
            });
            this.reloadCurrentTab();
          }
        })
        .catch((err) => {
          this.$notify({
            type: "error",
            title: "提示",
            message: err?.message || "继续支付失败",
          });
        });
    },

    // 获取金额
    getMoney() {
      getMyAssetInfoApi().then((res) => {
        if (res.res) {
          // 可开票
          res.obj["invoicingAmount"] = this.format_with_Intl(
            res.obj["invoicingAmount"]
          );
          // 欠款
          res.obj["arrearAmount"] = this.format_with_Intl(
            res.obj["arrearAmount"]
          );
          const arrear = parseFloat(res.obj.arrearAmount) || 0;
          const netBal = parseFloat(res.obj.netBalance);
          res.obj.showArrearHint = arrear > 0;
          res.obj.showNetDebt =
            !Number.isNaN(netBal) && netBal < 0;
          res.obj.netBalanceFormatted = !Number.isNaN(netBal)
            ? this.format_with_Intl(Math.abs(netBal))
            : "";
          res.obj["amount"] = this.format_with_Intl(res.obj["amount"]);
          if (res.obj.accountBalance != null) {
            res.obj.accountBalance = this.format_with_Intl(res.obj.accountBalance);
          }
          this.moneyInfo = res.obj;
        } else {
          this.$notify.error({
            title: "提示",
            message: res.resMsg,
          });
        }
      });
    },

    // 充值
    goPay() {
      this.openChooseTool = true;
    },

    getOrderList2() {
      const seq = this.bumpListRequestSeq();
      // 6=待申请发票(type=5)，7=待支付订单(type=1)，勿与 Tab 的 value 混用
      const tab = this.activeName - 0;
      const listType = tab === 6 ? 5 : 1;
      this.searching = true;
      getMyOrderListForTypeApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        supplier_name: "",
        customer_name: "",
        sale_user: "",
        order_status: "",
        order_id: this.searchVal,
        goods_name: "",
        order_startime: "",
        order_endtime: "",
        type: listType,
      })
        .then((res) => {
          if (seq !== this.listRequestSeq || !this.isPendingOrderTab()) return;
          if (res.res) {
            const { data, recordsTotal } = this.listPayload(res);
            this.tableData = data;
            this.total = recordsTotal;
          } else {
            this.$notify.error({
              title: "提示",
              message: res.resMsg || res.message || "加载失败",
            });
          }
        })
        .catch((err) => {
          if (seq !== this.listRequestSeq || !this.isPendingOrderTab()) return;
          this.$notify.error({
            title: "提示",
            message: err?.message || "加载失败",
          });
        })
        .finally(() => {
          if (seq === this.listRequestSeq) this.searching = false;
        });
    },

    // 获取实验订单
    getOrderList() {
      const seq = this.bumpListRequestSeq();
      this.searching = true;
      getOrderListForTypeApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        supplier_name: "",
        customer_name: "",
        sale_user: "",
        // 采购成本未确认
        order_status: this.activeName - 0 ? "" : "5",
        order_id: this.searchVal,
        goods_name: "",
        order_startime: "",
        order_endtime: "",
        type: this.activeName - 0,
      })
        .then((res) => {
          if (seq !== this.listRequestSeq || this.activeName != 5) return;
          if (res.res) {
            const { data, recordsTotal } = this.listPayload(res);
            this.tableData = data;
            this.total = recordsTotal;
          } else {
            this.$notify.error({
              title: "提示",
              message: res.resMsg,
            });
          }
        })
        .finally(() => {
          if (seq === this.listRequestSeq) this.searching = false;
        });
    },
    alterTime,

    // 条数改变
    handleSizeChange(e) {
      this.limit = e;
      this.reloadCurrentTab();
    },

    // 页数改变
    handleCurrentChange(e) {
      this.page = e;
      this.reloadCurrentTab();
    },

    // 检索
    searchOrder() {
      this.page = 1;
      this.reloadCurrentTab();
    },

    // Tab 切换（须用 tab-change：tab-click 触发时 activeName 尚未更新，会误拉流水）
    handleTabChange(name) {
      this.activeName = String(name);
      this.bumpListRequestSeq();
      this.tableData = [];
      this.total = 0;
      this.page = 1;
      this.searchVal = "";
      this.pay_time = "";
      this.reloadCurrentTab();
      this.startCountdownTimer();
    },

    withdraw() {
      this.openDialog = true;
    },

    closeDialog() {
      this.$refs["sub-form"].resetFields();
      this.openDialog = false;
      this.withdrawing = false;
    },

    submitForm() {
      this.$refs["sub-form"].validate((valid) => {
        if (valid) {
          this.withdrawing = true;
          const { name, money, card_num } = this.subForm;
          submitFormApi({
            money: money,
            bankNum: card_num,
            accountName: name,
          })
            .then((res) => {
              this.$notify({
                type: res.res ? "success" : "warning",
                title: "提示",
                message: res.res ? "提现申请发起成功" : res.resMsg,
              });
              if (res.res) {
                this.closeDialog();
                this.getMoney();
              }
            })
            .finally((_) => {
              this.withdrawing = false;
            });
        }
      });
    },

    // 验证金额
    verifyMoney(e) {
      let v = parseFloat(e);
      if (isNaN(v)) {
        v = 0;
      } else if (v > this.moneyInfo.amount) {
        v = this.moneyInfo.amount;
      }
      this.subForm.money = v;
    },

    // 提现全部金额
    allMoney() {
      this.subForm.money = this.moneyInfo.amount;
      this.$refs["m"].focus();
      this.$refs["m"].blur();
    },

    //   取消发票
    cancelInvoice(id) {
      this.$confirm("确认取消开票?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        cancelInvoiceApi({
          invoiceId: id,
        }).then((res) => {
          this.$notify({
            type: res.res ? "success" : "error",
            title: "提示",
            message: res.resMsg,
          });
          if (res.res) {
            this.getInvoiceList();
          }
        });
      });
    },

    // 确认
    confirmPayWay(id) {
      switch (id) {
        case 1:
          console.log("支付宝");
          break;
        case 2:
          this.$prompt("请输入充值金额", "提示", {
            confirmButtonText: "确定",
            cancelButtonText: "取消",
            inputPattern: /^\d+(\.\d{1,2})?$/,
            inputErrorMessage: "请输入正确金额",
          })
            .then(({ value }) => {
              if (value == null || String(value).trim() === "") {
                this.$message.warning("请输入充值金额");
                return;
              }
              return wxTopUpApi({ money: value }).then((res) => {
                const payload =
                  res?.obj ?? res?.data ?? (res?.codeUrl ? res : null);
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
              });
            })
            .catch(() => {});
          break;
        case 3:
          this.openOfflinePay = true;
          break;
        default:
          console.log("1");
      }
    },

    // 回执单充值
    confirmSubmit(e) {
      this.CHANGE_LOADING(1);
      payApi({
        money: e.money,
        file_id: e.fileId,
        pay_way: 3,
      })
        .then((res) => {
          this.$notify({
            type: res.res ? "success" : "warning",
            title: "提示",
            message: res.res ? "审核已提交" : res.errMsg,
          });
          if (res.res) {
            // 不会触发handleClose，
            this.openOfflinePay = false;
          }
        })
        .finally((_) => {
          // 需要手动改变loading状态
          this.CHANGE_LOADING();
        });
    },
  },
};
</script>

<template>
  <personal-page-shell
    title="我的资产"
    subtitle="账户余额、充值还款与资产明细一站式管理"
    icon="property"
  >
    <header v-if="moneyInfo" class="pc-stat-row property-summary">
      <div class="wrapper">
        <div class="label">账户余额</div>
        <div class="money">
          <span class="parse-int">{{ moneyInfo["amount"].split(".")[0] }}</span>
          <span class="parse-float"
            >.{{ moneyInfo["amount"].split(".")[1] }}</span
          >
        </div>
        <div v-if="moneyInfo.showArrearHint" class="sub-balance">
          充值已入账，可使用本余额在右侧「支付」页还款（单笔不超过账户余额）
        </div>
        <div v-if="moneyInfo.showNetDebt" class="sub-balance sub-balance-warn">
          净欠款 ¥{{ moneyInfo.netBalanceFormatted }}（待支付金额大于账户余额）
        </div>
        <!--         :disabled="!showPayBtn"-->
        <el-button type="text" @click="goPay">充值</el-button>
        <!--        <el-button type="text" @click="withdraw">提现</el-button>-->
        <!--        <el-button type="text">-->
        <!--          <router-link to="/b/pay_history">明细</router-link>-->
        <!--        </el-button>-->
      </div>
      <div class="wrapper">
        <div class="label">待支付金额</div>
        <div class="money">
          <span class="parse-int">{{
            moneyInfo["arrearAmount"].split(".")[0]
          }}</span>
          <span class="parse-float"
            >.{{ moneyInfo["arrearAmount"].split(".")[1] }}</span
          >
        </div>
        <el-button type="text">
          <router-link to="/b/repayment">支付</router-link>
        </el-button>
      </div>
      <div class="wrapper">
        <div class="label">可开票金额</div>
        <div class="money">
          <span class="parse-int">{{
            moneyInfo["invoicingAmount"].split(".")[0]
          }}</span>
          <span class="parse-float"
            >.{{ moneyInfo["invoicingAmount"].split(".")[1] }}</span
          >
        </div>
        <el-button type="text" @click="$router.push('/b/invoice')"
          >立即开票</el-button
        >
      </div>
    </header>

    <main>
      <el-tabs v-model="activeName" @tab-change="handleTabChange">
        <el-tab-pane
          :disabled="searching"
          :label="item.label"
          :name="item.value + ''"
          v-for="item in status_list"
          :key="item.value"
        >
          <div v-show="activeName < 4">
            <div class="search">
              <el-date-picker
                size="mini"
                style="margin-left: 10px"
                v-model="pay_time"
                type="datetimerange"
                :picker-options="pickerOptions"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                align="right"
              >
              </el-date-picker>
              <el-button
                :loading="searching"
                type="primary"
                size="mini"
                @click="searchOrder"
                >检索</el-button
              >
            </div>
            <el-table :data="tableData" style="width: 100%" border stripe>
              <el-table-column
                align="center"
                label="充值单号1"
                v-if="activeName == 1"
              >
                <template #default="{ row }">
                  <el-link>
                    <router-link :to="`/b/pay_detail/${row.id}|${row.type}`">
                      {{ row["pa_num"] ? row["pa_num"] : "暂无" }}
                    </router-link>
                  </el-link>
                </template>
              </el-table-column>
              <el-table-column
                align="center"
                v-if="activeName == 2"
                label="支付单号"
              >
                <template #default="{ row }">
                  <el-link>
                    <router-link
                      :to="`/b/payment_detail/${row.id}|${row.type}`"
                    >
                      {{ row["pa_num"] ? row["pa_num"] : "暂无" }}
                    </router-link>
                  </el-link>
                </template>
              </el-table-column>
              <el-table-column align="center" label="交易时间">
                <template #default="{ row }">
                  {{ alterTime(row["addTime"]) }}
                </template>
              </el-table-column>
              <!--              <el-table-column-->
              <!--                align="center"-->
              <!--                label="关联订单">-->
              <!--                <template #default="{ row }">-->
              <!--                  <el-link v-if="row.orderNum">-->
              <!--                    <router-link :to="`/b/order_detail/${row.orderId}`">-->
              <!--                      {{ row['orderNum'] }}-->
              <!--                    </router-link>-->
              <!--                  </el-link>-->
              <!--                  <span v-else>暂无</span>-->
              <!--                </template>-->
              <!--              </el-table-column>-->
              <el-table-column align="center" label="交易金额">
                <template #default="{ row }">
                  {{ row.money ? row.money.toFixed(2) : "0.00" }}
                </template>
              </el-table-column>
              <el-table-column align="center" label="交易方式">
                <template #default="{ row }">
                  {{
                    payWayList[row.pay_way] ? payWayList[row.pay_way] : "暂无"
                  }}
                </template>
              </el-table-column>
              <el-table-column align="center" label="操作类型">
                <template #default="{ row }">
                  {{
                    row.orderType != 1
                      ? handleList[row.orderType]
                      : row.pay_way == 7
                      ? "赠送"
                      : "充值"
                  }}
                </template>
              </el-table-column>
              <el-table-column align="center" label="回执单">
                <template #default="{ row }">
                  <el-image
                    class="hzd"
                    :src="row.hzdPath"
                    :preview-src-list="[row.hzdPath]"
                  >
                    <template #error class="err-text"> 暂无 </template>
                  </el-image>
                </template>
              </el-table-column>
              <el-table-column align="center" label="状态" min-width="140">
                <template #default="{ row }">
                  <div>{{ row.applyStatus }}</div>
                  <div
                    v-if="row.payStatusRaw == 1 && row.remainingSeconds > 0"
                    class="pending-close-tip"
                  >
                    {{ formatPendingCountdown(row.remainingSeconds) }} 后自动关闭
                  </div>
                </template>
              </el-table-column>
              <el-table-column align="center" label="操作" width="100">
                <template #default="{ row }">
                  <el-button
                    v-if="row.canContinuePay"
                    type="primary"
                    link
                    @click="continueRechargePay(row)"
                  >
                    继续支付
                  </el-button>
                </template>
              </el-table-column>
              <el-table-column align="center" label="类型" prop="ptype">
              </el-table-column>
              <el-table-column align="center" label="驳回原因">
                <template #default="{ row }">
                  <el-tooltip
                    v-if="row.mark"
                    effect="dark"
                    :content="row.mark"
                    placement="top-start"
                  >
                    <span>{{ row.mark }}</span>
                  </el-tooltip>
                  <span v-else>暂无</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-show="activeName >= 4">
            <div class="search">
              <el-input
                size="mini"
                v-model="searchVal"
                placeholder="请输入订单编号"
                maxlength="20"
              ></el-input>
              <el-button
                :loading="searching"
                type="primary"
                size="mini"
                @click="searchOrder"
                >检索</el-button
              >
            </div>
            <el-table
              :data="tableData"
              style="width: 100%"
              border
              stripe
              v-if="activeName == 4"
            >
              <el-table-column align="center" prop="addTime" label="关联订单">
                <template #default="{ row }">
                  <el-link v-if="row.type == 0">
                    <router-link :to="`/b/order_detail/${row.of_id}`">
                      {{ row["orderId"] }}
                    </router-link>
                  </el-link>
                  <el-link v-if="row.type == 1">
                    <router-link :to="`/b/order_detail/${row.of_id}|${row.type}`">
                      {{ row["orderId"] }}
                    </router-link>
                  </el-link>
                </template>
              </el-table-column>
              <el-table-column align="center" prop="addTime" label="申请时间">
                <template #default="{ row }">
                  {{ alterTime(row["invoice_date"]) }}
                </template>
              </el-table-column>
              <el-table-column align="center" label="发票金额">
                <template #default="{ row }">
                  {{ row["money"] ? row["money"].toFixed(2) : "0.00" }}
                </template>
              </el-table-column>
              <el-table-column align="center" label="发票类型">
                <template #default="{ row }">
                  {{ row["type"] === 1 ? "专用发票" : "普通发票" }}
<!--                  {{ row["invoice_type"] == 1 ? "电子普通发票" : row["invoice_type"] == 3 ? "电子增值税专票" : row["invoice_type"] == 2 ? '纸质发票' : '' }}-->
                </template>
              </el-table-column>
              <el-table-column align="center" label="发票资料">
                <template #default="{ row }">
                  <el-button
                    v-if="row.path"
                    type="text"
                    @click="checkInvoiceData(row['path'] + '/' + row['name'])"
                    >查看</el-button
                  >
                </template>
              </el-table-column>
              <!--            <el-table-column-->
              <!--              align="center"-->
              <!--              label="回款状态"-->
              <!--            >-->
              <!--              <template #default="{ row }">-->
              <!--                {{ row['is_pay']? '已回款' : '未回款' }}-->
              <!--              </template>-->
              <!--            </el-table-column>-->
              <el-table-column align="center" label="操作">
                <template #default="{ row }">
                  <el-button
                    v-if="row['status'] === 1"
                    @click="cancelInvoice(row.id)"
                    type="text"
                    >取消</el-button
                  >
                </template>
              </el-table-column>
            </el-table>
            <el-table
              :data="tableData"
              style="width: 100%"
              border
              stripe
              v-else
            >
              <el-table-column align="center" label="订单编号">
                <template #default="{ row }">
                  <el-link>
                    <router-link :to="`/b/order_detail/${row.id}`">
                      {{ row.order_id || row.orderId || "暂无" }}
                    </router-link>
                  </el-link>
                </template>
              </el-table-column>
              <el-table-column align="center" label="下单时间">
                <template #default="{ row }">
                  {{
                    alterTime(
                      row.order_time || row.orderTime || row.addTime,
                      false
                    )
                  }}
                </template>
              </el-table-column>
              <el-table-column align="center" label="下单金额">
                <template #default="{ row }">
                  {{ formatOrderMoney(row.totalPrice ?? row.total_price) }}
                </template>
              </el-table-column>
              <el-table-column align="center" label="状态">
                <template #default="{ row }">
                  {{
                    order_status_list[row.order_status ?? row.orderStatus] ||
                    row.order_statusstr ||
                    row.orderStatusstr ||
                    "—"
                  }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </main>

    <footer>
      <el-pagination
        background
        :page-sizes="[5, 10]"
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

    <el-dialog
      title="提现"
      v-model="openDialog"
      align-center
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <el-form
        class="sub-form"
        :model="subForm"
        label-width="110px"
        ref="sub-form"
        :rules="subFormRules"
        label-position="right"
      >
        <el-form-item label="提现金额：" prop="money">
          <el-input
            ref="m"
            v-model="subForm.money"
            maxlength="10"
            @change="verifyMoney"
          ></el-input>
          <el-button type="text" @click="allMoney" style="margin-left: 10px"
            >全部</el-button
          >
        </el-form-item>
        <el-form-item label="持卡人姓名：" prop="name">
          <el-input v-model="subForm.name" maxlength="11"></el-input>
        </el-form-item>
        <el-form-item label="银行卡号：" prop="card_num">
          <el-input v-model="subForm.card_num" maxlength="20"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="closeDialog" :loading="withdrawing">取 消</el-button>
        <el-button type="primary" :loading="withdrawing" @click="submitForm"
          >确 定</el-button
        >
      </div>
    </el-dialog>

    <choose-pay-way
      :is-top-up="true"
      v-model="openChooseTool"
      @selected="confirmPayWay"
    ></choose-pay-way>

    <QRcode
      @reload="onRechargeQrClosed"
      :search-flag="outTradeNo"
      v-model="openQRcode"
      :content="codeUrl"
    ></QRcode>

    <offline-pay
      @confirmSubmit="confirmSubmit"
      v-model="openOfflinePay"
      title="充值"
      :clt-account="defaultBankAccount"
      :clt-name="defaultBankName"
    ></offline-pay>
  </personal-page-shell>
</template>


<style scoped>
.el-message-box__input {
  .el-input {
    width: 100%;
  }
}

.el-dialog {
  width: 500px !important;
}

.el-input {
  width: 300px;
}
</style>

<style scoped lang="scss">
.pending-close-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #e6a23c;
  line-height: 1.4;
}
.hzd {
  line-height: 30px;
  color: #999;
  width: 30px;
  height: 30px;
  border-radius: 5px;
  vertical-align: top;
}

.search {
  margin-bottom: 15px;

  .el-input {
    width: 200px;
  }

  .el-button {
    margin-left: 10px;
  }
}

footer {
  margin-top: 20px;
}

main {
  margin-top: 50px;
}

.wrapper {
  margin-right: 100px;

  .label {
    font-size: 16px;
  }

  .el-button--text {
    font-size: 16px;
  }

  .money {
    color: var(--mainColor);
    font-weight: 600;
    line-height: 80px;

    .parse-int {
      font-size: 50px;
    }

    .parse-float {
      font-size: 37px;
    }
  }

  .sub-balance {
    margin-top: -12px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #8c8c8c;
    line-height: 1.4;
    max-width: 280px;
  }

  .sub-balance-warn {
    color: #e6a23c;
  }

  .money,
  .content {
    margin-top: 5px;
    height: 80px;
  }

  .content {
    display: flex;
    flex-direction: column;
    justify-content: center;
    font-size: 14px;

    span {
      color: #8c8c8c;
    }
  }
}

header {
  display: flex;
}

.container {
  padding: 30px;
}
</style>
