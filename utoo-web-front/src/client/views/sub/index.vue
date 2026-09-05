<script>
import {getUserSUbListApi} from '@client/api/user'
import {alterTime} from "@client/utils";
import {cancelConsultApi} from "@client/api";
import PersonalPageShell from "@client/components/personal/PersonalPageShell.vue";
export default {
  name: "Sub",
  components: { PersonalPageShell },
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
      tableData: [],
      page: 1,
      limit: 10,
      total: 0,
      loading: false,
      date: '',
      status_list: [
        {
        type: 'warning',
        val: '待回复'
      },
        {
          type: 'success',
          val: '已回复'
        },
        {
          type: 'success',
          val: '已生成订单'
        }, {
          type: 'info',
          val: '已取消'
        }],
      checked: false
    }
  },
  mounted() {
    this.getSubList()
  },
  methods: {
    alterTime,
    // 条数改变
    handleSizeChange(e) {
      this.limit = e
      this.getSubList()
    }
    ,

    // 页数改变
    handleCurrentChange(e) {
      this.page = e
      this.getSubList()
    },

    // 获取预约列表
    getSubList() {
      this.loading = true
      getUserSUbListApi({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
        startime: this.date ? this.alterTime(+new Date(this.date[0])) : '',
        endtime: this.date ? this.alterTime(+new Date(this.date[1])) : ''
      }).then(res => {
        if (res.res) {
          const payload = res.obj || res.data || {}
          this.tableData = payload.data || []
          this.total = payload.recordsTotal || 0
        } else {
          this.$notify.error({
            title: '提示',
            message: res.resMsg
          })
        }
      }).finally(_ => {
        this.loading = false
      })
    },

    // 搜索
    search() {
      this.limit = 10
      this.page = 1
      this.getSubList()
    },


    // 查看预约单详情
    viewDetail(id) {
      this.$router.push(`/b/sub_detail?id=${id}`)
    },

    // 取消预约
    cancelSub(id) {
      this.$confirm('确认取消预约?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        cancelConsultApi(id).then(res => {
          this.$notify({
            type: res.res ? 'success' : 'warning',
            title: '提示',
            message: res.resMsg
          })
          if (res.res) {
            this.getSubList()
          }
        })
      })
    },
  },
}
</script>

<template>
  <personal-page-shell
    title="我的预约"
    subtitle="查看检测预约申请记录与处理进度"
    icon="sub"
    :loading="loading"
  >
    <template #toolbar>
      <el-date-picker
        v-model="date"
        type="datetimerange"
        :picker-options="pickerOptions"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        class="pc-date-range"
      />
      <el-button :loading="loading" type="primary" @click="search">检索</el-button>
    </template>

    <el-table
        :data="tableData"
        style="width: 100%"
        border
        stripe
      >
        <el-table-column
          align="center"
          prop="addTime"
          label="申请时间"
        >
          <template #default="{ row }">
            {{ alterTime(row['addTime']) }}
          </template>
        </el-table-column>
        <el-table-column
          align="center"
          prop="testName"
          label="预约内容"
        />
        <el-table-column
          align="center"
          label="备注"
        >
          <template #default="{ row }">
            {{ row['content'] ? row['content'].slice(0, 30) + '...' : '暂无' }}
          </template>
        </el-table-column>
        <el-table-column
          align="center"
          prop="status"
          label="预约状态"
        >
          <template #default="{ row }">
            <el-tag :type="status_list[row['status']]['type']">{{ status_list[row['status']]['val'] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column align="center" label="操作">
          <template #default="{ row }">
            <el-button type="text" @click="viewDetail(row.id)">查看详情</el-button>
            <el-button type="text" v-if="row['is_cancel']" @click="cancelSub(row.id)">取&nbsp;消</el-button>
          </template>
        </el-table-column>
      </el-table>
    <footer class="pc-page-footer">
      <el-pagination
        background
        :page-sizes="[10, 20, 30,  50]"
        :page-size="limit"
        :current-page="page"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        layout="total, prev, pager, next, sizes"
        :total="total"
        :disabled="loading"
      />
    </footer>
  </personal-page-shell>
</template>

<style scoped lang="scss">
main, footer {
  margin-top: 20px;
}

header {
  .el-input {
    width: 200px;
  }

  .el-button {
    margin-left: 10px;
  }
}

.container {
  padding: 20px;
}
</style>
