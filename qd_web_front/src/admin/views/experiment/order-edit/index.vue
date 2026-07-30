<template>
  <div v-loading="loading" class="edit-page">
    <header class="page-head">
      <button type="button" class="back-link" @click="goBack">← 返回详情</button>
      <h2>编辑订单</h2>
      <p v-if="detail" class="sub">
        <span class="mono">{{ detail.orderId }}</span>
        · {{ detail.orderStatusLabel }}
      </p>
    </header>

    <el-form v-if="detail" label-width="120px" class="form-card" @submit.prevent>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="订单编号">
            <el-input :model-value="String(detail.orderId || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="制单人员">
            <el-input :model-value="String(detail.addUser || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="客户名称">
            <el-input :model-value="String(detail.customerName || detail.companyName || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="所属公司">
            <el-input :model-value="String(detail.supplierName || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="销售主管">
            <el-input :model-value="String(detail.saleManager || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="销售人员">
            <el-input :model-value="String(detail.saleUser || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="订单总价">
            <el-input v-model="form.totalPrice" placeholder="订单总价" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="付款方式">
            <el-input :model-value="String(detail.payWayName || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="预计收货时间">
            <el-date-picker
              v-model="form.deliveryTime"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="币种">
            <el-input :model-value="String(detail.currencyLabel || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="收件人">
            <el-input v-model="form.shipUser" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话">
            <el-input v-model="form.shipPhone" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="寄回地址">
            <el-input v-model="form.shipAddress" type="textarea" :rows="2" clearable />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="备注">
            <el-input v-model="form.mark" type="textarea" :rows="3" clearable />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
        <el-button @click="goBack">取消</el-button>
      </el-form-item>
    </el-form>
    <el-empty v-else-if="!loading" description="订单不存在或不可编辑" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getExpOrderDetail, updateExpOrderBasic } from '@admin/api/experiment'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const route = useRoute()
const router = useRouter()
const orderId = String(route.params.id || '')

const loading = ref(false)
const saving = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const form = reactive({
  totalPrice: '',
  shipUser: '',
  shipPhone: '',
  shipAddress: '',
  mark: '',
  deliveryTime: '',
})

function goBack() {
  router.push({ name: 'ExperimentOrderDetail', params: { id: orderId } })
}

async function load() {
  if (!orderId) return
  loading.value = true
  try {
    const res = await getExpOrderDetail(orderId)
    if (!isAjaxOk(res) || !res.obj) {
      detail.value = null
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    detail.value = obj
    form.totalPrice = obj.totalPrice != null ? String(obj.totalPrice) : ''
    form.shipUser = String(obj.shipUser || '')
    form.shipPhone = String(obj.shipPhone || '')
    form.shipAddress = String(obj.shipAddress || '')
    form.mark = String(obj.mark || obj.msg || '')
    form.deliveryTime = String(obj.deliveryTime || '').slice(0, 10)
  } finally {
    loading.value = false
  }
}

async function onSave() {
  saving.value = true
  try {
    const res = await updateExpOrderBasic({
      id: orderId,
      totalPrice: form.totalPrice,
      shipUser: form.shipUser,
      shipPhone: form.shipPhone,
      shipAddress: form.shipAddress,
      mark: form.mark,
      deliveryTime: form.deliveryTime,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success('保存成功')
    goBack()
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<style scoped>
.edit-page {
  padding: 8px 4px 24px;
}
.page-head {
  margin-bottom: 16px;
}
.back-link {
  border: 0;
  background: transparent;
  color: #409eff;
  cursor: pointer;
  padding: 0;
  margin-bottom: 8px;
}
.page-head h2 {
  margin: 0 0 4px;
  font-size: 20px;
}
.sub {
  margin: 0;
  color: #909399;
  font-size: 13px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.form-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px 20px 8px;
  max-width: 960px;
}
</style>
