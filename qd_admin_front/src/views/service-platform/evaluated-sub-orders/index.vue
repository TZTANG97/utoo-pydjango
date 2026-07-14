<template>
  <EvaluatedOrderList
    title="已评价分包订单"
    :fetcher="fetchEvaluatedSubOrderList"
    show-maoli
    show-add-time
  />
</template>

<script setup lang="ts">
import { fetchEvaluatedSubOrderList } from '@/api/service-platform'
import EvaluatedOrderList from '../components/EvaluatedOrderList.vue'
</script>
