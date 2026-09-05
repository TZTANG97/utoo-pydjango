<template>
  <div :class="{'has-logo':showLogo}" class="sidebar-inner">
    <logo v-if="showLogo" :collapse="isCollapse" />
    <!-- 个人中心菜单项少：不用 el-scrollbar，避免整栏可滚 -->
    <div class="sidebar-menu-wrap" @wheel.prevent>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :background-color="variables.menuBg"
        :text-color="variables.menuText"
        :unique-opened="false"
        :active-text-color="variables.menuActiveText"
        :collapse-transition="false"
        mode="vertical"
      >
        <sidebar-item v-for="route in routes" :key="route.path" :item="route" :base-path="route.path" />
      </el-menu>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Logo from './Logo'
import SidebarItem from './SidebarItem'
import variables from '@client/styles/variables.js'

export default {
  components: { SidebarItem, Logo },
  computed: {
    ...mapGetters([
      'sidebar'
    ]),
    routes() {
      // 统一 SPA 合并了 admin + client 路由；C 端侧栏只展示个人中心菜单，勿泄漏后台「登录」等项
      const all = this.$router.options.routes || []
      return all.filter((route) => {
        if (route.hidden || route.meta?.hidden) return false
        const p = route.path || ''
        if (p === '/admin' || p.startsWith('/admin/')) return false
        // 仅保留带侧栏图标的业务入口；首页/分类等无 icon 的不进侧栏
        const child = (route.children || []).find((c) => !c.hidden && !c.meta?.hidden)
        const icon = child?.meta?.icon || route.meta?.icon
        return !!icon
      })
    },
    activeMenu() {
      const route = this.$route
      const { meta, path } = route
      // if set path, the sidebar will highlight the path you set
      if (meta.activeMenu) {
        return meta.activeMenu
      }
      return path
    },
    showLogo() {
      return this.$store.state.settings.sidebarLogo
    },
    variables() {
      return variables
    },
    isCollapse() {
      return !this.sidebar.opened
    }
  }
}
</script>

<style scoped lang="scss">
.sidebar-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-menu-wrap {
  flex: 1 1 auto;
  min-height: 0;
  /* 固定不滚动：个人中心菜单项少，禁止内部滚轮 */
  overflow: hidden;
  overscroll-behavior: none;
}

.ggh-qr-code {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) scale(0.7);
}
</style>
