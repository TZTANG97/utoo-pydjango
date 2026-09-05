<template>
  <div id="tags-view-container" class="tags-view-container">
    <scroll-pane ref="scrollPane" class="tags-view-wrapper" @scroll="handleScroll">
      <router-link
        v-for="tag in visitedViews"
        ref="tag"
        :key="tag.fullPath || tag.path"
        :class="isActive(tag)?'active':''"
        :to="{ path: tag.path, query: tag.query || {} }"
        class="tags-view-item"
        @click.middle="!isAffix(tag)?closeSelectedTag(tag):''"
        @contextmenu.prevent.stop="openMenu(tag, $event)"
      >
        {{ tag.title }}
        <span
          v-if="!isAffix(tag)"
          class="tags-view-close"
          @click.prevent.stop="closeSelectedTag(tag)"
        >
          <el-icon><Close /></el-icon>
        </span>
      </router-link>
    </scroll-pane>
    <ul
      v-show="visible"
      :style="{ left: left + 'px', top: top + 'px' }"
      class="contextmenu"
      @click.stop
    >
      <li @click="refreshSelectedTag(selectedTag)">刷新</li>
      <li v-if="!isAffix(selectedTag)" @click="closeSelectedTag(selectedTag)">关闭</li>
      <li @click="closeOthersTags">关闭其他</li>
      <li @click="closeAllTags(selectedTag)">关闭全部</li>
    </ul>
  </div>
</template>

<script>
import { Close } from '@element-plus/icons-vue'
import ScrollPane from './ScrollPane'
import { resolvePath as joinPath } from '@client/utils/path'

export default {
  components: { ScrollPane, Close },
  data() {
    return {
      visible: false,
      top: 0,
      left: 0,
      selectedTag: {},
      affixTags: []
    }
  },
  computed: {
    visitedViews() {
      return this.$store.state.tagsView.visitedViews
    },
    routes() {
      return this.$store.state.permission.routes
    }
  },
  watch: {
    $route() {
      this.addTags()
      this.moveToCurrentTag()
    },
    visible(value) {
      if (value) {
        document.body.addEventListener('click', this.closeMenu)
      } else {
        document.body.removeEventListener('click', this.closeMenu)
      }
    }
  },
  mounted() {
    this.initTags()
    this.addTags()
  },
  methods: {
    isActive(route) {
      const key = route.fullPath || route.path
      return key === this.$route.fullPath
    },
    isAffix(tag) {
      return tag.meta && tag.meta.affix
    },
    filterAffixTags(routes, basePath = '/') {
      let tags = []
      routes.forEach(route => {
        if (route.meta && route.meta.affix) {
          const tagPath = joinPath(basePath, route.path)
          tags.push({
            fullPath: tagPath,
            path: tagPath,
            name: route.name,
            meta: { ...route.meta }
          })
        }
        if (route.children) {
          const tempTags = this.filterAffixTags(route.children, route.path)
          if (tempTags.length >= 1) {
            tags = [...tags, ...tempTags]
          }
        }
      })
      return tags
    },
    initTags() {
      const affixTags = this.affixTags = this.filterAffixTags(this.routes)
      for (const tag of affixTags) {
        // Must have tag name
        if (tag.name) {
          this.$store.dispatch('tagsView/addVisitedView', tag)
        }
      }
    },
    addTags() {
      const { name } = this.$route
      if (name) {
        this.$store.dispatch('tagsView/addView', this.$route)
      }
      return false
    },
    moveToCurrentTag() {
      const tags = this.$refs.tag
      if (!tags) return
      const list = Array.isArray(tags) ? tags : [tags]
      this.$nextTick(() => {
        const pane = this.$refs.scrollPane
        if (!pane) return
        for (const tag of list) {
          const to = tag.$props?.to ?? tag.to
          if (!to) continue
          const path = typeof to === 'string' ? to : to.path
          const fullPath = typeof to === 'string' ? to : (to.fullPath || to.path)
          if (fullPath === this.$route.fullPath || path === this.$route.path) {
            try {
              pane.moveToTarget(tag)
            } catch (e) {
              console.warn('[TagsView] moveToTarget skipped', e)
            }
            if (fullPath && fullPath !== this.$route.fullPath) {
              this.$store.dispatch('tagsView/updateVisitedView', this.$route)
            }
            break
          }
        }
      })
    },
    refreshSelectedTag(view) {
      this.$store.dispatch('tagsView/delCachedView', view).then(() => {
        const { fullPath } = view
        this.closeMenu()
        this.$nextTick(() => {
          this.$router.replace({
            path: '/redirect' + fullPath,
            query: view.query || {},
          })
        })
      })
    },
    closeSelectedTag(view) {
      this.$store.dispatch('tagsView/delView', view).then(({ visitedViews }) => {
        if (this.isActive(view)) {
          this.toLastView(visitedViews, view)
        }
      })
    },
    closeOthersTags() {
      const tag = this.selectedTag || {}
      this.$router.push({ path: tag.path, query: tag.query || {} })
      this.$store.dispatch('tagsView/delOthersViews', tag).then(() => {
        this.moveToCurrentTag()
      })
      this.closeMenu()
    },
    closeAllTags(view) {
      this.$store.dispatch('tagsView/delAllViews').then(({ visitedViews }) => {
        if (this.affixTags.some(tag => tag.path === view.path)) {
          return
        }
        this.toLastView(visitedViews, view)
      })
      this.closeMenu()
    },
    toLastView(visitedViews, view) {
      const latestView = visitedViews.slice(-1)[0]
      if (latestView) {
        this.$router.push(latestView.fullPath)
      } else {
        // now the default is to redirect to the home page if there is no tags-view,
        // you can adjust it according to your needs.
        if (view.name === 'Dashboard') {
          // to reload home page
          this.$router.replace({ path: '/redirect' + view.fullPath })
        } else {
          this.$router.push('/')
        }
      }
    },
    openMenu(tag, e) {
      const menuMinWidth = 105
      const maxLeft = window.innerWidth - menuMinWidth - 8
      // 使用 fixed + 视口坐标，避免被 tags 容器 height/overflow 裁切
      let left = e.clientX + 4
      if (left > maxLeft) left = maxLeft
      this.left = Math.max(8, left)
      this.top = Math.min(e.clientY + 4, window.innerHeight - 160)
      this.visible = true
      this.selectedTag = tag
    },
    closeMenu() {
      this.visible = false
    },
    handleScroll() {
      this.closeMenu()
    }
  }
}
</script>

