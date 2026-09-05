<script>
import {
  getIntegralListApi,
  getIntegralApi,
  getIntegralConvertRatio,
  userredeemloglist,
} from "@client/api/integral";
import { alterTime } from "@client/utils/index";
import PersonalPageShell from "@client/components/personal/PersonalPageShell.vue";

export default {
  name: "Integral",
  components: { PersonalPageShell },
  data() {
    return {
      activeName: "1",
      statusList: ["全部", "已获取", "已消耗"],
      statusIndex: 0,
      tableData: [],
      integral: null,
      dialogVisible: false,
      page: 1,
      total: 0,
      limit: 10,
      searching: false,
      flag: 1,
      money: 1.5,
      // 默认与中台一致，接口返回后再覆盖
      integral_convert_ratio: 2,
      listRequestId: 0,
    };
  },
  // async beforeUpdate() {

  // },
  mounted() {
    this.getIntegralList();
    this.getIntegral();
    this.$store.dispatch("user/getIntegralConvertRatio").then(() => {
      const ratio = Number(this.$store.getters.IntegralConvertRatio);
      this.integral_convert_ratio =
        Number.isFinite(ratio) && ratio > 0 ? ratio : 2;
    });
  },
  methods: {
    alterTime,

    // 获取积分列表
    getIntegralList() {
      const reqId = ++this.listRequestId;
      getIntegralListApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        type: this.statusIndex,
      }).then((res) => {
        if (reqId !== this.listRequestId) return;
        if (res.res) {
          const {
            obj: { recordsTotal, data },
          } = res;
          this.total = recordsTotal;
          this.tableData = data;
        } else {
          this.$notify.error({
            title: "提示",
            message: res.resMsg,
          });
        }
      });
    },
    // 获取兑换列表
    userredeemloglistFn() {
      const reqId = ++this.listRequestId;
      userredeemloglist({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        type: this.statusIndex,
      }).then((res) => {
        if (reqId !== this.listRequestId) return;
        if (res.res) {
          const {
            obj: { recordsTotal, data },
          } = res;
          this.total = recordsTotal;
          // 后端多为 camelCase，表格字段为 snake_case，统一映射
          this.tableData = (data || []).map((row) => ({
            ...row,
            order_id: row.order_id ?? row.orderId ?? "",
            user_name: row.user_name ?? row.trueName ?? row.userName ?? "",
            mobile: row.mobile ?? "",
            redeem_time: row.redeem_time ?? row.redeemTime,
            redeem_num: row.redeem_num ?? row.redeemNum,
            fhstatus: row.fhstatus ?? row.fhStatus ?? row.status,
          }));
        } else {
          this.$notify.error({
            title: "提示",
            message: res.resMsg,
          });
        }
      });
    },

    // 切换 tabs（须用 tab-change，避免 activeName 未更新时误拉列表）
    handleTabChange(name) {
      this.activeName = String(name ?? this.activeName);
      this.page = 1;
      this.tableData = [];
      this.total = 0;
      if (this.activeName === "1") {
        this.getIntegralList();
      } else {
        this.userredeemloglistFn();
      }
    },

    // 获取积分
    getIntegral() {
      getIntegralApi().then((res) => {
        if (res.res) {
          res.obj["expireIntegral"] = res.obj["expireIntegral"];
          res.obj["totalIntegral"] = res.obj["totalIntegral"];
          this.integral = res.obj;
        } else {
          this.$notify.error({
            title: "提示",
            message: res.resMsg,
          });
        }
      });
    },

    handleSizeChange(e) {
      this.limit = e;
      if (this.activeName == 1) {
        this.getIntegralList();
      } else {
        this.userredeemloglistFn();
      }
    },

    handleCurrentChange(e) {
      this.page = e;
      if (this.activeName == 1) {
        this.getIntegralList();
      } else {
        this.userredeemloglistFn();
      }
    },

    changeType(idx) {
      this.statusIndex = idx;
      this.page = 1;
      if (this.activeName == 1) {
        this.getIntegralList();
      } else {
        this.userredeemloglistFn();
      }
    },
  },
};
</script>

