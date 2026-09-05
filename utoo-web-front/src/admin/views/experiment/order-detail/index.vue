<template>
  <div class="order-detail-page">
    <order-detail-panel :order-id="orderId" @back="goBack" />
  </div>
</template>

<script setup lang="ts">
import { onActivated, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import OrderDetailPanel from '../components/OrderDetailPanel.vue'

const route = useRoute()
const router = useRouter()

/**
 * keep-alive 下不能直接 computed(route.params.id)：
 * 切到咨询详情等同样带 :id 的路由时，缓存中的订单详情会把咨询 id 当成订单 id 去拉。
 *
 * 本实例在创建时绑定订单 id（layout 对详情用 path 作 key，一单一实例）。
 * 同步时必须 rid === boundOrderId，否则主单→子单时缓存中的主单会被改成子单 id，
 * 关子单标签后出现「标签是主单、内容是子单」。
 */
const boundOrderId = String(route.params.id || '')
const orderId = ref(boundOrderId)

function syncOrderIdFromRoute() {
  if (route.name !== 'ExperimentOrderDetail') return
  const rid = route.params.id != null ? String(route.params.id) : ''
  if (!rid || rid !== boundOrderId) return
  orderId.value = rid
}

watch(
  () => [route.name, route.params.id] as const,
  () => {
    syncOrderIdFromRoute()
  }
)

onActivated(() => {
  syncOrderIdFromRoute()
})

function goBack() {
  const from = String(route.query.from || '')
  const map: Record<string, string> = {
    orders: '/admin/experiment/orders',
    'sub-orders': '/admin/experiment/sub-orders',
    'subcontract-orders': '/admin/experiment/subcontract-orders',
    'subcontract-sub-orders': '/admin/experiment/subcontract-sub-orders',
    'grab-orders': '/admin/experiment/grab-orders',
  }
  // 优先回标签上的来源列表，避免详情把列表标签挤掉后无法返回
  const fallback = map[from] || '/admin/experiment/orders'
  router.push(fallback)
}
</script>

<style scoped lang="scss">
.order-detail-page {
  min-height: calc(100vh - 120px);
  padding: 4px 2px 24px;
}
</style>
