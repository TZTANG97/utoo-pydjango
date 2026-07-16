<template>
  <div v-loading="loading" class="create-page">
    <header class="page-head">
      <button type="button" class="back-link" @click="goBack">← 返回详情</button>
      <h2>{{ titleText }}</h2>
      <p v-if="parent" class="sub">
        来源主单
        <span class="mono">{{ parent.orderId }}</span>
        · 勾选待处理产品行后创建
      </p>
    </header>

    <template v-if="parent">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        class="hint"
        title="仅显示主单中待处理（op_status=1）的产品行。创建后将生成子订单并挂接所选行。"
      />
      <el-table
        :data="pendingRows"
        border
        stripe
        class="line-table"
        @selection-change="onSel"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="childOrderId" label="子单号" min-width="130" show-overflow-tooltip />
        <el-table-column prop="goodsName" label="产品名称" min-width="120" show-overflow-tooltip />
        <el-table-column prop="goodsSpec" label="型号" min-width="100" show-overflow-tooltip />
        <el-table-column prop="projectName" label="测试项目" min-width="120" show-overflow-tooltip />
        <el-table-column prop="price" label="单价" width="90" align="right" />
        <el-table-column prop="orderStatusLabel" label="状态" width="100" />
      </el-table>
      <div class="actions">
        <el-button type="primary" :loading="saving" :disabled="!selected.length" @click="onCreate">
          创建子订单
        </el-button>
        <el-button @click="goBack">取消</el-button>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="主单不存在或没有待处理行" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createExpSubOrder, getExpOrderDetail } from '@/api/experiment'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const route = useRoute()
const router = useRouter()
const saleOrderId = String(route.query.saleOrderId || route.query.parentId || '')

const loading = ref(false)
const saving = ref(false)
const parent = ref<Record<string, unknown> | null>(null)
const children = ref<Record<string, unknown>[]>([])
const selected = ref<Record<string, unknown>[]>([])

const titleText = computed(() =>
  String(parent.value?.orderType || '') === '8' ? '创建实验分包子订单' : '创建实验子订单'
)

const pendingRows = computed(() =>
  children.value.filter((r) => Number(r.opStatus ?? 0) === 1)
)

function goBack() {
  if (saleOrderId) {
    router.push({ name: 'ExperimentOrderDetail', params: { id: saleOrderId } })
  } else {
    router.push('/experiment/orders')
  }
}

function onSel(rows: Record<string, unknown>[]) {
  selected.value = rows
}

async function load() {
  if (!saleOrderId) {
    ElMessage.warning('缺少主单 ID')
    return
  }
  loading.value = true
  try {
    const res = await getExpOrderDetail(saleOrderId)
    if (!isAjaxOk(res) || !res.obj) {
      parent.value = null
      children.value = []
      ElMessage.error(ajaxErrorMessage(res, '加载主单失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    parent.value = obj
    children.value = (obj.children as Record<string, unknown>[]) || []
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  const ids = selected.value.map((r) => r.id).filter((id) => id != null)
  if (!ids.length) {
    ElMessage.warning('请选择至少一行')
    return
  }
  saving.value = true
  try {
    const res = await createExpSubOrder({
      saleOrderId,
      childIds: ids,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '创建失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '创建成功'))
    const newId = (res.obj as { id?: number } | undefined)?.id
    if (newId) {
      router.push({ name: 'ExperimentOrderDetail', params: { id: String(newId) } })
    } else {
      goBack()
    }
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.create-page {
  padding: 8px 4px 32px;
}
.page-head {
  margin-bottom: 14px;
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
.hint {
  margin-bottom: 12px;
}
.line-table {
  margin-bottom: 16px;
}
.actions {
  display: flex;
  gap: 8px;
}
</style>
