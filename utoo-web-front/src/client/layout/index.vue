<template>
  <div :class="classObj" class="app-wrapper client-shell">
    <div v-if="device==='mobile'&&sidebar.opened" class="drawer-bg" @click="handleClickOutside" />
    <custom-header />
    <sidebar class="sidebar-container" />
    <div class="main-container" v-loading.lock="loading" element-loading-text="正在加载中...">
      <div :class="{'fixed-header':fixedHeader}">
        <navbar />
      </div>
      <tags-view />
      <app-main />
    </div>
  </div>
</template>

<script>
import { Navbar, Sidebar, AppMain, TagsView } from './components'
import CustomHeader from './components/header.vue'
import ResizeMixin from './mixin/ResizeHandler'
import {mapGetters} from "vuex";

export default {
  name: 'Layout',
  components: {
    Navbar,
    Sidebar,
    AppMain,
    TagsView,
    CustomHeader
  },
  mixins: [ResizeMixin],
  computed: {
    ...mapGetters(['loading']),
    sidebar() {
      return this.$store.state.app.sidebar
    },
    device() {
      return this.$store.state.app.device
    },
    fixedHeader() {
      return this.$store.state.settings.fixedHeader
    },
    classObj() {
      return {
        hideSidebar: !this.sidebar.opened,
        openSidebar: this.sidebar.opened,
        withoutAnimation: this.sidebar.withoutAnimation,
        mobile: this.device === 'mobile'
      }
    }
  },
  methods: {
    handleClickOutside() {
      this.$store.dispatch('app/closeSideBar', { withoutAnimation: false })
    }
  }
}
</script>

<style lang="scss" scoped>
  @import "@client/styles/mixin.scss";
  @import "@client/styles/variables.scss";

  .app-wrapper {
    @include clearfix;
    position: relative;
    height: 100%;
    width: 100%;
    overflow: hidden;
    /* 顶栏 fixed 后占位，避免正文顶到顶栏下 */
    padding-top: 52px;
    box-sizing: border-box;
    &.mobile.openSidebar{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
    }
  }

  /* 右侧主区：自身不增高撑开整页，只让 app-main 内部滚 */
  .main-container {
    height: calc(100vh - 52px);
    max-height: calc(100vh - 52px);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
  }
  .drawer-bg {
    background: #000;
    opacity: 0.3;
    width: 100%;
    top: 0;
    height: 100%;
    position: absolute;
    z-index: 999;
  }

  .fixed-header {
    position: fixed;
    top: 0;
    right: 0;
    z-index: 9;
    width: calc(100% - #{$sideBarWidth});
    transition: width 0.28s;
  }

  .hideSidebar .fixed-header {
    width: calc(100% - 54px)
  }

  .mobile .fixed-header {
    width: 100%;
  }
</style>

<style scoped>
/deep/.el-loading-mask {
  z-index: 2043 !important;
}

/deep/.el-loading-spinner>.circular {
  width: 50px;
  height: 50px;
}

/deep/.el-loading-text {
  color: var(--mainColor);
  font-size: 18px;
  margin-top: 10px;
}
</style>
