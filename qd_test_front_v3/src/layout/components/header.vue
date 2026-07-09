<script>
import {mapGetters} from "vuex";
import EventBus from "@/utils/event-bus";
import { defaultAvatarUrl } from "@/utils/oss-image";

export default {
  name: "Header",
  data() {
    return {
      showMiniCode: false,
      showUserMenus: false,
      level1_idx: 0,
      showCate: false,
      column_1: [],
      column_2: [],
      column_3: [],
      column_4: [],
    }
  },
  computed: {
    ...mapGetters(['cateList', 'avatar'])
  },
  watch: {
    level1_idx() {
      this.openCateDialog()
    }
  },
  methods: {
    onAvatarError(e) {
      if (e?.target) e.target.src = defaultAvatarUrl()
    },

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

    changePopup(key, status) {
      if (this[key] === status) return
      this[key] = status
    },

    clickLogo() {
      window.open(location.origin + '/#/home')
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
        window.open(location.origin + `/#/cate?parent_idx=${parentIdx}&child_idx=${childIdx}`)
      }
    },

    // 进入实验详情
    viewTestDetail(id) {
      this.showCate = false
      this.level1_idx = 0
      window.open(location.origin + `/#/test_detail/${id}`)
    },

    openDiscussion() {
      window.open(location.origin + '/#/discussion', '_blank')
    },

    // 选中一级
    selectedLevel1(idx) {
      if (this.level1_idx === idx) return
      this.level1_idx = idx
    },
  }
}
</script>

<template>
  <div class="custom-header">
    <div class="left">
      <div class="logo" @click="clickLogo">
        <img src="@/static/1.png" alt="">
      </div>
      <div class="test-pro" v-if="cateList.length" @mouseleave="showCate = false"
           @mouseenter="showCate = true, openCateDialog()">测试预约
      </div>
      <div class="test-pro">
        <router-link target="_blank" to="/companyInt">
          公司介绍
        </router-link>
      </div>
      <div class="test-pro">
        <a href="javascript:void(0)" @click.prevent="openDiscussion">讨论</a>
      </div>
    </div>

    <div class="right">
      <div class="mini" @mouseenter="changePopup('showMiniCode', true)"
           @mouseleave="changePopup('showMiniCode', false)">
        <img
          src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTggMGE4IDggMCAxMTAgMTZBOCA4IDAgMDE4IDB6bTAgMkM0LjY5MSAyIDIgNC42OTEgMiA4czIuNjkxIDYgNiA2IDYtMi42OTEgNi02LTIuNjkxLTYtNi02em0xLjc1IDEuNzEyYTIuNTM3IDIuNTM3IDAgMDExLjI3NiA0LjczMS43ODcuNzg3IDAgMDEtLjg4MS0xLjNsLjA4OC0uMDZhLjk2Mi45NjIgMCAxMC0xLjQzOS0uOTQ1bC0uMDA3LjExMnYzLjVhMi41MzcgMi41MzcgMCAxMS0zLjgtMi4yMDEuNzg4Ljc4OCAwIDAxLjg3NCAxLjMwNmwtLjA5LjA2YS45NjIuOTYyIDAgMTAxLjQzNS45NDdsLjAwNi0uMTEydi0zLjVBMi41MzggMi41MzggMCAwMTkuNzUgMy43MTJ6IiBmaWxsPSIjMEFCRjVCIi8+PC9zdmc+"
          alt="">
        <span>小程序</span>
        <div class="mini-code" v-show="showMiniCode" @mouseenter="changePopup('showMiniCode', true)"
             @mouseleave="changePopup('showMiniCode', false)">
          <img src="@/static/xcx.jpg" alt="">
          <span>微信扫一扫</span>
        </div>
      </div>
      <div class="user" @mouseenter="changePopup('showUserMenus', true)"
           @mouseleave="changePopup('showUserMenus', false)">
        <img :src="avatar" alt="" @error="onAvatarError">
        <svg-icon icon-class="down" class-name="down"></svg-icon>
        <div class="user-info" v-if="showUserMenus" @mouseenter="changePopup('showUserMenus', true)"
             @mouseleave="changePopup('showUserMenus', false)">
          <div class="logout" @click="logout">退&nbsp;出</div>
        </div>
      </div>
    </div>


    <!--   实验分类-->
    <div class="test-cate" :class="{ 'show-test-cate': showCate, 'hide-test-cate': !showCate }"
         @mouseenter="showCate = true" @mouseleave="showCate = false, level1_idx = 0" v-show="cateList.length">
      <div class="cate-main" ref="cate-main">
        <img class="test-cate-bg" src="@/static/level_1_bg.jpg" alt="">
        <div class="level-1-list">
          <div class="level-1-item" v-for="(item, idx) in cateList" :key="idx"
               :class="{ 'level-1-item-active': level1_idx === idx }">
            <div @mouseenter="selectedLevel1(idx)" class="level1-cate-name" @click="enterCateDetail(idx)">
              <span>{{ item['name'] }}</span>
              <svg-icon icon-class="right" class-name="right-icon-1"></svg-icon>
            </div>
          </div>
        </div>
        <div class="level-2-list">
          <div class="col-1 column" ref="column-1">
            <div class="level-2-item" v-for="(item, idx) in column_1" :key="idx">
              <div class="level2-label" @click="enterCateDetail(level1_idx, idx)">
                <span>{{ item['name'] }}</span>
                <svg-icon icon-class="right" class-name="right-icon-2"></svg-icon>
              </div>
              <div class="level-3-list">
                <!--查看实验详情-->
                <div class="level-3-item" v-for="(level3, idx2) in item['childList']" :key="idx2">
