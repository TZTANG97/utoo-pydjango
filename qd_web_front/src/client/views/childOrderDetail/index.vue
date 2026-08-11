<script>
import {
  getTestChildOrderDetailApi,
  submitEvaluateApi,
  againTestApi,
  confirmCompleteApi,
  getIotExperimentDataApi,
} from '@client/api/order'
import {alterTime} from '@client/utils/index'
import { downloadOrderFileApi } from '@client/api/index'

export default {
  name: 'ChildOrderDetail',
  data() {
    return {
      id: '',
      detail: null,
      logs: [],
      goodsDetail: [],
      testFiles: [],
      files: [],
      dialogVisible: false,
      form: {
        star: 5,
        evaluate_content: ''
      },
      evaluating: false,
      dialogTitle: '评价',
      productId: '',
      iotDialogVisible: false,
      iotLoading: false,
      iotData: null,
    }
  },
  computed: {
    iotSeries() {
      const series = this.iotData && this.iotData.series
      return Array.isArray(series) ? series : []
    },
    iotSummaryText() {
      if (!this.iotData) return ''
      const s = this.iotData.summary
      if (s == null) return ''
      if (typeof s === 'string') return s
      try {
        return JSON.stringify(s, null, 2)
      } catch (_) {
        return String(s)
      }
    },
  },
  mounted() {
    this.id = this.$route.params.id
    this.getDetail()
  },
  methods: {
    downloadOrderFileApi,

    alterTime,
    //   获取详情
    getDetail() {
      getTestChildOrderDetailApi({id: this.id}).then(res => {
        if (res.res) {
          this.detail = res.obj.of
          this.logs = res.obj.logs
          this.goodsDetail = res.obj.childs
          this.testFiles = []
          res.obj.childs.forEach(item => {
            this.testFiles = [...this.testFiles, ...item['testFiles']]
          })
          this.files = res.obj.files ? res.obj.files : []
        } else {
          this.$notify({
            type: 'error',
            title: '提示',
            message: res.resMsg
          })
        }
      })
    },

    openIotExperimentData(row) {
      if (!this.detail || !row || !row.id) return
      this.iotDialogVisible = true
      this.iotLoading = true
      this.iotData = null
      const orderId = this.detail.orderId || this.detail.order_id || ''
      getIotExperimentDataApi({
        orderId,
        childId: row.id,
        includeSeries: 1,
      })
        .then((res) => {
          if (res.res) {
            // 接口外层含 bind 元数据，曲线在 run 内
            const obj = res.obj || null
            this.iotData = (obj && obj.run) || obj
          } else {
            this.$notify({
              type: 'error',
              title: '提示',
              message: res.resMsg || '获取试验数据失败',
            })
          }
        })
        .catch((err) => {
          this.$notify({
            type: 'error',
            title: '提示',
            message: (err && err.message) || '获取试验数据失败',
          })
        })
        .finally(() => {
          this.iotLoading = false
        })
    },

    handleClose() {
      this.form.star = 5
      this.form.evaluate_content = ''
    },

    // 提交评价
    submitEval() {
      if (this.dialogTitle === '评价') {
        this.evaluating = true
        submitEvaluateApi({
          id: this.id,
          star: this.form.star,
          content: this.form.evaluate_content
        }).then(res => {
          this.$notify({
            type: res.res ? 'success' : 'warning',
            title: '提示',
            message: res.resMsg
          })

          if (res.res) {
            this.dialogVisible = false
            this.getDetail()
          }
        }).finally(_ => {
          this.evaluating = false
        })
      } else {
        if (!this.form.evaluate_content) return this.$notify({
          type: 'warning',
          title: '提示',
          message: '请输入备注'
        })
        this.evaluating = true
        againTestApi({
          orderId: this.productId,
          mark: this.form.evaluate_content
        }).then(res => {
          this.$notify({
            type: res.res ? 'success' : 'warning',
            title: '提示',
            message: res.resMsg
          })

          if (res.res) {
            this.dialogVisible = false
            this.getDetail()
          }
        }).finally(_ => {
          this.evaluating = false
        })
      }
    },

    // 确认完成
    confirmComplete() {
      this.$confirm('是否确认完成?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        confirmCompleteApi({
          id: this.productId
        }).then(res => {
          this.$notify({
            type: res.res ? 'success' : 'warning',
            title: '提示',
            message: res.resMsg
          })
          this.getDetail()
        })
      })
    },
  }
}
</script>

