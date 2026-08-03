<template>
  <div class="order-detail-page">
    <order-detail-panel :order-id="orderId" @back="goBack" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import OrderDetailPanel from '../components/OrderDetailPanel.vue'

const route = useRoute()
const router = useRouter()

const orderId = computed(() => String(route.params.id || ''))

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
