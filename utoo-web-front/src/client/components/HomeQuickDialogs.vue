<script setup>
import { computed } from "vue";

const props = defineProps({
  systemShow: Boolean,
  onlineServiceShow: Boolean,
  feedbackShow: Boolean,
  tableData: {
    type: Array,
    default: () => [],
  },
  page: {
    type: Number,
    default: 1,
  },
  limit: {
    type: Number,
    default: 5,
  },
  total: {
    type: Number,
    default: 0,
  },
  feedback: {
    type: String,
    default: "",
  },
  alterTime: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits([
  "update:systemShow",
  "update:onlineServiceShow",
  "update:feedbackShow",
  "update:feedback",
  "size-change",
  "page-change",
  "submit-feedback",
]);

const feedbackModel = computed({
  get: () => props.feedback,
  set: (val) => emit("update:feedback", val),
});

const systemVisible = computed({
  get: () => props.systemShow,
  set: (val) => emit("update:systemShow", val),
});

const serviceVisible = computed({
  get: () => props.onlineServiceShow,
  set: (val) => emit("update:onlineServiceShow", val),
});

const feedbackVisible = computed({
  get: () => props.feedbackShow,
  set: (val) => emit("update:feedbackShow", val),
});
</script>

<template>
  <el-dialog
    v-model="systemVisible"
    class="home-quick-dialog home-quick-dialog--wide"
    title="系统消息"
    width="720px"
    align-center
    destroy-on-close
  >
    <div class="dialog-intro">
      实验进度、订单状态等系统通知将在此展示
    </div>

    <el-table
      :data="tableData"
      class="home-message-table"
      height="360"
      stripe
      empty-text="暂无系统消息"
    >
      <el-table-column type="index" label="序号" width="64" align="center" />
      <el-table-column prop="addTime" label="日期" width="170">
        <template #default="{ row }">
          {{ alterTime(row.addTime) }}
        </template>
      </el-table-column>
      <el-table-column prop="info" label="描述" min-width="280" show-overflow-tooltip />
    </el-table>

    <div class="dialog-pagination">
      <el-pagination
        background
        :page-sizes="[5, 10]"
        :page-size="limit"
        :current-page="page"
        layout="total, prev, pager, next, sizes"
        :total="total"
        @size-change="(val) => emit('size-change', val)"
        @current-change="(val) => emit('page-change', val)"
      />
    </div>

    <template #footer>
      <el-button type="primary" @click="systemVisible = false">知道了</el-button>
    </template>
  </el-dialog>

  <el-dialog
    v-model="serviceVisible"
    class="home-quick-dialog"
    title="在线客服"
    width="680px"
    align-center
    destroy-on-close
  >
    <div class="service-header">
      <div class="service-badge">服务时间 8:30 – 18:30</div>
      <p class="service-tip">在线聊天功能调整中，请扫码添加企业微信沟通</p>
    </div>

    <div class="service-qr-grid">
      <div class="service-qr-card">
        <img src="@client/static/kefuQRcode.png" alt="企业微信客服二维码 1" />
        <span>扫码添加客服</span>
      </div>
      <div class="service-qr-card">
        <img src="@client/static/kefuQRcode2.png" alt="企业微信客服二维码 2" />
        <span>备用客服通道</span>
      </div>
    </div>
  </el-dialog>

  <el-dialog
    v-model="feedbackVisible"
    class="home-quick-dialog"
    title="意见反馈"
    width="480px"
    align-center
    :close-on-click-modal="false"
    destroy-on-close
  >
    <div class="dialog-intro">
      您的建议将帮助我们持续改进产品体验
    </div>

    <el-input
      v-model="feedbackModel"
      type="textarea"
      :rows="6"
      maxlength="500"
      show-word-limit
      placeholder="请描述您遇到的问题或改进建议…"
    />

    <template #footer>
      <el-button @click="feedbackVisible = false">取消</el-button>
      <el-button type="primary" :disabled="!feedbackModel.trim()" @click="emit('submit-feedback')">
        提交反馈
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.dialog-intro {
  margin: -4px 0 16px;
  font-size: 14px;
  color: #909399;
  line-height: 1.6;
}

.dialog-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.service-header {
  text-align: center;
  margin-bottom: 20px;
}

.service-badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 13px;
  color: var(--mainColor);
  background: rgba(233, 99, 2, 0.1);
  border: 1px solid rgba(233, 99, 2, 0.18);
}

.service-tip {
  margin: 12px 0 0;
  font-size: 15px;
  color: #303133;
  line-height: 1.6;
}

.service-qr-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.service-qr-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;

  &:hover {
    border-color: rgba(233, 99, 2, 0.25);
    box-shadow: 0 6px 20px rgba(233, 99, 2, 0.1);
  }

  img {
    width: 100%;
    max-width: 260px;
    border-radius: 8px;
  }

  span {
    font-size: 13px;
    color: #606266;
  }
}
</style>

<style lang="scss">
.home-quick-dialog {
  .el-dialog {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
  }

  .el-dialog__header {
    margin-right: 0;
    padding: 20px 24px 12px;
    border-bottom: 1px solid #f2f2f2;
  }

  .el-dialog__title {
    font-size: 18px;
    font-weight: 600;
    color: #303133;
  }

  .el-dialog__body {
    padding: 16px 24px 8px;
  }

  .el-dialog__footer {
    padding: 12px 24px 20px;
    border-top: 1px solid #f2f2f2;
  }
}

.home-message-table {
  border-radius: 8px;

  .el-table__header th {
    background: #fafafa !important;
    color: #606266;
    font-weight: 600;
  }
}
</style>
