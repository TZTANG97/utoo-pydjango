<script>
import subTest from "@client/components/subTest.vue";
import {
  getRecommendTestListApi,
  myExpMakeStatusList,
  addFeedBack,
} from "@client/api/test";
import { getSwiperListApi } from "@client/api/index";
import { mapGetters } from "vuex";
import {alterTime} from '@client/utils/index'
import eventBus from "@client/utils/event-bus";
import { loadAMap } from "@client/utils/loadScript";

export default {
  name: "Test",
  components: { subTest },
  data() {
    return {
      testList: [],
      openDialog: false,
      testId: "",
      maxDocumentHeight: 0,
      maxDocumentWidth: 0,
      startHeightList: [],
      recommendList: [],
      flag: true,
      timer: null,
      scroll_num: 0,
      swiperList: [],
      app: "",
      scrollingDisabled: false,
      dialogVisible: false,
      dialog_content: "",
      disableScroll: false,
      current_swiper_idx: 0,
      //   判断数据是否已经获取完。
      isGetData: false,
      onlineServiceShow: false,
      feedback: "",
      feedbackShow: false,
      systemShow: false,
      tableData: [],
      page: 1,
      limit: 5,
      total: 0,
      _homeScrollBound: false,
    };
  },
  mounted() {
    this.app = document.querySelector("#app");
    // 获取网页最大可用高度
    const maxDocumentHeight = document.documentElement.clientHeight;
    this.maxDocumentWidth = document.documentElement.clientWidth;
    this.maxDocumentHeight = maxDocumentHeight - 60;
    this.getRecommendTestList();
    this.getSwiperList();

    eventBus.$on("changeVal", (val) => {
      this.disableScroll = val;
    });

    this.bindHomeScroll();
    this.$nextTick(() => this.initMap());
  },

  beforeUnmount() {
    eventBus.$off("changeVal");
    this.unbindHomeScroll();
  },

  computed: {
    ...mapGetters(["showCate"]),
  },

  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.bindHomeScroll();
    });
  },

  beforeRouteLeave(to, from, next) {
    this.unbindHomeScroll();
    next();
  },

  methods: {
    bindHomeScroll() {
      if (!this.app) {
        this.app = document.querySelector("#app");
      }
      if (!this.app || this._homeScrollBound) return;
      this.app.classList.add("test-app");
      this.app.addEventListener("wheel", this.scrollEvent, { passive: false });
      this._homeScrollBound = true;
    },

    unbindHomeScroll() {
      if (!this.app) {
        this.app = document.querySelector("#app");
      }
      if (!this.app || !this._homeScrollBound) return;
      this.app.removeEventListener("wheel", this.scrollEvent);
      this.app.classList.remove("test-app");
      this._homeScrollBound = false;
      this.scroll_num = 0;
      this.scrollingDisabled = false;
      try {
        this.app.scrollTo({ top: 0 });
      } catch (_) {}
    },

    initMap() {
      if (!document.getElementById("map")) {
        return;
      }
      loadAMap()
        .then((AMap) => {
          const map = new AMap.Map("map", {
            resizeEnable: true,
            center: [121.185252, 31.346588],
            zoom: 13,
          });
          const marker = new AMap.Marker({
            position: map.getCenter(),
            icon: "//a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-red.png",
            anchor: "bottom-center",
            offset: new AMap.Pixel(0, 0),
          });
          marker.setMap(map);
          marker.setTitle("上海市嘉定区恒永路328号联东U谷嘉定国际企业港90幢102室");
          marker.setLabel({
            direction: "top",
            content:
              "<div class='info'>上海市嘉定区恒永路328号联东U谷嘉定国际企业港90幢102室</div>",
          });
        })
        .catch((e) => {
          console.warn("[test] 地图加载失败", e);
        });
    },
    alterTime,
    checkDetail(url = "") {
      if (url) {
        window.open(url);
      }
    },

    // 监听swiper切换
    changedSwiper(e) {
      this.current_swiper_idx = e;
    },

    cutSwiper(k) {
      this.$refs["carousel"][k]();
    },

    // 滚动事件
    scrollEvent(event) {
      if (this.systemShow || this.onlineServiceShow || this.feedbackShow) return;
      // 数据未就绪时仍允许浏览器默认滚动，避免整页被锁死
      if (!this.isGetData) return;

      // dialog打开，三级分类可滚动，菜单打开时 恢复默认滚动
      if (this.dialogVisible || this.disableScroll || this.showCate) return;

      // 全部为false则阻止默认滚动事件
      event.preventDefault && event.preventDefault();

      let delta = event.deltaY || event.wheelDelta || -event.detail;
      if (!this.scrollingDisabled) {
        this.scrollingDisabled = true;
        let allow_scroll = false,
          old_scroll_num = this.scroll_num,
          direction = 1;
        // 向下
        if (delta > 0) {
          // 因为多了个底部，所以加1
          if (this.scroll_num !== this.recommendList.length + 1) {
            this.scroll_num += 1;
            allow_scroll = true;
          }
        } else {
          if (this.scroll_num) {
            this.scroll_num -= 1;
            direction = -1;
            allow_scroll = true;
          }
        }

        if (allow_scroll) {
          let // 当前滚动高度
            current_height = old_scroll_num * this.maxDocumentHeight,
            // 剩余需要滚动的高度
            surplus_height = this.maxDocumentHeight;

          let timer = setInterval(() => {
            let v = surplus_height / 2;
            if (surplus_height > 1) {
              current_height += v * direction;
              surplus_height = v;
            } else {
              current_height += surplus_height * direction;
              surplus_height = 0;
            }

            if (this.app) {
              this.app.scrollTo({
                top: current_height,
                behavior: "smooth",
              });
            }

            if (!surplus_height) {
              clearInterval(timer);
              setTimeout(() => {
                this.scrollingDisabled = false;
              }, 600);
            }
          }, 15);
        } else {
          this.scrollingDisabled = false;
        }
      }
    },

    // 获取轮播图列表
    getSwiperList() {
      getSwiperListApi().then((res) => {
        if (res.res) {
          this.swiperList = res.obj;
        }
      });
    },

    // 获取推荐列表
    getRecommendTestList() {
      getRecommendTestListApi()
        .then((res) => {
          if (res.res) {
            this.recommendList = res.obj || [];
          }
        })
        .catch((e) => {
          console.warn("[test] getRecommendTestList failed", e);
        })
        .finally(() => {
          // 无论成败都放开滚轮，避免刷新后整页被锁死
          this.isGetData = true;
        });
    },

    // 了解更多
    getMoreInfo(id) {
      this.$router.push(`/test_detail/${id}`);
    },
    // 预约实验
    subscribeTest(id) {
      this.testId = id + "";
      this.openDialog = true;
    },

    // 点击查看更多显示dialog
    viewDetail(level, item) {
      item["project_details"]
        ? (item["project_details"] = item["project_details"].replace(
            /<img/g,
            /<img style="width: 100%;"/
          ))
        : "";
      this.dialog_content = item;
      // this.dialogVisible = true
      window.localStorage.setItem("cateDetail", JSON.stringify(item));
      window.open(location.origin + `/#/cateDetail`);
    },

    //   点击移动
    move(idx, direction, len) {
      let ele = this.$refs[`level-2-${idx}`][0],
        current_left = ele.style.left;
      current_left = current_left.replace("px", "") - 0;
      if (!current_left && direction === 1) return;
      if (current_left === (len - 3) * -290 && direction === -1) return;
      ele.style.left = current_left + 290 * direction + "px";
    },

    //   鼠标滑入testlist
    enterTestList(len) {
      if (len > 5) {
        this.disableScroll = true;
      }
    },
    // 在线客服
    onlineService() {
      this.onlineServiceShow = true;
    },
    feedbackFn() {
      let token = this.$store.getters.token;
      if (!token) {
        this.$router.push("/login");
      } else {
        this.feedbackShow = true;
      }
    },
    // 系统消息
    systemFn() {
      let token = this.$store.getters.token;
      if (!token) {
        this.$router.push("/login");
      } else {
          this.myExpMakeStatusListFn()
        this.systemShow = true;
      }

    },
    myExpMakeStatusListFn(){
      myExpMakeStatusList({
        draw: 1,
        start: (this.page - 1) * this.limit,
        length: this.limit,
      }).then((res) => {
        console.log(res,'res')
        this.tableData = res.obj.data
        this.total = res.obj.recordsTotal
      });
    },
    // 条数改变
    handleSizeChange(e) {
      this.limit = e;
      this.myExpMakeStatusListFn();
    },

    // 页数改变
    handleCurrentChange(e) {
      this.page = e;
      this.myExpMakeStatusListFn();
    },
    // 意见反馈
    feedbackShowFn() {
      addFeedBack({ content: this.feedback }).then((res) => {
        if (res.res) {
          this.$message({ type: "success", message: res.resMsg });
          this.feedbackShow = false;
        }
      });
    },
    // 回到顶部
    backTop() {
      this.scroll_num = 0;
      this.scrollingDisabled = false;
      const el = this.app || document.querySelector("#app");
      if (el) {
        el.scrollTo({
          top: 0,
          behavior: "smooth",
        });
      }
    },
  },
};
</script>

