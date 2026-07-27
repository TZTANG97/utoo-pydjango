<script>
import {mapGetters} from "vuex";
import discussionList from "@client/views/discussion/components/list.vue";
import layoutHeader from "@client/layout/components/header.vue";
import {
  commenttreebulder
} from "@client/api/discussion"
export default {
  components: {
    discussionList,
    layoutHeader
  },
  data() {
    return {
      listSort: localStorage.getItem('discussionListSort') || 'addTime_desc',
      sortOptions: [
        { label: '最新发布', value: 'addTime_desc' },
        { label: '最早发布', value: 'addTime_asc' },
        { label: '最近更新', value: 'updateTime_desc' },
        { label: '评论最多', value: 'commentCount_desc' },
      ],
      // 当前选中菜单
      menuIdx: 1,
      routerList: ['Test', 'Login', 'Cate'],
      level1_idx: 0,
      showCate: false,
      column_1: [],
      column_2: [],
      column_3: [],
      column_4: []
    }
  },
  computed: {
    ...mapGetters(['name', 'cateList'])
  },
  mounted() {
    let menuIdx = localStorage.getItem('menuIdx');
    if (!menuIdx) {
      localStorage.setItem('menuIdx', 1)
      menuIdx = 1
    }
    this.menuIdx = menuIdx - 0;
  },
  beforeRouteUpdate(to, from, next) {
    const idx = this.routerList.findIndex(item => to.name === item)
    if (idx !== -1) {
      this.menuIdx = idx + 1
    }
    next()
  },
  watch: {
    showCate(n, o) {
      this.$store.commit('cate/CHANGE_SHOW_CATE', n)
    },
    level1_idx() {
      this.openCateDialog()
    }
  },
  methods: {
// 退出
    async logout() {
      this.$confirm('确认退出?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        await this.$store.dispatch('user/resetToken').then(_ => {
          this.$router.push('/')
        })
      })

      // this.$router.push(`/login?redirect=${this.$route.fullPath}`)
    },

    onListSortChange(val) {
      this.listSort = val;
      localStorage.setItem('discussionListSort', val);
    },

    // 切换menus
    cutMenus(idx) {
      if (this.menuIdx === idx) return
      this.menuIdx = idx
      localStorage.setItem('menuIdx', idx)
    },

    // 选中一级
    selectedLevel1(idx) {
      if (this.level1_idx === idx) return
      this.level1_idx = idx
    },

    //   拿着一级id进入详情
    enterCateDetail(parentIdx, childIdx = -1) {
      this.showCate = false
      this.level1_idx = 0
      const currentPageName = this.$route['name']
      if (currentPageName === 'Cate') {
        EventBus.$emit('reload', {parent_idx: parentIdx, child_idx: childIdx})
      } else {
        this.menuIdx = 3
        localStorage.setItem('menuIdx', 3)
        this.$router.push({path: '/cate', query: {parent_idx: parentIdx, child_idx: childIdx}})
      }
    },

    // 进入实验详情
    viewTestDetail(id) {
      this.showCate = false
      this.level1_idx = 0
      window.open(location.origin + `/#/test_detail/${id}`)
    },

    // 打开dialog弹窗
    async openCateDialog() {
      if (!this.showCate) return
      let level_2 = this.cateList[this.level1_idx]['childList']
      this.column_1 = level_2[0] ? [level_2[0]] : []
      this.column_2 = level_2[1] ? [level_2[1]] : []
      this.column_3 = level_2[2] ? [level_2[2]] : []
      this.column_4 = level_2[3] ? [level_2[3]] : []

      if (level_2.length > 4) {
        level_2 = level_2.slice(4)
        for (let i = 0; i < level_2.length; i++) {
          await this.nextTick(level_2[i])
        }
      }
    },

    // 找最小
    findMinIndex(arr) {
      if (arr.length === 0) {
        return -1; // 如果数组为空，返回 -1 表示未找到
      }

      let minIndex = 0; // 假设第一个元素是最小值的索引
      let minValue = arr[0]; // 假设第一个元素是最小值

      for (let i = 1; i < arr.length; i++) {
        if (arr[i] < minValue) {
          minValue = arr[i]; // 更新最小值
          minIndex = i; // 更新最小值的索引
        }
      }

      return minIndex;
    },

    nextTick(item) {
      return new Promise((resolve) => {
        this.$nextTick(() => {
          let column_1_client_height = this.$refs['column-1'].clientHeight,
            column_2_client_height = this.$refs['column-2'].clientHeight,
            column_3_client_height = this.$refs['column-3'].clientHeight,
            column_4_client_height = this.$refs['column-4'].clientHeight;
          let min_idx = this.findMinIndex([column_1_client_height, column_2_client_height, column_3_client_height, column_4_client_height])

          this[`column_${min_idx + 1}`].push(item)
          resolve()
        })
      })
    },
  }
}

</script>

<template>
  <div class="discussion-page">
    <div class="discussion-shell">
      <header class="page-header">
        <div class="page-header__text">
          <h1 class="page-title">讨论社区</h1>
          <p class="page-desc">分享检测经验，交流行业观点与问题</p>
        </div>
      </header>
      <div class="list-toolbar">
        <span class="list-toolbar__label">排序</span>
        <el-select
          :model-value="listSort"
          class="list-toolbar__select"
          placeholder="排序方式"
          @update:model-value="onListSortChange"
        >
          <el-option
            v-for="opt in sortOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </div>
      <discussionList :sort-by="listSort" />
    </div>
  </div>
</template>


