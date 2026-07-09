<template>
  <el-scrollbar ref="scrollContainer" :vertical="false" class="scroll-container" @wheel.prevent="handleScroll">
    <slot />
  </el-scrollbar>
</template>

<script>
const tagAndTagSpacing = 4 // tagAndTagSpacing

export default {
  name: 'ScrollPane',
  data() {
    return {
      left: 0
    }
  },
  computed: {
    scrollWrapper() {
      const sc = this.$refs.scrollContainer
      if (!sc) return null
      // Element Plus 2.x 使用 wrapRef，旧版为 $refs.wrap
      return sc.wrapRef || sc.$refs?.wrap || sc.$el?.querySelector?.('.el-scrollbar__wrap') || null
    }
  },
  mounted() {
    this.$nextTick(() => {
      const wrap = this.scrollWrapper
      if (wrap?.addEventListener) {
        wrap.addEventListener('scroll', this.emitScroll, true)
      }
    })
  },
  beforeUnmount() {
    const wrap = this.scrollWrapper
    if (wrap?.removeEventListener) {
      wrap.removeEventListener('scroll', this.emitScroll)
    }
  },
  methods: {
    handleScroll(e) {
      const eventDelta = e.wheelDelta || -e.deltaY * 40
      const $scrollWrapper = this.scrollWrapper
      if (!$scrollWrapper) return
      $scrollWrapper.scrollLeft = $scrollWrapper.scrollLeft + eventDelta / 4
    },
    emitScroll() {
      this.$emit('scroll')
    },
    moveToTarget(currentTag) {
      const sc = this.$refs.scrollContainer
      const $container = sc?.$el || sc
      const $scrollWrapper = this.scrollWrapper
      if (!$container || !$scrollWrapper) return
      const $containerWidth = $container.offsetWidth
      const tagList = this.$parent.$refs.tag

      let firstTag = null
      let lastTag = null

      // find first tag and last tag
      if (tagList.length > 0) {
        firstTag = tagList[0]
        lastTag = tagList[tagList.length - 1]
      }

      if (!tagList || !tagList.length) return

      if (firstTag === currentTag) {
        $scrollWrapper.scrollLeft = 0
      } else if (lastTag === currentTag) {
        $scrollWrapper.scrollLeft = $scrollWrapper.scrollWidth - $containerWidth
      } else {
        const currentIndex = tagList.findIndex(item => item === currentTag)
        if (currentIndex < 0) return
        const prevTag = tagList[currentIndex - 1]
        const nextTag = tagList[currentIndex + 1]
        const curEl = currentTag.$el || currentTag
        if (!curEl?.offsetLeft && curEl?.offsetLeft !== 0) return

        if (nextTag?.$el) {
          const afterNextTagOffsetLeft =
            nextTag.$el.offsetLeft + nextTag.$el.offsetWidth + tagAndTagSpacing
          if (afterNextTagOffsetLeft > $scrollWrapper.scrollLeft + $containerWidth) {
            $scrollWrapper.scrollLeft = afterNextTagOffsetLeft - $containerWidth
            return
          }
        }
        if (prevTag?.$el) {
          const beforePrevTagOffsetLeft = prevTag.$el.offsetLeft - tagAndTagSpacing
          if (beforePrevTagOffsetLeft < $scrollWrapper.scrollLeft) {
            $scrollWrapper.scrollLeft = beforePrevTagOffsetLeft
          }
        }
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.scroll-container {
  white-space: nowrap;
  position: relative;
  overflow: hidden;
  width: 100%;
  ::v-deep {
    .el-scrollbar__bar {
      bottom: 0;
    }
    .el-scrollbar__wrap {
      height: 49px;
    }
  }
}
</style>
