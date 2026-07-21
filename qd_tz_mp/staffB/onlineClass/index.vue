<template>
    <view class="content">
        <view class="u-wrap">
            <view class="search-box">
                <view class="my-search-input" @click="searchfn">
                    <u-icon color="#95989E" name="search" size="28"></u-icon>
                    <text>请输入产品名称</text>
                </view>
            </view>
            <view class="u-menu-wrap">
                <scroll-view scroll-y scroll-with-animation class="u-tab-view menu-scroll-view" :scroll-top="scrollTop">
                    <!-- 选择仓库 -->
                    <view class="u-tab-item selectBox" v-if="userInfo.wx_nickname == 'admin'">
                        <picker range-key="name" mode="selector" @change="bindPickerChange" :value="index"
                                :range="selectList">
                            <view>{{ selectList[curIndex].name }}</view>
                        </picker>
                    </view>
                    <!-- 选择分类 -->
                    <view class="u-tab-item" v-for="(item, index) in oneMenulist" :key="index"
                          :class="[current == index ? 'u-tab-item-active' : '']" @click="swichMenu(item, index)">
                        <view class="u-line-1" :class="{ 'login-active': userInfo.userName }">{{ item.className }}</view>
                        <view>
                            <view class="u-line-1">库存量</view>
                            <view class="u-line-1">({{ item.nums }}/{{ item.totalnum }})</view>
                        </view>
                    </view>
                </scroll-view>
                <!-- 分类具体内容 -->
                <view class="item-container">
                    <block v-for="(item, index) in twoMenulist" :key="index">
                        <view class="thumb-box" @click="menuitemsearch(item)">
                            <image class="item-menu-image" :src="item.imgurl" mode="" :lazy-load="true" shape="circle"></image>
                            <view class="item-menu-name">{{ item.className }}</view>
                            <view class="item-menu-name">库存量({{ item.nums }}/{{ item.totalnum }})</view>
                        </view>
                    </block>
                </view>
            </view>
        </view>
    </view>
</template>

<script>
import {
    fetchGradeMenus,
    fetchPullDownMenus
} from "@/api/index.js";
export default {
    data() {
        return {
            index: 0,
            scrollTop: 0,
            userInfo: {},
            navbar: [],
            gc_id: "",
            showMenu: false,
            oneMenulist: [], //一级分类
            twoMenulist: [], //二级分类
            current: "0", // 预设当前项的值
            celltitle: "",
            data: {
                nums: 0,
                totalnum: 0,
            },
            selectList: [],
            store_id: "0",
            curIndex: 0,
            lang:'',
            langButShow:'',
            defautValue:'0',
            show:false,
            options:[{
                label: '中文',
                value: '1',
            },{
                label: 'English',
                value: '2',
            },],
            url: 'https://qgongye.oss-cn-shanghai.aliyuncs.com/',
        }
    },
    onLoad(){
        this.storeHouseList();
        this.userInfo = uni.getStorageSync("userInfo");
        // this.bindPickerChange({
        //     detail: {
        //         value: "0"
        //     }
        // });
        this.appIndexClass();
    },
    methods: {
        // 选择仓库
        bindPickerChange(e) {
            this.curIndex = e.detail.value;
            const selected = this.selectList[e.detail.value];
            this.store_id = selected ? selected.value : 0;
            getApp().globalData.storeId = this.store_id;
            this.current = 0;
            this.appIndexClass();
        },

        // 获取下拉菜单
        storeHouseList() {
            fetchPullDownMenus().then((res) => {
                this.selectList = res.obj;
            });
        },
        // 获取全部分类
        appIndexClass() {
            fetchGradeMenus({
                gc_id: "",
                // 为空则为获取分类
                store_id: this.store_id,
                type: 1,
            }).then(async (res) => {
                this.oneMenulist = res.obj;
                this.data.nums = 0;
                this.data.totalnum = 0;
                this.twoMenulist = [];
                res.obj.forEach((item) => {
                    this.data.nums = this.data.nums + item.nums;
                    this.data.totalnum = this.data.totalnum + item.totalnum;
                });
                if (res.res) {
                    res.obj.forEach((item) => {
                        console.log(item)
                        item.imgurl = this.url + "/" + item.path + "/" + item.name;
                        this.twoMenulist.push(item);
                    });
                }
                this.celltitle = "全部分类(库存量" + this.data.nums + "/" + this.data.totalnum + ")";
                this.oneMenulist.unshift({
                    className:  '全部分类',
                    en_className: 'All categories',
                    id: "",
                    nums: this.data.nums,
                    totalnum: this.data.totalnum,
                });
                // const result = await fetchGradeMenus({
                //     gc_id: '',
                //     store_id: this.store_id,
                //     type: 2,
                // })
                // console.log(this.oneMenulist)
                // if (result.res) {
                //     result.obj.forEach((item) => {
                //         console.log(item)
                //         item.imgurl = this.url + "/" + item.path + "/" + item.name;
                //         this.twoMenulist.push(item);
                //     });
                // }
            });
        },

        // 获取二级
        getThrClass(id) {
            fetchGradeMenus({
                gc_id: id,
                store_id: this.store_id,
                type: 1,
            }).then((res) => {
                // 全部
                console.log(res)
                if (!this.current) {
                    res.obj.filter((item, i) => {
                        if(item.path && item.path.indexOf('http') > -1) {
                            item.imgurl = item.path + "/" + item.name;
                        } else {
                            item.imgurl = this.url + "/" + item.path + "/" + item.name;
                        }
                        this.twoMenulist.push(item);
                    });
                } else {
                    res.obj.filter((item, i) => {
                        if(item.path && item.path.indexOf('http') > -1) {
                            item.imgurl = item.path + "/" + item.name;
                        } else {
                            item.imgurl = this.url + "/" + item.path + "/" + item.name;
                        }
                    });
                    this.twoMenulist = res.obj;
                }
            });
        },
        // 点击左边的栏目切换
        swichMenu(item, index) {
            if (index == this.current) return;
            this.current = index;
            this.twoMenulist = [];
            if (!this.current) {
                this.appIndexClass();
            } else {
                this.getThrClass(item.id);
            }
        },

        menuitemsearch(item) {
            uni.navigateTo({
                url: `/staffB/onlineClass/searchpage?gc_id=${item.id}&level=${this.current == 0 ? 0 : 1}&store_id=${
                    this.store_id
                }`,
            });
        },
        searchfn() {
            uni.navigateTo({
                url: `/staffB/onlineClass/searchpage?store_id=${this.store_id}`,
            });
        },
    },
};
</script>

