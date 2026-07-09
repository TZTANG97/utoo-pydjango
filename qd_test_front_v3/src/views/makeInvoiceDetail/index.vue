<script>
import {fetchMakeInvoiceDetailApi, downloadOrderFileApi} from '@/api/index'
import {alterTime} from "@/utils";
import {cancelInvoiceApi} from "@/api/order";

export default {
  name: 'makeInvoiceDetail',
  data() {
    return {
      id: '',
      detail: null,
      invoice_status: {
        '1': '开票中',
        '2': '退票中',
        '3': '已作废',
        '4': '已开票',
        '5': '已取消',
      },
      relevanceOrderNum: '',
      relevanceOrderId: '',
      files: []
    }
  },
  mounted() {
    const {id = ''} = this.$route.params
    this.id = id
    this.getDetail()
  },
  methods: {
    downloadOrderFileApi,
    //   取消开票
    cancelInvoice() {
      this.$confirm('确认取消开票?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        cancelInvoiceApi({
          invoiceId: this.id
        }).then(res => {
          this.$notify({
            type: res.res ? 'success' : 'error',
            title: '提示',
            message: res.resMsg
          })
          if (res.res) {
            this.getDetail()
          }
        })
      })

    },

    getDetail() {
      fetchMakeInvoiceDetailApi({id: this.id}).then(res => {
        if (res.res) {
          const payload = res.obj || res.data || {}
          this.detail = payload.obj
          this.files = payload.files || []
          const of0 = (payload.ofList || [])[0]
          if (of0) {
            this.relevanceOrderId = of0.id
            this.relevanceOrderNum = of0.order_id || ''
          }
        }
      })
    },
    alterTime
  }
}
</script>

<template>
  <div class="container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>开票详情</span>
      </div>
      <el-descriptions v-if="detail">
        <el-descriptions-item label="开票编号">
          {{ detail.invoice_num ? detail.invoice_num : '暂无' }}
        </el-descriptions-item>
        <el-descriptions-item label="关联订单">
          <el-Link>
            <router-link :to="`/b/order_detail/${relevanceOrderId}`">{{ relevanceOrderNum }}</router-link>
          </el-Link>
        </el-descriptions-item>
        <el-descriptions-item label="开票时间">{{ alterTime(detail.addTime) }}</el-descriptions-item>
        <el-descriptions-item label="开票金额">{{ detail.invoice_money ? detail.invoice_money.toFixed(2) : '0.00' }}
        </el-descriptions-item>
        <el-descriptions-item label="发票抬头">{{ detail.invoice_title }}</el-descriptions-item>
        <el-descriptions-item label="信用代码">{{ detail.credit_code }}</el-descriptions-item>
        <el-descriptions-item label="开户行名称" v-if="detail.bank_name">{{ detail.bank_name }}</el-descriptions-item>
        <el-descriptions-item label="开户行账号" v-if="detail.bank_account">{{
            detail.bank_account
          }}
        </el-descriptions-item>
        <el-descriptions-item label="注册地址" v-if="detail.reg_address">{{ detail.reg_address }}</el-descriptions-item>
        <el-descriptions-item label="注册电话" v-if="detail.reg_mobile">{{ detail.reg_mobile }}</el-descriptions-item>
        <el-descriptions-item label="发票类型">
          {{ detail["invoice_type"] == 1 ? "电子普通发票" : detail["invoice_type"] == 3 ? "电子增值税专票" : row["invoice_type"] == 2 ? '纸质发票' : '' }}
        </el-descriptions-item>
        <!-- <el-descriptions-item label="收票方式">
          {{
            detail['invoice_type'] === 1 ? '电子发票' : '纸质发票'
          }}
        </el-descriptions-item> -->
        <el-descriptions-item label="电子邮箱" v-if="detail.invoice_type === 1">{{
            detail.email
          }}
        </el-descriptions-item>
        <el-descriptions-item label="收货地址" v-else>{{ detail.address_info }}</el-descriptions-item>
        <el-descriptions-item label="开票状态">{{ invoice_status[detail['status'] + ''] }}</el-descriptions-item>
        <el-descriptions-item label="发票资料" v-if="files.length">
          <div class="file-list">
            <div v-for="item in files" :key="item.id">
              <a :href="item.path + '/' + item.name" target="_blank" :download="item.info">{{ item.info }}</a>
              <span @click="downloadOrderFileApi(item)">下载</span>
            </div>
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
    <el-button v-if="detail && detail['status'] === 1" @click="cancelInvoice" type="primary">取&nbsp;消</el-button>

  </div>
</template>

<style scoped lang="scss">

.file-list {

  span {
    color: var(--mainColor);
    cursor: pointer;
  }

  a {
    display: block;
    color: var(--mainColor);

    &:nth-child(n+2) {
      margin-top: 5px;
    }
  }
}

.el-link {
  font-size: 15.5px;
}

.el-button {
  margin-top: 10px;
}

.container {
  padding: 20px;
}
</style>
