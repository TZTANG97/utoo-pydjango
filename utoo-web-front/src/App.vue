<template>
  <div id="app-root" :class="rootClass">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const rootClass = computed(() =>
  route.path.startsWith('/admin') ? 'is-admin' : 'is-client'
)
</script>

<style>
#app-root.is-client {
  min-width: 1240px;
  height: 100%;
}
#app-root.is-admin {
  min-width: 0;
  height: 100%;
}
html,
body,
#app {
  height: 100%;
  margin: 0;
}
</style>