<style scoped lang="scss">
.head {
  display: flex;
  justify-content: space-between;
  min-width: 1240px;
  position: fixed;
  padding: 0 100px;
  left: 0;
  top: 0;
  width: 100%;
  height: 60px;
  background-color: var(--mainColor);
  line-height: 60px;
  color: #fff;
  font-size: 16px;
  z-index: 9;
}

.logo {
  img {
    height: 44px;
    width: 185px;
    vertical-align: middle;
    cursor: pointer;
  }
}

.menus-list {
  a {
    display: inline-block;
    height: 60px;

    &:nth-child(n+2) {
      margin-left: 70px;
    }
  }
}

.user {
  a, span {
    display: inline-block;
    height: 60px;
    margin-left: 30px;
    cursor: pointer;
  }
}
.discussion-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f6f8 0%, #eef0f4 100%);
  padding: 88px 20px 48px;
}

.discussion-shell {
  max-width: 880px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
  padding: 24px 28px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--mainColor) 0%, #ff8c42 100%);
  color: #fff;
  box-shadow: 0 8px 24px rgba(233, 99, 2, 0.22);
}

.page-title {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.page-desc {
  margin: 8px 0 0;
  font-size: 14px;
  opacity: 0.92;
}

.list-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 14px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.list-toolbar__label {
  font-size: 14px;
  color: #595959;
}

.list-toolbar__select {
  width: 160px;
}

</style>

<style scoped lang="scss">

.logo {
  img {
    height: 44px;
    width: 185px;
    vertical-align: middle;
    cursor: pointer;
  }
}

.menus-list {
  a {
    display: inline-block;
    height: 60px;

    &:nth-child(n+2) {
      margin-left: 70px;
    }
  }
}

.user {
  a, span {
    display: inline-block;
    height: 60px;
    margin-left: 30px;
    cursor: pointer;
  }
}

.head {
  display: flex;
  justify-content: space-between;
  min-width: 1240px;
  position: fixed;
  padding: 0 100px;
  left: 0;
  top: 0;
  width: 100%;
  height: 60px;
  background-color: var(--mainColor);
  line-height: 60px;
  color: #fff;
  font-size: 16px;
  z-index: 9;
}

.container {
  overflow: hidden;
}

.show-test-cate {
  height: 636px !important;
  padding: 30px 0;
  opacity: 1;
}

.hide-test-cate {
  height: 0 !important;
  opacity: 0;
}


.level-1-item-active {
  color: var(--mainColor);
  font-size: 20px !important;
  //.level1-cate-name {
  //  span::after {
  //    width: 100% !important;
  //  }
  //}
}


.level-2-list {
  position: relative;
  width: 83%;
  overflow-y: scroll;
  box-sizing: border-box;
  height: 100%;

  .column {
    position: absolute;
    top: 0;
    left: 0;
    width: 25%;
  }

  .col-2 {
    left: 25%;
  }

  .col-3 {
    left: 50%;
  }

  .col-4 {
    left: 75%;
  }

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(233, 99, 2, .3);
    border-radius: 10px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: var(--mainColor);
  }

  .level-2-item {
    padding-left: 60px;

    &:nth-child(n+2) {
      margin-top: 50px;
    }

    .level2-label {
      font-weight: 600;
      font-size: 18px;
      cursor: pointer;

      .right-icon-2 {
        stroke: #000;
        stroke-width: 90;
      }

      &:hover {
        color: var(--mainColor);

        .right-icon-2 {
          stroke: var(--mainColor);
        }
      }
    }


    .level-3-list {
      margin-top: 25px;

      .level-3-item {
        font-size: 15px;
        cursor: pointer;
        width: 230px;
        text-overflow: ellipsis;
        white-space: nowrap;
        overflow: hidden;
        color: #535353;

        &:hover {
          color: var(--mainColor);
        }

        &:nth-child(n+2) {
          margin-top: 18px;
        }
      }
    }
  }
}

.level-1-list {
  position: relative;
  z-index: 2;
  width: 17%;
  height: 100%;
  //border-right: 1px solid rgba(61, 61, 61, .15);
  box-sizing: border-box;
  overflow-y: scroll;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(233, 99, 2, .3);
    border-radius: 10px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: var(--mainColor);
  }
}

.level-1-item {
  cursor: pointer;
  font-size: 17px;

  &:nth-child(n+2) {
    margin-top: 30px;
  }

  .level1-cate-name {
    display: -webkit-box;
    vertical-align: middle;
    overflow: hidden;
    -webkit-box-orient: vertical;
    text-overflow: ellipsis;
    -webkit-line-clamp: 2;
    max-width: 80%;
    line-height: 1.2;
    margin: auto;

    //span {
    //  position: relative;
    //
    //  &::after {
    //    display: block;
    //    content: '';
    //    position: absolute;
    //    left: 0;
    //    bottom: 0;
    //    width: 0;
    //    height: 2px;
    //    background-color: var(--mainColor);
    //    transition: width .3s;
    //  }
    //}
  }
}


.test-cate {
  position: fixed;
  left: 0;
  top: 60px;
  background-color: #fff;
  height: 636px;
  width: 100%;
  z-index: 99;
  min-width: 1240px;
  max-width: 100%;
  box-shadow: 0 12px 10px #00000012;
  transition: all .3s;

  .test-cate-bg {
    position: absolute;
    left: 0;
    top: 0;
    width: 17%;
    height: 100%;
  }

  .cate-main {
    height: 100%;
    display: flex;
  }

  .cate-header {
    display: flex;

    .el-input {
      width: 300px;
    }

    .el-button {
      margin-left: 20px;
      width: 100px;
      font-size: 15px;
    }
  }
}

</style>
