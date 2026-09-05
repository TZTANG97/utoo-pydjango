<script>
import { fetchAccountDetailApi } from '@client/api/index'
import {alterTime} from '@client/utils/index'
export default {
  name: "payHistory",
  data() {
    return {
      pickerOptions: {
        shortcuts: [{
          text: '最近一周',
          onClick(picker) {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
            picker.$emit('pick', [start, end]);
          }
        }, {
          text: '最近一个月',
          onClick(picker) {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
            picker.$emit('pick', [start, end]);
          }
        }, {
          text: '最近三个月',
          onClick(picker) {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
            picker.$emit('pick', [start, end]);
          }
        }]
      },
      total: 0,
      page: 1,
      limit: 10,
      pay_time: '',
      searching: false,
      tableData: [],
      type: '',
      payWayList: {
        1: "支付宝",
        2: "微信",
        3: "线下支付",
        4: '余额支付',
        5: '线下充值',
        6: '会员余额收款',
        7: '线下充值'
      },
      handleList: {
        1: '充值',
        2: '支付',
        3: '订单缴费',
        4: '提现',
      },
      applyStatusList: {
        1: '审核中',
        2: '审核通过',
        3: '审核拒绝',
      }
    }
  },
  mounted() {
    this.getList()
  },
  methods: {

    alterTime,

    // 条数改变
    handleSizeChange(e) {
      this.limit = e
      this.getList()
    },

    // 页数改变
    handleCurrentChange(e) {
      this.page = e
      this.getList()
    },

    searchOrder() {
      this.page = 1
      this.getList()
    },


    // 获取流水列表
    getList() {
      this.searching = true
      fetchAccountDetailApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        startTime: this.pay_time ? this.alterTime(+new Date(this.pay_time[0])) : '',
        endTime: this.pay_time ? this.alterTime(+new Date(this.pay_time[1])) : '',
        // 1充值2提现
        type: this.type
      }).then(res => {
        if(res.res) {
          const { obj: {data, recordsTotal} } = res
          this.tableData = data
          this.total = recordsTotal
        } else {
          this.$notify.error(res.errMsg? res.errMsg : '获取失败')
        }
      }).finally(_ => {
        this.searching = false
      })
    },
  }
}
</script>

<template>
  <div class="container">
    <div class="search">
      <el-select v-model="type" placeholder="请选择交易类型" size="mini" clearable>
        <el-option
          label="充值"
          :value="1">
        </el-option>
        <el-option
          label="支付"
          :value="2">
        </el-option>
        <el-option
          label="订单缴费"
          :value="3">
        </el-option>
        <el-option
          label="提现"
          :value="4">
        </el-option>
      </el-select>
      <el-date-picker
        size="mini"
        style="margin-left: 10px"
        v-model="pay_time"
        type="datetimerange"
        :picker-options="pickerOptions"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        align="right">
      </el-date-picker>
      <el-button :loading="searching" type="primary" size="mini" @click="searchOrder">检索</el-button>
    </div>
    <el-table
      :data="tableData"
      style="width: 100%"
      border
      stripe
    >
      <el-table-column
        align="center"
        label="交易时间"
      >
        <template #default="{ row }">
          {{ alterTime(row['addTime']) }}
        </template>
      </el-table-column>
      <el-table-column
        align="center"
        label="关联订单">
        <template #default="{ row }">
          <el-link v-if="row.orderNum">
            <router-link :to="`/b/order_detail/${row.orderId}`">
              {{ row['orderNum'] }}
            </router-link>
          </el-link>
          <span v-else>暂无</span>
        </template>
      </el-table-column>
      <el-table-column
        align="center"
        label="交易金额">
        <template #default="{ row }">
          {{ row.money?  row.money.toFixed(2) : '0.00'}}
        </template>
      </el-table-column>
      <el-table-column
        align="center"
        label="交易方式">
        <template #default="{ row }">
          {{ payWayList[row.pay_way]? payWayList[row.pay_way] : '暂无'}}
        </template>
      </el-table-column>
      <el-table-column
        align="center"
        label="操作类型">
        <template #default="{ row }">
          {{ handleList[row.orderType - 0] }}
        </template>
      </el-table-column>
      <el-table-column
        align="center"
        label="付款回执单">
        <template #default="{ row }">
          <el-image
            class="hzd"
            :src="row.hzdPath"
            :preview-src-list="[row.hzdPath]">
            <template #error class="err-text">
              暂无
            </template>
          </el-image>
        </template>
      </el-table-column>
      <el-table-column
        align="center"
        label="状态">
        <template #default="{ row }">
          {{ applyStatusList[row.applyStatus - 0] }}
        </template>
      </el-table-column>
      <el-table-column
        align="center"
        label="驳回原因">
        <template #default="{ row }">
          <el-tooltip v-if="row.mark" effect="dark" :content="row.mark" placement="top-start">
            <span>{{ row.mark }}</span>
          </el-tooltip>
          <span v-else>暂无</span>
        </template>
      </el-table-column>
    </el-table>
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
  </div>
</template>

<style scoped lang="scss">

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

.container {
  padding: 30px;
}
</style>
