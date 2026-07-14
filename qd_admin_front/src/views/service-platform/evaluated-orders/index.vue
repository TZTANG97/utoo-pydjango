<template>
  <EvaluatedOrderList
    title="已评价实验订单"
    :fetcher="fetchEvaluatedOrderList"
    show-maoli
    show-add-time
  />
</template>

<script setup lang="ts">
import { fetchEvaluatedOrderList } from '@/api/service-platform'
import EvaluatedOrderList from '../components/EvaluatedOrderList.vue'
</script>
