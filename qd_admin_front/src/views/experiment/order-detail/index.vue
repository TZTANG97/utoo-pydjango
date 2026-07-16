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
    orders: '/experiment/orders',
    'sub-orders': '/experiment/sub-orders',
    'subcontract-orders': '/experiment/subcontract-orders',
    'subcontract-sub-orders': '/experiment/subcontract-sub-orders',
  }
  router.push(map[from] || '/experiment/orders')
}
</script>

<style scoped lang="scss">
.order-detail-page {
  min-height: calc(100vh - 120px);
  padding: 4px 2px 24px;
}
</style>
