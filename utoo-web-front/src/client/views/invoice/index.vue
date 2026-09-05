<script>
import { getInvoiceListApi, cancelInvoiceApi } from "@client/api/order";
import { getUserInvoiceInfoApi } from "@client/api/user";
import { alterTime } from "@client/utils";
import { fetchInvoiceDetailListApi } from "@client/api";
import PersonalPageShell from "@client/components/personal/PersonalPageShell.vue";

export default {
  name: "Invoice",
  components: { PersonalPageShell },
  data() {
    return {
      tableList: [],
      activeName: "1",
      // '专用发票',
      tabsList: ["申请记录", "明细记录"],
      page: 1,
      limit: 5,
      total: 0,
      // 申请记录
      tableData: [],
      // 明细记录
      tableData2: [],
      searchVal: "",
      searching: false,
      invoice_money: "0.00",
      invoice_status: {
        1: "开票中",
        2: "退票中",
        3: "已作废",
        4: "已开票",
        5: "已取消",
      },
      invoice_info: "",
      listRequestId: 0,
    };
  },
  mounted() {
    this.getInvoiceList();
    this.getUserInvoiceInfo();
  },
  methods: {
    // 获取明细记录
    getDetailList() {
      const reqId = ++this.listRequestId;
      this.searching = true;
      fetchInvoiceDetailListApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        orderId: this.searchVal,
        length: this.limit,
        type: 2,
      })
        .then((res) => {
          if (reqId !== this.listRequestId) return;
          if (res.res) {
            const payload = res.obj || res.data || {};
            this.tableData2 = payload.data || [];
            this.total = payload.recordsTotal || 0;
          } else {
            this.$notify.error({
              title: "提示",
              message: res.resMsg,
            });
          }
        })
        .finally((_) => {
          if (reqId !== this.listRequestId) return;
          this.searching = false;
        });
    },

    // 千分位
    format_with_Intl(num = 0) {
      let str = parseFloat(num).toFixed(2);
      let parts = str.split(".");
      let integerPart = parts[0];
      integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      return `${integerPart}.${parts[1]}`;
    },

    // 获取默认的发票信息
    getUserInvoiceInfo() {
      getUserInvoiceInfoApi().then((res) => {
        if (res.res) {
          this.invoice_info = res.obj;
        }
      });
    },

    handleTabChange(name) {
      this.activeName = String(name ?? this.activeName);
      this.page = 1;
      this.searchVal = "";
      if (this.activeName === "1") {
        this.getInvoiceList();
      } else {
        this.getDetailList();
      }
    },

    //   跳转个人中心「发票信息」并打开新增发票弹窗（与旧版 params.active=2 + invoiceDialog 一致）
    viewInvoiceInfo() {
      this.$router.push({
        path: "/b/profile",
        query: { active: "2", openInvoice: "1" },
      });
    },

    // 条数改变
    handleSizeChange(e) {
      this.limit = e;
      if (this.activeName == 1) {
        this.getInvoiceList();
      } else {
        this.getDetailList();
      }
    },

    // 页数改变
    handleCurrentChange(e) {
      this.page = e;
      if (this.activeName == 1) {
        this.getInvoiceList();
      } else {
        this.getDetailList();
      }
    },

    alterTime,

    //   获取发票列表
    getInvoiceList() {
      const reqId = ++this.listRequestId;
      this.searching = true;
      getInvoiceListApi({
        start: (this.page - 1) * this.limit,
        length: this.limit,
        orderId: this.searchVal,
        draw: 1,
        //   1专票 2普票
        // 因为删除了专用发票，所以需要加1
        type: 2,
      })
        .then((res) => {
          if (reqId !== this.listRequestId) return;
          if (res.res) {
            const payload = res.obj || res.data || {};
            const table = payload.data || {};
            this.tableData = table.data || [];
            this.total = table.recordsTotal || 0;
            this.invoice_money = Number(payload.stayApplyMoney || 0).toFixed(2);
          } else {
            this.$notify.error({
              title: "提示",
              message: res.resMsg,
            });
          }
        })
        .finally((_) => {
          if (reqId !== this.listRequestId) return;
          this.searching = false;
        });
    },

    //   搜索订单
    searchOrder() {
      this.page = 1;
      if (this.activeName == 1) {
        this.getInvoiceList();
      } else {
        this.getDetailList();
      }
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

    checkInvoiceData(url) {
      window.open(url);
    },
  },
};
</script>

