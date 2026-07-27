<script>
import { mapGetters } from "vuex";
import EventBus from "@client/utils/event-bus";
import { getToken } from "@client/utils/auth";

export default {
  name: "Home",
  data() {
    return {
      // 当前选中菜单
      menuIdx: 1,
      routerList: ["Test", "Login", "Cate"],
      level1_idx: 0,
      showCate: false,
      column_1: [],
      column_2: [],
      column_3: [],
      column_4: [],
      app:'',
    };
  },
  computed: {
    ...mapGetters(["name", "cateList"]),
    isLoggedIn() {
      return !!(this.name || getToken());
    },
  },
  mounted() {
    this.app = document.querySelector('#app');
    if (getToken() && !this.name) {
      this.$store.dispatch("user/getInfo").catch(() => {});
    }
    let menuIdx = localStorage.getItem("menuIdx");
    if (!menuIdx) {
      localStorage.setItem("menuIdx", 1);
      menuIdx = 1;
    }
    this.menuIdx = menuIdx - 0;
  },
  beforeRouteUpdate(to, from, next) {
    const idx = this.routerList.findIndex((item) => to.name === item);
    if (idx !== -1) {
      this.menuIdx = idx + 1;
    }
    next();
  },
  watch: {
    showCate(n, o) {
      this.$store.commit("cate/CHANGE_SHOW_CATE", n);
    },
    level1_idx() {
      this.openCateDialog();
    },
  },
  methods: {
    // 退出
    async logout() {
      this.$confirm("确认退出?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(async () => {
        await this.$store.dispatch("user/resetToken").then((_) => {
          this.$router.push("/");
        });
      });

      // this.$router.push(`/login?redirect=${this.$route.fullPath}`)
    },

    goPersonalCenter() {
      if (!getToken()) {
        this.$router.push("/login?redirect=/b/order");
        return;
      }
      this.$router.push("/b/order");
    },

    // 切换menus
    cutMenus(idx) {
      if (this.menuIdx === idx) return;
      this.menuIdx = idx;
      localStorage.setItem("menuIdx", idx);
    },

    // 选中一级
    selectedLevel1(idx) {
      if (this.level1_idx === idx) return;
      this.level1_idx = idx;
    },

    //   拿着一级id进入详情
    enterCateDetail(parentIdx, childIdx = -1) {
      this.showCate = false;
      this.level1_idx = 0;
      const currentPageName = this.$route["name"];
      if (currentPageName === "Cate") {
        EventBus.$emit("reload", {
          parent_idx: parentIdx,
          child_idx: childIdx,
        });
      } else {
        this.menuIdx = 3;
        localStorage.setItem("menuIdx", 3);
        this.$router.push({
          path: "/cate",
          query: { parent_idx: parentIdx, child_idx: childIdx },
        });
      }
    },

    // 进入实验详情
    viewTestDetail(id) {
      this.showCate = false;
      this.level1_idx = 0;
      window.open(location.origin + `/#/test_detail/${id}`);
    },

    openDiscussion() {
      window.open(location.origin + "/#/discussion", "_blank");
    },

    // 打开dialog弹窗
    async openCateDialog() {
      if (!this.showCate) return;
      let level_2 = this.cateList[this.level1_idx]["childList"];
      this.column_1 = level_2[0] ? [level_2[0]] : [];
      this.column_2 = level_2[1] ? [level_2[1]] : [];
      this.column_3 = level_2[2] ? [level_2[2]] : [];
      this.column_4 = level_2[3] ? [level_2[3]] : [];

      if (level_2.length > 4) {
        level_2 = level_2.slice(4);
        for (let i = 0; i < level_2.length; i++) {
          await this.nextTick(level_2[i]);
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
          let column_1_client_height = this.$refs["column-1"].clientHeight,
            column_2_client_height = this.$refs["column-2"].clientHeight,
            column_3_client_height = this.$refs["column-3"].clientHeight,
            column_4_client_height = this.$refs["column-4"].clientHeight;
          let min_idx = this.findMinIndex([
            column_1_client_height,
            column_2_client_height,
            column_3_client_height,
            column_4_client_height,
          ]);

          this[`column_${min_idx + 1}`].push(item);
          resolve();
        });
      });
    },
    // 回到顶部
    backTop() {
      this.app.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    },
  },
};
</script>

<template>
  <div class="container">
    <div class="head">
      <div class="menus">
        <div class="menus-list">
          <router-link class="logo" target="_blank" to="/">
            <img src="@client/static/1.png" alt="" />
          </router-link>
          <a
            v-if="cateList.length"
            @mouseleave="showCate = false"
            @mouseenter="(showCate = true), openCateDialog()"
          >
            测试预约
          </a>
          <router-link target="_blank" to="/companyInt">
            公司介绍
          </router-link>
          <a href="javascript:void(0)" @click.prevent="openDiscussion">讨论</a>
        </div>
      </div>
      <div class="user">
        <router-link to="/login" v-if="!isLoggedIn">登&nbsp;录</router-link>
        <a v-else href="javascript:void(0)" @click.prevent="goPersonalCenter">
          个人中心
        </a>
        <template v-if="name">
          <span style="margin-left: 40px; cursor: auto">{{ `@${name}` }}</span>
          <span class="logout" @click="logout">退出</span>
        </template>
      </div>
    </div>

    <!--   实验分类-->
    <div
      class="test-cate"
      :class="{ 'show-test-cate': showCate, 'hide-test-cate': !showCate }"
      @mouseenter="showCate = true"
      @mouseleave="(showCate = false), (level1_idx = 0)"
    >
      <img class="test-cate-bg" src="@client/static/level_1_bg.jpg" alt="" />
      <div class="cate-main" ref="cate-main">
        <div class="level-1-list">
          <div
            class="level-1-item"
            v-for="(item, idx) in cateList"
            :key="idx"
            :class="{ 'level-1-item-active': level1_idx === idx }"
          >
            <div
              @mouseenter="selectedLevel1(idx)"
              class="level1-cate-name"
              @click="enterCateDetail(idx)"
            >
              <span>{{ item["name"] }}</span>
              <svg-icon icon-class="right" class-name="right-icon-1"></svg-icon>
            </div>
          </div>
        </div>
        <div class="level-2-list">
          <div class="col-1 column" ref="column-1">
            <div
              class="level-2-item"
              v-for="(item, idx) in column_1"
              :key="idx"
            >
              <div
                class="level2-label"
                @click="enterCateDetail(level1_idx, idx)"
              >
                <span>{{ item["name"] }}</span>
                <svg-icon
                  icon-class="right"
                  class-name="right-icon-2"
                ></svg-icon>
              </div>
              <div class="level-3-list">
                <!--查看实验详情-->
                <div
                  class="level-3-item"
                  v-for="(level3, idx2) in item['childList']"
                  :key="idx2"
                >
