<script>
import {mapGetters} from "vuex";
import EventBus from "@/utils/event-bus";
import {getTestListAPi} from '@/api/test'

export default {
  name: "Cate",
  data() {
    return {
      level_1_idx: 0,
      level_2_idx: 0,
      level2_menus_list: [],
      testList: [],
      keyWord: '',
      // 是否正在请求中....
      loading: false,
      page: 1,
      isRefresh: true,
      classId: '',
      scroll: false
    }
  },
  computed: {
    ...mapGetters(['cateList'])
  },
  mounted() {

    document.body.classList.add('body-bg')

    this.reloadPage(this.$route.query)
    this.searchTest()
    EventBus.$on('reload', params => {
      this.reloadPage(params)
      this.searchTest()
    })
    window.addEventListener('scroll', this.listenScroll)
  },

  beforeDestroy() {
    window.removeEventListener('scroll', this.listenScroll);
    EventBus.$off('reload');
    document.body.classList.remove('body-bg')
  },

  filters: {
    sliceIntro(intro) {
      if(!intro) return ''
      if (intro.length <= 46) {
        return intro
      } else {
        return intro.slice(0, 46) + '...'
      }
    },
  },

  methods: {

    // 监听滚动
    listenScroll() {
      this.scrollBottom()
      if (document.documentElement.scrollTop >= 100) {
        this.scroll = true
      } else {
        this.scroll = false
      }
    },


    // 获取实验列表
    getTestList() {
      this.loading = true
      getTestListAPi({
        classId: this.classId,
        keyWord: this.keyWord,
        draw: 1,
        start: (this.page - 1) * 10,
        length: 10
      }).then(res => {
        if (res.res) {
          if (res.obj['data'].length !== 10) {
            this.isRefresh = false
          } else {
            this.page++;
          }
          this.testList = [...this.testList, ...res.obj['data']]
        } else {
          this.$notify.error({
            title: '提示',
            message: res.resMsg,
          })
        }
      }).finally(_ => {
        this.loading = false
      })
    },


    //   根据参数调整页面内容
    reloadPage(params) {
      const {parent_idx, child_idx} = params
      if (!isNaN(parent_idx) && parent_idx > -1) {
        this.level2_menus_list = this.cateList[parent_idx]['childList']
        this.level_1_idx = parent_idx - 0 + 1
      }

      if (!isNaN(child_idx) && child_idx > -1) {
        this.level_2_idx = child_idx - 0 + 1
      }


      if (this.level_2_idx) {
        this.classId = this.level2_menus_list[this.level_2_idx - 1]['id']
      } else if (this.level_1_idx) {
        this.classId = this.cateList[this.level_1_idx - 1]['id']
      } else {
        this.classId = ''
      }
    },


    //   更改一级分类
    changeLevel1(idx) {
      if (this.loading || this.level_1_idx === idx) return
      this.level_1_idx = idx
      this.level_2_idx = 0
      if (!idx) {
        this.classId = ''
        this.level2_menus_list = []
        this.cateList.forEach(item => {
          item['childList'].forEach(item2 => {
            this.level2_menus_list.push(item2)
          })
        })
      } else {
        this.classId = this.cateList[idx - 1]['id']
        this.level2_menus_list = this.cateList[this.level_1_idx - 1]['childList']
      }

      this.page = 1
      this.isRefresh = true
      this.testList = []
      this.searchTest()
    },

    // 更改二级分类
    changeLevel2(idx) {
      if (this.loading || this.level_2_idx === idx) return
      this.level_2_idx = idx
      if (idx) {
        this.classId = this.level2_menus_list[idx - 1]['id']
      } else if (this.level_1_idx) {
        this.classId = this.cateList[this.level_1_idx - 1]['id']
      } else {
        this.classId = ''
      }
      this.page = 1
      this.isRefresh = true
      this.testList = []
      this.searchTest()
    },

    // 回到顶部
    getTop() {
      document.documentElement.scrollTop = 0
    },

    searchTest() {
      this.page = 1
      this.isRefresh = true
      this.testList = []
      this.getTestList()
    },


    // 监听触底
    scrollBottom() {
      let scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
      let clientHeight = document.documentElement.clientHeight;
      let scrollHeight = document.documentElement.scrollHeight;
      if (scrollTop + clientHeight >= (scrollHeight- 50)) {
        if (this.isRefresh && !this.loading) {
          this.getTestList()
        }
      }
    },

    //   查看实验详情
    viewTestDetail(id) {
      this.$router.push(`/test_detail/${id}`)
    },
  }
}
</script>

