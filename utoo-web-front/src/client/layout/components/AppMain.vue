<template>
  <section class="app-main">
    <router-view v-slot="{ Component, route }">
      <transition name="fade-transform" mode="out-in">
        <keep-alive :include="cachedViews" :max="20">
          <component :is="Component" v-if="Component" :key="viewKey(route)" />
        </keep-alive>
      </transition>
    </router-view>
  </section>
</template>

<script>
export default {
  name: 'AppMain',
  computed: {
    cachedViews() {
      return this.$store.state.tagsView.cachedViews
    },
  },
  methods: {
    viewKey(route) {
      const name = route?.name || route?.path || 'anonymous-view'
      const params = route?.params && Object.keys(route.params).length
        ? JSON.stringify(route.params)
        : ''
      return `${name}${params ? `:${params}` : ''}`
    },
  },
}
</script>

<style scoped>
.app-main {
  /* 在 main-container 的 flex 布局里占满剩余高度，只在这里滚动 */
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
  overscroll-behavior: contain;
}

.fixed-header + .app-main {
  padding-top: 0;
}
</style>

<style lang="scss">
// fix css style bug in open el-dialog
.el-popup-parent--hidden {
  .fixed-header {
    padding-right: 15px;
  }
}
</style>
