<template>
  <section class="app-main">
    <router-view v-slot="{ Component, route }">
      <transition name="fade-transform" mode="out-in">
        <keep-alive :include="cachedViews" :max="20">
          <component :is="Component" v-if="Component" :key="route.fullPath" />
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
}
</script>

<style scoped>
.app-main {
  /**
   * 作者：yanmh0722@163.com
   * 时间：2023/10/20 15:26:33
   * 功能：自定义header
   */
  /*50 = navbar  */
  height: calc(100vh - 84px - 50px);
  width: 100%;
  position: relative;
  overflow-y: scroll;
}

.fixed-header + .app-main {
  padding-top: 50px;
}
</style>

<style lang="scss">
// fix css style bug in open el-dialog
.el-popup-parent--hidden {
  .fixed-header {
    padding-right: 15px;
  }
}

.hasTagsView {
  .app-main {
    min-height: calc(100vh - 84px);
  }

  .fixed-header + .app-main {
    padding-top: 84px;
  }
}
</style>
