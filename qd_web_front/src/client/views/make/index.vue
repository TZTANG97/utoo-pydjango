<script>
import VueQr from 'vue-qr'
import {getPDFInfoApi} from "@client/api";
import {alterTime} from "@client/utils";

export default {
  name: "Make",
  components: {VueQr},
  data() {
    return {
      pdfData: null
    }
  },
  mounted() {
    const id = this.$route.params.id
    if (!id) {
      return this.$message.warning({
        title: '提示',
        message: '订单ID不能为空'
      })
    }
    getPDFInfoApi(id).then(res => {
      if (res.res) {
        let address = '',
          recovery = ''
        const {
          obj: {
            order_id,
            addTime,
            sampleDelivery,
            childList
          }
        } = res

        if(sampleDelivery) {
          address = sampleDelivery.address
          recovery = sampleDelivery.recovery
        }

        this.pdfData = {
          order_id,
          addTime,
          address,
          recovery,
          childList
        }
      } else {
        this.$notify({
          type: 'warning',
          title: '提示',
          message: res.resMsg
        })
      }
    })
  },
  methods: {
    alterTime,
    downloadPDF() {
      this.$prompt('请输入PDF名称', '下载PDF', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: this.pdfData.childList[0]['experiment_class_name'] + '-预约单'
      }).then(({value}) => {
        this.$PDFSave(this.$refs['content'], value)
      })
    },
  },
}
</script>

<template>
  <div class="container" v-if="pdfData">
    <div class="download" ref="content">
      <div class="title">{{ pdfData.childList[0].experiment_project_name }}-预约单</div>
      <div class="qrcode">
        <vue-qr :text="pdfData.order_id" qid="testid"/>
        <div class="make-id">{{ pdfData.order_id }}</div>
      </div>
      <table border="1" cellspacing="0">
        <tr>
          <td>实验项目：</td>
          <td>{{ pdfData.childList[0].experiment_project_name }}</td>
        </tr>
        <tr>
          <td class="k">订单编号：</td>
          <td class="v">{{ pdfData.order_id }}</td>
        </tr>
        <tr>
          <td class="k">下单时间：</td>
          <td class="v">{{ alterTime(pdfData.addTime) }}</td>
        </tr>
        <tr>
          <td class="k">样品寄送地址：</td>
          <td class="v">{{ pdfData.address }}</td>
        </tr>
        <tr>
          <td class="k">是否回收样品：</td>
          <td class="v">{{ pdfData.recovery? (pdfData.recovery === 1 ? '是' : '否') : '' }}</td>
        </tr>
        <tr>
          <td colspan="2">
            <div class="child-order-list">
              <div class="child-order-item" v-for="(item, idx) in pdfData.childList" :key="idx">
                <span>样品编号：{{ item.orderId }}</span>
                <span>样品名称：{{ item.goodsName }}</span>
                <span>样品数量：{{ item.goodsNums }}</span>
                <span>实验项目：{{ item.experiment_project_name }}</span>
              </div>
            </div>
          </td>
        </tr>
      </table>
    </div>
    <el-button type="primary" @click="downloadPDF">一键导出</el-button>
  </div>
</template>

<style scoped lang="scss">
.el-button {
  display: block;
  margin: auto;
}

.child-order-list {
  padding: 20px 0;
}

.child-order-item {
  &:nth-child(n+2) {
    margin-top: 20px;
  }

  span:nth-child(n+2) {
    margin-right: 20px;
  }
}

.qrcode {
  position: absolute;
  right: 50px;
  top: 32px;
  text-align: center;

  img {
    width: 80px;
    height: 80px;
  }

  .make-id {
    font-size: 5px;
  }
}


.title {
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  margin-top: 70px;
}

table {
  margin: 70px auto;

  td {
    padding: 10px;
  }

  .k {
    width: 200px;
  }

  .v {
    width: 500px;
  }
}

.download {
  width: 800px;
  position: relative;
  overflow: hidden;
  margin: auto;
}
</style>
