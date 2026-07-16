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

    <el-form v-if="detail" label-width="110px" class="form-card" @submit.prevent>
      <el-form-item label="客户名称">
        <el-input :model-value="String(detail.customerName || detail.companyName || '')" disabled />
      </el-form-item>
      <el-form-item label="总价">
        <el-input v-model="form.totalPrice" placeholder="订单总价" clearable />
      </el-form-item>
      <el-form-item label="收件人">
        <el-input v-model="form.shipUser" clearable />
      </el-form-item>
      <el-form-item label="联系电话">
        <el-input v-model="form.shipPhone" clearable />
      </el-form-item>
      <el-form-item label="寄回地址">
        <el-input v-model="form.shipAddress" type="textarea" :rows="2" clearable />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.mark" type="textarea" :rows="3" clearable />
      </el-form-item>
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
import { getExpOrderDetail, updateExpOrderBasic } from '@/api/experiment'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

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
    form.mark = String(obj.mark || '')
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
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '保存成功'))
    goBack()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.edit-page {
  max-width: 720px;
  padding: 8px 4px 32px;
}
.page-head {
  margin-bottom: 16px;
}
.page-head h2 {
  margin: 0;
  font-size: 20px;
}
.sub {
  margin: 6px 0 0;
  color: #5f7068;
  font-size: 13px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.back-link {
  border: 0;
  background: transparent;
  color: #1f6f5b;
  padding: 0;
  margin-bottom: 8px;
  cursor: pointer;
  font-size: 13px;
}
.form-card {
  padding: 18px 20px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #d7e0db;
}
</style>