<template>
  <div class="home-test" ref="home-test">
    <div class="carousel">
      <el-carousel
        indicator-position="none"
        class="a-swiper"
        trigger="click"
        arrow="never"
        @change="changedSwiper"
        :height="maxDocumentHeight + 'px'"
        :interval="7000"
        ref="carousel"
      >
        <el-carousel-item
          v-for="(item, idx) in swiperList"
          :key="idx"
          @click.native="checkDetail(item.website)"
        >
          <img
            style="width: 100%; height: 100%; cursor: pointer"
            :src="item.picUrl"
            alt=""
          />
<!--          <div-->
<!--            class="swiper-decoration"-->
<!--            :class="-->
<!--              current_swiper_idx === idx ? 'swiper-decoration-active' : ''-->
<!--            "-->
<!--            v-show="item.is_show"-->
<!--          >-->
<!--            <div class="top">-->
<!--              <div class="line"></div>-->
<!--              <div-->
<!--                class="company-name"-->
<!--                :style="{-->
<!--                  color: item.subheadingcolor,-->
<!--                  fontSize: item.subheadingsize + 'px',-->
<!--                }"-->
<!--              >-->
<!--                {{ item.subheading }}-->
<!--              </div>-->
<!--            </div>-->
<!--            <div-->
<!--              class="title"-->
<!--              :style="{-->
<!--                color: item.titlecolor,-->
<!--                fontSize: item.titlesize + 'px',-->
<!--              }"-->
<!--            >-->
<!--              {{ item.title }}-->
<!--            </div>-->
<!--            <div-->
<!--              class="desc"-->
<!--              :style="{-->
<!--                color: item.badescribecolor,-->
<!--                fontSize: item.badescribesize + 'px',-->
<!--              }"-->
<!--            >-->
<!--              {{ item.badescribe }}-->
<!--            </div>-->
<!--          </div>-->
        </el-carousel-item>
        l
      </el-carousel>
      <div class="direction-icon" v-if="!scroll_num">
        <svg-icon
          @click="cutSwiper('prev')"
          icon-class="swiper-left"
          class-name="icon"
        ></svg-icon>
        <svg-icon
          @click="cutSwiper('next')"
          icon-class="swiper-right"
          class-name="icon"
        ></svg-icon>
      </div>
    </div>

    <div class="product-recommend">
      <div
        class="laboratory"
        v-for="(item, idx) in recommendList"
        :key="idx"
        :style="{ height: maxDocumentHeight + 'px' }"
      >
        <div class="l">
          <div class="title">
            {{ item.name }}
          </div>
          <div class="desc">
            {{ item["intro"] }}
          </div>
          <div class="more" @click="viewDetail(1, item)">
            <span>更多</span>
            <svg-icon iconClass="more" class-name="icon"></svg-icon>
          </div>
        </div>
        <div class="r">
          <template v-if="item['childList'].length > 3">
            <svg-icon
              icon-class="test-left"
              @click="move(idx, 1, item['childList'].length)"
              class-name="direction-icon left"
            ></svg-icon>
            <svg-icon
              icon-class="test-right"
              @click="move(idx, -1, item['childList'].length)"
              class-name="direction-icon right"
            ></svg-icon>
          </template>
          <div class="level-2-cate" :ref="`level-2-${idx}`" style="left: 0">
            <div
              class="level-2"
              v-for="(level2, idx2) in item['childList']"
              :key="idx2"
              @mouseenter="enterTestList((level2.childList || []).length)"
              @mouseleave="disableScroll = false"
            >
              <span class="test-name">{{ level2.name }}</span>
              <div class="cover">
                <img :src="level2['main_photo']" :alt="level2.name" />
                <div
                  class="bottom-popup"
                  :class="{
                    'is-empty': !(level2.childList && level2.childList.length),
                  }"
                >
                  <template v-if="level2.childList && level2.childList.length">
                    <div class="title">{{ level2.name }}</div>
                    <div class="partition"></div>
                    <div class="test-list">
                      <div
                        class="test"
                        v-for="(test, tIdx) in level2.childList"
                        :key="tIdx"
                        @click.stop="$router.push(`/test_detail/${test['id']}`)"
                      >
                        <span>{{ test["name"] }}</span>
                        <svg-icon
                          icon-class="more"
                          class-name="test-arrow"
                        ></svg-icon>
                      </div>
                    </div>
                    <div class="more" @click.stop="viewDetail(2, level2)">
                      <span>了解更多</span>
                      <svg-icon iconClass="more" class-name="icon"></svg-icon>
                    </div>
                  </template>
                  <template v-else>
                    <div class="more more-alone" @click.stop="viewDetail(2, level2)">
                      <span>了解更多</span>
                      <svg-icon iconClass="more" class-name="icon"></svg-icon>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div
        class="laboratory particular"
        :style="{
          height: maxDocumentHeight + 'px',
          paddingTop: (maxDocumentHeight - 154 - 430) / 2 + 'px',
        }"
      >
        <div class="footer">
          <div class="contact-way">
            <img src="@client/static/all_name.png" alt="" />
            <div class="address">
              <a>版权信息</a>
              <span>|</span>
              <a>隐私政策</a>
              <span>|</span>
              <a>使用条款</a>
              <span>|</span>
              <a>免责声明</a>
              <span>|</span>
              <a>资质证明</a>
              <!--              地址：上海市嘉定区恒永路328号联东U谷嘉定国际企业港90幢102室-->
            </div>
          </div>
          <div class="line"></div>
          <div class="copyright">
            © 版权所有 愉兔检测科技(上海)有限公司
            <a
              href="https://beian.miit.gov.cn"
              target="_blank"
              style="margin-left: 10px"
            >
              沪ICP备2024071492号-2
            </a>
          </div>
        </div>
        <div
          id="map"
          @mouseenter="disableScroll = true"
          @mouseleave="disableScroll = false"
        ></div>
        <div class="company-info">
          <div class="item-list">
            <div class="info-item">
              <img src="@client/static/phone.png" alt="" />
              <span>咨询：18916012783</span>
            </div>
            <div class="info-item">
              <img src="@client/static/email.png" alt="" />
              <span>邮箱：info@utootest.cn</span>
            </div>
            <div class="info-item">
              <img src="@client/static/post_code.png" alt="" />
              <span>邮编：200000</span>
            </div>
            <div class="info-item">
              <img src="@client/static/address.png" alt="" />
              <span
                >地址：上海市嘉定区恒永路328号联东U谷嘉定国际企业港90幢102室</span
              >
            </div>
          </div>
          <div class="qrcode-list">
            <div class="qrcode">
              <img src="@client/static/gzh.jpg" alt="官方公众号" />
              <div class="label">
                <img src="@client/static/wechat.png" alt="" />
                <span>关注愉兔</span>
              </div>
            </div>
            <div class="qrcode">
              <img src="@client/static/xcx.jpg" alt="官方小程序" />
              <div class="label">
                <img src="@client/static/xcx_icon.png" alt="" />
                <span>扫码下单</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      class="detail-dialog"
      title="系统消息"
      v-model="systemShow"
    >
      <!-- <div style="width: 100%;height: 400px;overflow: auto;"> -->
        <el-table :data="tableData" style="width: 100%;" height="400">
        <el-table-column type="index" label="序号"> </el-table-column>
        <el-table-column prop="addTime" label="日期">
          <template #default="{ row }">
            {{ alterTime(row.addTime) }}
          </template>
        </el-table-column>
        <el-table-column prop="info" label="描述">
        </el-table-column>
      </el-table>

      <div style="display: flex;justify-content: right">
        <el-pagination
          background
          :page-sizes="[5, 10]"
          :page-size="limit"
          :current-page="page"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          layout="total, prev, pager, next, sizes"
          :total="total"
        >
        </el-pagination>
      </div>
      <!-- </div> -->
      <template #footer>
        <el-button
          type="primary"
          style="width: 80px; height: 40px; font-size: 15px"
          size="mini"
          @click="systemShow = false"
          >确 定</el-button
        >
      </template>
    </el-dialog>

    <el-dialog
      class="detail-dialog"
      :title="`分类详情（${dialog_content['name']}）`"
      v-model="dialogVisible"
    >
      <div class="cate-content">
        <div class="cate-main-img">
          <img :src="dialog_content['main_photo']" alt="" />
        </div>
        <div class="jj">简介：{{ dialog_content["intro"] }}</div>
        <div class="project-desc">
          <span>项目介绍：</span>
          <div v-html="dialog_content['project_details']" />
        </div>
      </div>
      <!--      <span slot="footer" class="dialog-footer">-->
      <!--    <el-button @click="dialogVisible = false">取 消</el-button>-->
      <!--    <el-button type="primary" @click="dialogVisible = false">确 定</el-button>-->
      <!--  </span>-->
    </el-dialog>

    <sub-test :open-dialog.sync="openDialog" :test-id="testId" />

    <el-dialog
      class="detail-dialog"
      title="在线客服（8:30 - 18:30）"
      v-model="onlineServiceShow"
      width="660px"
    >
      <div style="width: 100%;text-align: center;font-size: 16px;font-weight: 700">
        <p>在线聊天功能调整中</p>
        <p>可添加企业微信沟通</p>
      </div>
      <div style="width: 630px;display: flex;justify-content: space-between">
        <img width="300" src="@client/static/kefuQRcode.png" alt="" />
        <img width="300" src="@client/static/kefuQRcode2.png" alt="" />
      </div>
    </el-dialog>

    <el-dialog
      width="30%"
      :close-on-click-modal="false"
      style="height: 380px !important"
      title="意见反馈"
      v-model="feedbackShow"
    >
      <div>
        <el-input
          type="textarea"
          v-model="feedback"
          placeholder="请输入意见反馈"
        ></el-input>
      </div>
      <div style="text-align: right; margin-top: 40px">
        <el-button
          style="width: 80px; height: 40px; font-size: 16px"
          size="mini"
          type="primary"
          @click="feedbackShowFn"
          >确定</el-button
        >
        <el-button
          style="width: 80px; height: 40px; font-size: 16px"
          size="mini"
          @click="feedbackShow = false"
          >取消</el-button
        >
      </div>
    </el-dialog>

    <div class="fixedBox">
      <div @click="systemFn">
        <img width="30px" height="30px" src="@client/static/xiaoxi.png" alt="" /><span
          >系统消息</span
        >
      </div>
      <div @click="onlineService">
        <img width="30px" height="30px" src="@client/static/kefu.png" alt="" /><span
          >在线客服</span
        >
      </div>
      <div @click="feedbackFn">
        <img width="30px" height="30px" src="@client/static/yijian.png" alt="" /><span
          >意见反馈</span
        >
      </div>
      <div @click="backTop" :class="{ 'is-disabled': !scroll_num }">
        <img
          width="30px"
          height="30px"
          src="@client/static/yijiandaoding.png"
          alt=""
        /><span>一键到顶</span>
      </div>
    </div>

    <!-- <div class="back-top" v-if="scroll_num" @click="backTop">
      <i class="el-icon-caret-top"></i>
    </div> -->
  </div>