<template>
  <personal-page-shell
    title="我的积分"
    subtitle="查看积分余额、收支明细与兑换记录"
    icon="integral"
  >
    <header v-if="integral" class="pc-stat-row">
      <div class="my-integral">
        <span class="integer">{{ integral["totalIntegral"] }}</span>
        <div class="inter-label">
          我的积分
          <svg-icon
            icon-class="doubt"
            class-name="doubt"
            @click="(dialogVisible = true), (flag = 1)"
          ></svg-icon>
        </div>
      </div>
      <div class="expiring-soon">
        <span class="integer">{{ integral["expireIntegral"] }}</span>
        <div class="inter-label">
          即将过期积分
          <svg-icon
            icon-class="doubt"
            class-name="doubt"
            @click="(dialogVisible = true), (flag = 2)"
          ></svg-icon>
        </div>
      </div>
    </header>

    <el-tabs v-model="activeName" @tab-change="handleTabChange">
        <el-tab-pane label="积分收支明细" name="1">
          <div class="status-list">
            <div
              class="btn-status"
              v-for="(item, idx) in statusList"
              :key="idx"
              :class="{ 'status-active': idx === statusIndex }"
              @click="changeType(idx)"
            >
              <span>{{ item }}</span>
            </div>
          </div>
          <el-table :data="tableData" class="table">
            <el-table-column label="关联编号" align="center">
              <template #default="{ row: { orderNum, orderId, type } }">
                <router-link
                  :to="`/b/order_detail2/${orderId}`"
                  v-if="type == 2"
                >
                  <span class="order-num">{{ orderNum }}</span>
                </router-link>
                <router-link
                  :to="`/b/order_detail/${orderId}`"
                  v-else-if="type != 4 && type != 2"
                >
                  <span class="order-num">{{ orderNum }}</span>
                </router-link>
                <span v-else>签到获取积分</span>
              </template>
            </el-table-column>
            <el-table-column label="时间" align="center">
              <template #default="{ row: { addTime } }">
                {{ alterTime(addTime) }}
              </template>
            </el-table-column>
            <el-table-column label="积分收支类型" align="center">
              <template #default="{ row: { type } }">
                {{
                  type == 1
                    ? "订单完成增加"
                    : type == 2
                    ? "兑换支出"
                    : type == 3
                    ? "积分支出"
                    : type == 4
                    ? "签到"
                    : ""
                }}
              </template>
            </el-table-column>
            <!-- <el-table-column label="积分收支状态" align="center">
              <template #default="{ row: { type, } }">
                <span :style="{color:type == 1 || type == 4 ? 'green' : type == 2 || type == 3 ? 'red' : '#000'}">{{ type == 1 || type == 4 ? "已获取" : type == 2 || type == 3 ? "已支出" : ''}}</span>
              </template>
            </el-table-column> -->
            <el-table-column label="积分" align="center">
              <template #default="{ row: { type, integral } }">
                {{ type == 1 ? "+" : "" }}{{ integral }}
              </template>
            </el-table-column>
            <!--            <el-table-column label="状态">-->
            <!--            </el-table-column>-->
            <!--            <el-table-column label="操作">-->
            <!--            </el-table-column>-->
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="积分兑换记录" name="2">
          <el-table :data="tableData" class="table">
            <el-table-column label="关联编号" align="center">
              <template #default="{ row: { id, type,order_id } }">
                <router-link :to="`/b/order_detail2/${id}`">
                  <span class="order-num">{{ order_id }}</span>
                </router-link>
              </template>
            </el-table-column>
            <el-table-column label="用户名" prop="user_name"> </el-table-column>
            <el-table-column label="手机号" prop="mobile"> </el-table-column>
            <el-table-column label="兑换时间" prop="redeem_time">
              <template #default="{ row }">
                {{
                  row.redeem_time || row.redeemTime
                    ? alterTime(row.redeem_time || row.redeemTime)
                    : "-"
                }}
              </template>
            </el-table-column>
            <el-table-column label="商品名称" prop="goodName"> </el-table-column>
            <el-table-column label="商品数量" prop="redeem_num"> </el-table-column>
            <el-table-column label="消费积分" prop="integralsum">
              <template #default="{ row: { type, integralsum } }">
                {{ type == 1 ? "+" : "" }}{{ integralsum }}
              </template>
            </el-table-column>
            <el-table-column label="发货状态" prop="fhstatus">
              <template #default="{ row: { fhstatus } }">
                {{ fhstatus == 1 ? '待发货' : fhstatus == 2 ? '已发货' : '' }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>

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

    <el-dialog title="积分规则" v-model="dialogVisible" width="30%">
      <span v-if="flag === 1">
        1. 消费 1 元获得 1 积分，100 积分可抵扣
        {{ integral_convert_ratio }} 元，积分可累积使用
        <br />
        2. 网页/小程序预约下单时可自主选择是否使用积分抵扣
        <br />
        3. 仅限微信支付、余额支付两种支付方式使用积分抵扣
      </span>
      <span v-else>
        1. 积分有效期为获得之日起的一年内，请及时使用您的积分
        <br />
        2. 若您有即将到期的积分，会在到期 30 日前于此处显示
      </span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="dialogVisible = false"
            >确 定</el-button
          >
        </span>
      </template>
    </el-dialog>
  </personal-page-shell>
</template>

<style scoped lang="scss">
br {
  margin: 10px 0;
}

.order-num:hover {
  color: var(--mainColor);
  border-bottom: 1px solid var(--mainColor);
}

.doubt {
  cursor: pointer;
}

.table {
  margin-top: 30px;
}

.status-active {
  color: #fff !important;
  background-color: var(--mainColor);
  border: 1px solid var(--mainColor) !important;
}

footer {
  margin-top: 20px;
}

main {
  margin-top: 50px;

  .status-list {
    display: flex;

    .btn-status {
      padding: 5px 15px;
      border: 1px solid #dbdbdb;
      font-size: 14px;
      color: rgba(0, 0, 0, 0.65);
      box-sizing: border-box;
      cursor: pointer;
      transition: all 0.3s;

      &:nth-child(n + 2) {
        margin-left: 30px;
      }
    }
  }
}

header {
  display: flex;

  span {
    color: var(--mainColor);
    font-weight: 600;
    font-size: 37px;
  }

  .integer {
    font-size: 50px;
  }

  .inter-label {
    color: rgba(0, 0, 0, 0.45);
    font-size: 14px;
    margin-top: 10px;
  }

  .expiring-soon {
    margin-left: 100px;
  }
}

.container {
  padding: 30px;
}
</style>
