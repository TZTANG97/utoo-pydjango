<template>
  <div class="admin-layout admin-shell">
    <aside class="sidebar" :class="{ collapsed: collapsed }">
      <div class="brand">
        <span class="brand-mark">UTOO</span>
        <span v-if="!collapsed" class="brand-text">愉兔检测管理平台</span>
      </div>
      <el-scrollbar class="menu-scroll">
        <el-menu
          :key="activeMenu"
          :default-active="activeMenu"
          :collapse="collapsed"
          background-color="#1f2937"
          text-color="#cbd5e1"
          active-text-color="#ffffff"
          @select="onMenuSelect"
        >
          <el-menu-item index="/admin/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <template #title>欢迎页</template>
          </el-menu-item>
          <template v-for="item in menuTree" :key="String(item.id)">
            <el-sub-menu
              v-if="item.children?.length"
              :index="`menu-${item.id}`"
            >
              <template #title>
                <el-icon><Menu /></el-icon>
                <span>{{ item.menu_name || '未命名菜单' }}</span>
              </template>
              <el-menu-item
                v-for="child in item.children"
                :key="String(child.id)"
                :index="resolveMenuPath(child)"
                :disabled="!resolveMenuPath(child)"
                :class="{ 'menu-pending': !isMenuReady(child) }"
              >
                {{ child.menu_name || '未命名菜单' }}
              </el-menu-item>
            </el-sub-menu>
            <el-menu-item
              v-else
              :index="resolveMenuPath(item)"
              :disabled="!resolveMenuPath(item)"
              :class="{ 'menu-pending': !isMenuReady(item) }"
            >
              <el-icon><Document /></el-icon>
              <template #title>{{ item.menu_name || '未命名菜单' }}</template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>
    </aside>

    <section class="main-section">
      <header class="navbar">
        <div class="navbar-left">
          <el-button link @click="collapsed = !collapsed">
            <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
          </el-button>
          <span class="page-title">{{ currentTitle }}</span>
        </div>
        <div class="navbar-right">
          <span class="user-name">{{ userStore.userName || userStore.loginName }}</span>
          <el-tag v-if="userStore.roleName" size="small" type="warning">
            {{ userStore.roleName }}
          </el-tag>
          <el-button type="danger" link @click="handleLogout">退出登录</el-button>
        </div>
      </header>

      <tags-view />

      <main class="app-main">
        <router-view v-slot="{ Component }">
          <keep-alive :max="30">
            <component
              :is="Component"
              v-if="Component"
              :key="contentViewKey"
            />
          </keep-alive>
        </router-view>
      </main>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Document,
  Expand,
  Fold,
  HomeFilled,
  Menu,
} from '@element-plus/icons-vue'
import TagsView from '@admin/layout/components/TagsView.vue'
import { resolveRouteTitle, useTagsViewStore } from '@admin/stores/tags-view'
import { useUserStore } from '@admin/stores/user'
import { isMenuReady, resolveMenuPath } from '@admin/utils/menu-route'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const tagsViewStore = useTagsViewStore()
const collapsed = ref(false)

const menuTree = computed(() => userStore.menus)
const activeMenu = computed(() => {
  // 带 query 的菜单（类目/样品属性 type）需用 fullPath 才能高亮正确项
  const q = route.fullPath
  if (q.includes('?')) return q.startsWith('/') ? q : `/${q}`
  return route.path
})
/** 用 useRoute() 计算 key，避免 router-view slot 的 route 短暂滞后导致 keep-alive 仍显示旧页 */
const contentViewKey = computed(() => tagsViewStore.viewKey(route))

async function onMenuSelect(index: string) {
  if (!index || index.startsWith('menu-')) return
  if (route.fullPath !== index && route.path !== index) {
    await router.push(index)
  }
  // 侧栏跳转后强制内容区与当前路由对齐（修复 hash 已变仍显示旧 tab 内容）
  tagsViewStore.refreshView(route.path)
}
const currentTitle = computed(() => {
  if (route.name === 'LegacyPending') {
    const menuId = String(route.params.menuId || '')
    return userStore.pendingMenus[menuId]?.title || '功能迁移中'
  }
  const tag = tagsViewStore.visitedViews.find((v) => v.path === route.path)
  if (tag?.title) return tag.title
  return resolveRouteTitle(route) || String(route.meta.title || '欢迎页')
})

async function handleLogout() {
  tagsViewStore.reset()
  userStore.logout()
  await router.replace('/admin/login')
}
</script>

<style scoped lang="scss">
.admin-layout {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background: #1f2937;
  color: #fff;
  transition: width 0.2s ease;
  display: flex;
  flex-direction: column;

  &.collapsed {
    width: 64px;
  }
}

.brand {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  background: linear-gradient(135deg, #f97316, #ea580c);
}

.brand-mark {
  font-weight: 700;
  letter-spacing: 0.5px;
}

.brand-text {
  font-size: 14px;
  white-space: nowrap;
}

.menu-scroll {
  flex: 1;
}

:deep(.menu-pending) {
  opacity: 0.72;
}

.main-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.navbar {
  height: 56px;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-left,
.navbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  line-height: 1;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.2;
}

.user-name {
  color: #4b5563;
  font-size: 14px;
  line-height: 1.2;
}

.app-main {
  flex: 1;
  overflow: auto;
  padding: 20px;
}
</style>
