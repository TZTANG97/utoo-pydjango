<script>
import {getAllowBillListApi} from '@client/api/order'
import {alterTime} from '@client/utils/index'
import MakeInvoice from '@client/components/makeInvoice.vue'

export default {
  name: "Billing",
  components: {MakeInvoice},
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
      pay_time: '',
      tableData: [],
      searchVal: '',
      searching: false,
      limit: 10,
      page: 1,
      total: 0,
      dialogVisible: false,
      // 多选时选中的数据
      selected_list: [],
      ids: '',
      // dialog用来展示的可开票金额
      money: 0.00
    }
  },
  mounted() {
    this.getList()
  },
  watch: {
    // 监听dialog关闭
    dialogVisible(n) {
      if (!n) {
        this.limit = 10
        this.page = 1
        this.toggleSelection()
        this.getList()
      }
    }
  },
  methods: {
    alterTime,
    // 条数改变
    handleSizeChange(e) {
      this.limit = e
      this.toggleSelection()
      this.money = 0
      this.getList()

    },

    // 页数改变
    handleCurrentChange(e) {
      this.page = e
      // 清空多选
      this.toggleSelection()
      // 清空已累计金额
      this.money = 0
      this.getList()
    },

    // 多选
    handleSelectionChange(selected_list) {
      this.selected_list = selected_list
    },

    //  搜索
    searchOrder() {
      this.limit = 10
      this.page = 1
      // 清空多选
      this.toggleSelection()
      this.getList()
    },

    //   开票
    billing(type = 1, info = '') {
      this.ids = ''

      if (type === 1) {
        this.ids = info['id'] + ''
        this.money = info['money']
      } else {
        if (!this.selected_list.length) {
          return this.$notify.warning({
            title: '提示',
            message: '至少选择一个订单'
          })
        }

        let m = 0

        let id_list = []

        this.selected_list.forEach(item => {
          id_list.push(item['id'] + '')
          m += item['money'] - 0
        })
        this.money = m
        this.ids = id_list.join()
      }
      this.dialogVisible = true
    },

    //   获取列表
    getList() {
      this.searching = true
      getAllowBillListApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        orderId: this.searchVal,
        startTime: this.pay_time ? this.alterTime(+new Date(this.pay_time[0])) : '',
        endTime: this.pay_time ? this.alterTime(+new Date(this.pay_time[1])) : ''
      }).then(res => {
        if (res.res) {
          this.tableData = res.obj.data || []
          this.total = res.obj.recordsTotal || 0
        } else {
          this.$notify.error({
            title: '提示',
            message: res.error
          })
        }
      }).finally(_ => {
        this.searching = false
      })
    },

    // 清空Table选中
    toggleSelection() {
      this.$refs.multipleTable.clearSelection();
    },
  }
}
</script>

<template>
  <div class="container">
    <make-invoice v-model:dialog-visible="dialogVisible" :money="money" :ids="ids" :order-type="1"/>
    <header>
      <div class="search">
        <el-input size="mini" v-model="searchVal" placeholder="请输入订单编号" maxlength="20"></el-input>
        <el-date-picker
          size="mini"
          v-model="pay_time"
          type="datetimerange"
          :picker-options="pickerOptions"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          align="right">
        </el-date-picker>
        <el-button :loading="searching" type="primary" size="mini" @click="searchOrder">检索</el-button>
        <el-button :loading="searching" type="primary" size="mini" @click="billing(2)">批量开票</el-button>
      </div>
    </header>

    <main>
      <el-table
        :data="tableData"
        style="width: 100%"
        border
        stripe
        ref="multipleTable"
        @selection-change="handleSelectionChange"
      >
        <el-table-column
          type="selection"
          width="55"
          align="center"
        >
        </el-table-column>
        <el-table-column
          align="center"
          label="关联订单"
        >
          <template #default="{ row }">
            <el-link>
              <router-link :to="`/b/order_detail/${row.of_id}`">
                {{ row['order_id'] }}
              </router-link>
            </el-link>
          </template>
        </el-table-column>
        <el-table-column
          align="center"
          label="可开票金额"
        >
          <template #default="{ row }">
            {{ row['money'] ? row['money'].toFixed(2) : '0.00' }}
          </template>
        </el-table-column>
        <el-table-column
          align="center"
          label="支付时间"
        >
          <template #default="{ row }">
            {{ alterTime(row['addTime']) }}
          </template>
        </el-table-column>
        <el-table-column align="center" label="操作">
          <template #default="{ row }">
            <el-button @click="billing(1, row)" type="text">开票</el-button>
          </template>
        </el-table-column>
      </el-table>
    </main>


    <footer>
      <el-pagination
        background
        :page-sizes="[10, 20, 30]"
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

.money {
  font-size: 34px;
  font-weight: bold;
  color: var(--mainColor);
  margin-right: 4px;
}

header {
  .el-input {
    width: 200px;
  }

  .el-button, .el-date-editor {
    margin-left: 20px;
  }
}

footer {
  margin-top: 20px;
}

main {
  margin-top: 50px;
}

.container {
  padding: 20px;
}
</style>
