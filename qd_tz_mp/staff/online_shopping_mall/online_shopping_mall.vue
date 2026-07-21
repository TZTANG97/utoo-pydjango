<template>
    <view class="shopping_box">
        <view class="search_box">
            <input class="search_input" placeholder="请输入"></input>
            <view class="search_btn_box">
                <view class="search_btn">
                    搜索
                </view>
            </view>
        </view>
        <view class="top_type_box">
            <view class="top_type_item" @click="toTypeList(1)">
                <view class="type_item_left"></view>
                <view class="type_item_right">材料<br/>试剂</view>
            </view>
            <view class="top_type_item" @click="toTypeList(2)">
                <view class="type_item_left"></view>
                <view class="type_item_right">实验<br/>耗材</view>
            </view>
            <view class="top_type_item" @click="toTypeList(3)">
                <view class="type_item_left"></view>
                <view class="type_item_right">科研<br/>仪器</view>
            </view>
        </view>

        <view class="top_type_box top_type_box1">
            <view class="top_type_item" @click="toPoints">
                <view class="type_item_left"></view>
                <view class="type_item_right">监测优惠券</view>
            </view>
            <view class="top_type_item" style="margin-left: 16rpx" @click="toPoints">
                <view class="type_item_left"></view>
                <view class="type_item_right">周边用具</view>
            </view>
        </view>

        <view class="shop-list">
            <view class="shopItem" @click="shopItemFn(item)" v-for="(item,index) in list">
                <img :src="'https://qgongye.oss-cn-shanghai.aliyuncs.com/'+item.path+'/'+item.name" alt="图片待定" />
                <view class="msg">
                    <p>{{item.good_name}}</p>
                    <view class="jf">
                        <text>{{item.nums}}积分</text>
                        <text>库存：{{item.inventory_num || 0}}</text>
                    </view>
                </view>
            </view>
        </view>
        <u-toast ref="uToast" />

        <my-loading :loading="loading" :total="list.length" :is-refresh="isRefresh"></my-loading>
    </view>
</template>

<script>
import {List_dpt} from "@/api/points";
import MyLoading from "@/components/loading.vue";

export default {
    components: {MyLoading},
    data() {
        return {
            list:[],
            loading: false,
            isRefresh: true,
            page: 1,
            userInfo: null
        };
    },
    onShow() {
        this.userInfo = uni.getStorageSync('userInfo');
    },
    created() {
        this.List_dptFn()
    },
    onReachBottom() {
        if (this.isRefresh) {
            this.page++;
            this.List_dptFn()
        }
    },
    methods: {
        toTypeList(type) {
          if(type == 1 || type == 2) {
              this.$tip('敬请期待')
              return;
          }
        },
        // 商品列表
        List_dptFn(){
            List_dpt({
                draw: 1,
                start: (this.page - 1) * 10,
                length: 10,
            }).then(res => {
                if (res.data) {
                    this.list = [...this.list, ...res.data]
                    if (res.data.length !== 10) {
                        this.isRefresh = false
                    }
                } else {
                    this.$tip(res.resMsg)
                }
            })
        },
        shopItemFn(item) {
            if(!this.userInfo){
                uni.switchTab({
                    url: '/pages/my/my'
                });
            }else{
                uni.navigateTo({
                    url: '/staff/points_mall/productDetails?id=' + item.id
                })
            }
        },
        toPoints() {
            uni.navigateTo({
                url: '/staff/points_mall/points_mall'
            })
        }
    },
}
</script>

<style lang="scss" scoped>
.shopping_box {
    padding: 32rpx;
    .search_box {
        display: flex;
        align-items: center;
        border-radius: 16rpx;
        margin: 10rpx 0;
        height: 80rpx;
        border: 1px solid #cccccc;
        padding: 0 16rpx;
        .search_input {
            flex: 5;
            line-height: 80rpx;
            font-size: 26rpx;
        }
        .search_btn_box {
            flex: 1;
            margin-left: 30rpx;
            .search_btn {
                text-align: center;
                height: 60rpx;
                line-height: 60rpx;
                background: $primary;
                color: #ffffff;
                border-radius: 16rpx;
            }
        }
    }
}
.shop-list {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;

    .shopItem {
        width: 48%;
        margin: 20rpx 0;
        background-color: #faf7f2;

        img {
            width: 100%;
            height: 300rpx;
            background-color: #fff;
        }

        .msg {
            padding: 20rpx;

            p {
                padding-bottom: 20rpx;
                color: #5b5a56;
                font-size: 24rpx;
            }

            .jf {
                display: flex;
                justify-content: space-between;
                color: #5b5a56;

                text {
                    font-size: 24rpx;
                }
            }
        }
    }
}
.top_type_box {
    display: flex;
    justify-content: space-between;
    margin-top: 20rpx;
    .top_type_item {
        flex: 1;
        margin: 0 16rpx;
        &:first-child {
            margin: 0;
        }
        &:last-child {
            margin: 0;
        }
        border-radius: 16rpx;
        border: 2px solid $primary;
        display: flex;
        padding: 10rpx;
        align-items: center;
        justify-content: space-around;
        .type_item_left {
            width: 80rpx;
            height: 80rpx;
        }
        .type_item_right {
            font-size: 30rpx;
            font-weight: 600;
        }
    }
}
.top_type_box1 {
    .top_type_item {
        background: $primary;
        .type_item_right {
            color: #ffffff;
        }
    }
}
</style>