<style lang="scss" scoped>
::v-deep .u-input__input {
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB",
  "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
  font-size: 22rpx !important;
  line-height: 60rpx;
  zoom: 0.7;
}

.login-active {
  font-size: 22rpx !important;
}

.content {
  height: 100vh;
  overflow: auto;
  padding: 0;
  background: #ffffff;
}

.search-box {
  display: flex;
  margin: 30rpx 27rpx;
  height: 50rpx;
  .lang-box{
    text-align: right;
    color: gray;
    font-size: 22upx;
  }

  .my-search-input {
    flex: 1;
      height: 60rpx;
      background-color: #f2f2f2;
      border-radius: 40rpx;
      box-sizing: border-box;
      padding: 0 20rpx 0 60rpx;
      font-size: 26rpx;
      display: flex;
      align-items: center;
    text {
      margin-left: 10rpx;
      color: #95989e;
    }
  }
}

.u-wrap {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.u-menu-wrap {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.u-search-inner {
  background-color: rgb(234, 234, 234);
  border-radius: 100rpx;
  display: flex;
  align-items: center;
  padding: 10rpx 16rpx;
}

.u-tab-view {
  max-width: 30%;
  height: 100%;
  background: #f6f6f6;
}

.u-tab-item {
  height: 140rpx;
  background: #f6f6f6;
  box-sizing: border-box;
  font-size: 26rpx;
  color: #444;
  font-weight: 400;
  line-height: 1;
  display: flex;
  padding: 8rpx 0px;
  padding-left: 18rpx;
  justify-content: center;
  flex-direction: column;
  align-content: flex-start;
}

.u-tab-item-active {
  position: relative;
  color: #000;
  background: #fff;
}

.u-tab-item-active::before {
  content: "";
  position: absolute;
  border-left: 4px solid #26c2cd;
  height: 32rpx;
  left: 0;
  top: 60rpx;
}

.right-box {
  background-color: rgb(250, 250, 250);
}

.selectBox {
  height: 80rpx;
  background-color: #fff;
  border-bottom: 1rpx solid #e7e7e7;
}

.page-view {
  padding: 16rpx;
}

.class-item {
  margin-bottom: 30rpx;
  background-color: #fff;
  padding: 16rpx;
  border-radius: 8rpx;
}

.item-title {
  font-size: 26rpx;
  color: $u-main-color;
  font-weight: bold;
}

.item-menu-name {
  font-weight: normal;
  font-size: 24rpx;
  color: $u-main-color;
}

.item-container {
  display: flex;
  width: 70%;
  flex-wrap: wrap;
  align-content: flex-start;
  overflow: hidden;
  height: 100%;
  padding-bottom: 110rpx;
  overflow: auto;
}

.thumb-box {
  width: 50%;
  margin-top: 50rpx;
  text-align: center;
}

.item-menu-image {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  border: 1rpx solid #efefef;
}

.u-line-1 {
  padding: 8rpx 0;
}

// @media screen and (min-width: 480px) {
// 	.u-tab-view {
// 		width: 20%;
// 	}
// 	.item-container {
// 		width: 80%;
// 	}
// 	.thumb-box {
// 		width: 25%;
// 		margin-top: 50rpx;
// 		text-align: center;
// 	}
// }
</style>
