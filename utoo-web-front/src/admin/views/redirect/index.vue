<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

onMounted(() => {
  const path = route.params.path
  const target = Array.isArray(path) ? path.join('/') : String(path || 'dashboard')
  router.replace(`/${target}`)
})
</script>

<template>
  <div />
</template>