<template>
  <div class="cate" v-if="cateList.length">
    <div class="table-options">
      <div class="level-1 level">
        <div class="level-1-list level-list">
          <div class="level-1-name level-name" :class="{ 'level-name-active': !level_1_idx, 'disabled-click': loading }"
               @click="changeLevel1(0)">
            全部
          </div>
          <div class="level-1-name level-name" v-for="(item ,idx) in cateList" :key="idx"
               :class="{ 'level-name-active': level_1_idx === idx + 1, 'disabled-click': loading }"
               @click="changeLevel1(idx + 1)">
            {{ item['name'] }}
          </div>
        </div>
      </div>

      <div class="level-2 level">
        <div class="level-2-list level-list">
          <div class="level-2-name level-name" :class="{ 'level-name-active': !level_2_idx, 'disabled-click': loading }"
               @click="changeLevel2(0)">
            全部
          </div>
          <div class="level-2-name level-name" v-for="(item ,idx) in level2_menus_list" :key="idx"
               :class="{ 'level-name-active': level_2_idx === idx + 1, 'disabled-click': loading }"
               @click="changeLevel2(idx + 1)">
            {{ item['name'] }}
          </div>
        </div>
      </div>
    </div>

    <!--    关键字检索-->
    <div class="search">
      <el-input placeholder="输入关键字进行检索" v-model="keyWord" maxlength="30"></el-input>
      <el-button type="primary" @click="searchTest" :loading="loading">搜索</el-button>
    </div>


    <!--实验列表-->
    <div class="test-list">
      <el-tooltip class="item" effect="light" :content="item['name']" placement="right-start"
                  v-for="(item, idx) in testList" :key="idx">
        <div class="test-item" @click="viewTestDetail(item['id'])">
          <img class="test-main-img"
               :src="item['main_photo']" alt="">
          <div class="test-name">
            {{ item['name'] }}
          </div>
          <div class="test-desc">
            {{ item['intro'] | sliceIntro }}
          </div>
        </div>
      </el-tooltip>
    </div>


    <div class="empty" v-if="!testList.length && !isRefresh">
      暂无数据
    </div>


    <!-- 底部加载-->
    <div class="loading-data">
      <span v-if="!isRefresh && testList.length">没有更多数据了~</span>
      <span v-if="loading">拼命加载中...</span>
    </div>


    <!--    手写一个回到顶部-->
    <div class="get-top" v-show="scroll" @click="getTop">
      <svg-icon class-name="top-svg" icon-class="top"></svg-icon>
    </div>

  </div>
</template>

<style scoped lang="scss">
.empty {
  text-align: center;
  padding: 50px;
  color: #959595;
  font-size: 30px;
}

.loading-data {
  margin: 30px 0;
  text-align: center;
  color: #959595;
}

.get-top {
  display: flex;
  position: fixed;
  justify-content: center;
  align-items: center;
  right: 40px;
  bottom: 60px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #fff;
  box-shadow: 0 15px 30px rgba(0, 0, 0, .1);
  cursor: pointer;

  .top-svg {
    font-size: 35px;
  }
}


.disabled-click {
  cursor: not-allowed;
}


.test-list {
  display: flex;
  flex-wrap: wrap;
  width: 1240px;
  margin: 40px auto;

  .test-item {
    width: 295px;
    height: 456px;
    background-color: #fff;
    padding: 15px;
    transition: all .3s;
    cursor: pointer;

    &:hover {
      box-shadow: 0 15px 30px rgba(0, 0, 0, .15);
      transform: translate3d(0, -2px, 0);
    }

    .test-name {
      margin-top: 10px;
      text-align: center;
    }

    .test-desc {
      margin-top: 10px;
      line-height: 1.5;
      color: #b0b0b0;
      font-size: 15px;
      padding: 0 13px;
    }

    img {
      width: 100%;
      height: 300px;
    }

    &:nth-child(4n+2) {
      margin-left: 20px;
    }

    &:nth-child(4n+3) {
      margin-left: 20px;
    }

    &:nth-child(4n+4) {
      margin-left: 20px;
    }

    &:nth-child(n+5) {
      margin-top: 20px;
    }
  }
}

.search {
  width: 1240px;
  margin: 20px auto;

  .el-input {
    width: 260px;
  }

  .el-button {
    margin-left: 20px;
    width: 90px;
  }
}

.level-name-active {
  color: var(--mainColor) !important;
  font-weight: 600;
}

.table-options {
  width: 1240px;
  background: #fafbfc;
  border: 1px solid #d9e0e8;
  margin: 120px auto 0;

  .level {
    border-bottom: 1px solid #d9e0e8;

    .level-list {
      display: flex;
      flex-wrap: wrap;
      font-size: 18px;
      box-sizing: border-box;
      padding: 20px;

      .level-name {
        padding: 20px 15px;
        color: #666;
        cursor: pointer;
      }
    }
  }
}

.cate {
  overflow: hidden;
}
</style>