<template>
  <personal-page-shell
    title="发票管理"
    subtitle="管理开票信息、申请记录与发票明细"
    icon="invoice"
  >
    <header class="pc-stat-row invoice-summary">
      <div class="wrapper">
        <div class="label">可索取发票金额</div>
        <div class="money">
          <span class="parse-int">{{
            format_with_Intl(invoice_money).split(".")[0]
          }}</span>
          <span class="parse-float"
            >.{{ format_with_Intl(invoice_money).split(".")[1] }}</span
          >
        </div>
        <el-button type="text" @click="$router.push('/b/billing')"
          >我要开票</el-button
        >
      </div>
      <div class="wrapper">
        <div class="label">发票信息</div>
        <div class="content">
          <span v-if="invoice_info"
            >发票抬头： {{ invoice_info["invoice_title"] }}</span
          >
          <br />
          <span v-if="invoice_info"
            >企业税号： {{ invoice_info["taxNum"] }}</span
          >
        </div>
        <el-button type="text" @click="viewInvoiceInfo">添加开票信息</el-button>
      </div>
    </header>

    <el-tabs v-model="activeName" @tab-change="handleTabChange">
        <el-tab-pane
          v-for="(item, idx) in tabsList"
          :key="idx"
          :name="idx + 1 + ''"
          :label="item"
        >
          <div class="search">
            <el-input
              size="mini"
              v-model="searchVal"
              placeholder="请输入订单编号"
              maxlength="40"
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
            v-show="activeName == 1"
            :data="tableData"
            style="width: 100%"
            border
            stripe
          >
            <el-table-column align="center" prop="addTime" label="开票编号">
              <template #default="{ row }">
                <el-link>
                  <router-link :to="`/b/make_invoice_detail/${row.id}`">
                    {{ row["invoice_num"] }}
                    <!--                    {{ row['invoice_num']? row['invoice_num'] : '暂无' }}-->
                  </router-link>
                </el-link>
              </template>
            </el-table-column>
            <el-table-column align="center" prop="addTime" label="关联订单">
              <template #default="{ row }">
                <el-link>
                  <router-link :to="`/b/order_detail/${row.ofid}`">
                    {{ row["order_id"] }}
                  </router-link>
                </el-link>
              </template>
            </el-table-column>
            <el-table-column align="center" prop="addTime" label="开票时间">
              <template #default="{ row }">
                {{ alterTime(row["addTime"]) }}
              </template>
            </el-table-column>
            <el-table-column
              align="center"
              prop="invoice_title"
              label="发票抬头"
            />
            <el-table-column align="center" label="发票金额">
              <template #default="{ row }">
                {{
                  row["invoice_money"]
                    ? row["invoice_money"].toFixed(2)
                    : "0.00"
                }}
              </template>
            </el-table-column>
            <el-table-column align="center" label="发票类型">
              <template #default="{ row }">
                {{ row["type"] === 1 ? "专用发票" : "普通发票" }}
<!--                {{ row["invoice_type"] == 1 ? "电子普通发票" : row["invoice_type"] == 3 ? "电子增值税专票" : row["invoice_type"] == 2 ? '纸质发票' : '' }}-->
              </template>
            </el-table-column>
            <el-table-column align="center" prop="status" label="发票状态">
              <template #default="{ row }">
                {{ invoice_status[row["status"] + ""] }}
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
            v-show="activeName == 2"
            :data="tableData2"
            style="width: 100%"
            border
            stripe
          >
            <el-table-column align="center" prop="addTime" label="关联订单">
              <template #default="{ row }">
                <!-- <el-link>
                  <router-link :to="`/b/order_detail/${row.of_id}`">
                    {{ row['orderId'] }}
                  </router-link>
                </el-link> -->
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
            <el-table-column align="center" prop="addTime" label="开票时间">
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
<!--                {{ row["invoice_type"] == 1 ? "电子普通发票" : row["invoice_type"] == 3 ? "电子增值税专票" : row["invoice_type"] == 2 ? '纸质发票' : '' }}-->
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
          </el-table>
        </el-tab-pane>
      </el-tabs>
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
  </personal-page-shell>
</template>

<style scoped lang="scss">
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

header {
  display: flex;
}

.container {
  padding: 30px;
}
</style>
