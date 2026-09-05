<template>
  <div class="tags-view" @click="hideContextMenu">
    <el-scrollbar class="tags-scroll">
      <div class="tags-inner">
        <router-link
          v-for="tag in tagsViewStore.visitedViews"
          :key="tag.path"
          :to="tag.fullPath"
          class="tags-item"
          :class="{ active: isActive(tag) }"
          @contextmenu.prevent="openContextMenu($event, tag)"
        >
          <span class="tags-title">{{ tag.title }}</span>
          <span
            v-if="!tag.affix"
            class="tags-close"
            @click.prevent.stop="closeTag(tag)"
          >
            ×
          </span>
        </router-link>
      </div>
    </el-scrollbar>

    <ul
      v-show="menu.visible"
      class="context-menu"
      :style="{ left: `${menu.x}px`, top: `${menu.y}px` }"
    >
      <li @click="onRefresh">刷新</li>
      <li :class="{ disabled: menu.tag?.affix }" @click="onClose">关闭</li>
      <li @click="onCloseOthers">关闭其他</li>
      <li @click="onCloseAll">关闭全部</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTagsViewStore, type TagView } from '@admin/stores/tags-view'

const route = useRoute()
const router = useRouter()
const tagsViewStore = useTagsViewStore()

const menu = reactive({
  visible: false,
  x: 0,
  y: 0,
  tag: null as TagView | null,
})

function isActive(tag: TagView) {
  return tag.path === route.path
}

watch(
  () => route.fullPath,
  () => {
    tagsViewStore.addView(route)
    hideContextMenu()
  },
  { immediate: true }
)

function openContextMenu(e: MouseEvent, tag: TagView) {
  menu.visible = true
  menu.tag = tag
  const menuWidth = 120
  const menuHeight = 140
  const maxX = window.innerWidth - menuWidth - 8
  const maxY = window.innerHeight - menuHeight - 8
  menu.x = Math.min(e.clientX, maxX)
  menu.y = Math.min(e.clientY, maxY)
}

function hideContextMenu() {
  menu.visible = false
  menu.tag = null
}

async function ensureActive(tag: TagView) {
  if (route.path !== tag.path) {
    await router.push(tag.fullPath)
  }
}

async function onRefresh() {
  const tag = menu.tag
  hideContextMenu()
  if (!tag) return
  await ensureActive(tag)
  tagsViewStore.refreshView(tag.path)
}

async function closeTag(tag: TagView) {
  if (tag.affix) return
  const wasActive = isActive(tag)
  const viewsBefore = tagsViewStore.visitedViews
  const idx = viewsBefore.findIndex((item) => item.path === tag.path)
  const fallback =
    (idx > 0 ? viewsBefore[idx - 1] : null) ||
    viewsBefore[idx + 1] ||
    null
  tagsViewStore.delView(tag.path)
  // 关闭详情等标签后丢弃 keep-alive 缓存，避免再次打开仍显示串单后的脏数据
  tagsViewStore.refreshView(tag.path)
  if (!wasActive) return

  const views = tagsViewStore.visitedViews
  const target =
    (fallback && views.find((v) => v.path === fallback.path)) ||
    views[views.length - 1]
  if (target) {
    await router.push(target.fullPath)
  } else {
    await router.push('/admin/dashboard')
  }
}

async function onClose() {
  const tag = menu.tag
  hideContextMenu()
  if (!tag || tag.affix) return
  await closeTag(tag)
}

async function onCloseOthers() {
  const tag = menu.tag
  hideContextMenu()
  if (!tag) return
  tagsViewStore.delOthers(tag.path)
  if (route.path !== tag.path) {
    await router.push(tag.fullPath)
  }
}

async function onCloseAll() {
  hideContextMenu()
  tagsViewStore.delAll()
  const affixed = tagsViewStore.visitedViews[0]
  await router.push(affixed?.fullPath || '/admin/dashboard')
}

function onGlobalClick() {
  if (menu.visible) hideContextMenu()
}

onMounted(() => {
  document.addEventListener('click', onGlobalClick)
  document.addEventListener('scroll', hideContextMenu, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onGlobalClick)
  document.removeEventListener('scroll', hideContextMenu, true)
})
</script>

<style scoped lang="scss">
.tags-view {
  position: relative;
  height: 36px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.tags-scroll {
  height: 100%;
  white-space: nowrap;
}

.tags-inner {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 12px;
}

.tags-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 26px;
  padding: 0 10px;
  border: 1px solid #dcdfe6;
  border-radius: 2px;
  color: #606266;
  font-size: 12px;
  background: #fff;
  text-decoration: none;
  transition: all 0.15s ease;

  &:hover {
    color: #409eff;
  }

  &.active {
    color: #fff;
    background: #409eff;
    border-color: #409eff;

    .tags-close {
      color: #fff;

      &:hover {
        background: rgba(255, 255, 255, 0.25);
      }
    }
  }
}

.tags-title {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tags-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  line-height: 1;
  border-radius: 50%;
  font-size: 14px;
  color: #909399;
  cursor: pointer;

  &:hover {
    background: #c0c4cc;
    color: #fff;
  }
}

.context-menu {
  position: fixed;
  z-index: 3000;
  margin: 0;
  padding: 6px 0;
  list-style: none;
  min-width: 120px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);

  li {
    padding: 8px 16px;
    font-size: 13px;
    color: #606266;
    cursor: pointer;

    &:hover:not(.disabled) {
      background: #f5f7fa;
      color: #409eff;
    }

    &.disabled {
      color: #c0c4cc;
      cursor: not-allowed;
    }
  }
}
</style>