<!--                  <span>{{ level3['name'] }}</span>-->
                  <img style="width: 100%;" :src="level3.main_photo" />
                  <div class="mask">
                    <el-button type="primary" @click="viewTestDetail(level3['id'])">立即预约</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-2 column" ref="column-2">
            <div class="level-2-item" v-for="(item, idx) in column_2" :key="idx">
              <div class="level2-label" @click="enterCateDetail(level1_idx, idx)">
                <span>{{ item['name'] }}</span>
                <svg-icon icon-class="right" class-name="right-icon-2"></svg-icon>
              </div>
              <div class="level-3-list">
                <!--查看实验详情-->
                <div class="level-3-item" v-for="(level3, idx2) in item['childList']" :key="idx2">
<!--                  <span>{{ level3['name'] }}</span>-->
                  <img style="width: 100%;" :src="level3.main_photo" />
                  <div class="mask">
                    <el-button type="primary" @click="viewTestDetail(level3['id'])">立即预约</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-3 column" ref="column-3">
            <div class="level-2-item" v-for="(item, idx) in column_3" :key="idx">
              <div class="level2-label" @click="enterCateDetail(level1_idx, idx)">
                <span>{{ item['name'] }}</span>
                <svg-icon icon-class="right" class-name="right-icon-2"></svg-icon>
              </div>
              <div class="level-3-list">
                <!--查看实验详情-->
                <div class="level-3-item" v-for="(level3, idx2) in item['childList']" :key="idx2">
<!--                  <span>{{ level3['name'] }}</span>-->
                  <img style="width: 100%;" :src="level3.main_photo" />
                  <div class="mask">
                    <el-button type="primary" @click="viewTestDetail(level3['id'])">立即预约</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-4 column" ref="column-4">
            <div class="level-2-item" v-for="(item, idx) in column_4" :key="idx">
              <div class="level2-label" @click="enterCateDetail(level1_idx, idx)">
                <span>{{ item['name'] }}</span>
                <svg-icon icon-class="right" class-name="right-icon-2"></svg-icon>
              </div>
              <div class="level-3-list">
                <!--查看实验详情-->
                <div class="level-3-item" v-for="(level3, idx2) in item['childList']" :key="idx2">
<!--                  <span>{{ level3['name'] }}</span>-->
                  <img style="width: 100%;" :src="level3.main_photo" />
                  <div class="mask">
                    <el-button type="primary" @click="viewTestDetail(level3['id'])">立即预约</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">


.logo, .mini, .user, .test-pro {
  cursor: pointer;
}

.custom-header, .left, .right, .mini, .user {
  display: flex;
  align-items: center;
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


.test-pro {
  height: 50px;
  line-height: 50px;
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
        position: relative;
        &:hover {
          .mask {
            opacity: 1;
          }
        }
        .mask {
          display: flex;
          position: absolute;
          top: 0;
          bottom: 0;
          left: 0;
          right: 0;
          opacity: 0;
          background: rgba(0,0,0,0.3);
          align-items: center;
          justify-content: center;

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
  //background: url("../../static/level_1_bg.png") no-repeat;
  //background-color: #F3F3F3;
  //background-size: 100% 100%;
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
  top: 50px;
  background-color: #fff;
  //height: 636px;
  width: 100%;
  z-index: 1002;
  //padding: 30px 0;
  min-width: 1240px;
  box-shadow: 0 12px 10px #00000012;
  color: #000;
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


.user-info {
  position: absolute;
  right: -40px;
  top: 50px;
  width: 150px;
  background-color: var(--mainColor);
  z-index: 2;
  text-align: center;
  font-size: 15px;


  div {
    height: 45px;
    line-height: 45px;

    &:hover {
      background-color: rgba(255, 255, 255, .3);
    }
  }
}

.user {
  position: relative;
  margin-left: 50px;
  height: 50px;

  .down {
    width: 12px;
    height: 12px;
    fill: #fff;
    margin-left: 5px;
  }

  img {
    width: 33px;
    height: 33px;
    border-radius: 50%;
  }
}


.mini-code {
  position: absolute;
  right: 0;
  top: 50px;
  width: 200px;
  padding: 20px;
  background-color: var(--mainColor);
  z-index: 2044;
  text-align: center;

  img {
    width: 100%;
    height: 100%;
  }

  span {
    display: block;
    margin-top: 15px;
  }
}

.mini {
  position: relative;
  height: 50px;

  span {
    margin-left: 10px;
  }
}

.test-pro {
  margin-left: 50px;
}

.logo {
  display: flex;
  align-items: center;

  img {
    width: 138px;
    height: 35px;
  }
}

.custom-header {
  justify-content: space-between;
  height: 50px;
  width: 100%;
  background-color: var(--mainColor);
  padding: 0 40px;
  //overflow: hidden;
  font-size: 14px;
  color: #fff;
}
</style>