<!--                  <span>{{ level3["name"] }}</span>-->
                  <img style="width: 100%;" :src="level3.main_photo" />
                  <div class="mask">
                    <el-button type="primary" @click="viewTestDetail(level3['id'])">立即预约</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-2 column" ref="column-2">
            <div
              class="level-2-item"
              v-for="(item, idx) in column_2"
              :key="idx"
            >
              <div
                class="level2-label"
                @click="enterCateDetail(level1_idx, idx)"
              >
                <span>{{ item["name"] }}</span>
                <svg-icon
                  icon-class="right"
                  class-name="right-icon-2"
                ></svg-icon>
              </div>
              <div class="level-3-list">
                <!--查看实验详情-->
                <div
                  class="level-3-item"
                  v-for="(level3, idx2) in item['childList']"
                  :key="idx2"
                >
<!--                  <span>{{ level3["name"] }}</span>-->
                  <img style="width: 100%;" :src="level3.main_photo" />
                  <div class="mask">
                    <el-button type="primary" @click="viewTestDetail(level3['id'])">立即预约</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-3 column" ref="column-3">
            <div
              class="level-2-item"
              v-for="(item, idx) in column_3"
              :key="idx"
            >
              <div
                class="level2-label"
                @click="enterCateDetail(level1_idx, idx)"
              >
                <span>{{ item["name"] }}</span>
                <svg-icon
                  icon-class="right"
                  class-name="right-icon-2"
                ></svg-icon>
              </div>
              <div class="level-3-list">
                <!--查看实验详情-->
                <div
                  class="level-3-item"
                  v-for="(level3, idx2) in item['childList']"
                  :key="idx2"
                >
<!--                  <span>{{ level3["name"] }}</span>-->
                  <img style="width: 100%;" :src="level3.main_photo" />
                  <div class="mask">
                    <el-button type="primary" @click="viewTestDetail(level3['id'])">立即预约</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-4 column" ref="column-4">
            <div
              class="level-2-item"
              v-for="(item, idx) in column_4"
              :key="idx"
            >
              <div
                class="level2-label"
                @click="enterCateDetail(level1_idx, idx)"
              >
                <span>{{ item["name"] }}</span>
                <svg-icon
                  icon-class="right"
                  class-name="right-icon-2"
                ></svg-icon>
              </div>
              <div class="level-3-list">
                <!--查看实验详情-->
                <div
                  class="level-3-item"
                  v-for="(level3, idx2) in item['childList']"
                  :key="idx2"
                >
<!--                  <span>{{ level3["name"] }}</span>-->
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

    <!-- <div class="fixedBox">
      <div>
        <img width="30px" height="30px" src="@client/static/xiaoxi.png" alt="" /><span
          >系统消息</span
        >
      </div>
      <div>
        <img width="30px" height="30px" src="@client/static/kefu.png" alt="" /><span
          >在线客服</span
        >
      </div>
      <div>
        <img width="30px" height="30px" src="@client/static/yijian.png" alt="" /><span
          >意见反馈</span
        >
      </div>
      <div @click="backTop">
        <img
          width="30px"
          height="30px"
          src="@client/static/yijiandaoding.png"
          alt=""
        /><span>一键到顶</span>
      </div>
    </div> -->

    <!--    对于首页的实验列表进行缓存-->
    <router-view v-slot="{ Component }">
      <keep-alive :include="['Test']">
        <component :is="Component" :key="$route.fullPath" />
      </keep-alive>
    </router-view>


  </div>
</template>

<style scoped lang="scss">
.fixedBox {
  position: fixed;
  right: 0;
  top: 40%;
  z-index: 1000;
  div {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 50px;
    height: 50px;
    background-color: #f29800;
    cursor: pointer;
    span {
      display: none;
    }
    img {
      display: block;
    }
  }
  div:hover {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 50px;
    height: 50px;
    color: #fff;
    font-size: 12px;
    background-color: #cecece;
    span {
      display: block;
    }
    img {
      display: none;
    }
  }
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

    &:nth-child(n + 2) {
      margin-left: 70px;
    }
  }
}

.user {
  a,
  span {
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
    background: rgba(233, 99, 2, 0.3);
    border-radius: 10px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: var(--mainColor);
  }

  .level-2-item {
    padding-left: 60px;

    &:nth-child(n + 2) {
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
        &:nth-child(n + 2) {
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
    background: rgba(233, 99, 2, 0.3);
    border-radius: 10px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: var(--mainColor);
  }
}

.level-1-item {
  cursor: pointer;
  font-size: 17px;

  &:nth-child(n + 2) {
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
  transition: all 0.3s;

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