</template>

<style>
.amap-logo,
.amap-copyright {
  display: none !important;
}

.amap-icon img {
  width: 25px;
  height: 34px;
}

.amap-marker-label {
  border: 0;
  padding: 7px;
  border-radius: 4px;
  white-space: normal;
}

.info {
  width: 300px;
  font-size: 14px;
  line-height: 1.2;
}
</style>

<style scoped lang="scss">
// /deep/ .el-dialog {
//   width: 900px;
//   height: 700px;

//   .el-dialog__body {
//     height: 90%;
//   }
// }

// /deep/ .el-carousel__arrow {
//   //display: none !important;
// }
</style>

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
    user-select: none;
    span {
      display: none;
    }
    img {
      display: block;
      pointer-events: none;
    }
    &.is-disabled {
      opacity: 0.45;
      cursor: default;
    }
  }
  div:hover:not(.is-disabled) {
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
.back-top {
  position: fixed;
  right: 40px;
  bottom: 60px;
  border-radius: 50%;
  z-index: 2045;
  background-color: #fff;
  box-shadow: 0 0 10px var(--mainColor);
  padding: 10px;
  font-size: 30px;
  color: var(--mainColor);
  cursor: pointer;
}

.particular {
  align-items: normal !important;
  position: relative;
  width: 100% !important;
  padding-left: calc((100% - 1240px) / 2);
  padding-right: calc((100% - 1240px) / 2);
  background: url("../../static/footer_bg.png") no-repeat 100% 100%;

  .company-info {
    height: 430px;

    .qrcode-list {
      display: flex;
      justify-content: space-between;
    }

    .qrcode {
      display: inline-block;

      .label {
        font-size: 15px;

        img {
          width: 22px;
          height: 22px;
          vertical-align: middle;
          margin-right: 10px;
        }
      }
    }

    .label {
      text-align: center;
      color: #555757;
      margin-top: 15px;
    }

    .item-list {
      padding-bottom: 30px;
      border-bottom: 3px solid #555757;
    }

    .info-item {
      color: #555757;

      &:nth-child(n + 2) {
        margin-top: 7px;
      }
    }

    .info-item {
      line-height: 2;

      span {
        display: inline-block;
        max-width: 388px;
        vertical-align: top;
      }

      img {
        width: 20px;
        height: 20px;
        margin-right: 10px;
        vertical-align: middle;
      }
    }

    .qrcode > img {
      width: 122px;
      height: 125px;
      vertical-align: top;
      margin-top: 45px;
    }
  }

  #map {
    width: 660px;
    height: 430px;
  }
}