<template>
  <div class="container">
    <el-card class="box-card" v-if="detail">
      <div slot="header" class="clearfix">
        <span>子订单详情</span>
      </div>
      <div class="row">
        <div class="text item">
          <span>子订单编号：</span>
          <span>{{ detail['order_id'] }}</span>
        </div>
        <div class="text item">
          <span>来源单号：</span>
          <span>{{ detail.parentOf ? detail.parentOf.order_id : '' }}</span>
        </div>
        <div class="text item">
          <span>订单状态：</span>
          <span>{{ detail.order_statusstr }}</span>
        </div>
      </div>
      <div class="row">
        <div class="text item">
          <span>预计收货时间：</span>
          <span>{{ detail['delivery_time'] ? alterTime(detail['delivery_time']) : '' }}</span>
        </div>
        <div class="text item" v-if="detail && detail.order_type == 10">
          <span>订单类型：</span>
          <span>{{ detail['testClass']['name'] }}</span>
        </div>
        <div class="text item" v-if="testFiles.length">
          <span>测试数据：</span>
          <div class="order-data-list">
            <div v-for="(file, idx) in testFiles" :key="idx">
              <a :href="`${file.path}/${file.name}`" target="_blank" :download="`${file.info}.${file.ext}`">
                {{ file.info }}
              </a>
            </div>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="text item">
          <span>云视频：</span>
          <span>{{ detail['is_video']? '是' : '否' }}</span>
        </div>
      </div>

      <div class="row" v-if="files.length">
        <div class="text item">
          <span>订单资料：</span>
          <div class="order-data-list">
            <div v-for="(file, idx) in files" :key="idx">
              <a :href="`${file.path}/${file.name}`" target="_blank" :download="`${file.info}.${file.ext}`">
                {{ file.info }}
              </a>
              <span @click="downloadOrderFileApi(file)">下载</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    <!--    产品信息-->
    <el-table
      v-if="goodsDetail.length"
      :data="goodsDetail"
      style="width: 100%; margin-top: 20px"
      border
      stripe
    >
      <el-table-column
        align="center"
        label="客户名称"
        prop="goods_brand_name"
      />
      <el-table-column
        align="center"
        label="样品名称"
        prop="goods_name"
      />
      <el-table-column
        align="center"
        label="样品型号"
        prop="goods_spec"
      />
      <el-table-column
        align="center"
        prop="goods_nums"
        label="样品数量"
      />
      <el-table-column
        prop="experiment_project_name"
        align="center"
        label="实验项目"
      />
      <template v-if="detail && detail.order_type == 10">
        <el-table-column
          prop="experiment_class_name"
          align="center"
          label="实验分类"/>
      </template>
      <el-table-column
        align="center"
        label="状态">
        <template #default="{ row }">
          {{ row['orderStautsStr'] }}
        </template>
      </el-table-column>
      <el-table-column
        align="center"
        label="操作"
        min-width="160"
      >
        <template #default="{ row }">
          <el-button type="text" size="mini" @click="openIotExperimentData(row)">试验数据</el-button>
          <el-button type="text" v-if="row.ispcfc" size="mini" @click="dialogTitle = '复测', dialogVisible = true, productId = row.id">复测
          </el-button>
          <el-button type="text" v-if="row.ispcqr" size="mini" @click="productId = row.id, confirmComplete()">确认完成</el-button>
        </template>
      </el-table-column>
    </el-table>

<!--    <el-button v-if="detail && detail.ispjqx" class="evaluate" type="primary"-->
<!--               @click="dialogTitle = '评价', dialogVisible = true">评价-->
<!--    </el-button>-->

    <el-dialog
      :title="dialogTitle"
      :visible.sync="dialogVisible"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      @close="handleClose">
      <el-form class="sub-form" :model="form" ref="sub-form" label-position="top">
        <el-form-item label="综合评价：" prop="star" v-if="dialogTitle === '评价'">
          <el-rate v-model="form.star"></el-rate>
        </el-form-item>
        <el-form-item :label="dialogTitle === '评价'? '评价内容：' : '备注'" prop="evaluate_content">
          <el-input type="textarea" v-model="form.evaluate_content" maxlength="120"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="evaluating" @click="submitEval">确 定</el-button>
      </span>
    </el-dialog>

    <el-dialog
      title="试验数据"
      :visible.sync="iotDialogVisible"
      width="720px"
      :close-on-click-modal="false"
    >
      <div v-loading="iotLoading">
        <template v-if="iotData">
          <div class="iot-block">
            <div class="iot-label">摘要</div>
            <pre class="iot-summary">{{ iotSummaryText || '-' }}</pre>
          </div>
          <div class="iot-block">
            <div class="iot-label">序列点数</div>
            <span>{{ iotSeries.length }}</span>
          </div>
          <div class="iot-block" v-if="iotData.reportUrl">
            <div class="iot-label">报告</div>
            <a :href="iotData.reportUrl" target="_blank" rel="noopener">{{ iotData.reportUrl }}</a>
          </div>
          <el-table
            v-if="iotSeries.length"
            :data="iotSeries.slice(0, 50)"
            border
            stripe
            max-height="320"
            style="width: 100%; margin-top: 12px"
          >
            <el-table-column
              v-for="col in Object.keys(iotSeries[0] || {})"
              :key="col"
              :prop="col"
              :label="col"
              min-width="100"
              show-overflow-tooltip
            />
          </el-table>
          <p v-if="iotSeries.length > 50" class="iot-hint">仅展示前 50 条序列点</p>
        </template>
        <el-empty v-else-if="!iotLoading" description="暂无试验数据" />
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="iotDialogVisible = false">关 闭</el-button>
      </span>
    </el-dialog>

    <el-timeline style="margin-top: 40px">
      <el-timeline-item
        v-for="(activity, index) in logs"
        :key="index"
        :timestamp="alterTime(activity.addTime)">
        {{ activity.log_info }}
      </el-timeline-item>
    </el-timeline>
  </div>
</template>


<style scoped>
.el-dialog {
  width: 500px !important;
}

/deep/.el-textarea__inner {
  height: 150px;
  padding: 5px;
}

.el-rate__icon {
  font-size: 25px !important;
}

.el-input {
  width: 300px;
}

.el-dialog__body {
  padding: 0 20px;
}

.el-form-item__label {
  padding: 0 !important;
}
</style>

<style scoped lang="scss">

.evaluate {
  margin-top: 20px;
}

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

.row {
  display: flex;

  &:nth-child(n+2) {
    margin-top: 30px;
  }
}

.el-timeline {
  padding: 0;
}

.item {
  width: 33%;
}

.container {
  padding: 20px;
}

.iot-block {
  margin-bottom: 12px;
  line-height: 1.5;
}
.iot-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}
.iot-summary {
  margin: 0;
  padding: 8px 10px;
  background: #f7f8fa;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  max-height: 180px;
  overflow: auto;
}
.iot-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #999;
}
</style>