<style lang="scss" scoped>
.tags-view-container {
  height: 44px;
  width: 100%;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e6ebf2;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
  overflow: visible;
  position: relative;
  .tags-view-wrapper {
    .tags-view-item {
      display: inline-flex;
      align-items: center;
      position: relative;
      cursor: pointer;
      height: 30px;
      line-height: 30px;
      border: 1px solid #d5dbe6;
      color: #475569;
      background: #fff;
      padding: 0 12px;
      font-size: 13px;
      margin-left: 8px;
      margin-top: 7px;
      border-radius: 999px;
      transition: all .2s ease;
      &:first-of-type {
        margin-left: 15px;
      }
      &:last-of-type {
        margin-right: 15px;
      }
      &:hover {
        color: var(--mainColor);
        border-color: rgba(233, 99, 2, 0.35);
        background: rgba(233, 99, 2, 0.05);
      }
      &.active {
        background: linear-gradient(135deg, #e96302 0%, #f28a37 100%);
        color: #fff;
        border-color: transparent;
        box-shadow: 0 10px 24px rgba(233, 99, 2, 0.24);
        &::before {
          content: '';
          background: #fff;
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          position: relative;
          margin-right: 2px;
        }
        .tags-view-close {
          color: #fff;
          &:hover {
            background-color: rgba(255, 255, 255, 0.3);
          }
        }
      }
    }
  }
  .contextmenu {
    margin: 0;
    background: #fff;
    z-index: 4000;
    position: fixed;
    list-style-type: none;
    padding: 6px 0;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 400;
    color: #333;
    border: 1px solid #e6ebf2;
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.16);
    min-width: 105px;
    li {
      margin: 0;
      padding: 8px 16px;
      cursor: pointer;
      &:hover {
        background: rgba(233, 99, 2, 0.08);
        color: var(--mainColor);
      }
    }
  }
}
</style>

<style lang="scss">
.tags-view-wrapper {
  .tags-view-item {
    .tags-view-close {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      margin-left: 6px;
      vertical-align: middle;
      border-radius: 50%;
      transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
      .el-icon {
        font-size: 12px;
      }
      &:hover {
        background-color: #b4bccc;
        color: #fff;
      }
    }
  }
}
</style>