.cate-content {
  overflow-y: scroll;
  height: 570px;

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

  .project-desc {
    margin-top: 30px;
  }

  .jj {
    margin-top: 20px;
    line-height: 1.7;
  }

  .cate-main-img {
    text-align: center;

    img {
      max-width: 300px;
    }
  }
}

//.level-2-active {
//  img {
//    transform: scale(1.3);
//    transition: all .5s;
//  }
//}
.laboratory {
  display: flex;
  width: 1240px;
  margin: auto;
  justify-content: space-between;
  align-items: center;

  .r {
    position: relative;
    width: 870px;
    height: 530px;
    overflow: hidden;

    .direction-icon {
      position: absolute;
      fill: rgba(0, 0, 0, 0.7);
      font-size: 35px;
      top: 50%;
      border-radius: 50%;
      z-index: 6;
      transform: translateY(-50%);
      cursor: pointer;
    }

    .left {
      left: 0;
    }

    .right {
      right: 0;
    }

    .level-2-cate {
      position: absolute;
      left: 0;
      white-space: nowrap;
      transition: all 0.3s;

      .level-2 {
        display: inline-block;
        position: relative;
        width: 290px;
        margin-right: 0;
        vertical-align: top;
        background-size: 100% 100%;
        overflow: hidden;
        border-radius: 8px;

        .cover {
          position: relative;
          height: 500px;
          overflow: hidden;
          border-radius: 8px;
          background: #f3f3f3;
        }

        &:hover {
          img {
            transform: scale(1.06);
          }

          .bottom-popup {
            transform: translateY(0);
            opacity: 1;
            pointer-events: auto;
          }
        }

        .bottom-popup {
          position: absolute;
          left: 0;
          right: 0;
          bottom: 0;
          width: 100%;
          max-height: 62%;
          min-height: 88px;
          background: linear-gradient(
            180deg,
            rgba(226, 120, 12, 0.92) 0%,
            rgba(214, 98, 0, 0.98) 100%
          );
          backdrop-filter: blur(2px);
          transition: transform 0.28s ease, opacity 0.28s ease;
          box-sizing: border-box;
          padding: 16px 16px 14px;
          transform: translateY(100%);
          opacity: 0;
          pointer-events: none;
          display: flex;
          flex-direction: column;

          &.is-empty {
            max-height: none;
            min-height: 0;
            height: auto;
            padding: 14px 16px;
          }

          .more {
            margin-top: 10px;
            font-size: 13px;
            color: #fff;
            cursor: pointer;
            flex-shrink: 0;

            .icon {
              vertical-align: middle;
              margin-left: 4px;
              fill: #fff;
              width: 14px;
              height: 14px;
            }

            &:hover {
              opacity: 0.9;
            }
          }

          .more-alone {
            margin-top: 0;
            text-align: center;
            font-size: 14px;
          }

          .test-list {
            margin-top: 12px;
            font-size: 13px;
            color: hsla(0, 0%, 100%, 0.88);
            line-height: 1.9;
            cursor: pointer;
            flex: 1;
            min-height: 0;
            max-height: 140px;
            overflow-y: auto;
            overscroll-behavior: contain;

            .test {
              display: flex;
              align-items: center;
              justify-content: space-between;
              gap: 8px;
              padding: 2px 0;
              width: 100%;
              box-sizing: border-box;

              span {
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                flex: 1;
                min-width: 0;
              }

              .test-arrow {
                flex-shrink: 0;
                fill: hsla(0, 0%, 100%, 0.75);
                width: 12px;
                height: 12px;
              }
            }

            &::-webkit-scrollbar {
              width: 4px;
            }

            &::-webkit-scrollbar-thumb {
              background: hsla(0, 0%, 100%, 0.45);
              border-radius: 4px;
            }

            &::-webkit-scrollbar-thumb:hover {
              background: hsla(0, 0%, 100%, 0.75);
            }

            .test:hover {
              color: #fff;

              .test-arrow {
                fill: #fff;
              }
            }
          }

          .title {
            font-size: 17px;
            font-weight: 600;
            color: #fff;
            line-height: 1.3;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .partition {
            width: 36px;
            height: 2px;
            background-color: hsla(0, 0%, 100%, 0.65);
            margin-top: 10px;
            border-radius: 1px;
          }
        }

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: transform 0.45s ease;
        }

        .test-name {
          display: block;
          height: 30px;
          line-height: 30px;
          margin-bottom: 8px;
          color: #222;
          font-size: 18px;
          font-weight: 600;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          padding: 0 2px;
        }
      }
    }
  }

  .l {
    position: relative;
    width: 330px;
    height: 500px;
    box-sizing: border-box;

    .more {
      text-align: right;
      cursor: pointer;

      .icon {
        width: 15px;
        height: 15px;
        vertical-align: bottom;
        margin-left: 5px;
      }
    }

    .desc,
    .more {
      font-size: 15px;
      color: #666;
    }

    .desc {
      margin: 30px 0;
      text-indent: 30px;
      line-height: 2;
      max-height: 275px;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .title {
      font-size: 40px;
      margin-top: 50px;
    }
  }
}

.swiper-decoration-active {
  left: 230px !important;
  opacity: 1 !important;
  transform: skewX(0) !important;
  font-style: normal !important;
}

.carousel {
  margin-top: 60px;

  .a-swiper {
    position: relative;

    .swiper-decoration {
      width: 700px;
      height: 212px;
      position: absolute;
      left: 1100px;
      top: 200px;
      z-index: 10;
      opacity: 0;
      transition: all 1.3s ease-in;
      font-style: italic;
      transform: skewX(-45deg);
      color: #fff;

      .top {
        display: flex;
        align-items: center;

        .line {
          width: 200px;
          height: 8px;
          background-color: var(--mainColor);
        }

        .company-name {
          margin-left: 20px;
          font-weight: bold;
        }
      }

      .title {
        font-size: 80px;
        font-weight: bold;
        word-break: break-word;
      }

      .desc {
        font-size: 18px;
        margin-top: 20px;
      }
    }
  }

  .direction-icon {
    display: flex;
    justify-content: space-between;
    width: 100%;
    padding: 0 80px 0 30px;
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    z-index: 2;

    .icon {
      font-size: 30px;
      fill: #ffffff;
      transition: all 0.2s;
      cursor: pointer;

      &:hover {
        fill: var(--mainColor);
      }

      &:nth-child(2) {
        margin-left: 10px;
      }
    }
  }
}

.empty {
  background-color: #f8f4ff;
}

.footer,
.swiper-list {
  min-width: 1240px;
}

.el-button--default {
  margin-left: 18px;
}

.el-button {
  width: 160px;
  height: 54px;
  font-size: 18px;
}

.footer {
  position: absolute;
  background-color: var(--mainColor);
  font-size: 16px;
  color: #fff;
  left: 0;
  bottom: 0;
  width: 100%;
  z-index: 3;
  height: 154px;
  padding: 15px calc((100% - 1240px) / 2);

  .contact-way {
    display: flex;
    align-items: center;
    justify-content: space-between;

    div:nth-child(n + 2) {
      margin-left: 40px;
    }

    img {
      height: 54px;
      width: 350px;
    }

    .address > span {
      margin: 0 10px;
    }
  }

  .line {
    height: 1px;
    background-color: #e9e9e9;
    margin: 24px 0;
  }

  .copyright {
    text-align: center;
  }
}

//.btns {
//  display: flex;
//  margin-top: 32px;
//  font-size: 16px;
//
//  div {
//    width: 160px;
//    height: 54px;
//    text-align: center;
//    line-height: 54px;
//    cursor: pointer;
//  }
//}
//
//.swiper-list {
//  margin-top: 60px;
//  overflow: hidden;
//  min-width: 1240px;
//
//  .swiper-item {
//    display: flex;
//    align-items: center;
//    justify-content: center;
//    background-color: #F8F4FF;
//
//    .test-info {
//
//      .test-name, .test-facility-name {
//        width: 311px;
//      }
//
//      .test-name {
//        font-size: 36px;
//        font-weight: bold;
//      }
//
//      .test-facility-name {
//        margin-top: 26px;
//        font-size: 24px;
//        font-weight: bold;
//      }
//
//    }
//  }
//
//  img {
//    max-width: 800px;
//    max-height: 800px;
//    margin-left: 60px;
//  }
//}
</style>
