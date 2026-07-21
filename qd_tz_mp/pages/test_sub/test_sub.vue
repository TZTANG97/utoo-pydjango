<template>
	<view class="container">
		<!-- indicatorMode="dot" indicatorStyle="top" :indicator="true" :circular="true"-->
		<!-- <swiper :autoplay="true" :current="current">
			<swiper-item v-for="item in bannerList" :key="item.id">
				<image :src="item.picUrl" mode=""></image>
			</swiper-item>
		</swiper> -->
		<u-swiper @click="swiperFn" :list="bannerList" @change="swiperChange" name="picUrl" mode="dot"
			indicator-pos="bottomCenter"></u-swiper>
		<view class="msgBox" @click="swiperFn">
			<view :style="{color:titlecolor,fontSize:titlesize+'px'}">{{title}}</view>
			<view :style="{color:badescribecolor,fontSize:badescribesize+'px'}">{{badescribe}}</view>
			<view :style="{color:subheadingcolor,fontSize:subheadingsize+'px'}">{{subheading}}</view>
		</view>
		<view class="plateBox">
			<view class="plate">
				<view @click="goyuyue" class="plate-item" style="border-right: 1rpx #fff solid;">
					<navigator style="width: 100%;height: 100%;" open-type="switchTab" url="/pages/index/index"
						hover-class="none">
						<image src="@/static/sub.png" mode=""></image>
					</navigator>
					<view>测试预约</view>
					<view>Booking Test</view>
				</view>
				<view class="centerG">
					<view></view>
				</view>
				<view @click="goshop" class="plate-item" style="border-left: 1rpx #fff solid; display:flex; align-items: center; flex-direction: column; justify-content: center">
					<image src="@/static/shop.png" mode="" style="width: 110rpx; height: 110rpx"></image>
					<view>在线商城</view>
					<view>Online Store</view>
				</view>
			</view>
			<view class="userInfo" :style="{background:!userInfo || userInfo.uType == 0 ? '#fff' : 'none'}">
				<view class="topBox" @click="goUser" v-if="!userInfo || userInfo.uType == 0">
					<image :src="userInfo['photo']" v-if="userInfo['photo']"
						style="width: 40rpx;height: 40rpx;margin-right: 10rpx;"></image>
					<image src="@/static/head.png" v-else style="width: 40rpx;height: 40rpx;margin-right: 10rpx;">
					</image>
					<text style="width: 220rpx;" v-if="userInfo.wx_nickname">{{userInfo.wx_nickname}}</text>
					<text style="width: 220rpx;" v-else>请登录</text>
					<view style="width: 150rpx;">用户LV{{lv}}</view>
					<text style="font-weight: 700;width: 240rpx;text-align: right;">积分：{{userInfo ? totalIntegral : ''}}</text>
				</view>
				<view class="bottomBox" @click="goUser" v-if="!userInfo || userInfo.uType == 0">
					<view>
						<text class="num">{{userNum.orderCount}}</text>
						<text class="msg">我的订单</text>
					</view>
					<view class="centerBox">
						<text class="num">{{userNum.fpCount}}</text>
						<text class="msg">我的发票</text>
					</view>
					<view>
						<text class="num">{{userNum.yuyueCount}}</text>
						<text class="msg">预约记录</text>
					</view>
				</view>
			</view>
		</view>

		<!-- <image class="logo" src="https://qgongye.oss-cn-shanghai.aliyuncs.com/upload/order/a27330fb-080a-4d36-a7cb-3598af54543d.png" mode=""></image>

		<view class="plate">
			<view class="plate-item">
				<navigator style="width: 100%;height: 100%;" open-type="switchTab" url="/pages/index/index" hover-class="none" >
					<image src="@/static/sub.png" mode=""></image>
				</navigator>
				<view>测试预约</view>
				<view>Booking Test</view>
			</view>
			<view class="plate-item">
				<image src="@/static/shop.png" mode="" @click="$toast('敬请期待')"></image>
				<view>在线商城</view>
				<view>Online Store</view>
			</view>
		</view>

		<view style="position: relative;">
			<swiper :circular="true" :current="current">
				<swiper-item v-for="item in bannerList" :key="item.id">
					<image :src="item.picUrl" mode=""></image>
				</swiper-item>
			</swiper>
			<view class="idcp">
				<image @click="cutSwiper(1)" src="@/static/banner-left.png" mode=""></image>
				<image @click="cutSwiper(2)" class="rotate" src="@/static/banner-left.png" mode=""></image>
			</view>

			<view class="dialog" @click="checkActivity">
			</view>
		</view> -->
		<!-- <image class="go-sub" src="https://qgongye.oss-cn-shanghai.aliyuncs.com/upload/order/4bce0371-8ec9-41db-91e9-fe0b988b1dc6.png" mode=""></image> -->
	</view>
</template>

<script>
	import {
		getBannerApi
	} from '@/api/index.js'
	import {
		fetchMyPointsApi,
		getUserNumberApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
				current: 0,
				bannerList: [],
				lv: 0,
				userInfo: null,
				userNum: {
					balance: 0,
					fpCount: 0,
					orderCount: 0,
					totalIntegral: 0,
					yuyueCount: 0,
				},
				totalIntegral: 0,
				title: '',
				badescribe: '',
				subheading: '',
				titlecolor: '#000',
				badescribecolor: '#000',
				subheadingcolor: '#000',
				titlesize: 12,
				badescribesize: 12,
				subheadingsize: 12,
				swiperIndex: 0,
			}
		},
		onShow() {
			this.userNum = {
				balance: 0,
				fpCount: 0,
				orderCount: 0,
				totalIntegral: 0,
				yuyueCount: 0,
			}

			this.userInfo = uni.getStorageSync('userInfo');
			console.log(this.userInfo,'userInfo')
			// 0普通 1内部
			if (this.userInfo && !this.userInfo.uType) {
				getUserNumberApi().then(res => {
					if (res.res) {
						this.userNum = res.obj
						this.wcOrderCount = Math.floor(res.obj.wcOrderCount / 5)
					}
				})
				fetchMyPointsApi().then(res => {
					if (res.res) {
						this.totalIntegral = res.obj.totalIntegral
						uni.setStorageSync('totalIntegral', res.obj.totalIntegral)
					}
				})
			}
		},
		onLoad() {
			getBannerApi().then(res => {
				if (res.res) {
					this.bannerList = res.obj
					this.title = this.bannerList[0].title
					this.badescribe = this.bannerList[0].badescribe
					this.subheading = this.bannerList[0].subheading

					this.titlecolor = this.bannerList[0].titlecolor
					this.badescribecolor = this.bannerList[0].badescribecolor
					this.subheadingcolor = this.bannerList[0].subheadingcolor

					this.titlesize = this.bannerList[0].titlesize
					this.badescribesize = this.bannerList[0].badescribesize
					this.subheadingsize = this.bannerList[0].subheadingsize
				}
			})
		},
		methods: {
			swiperFn(e) {
				if (this.bannerList[this.swiperIndex].website && (this.bannerList[this.swiperIndex].website.includes(
						"my") || this.bannerList[this.swiperIndex].website.includes("test_sub") || this.bannerList[this
							.swiperIndex].website.includes("index"))) {
					uni.switchTab({
						url: '/' + this.bannerList[this.swiperIndex].website
					});
				} else {
					if (this.bannerList[this.swiperIndex].website) {
						uni.redirectTo({
							url: '/' + this.bannerList[this.swiperIndex].website
						})
					}
				}
				// if (e) {
				// 	console.log(e,'eeeeeee')
				// 	if(this.bannerList[e].website && (this.bannerList[e].website.includes("my") || this.bannerList[e].website.includes("test_sub")||this.bannerList[e].website.includes("index"))){
				// 		uni.switchTab({
				// 			url: '/'+this.bannerList[e].website
				// 		});
				// 	}else{
				// 		if (this.bannerList[e].website) {
				// 			uni.redirectTo({
				// 				url:'/'+this.bannerList[e].website
				// 			})
				// 		}
				// 	}
				// } else {
				// 	console.log('dddddddddddddddddd')
				// 	if(this.bannerList[this.swiperIndex].website && (this.bannerList[this.swiperIndex].website.includes("my") || this.bannerList[this.swiperIndex].website.includes("test_sub")||this.bannerList[this.swiperIndex].website.includes("index"))){
				// 		uni.switchTab({
				// 			url: '/'+this.bannerList[this.swiperIndex].website
				// 		});
				// 	}else{
				// 		if (this.bannerList[this.swiperIndex].website) {
				// 			uni.redirectTo({
				// 				url:'/'+this.bannerList[this.swiperIndex].website
				// 			})
				// 		}
				// 	}
				// }
			},
			swiperChange(e) {
				this.swiperIndex = e
				this.title = this.bannerList[e].title
				this.badescribe = this.bannerList[e].badescribe
				this.subheading = this.bannerList[e].subheading

				this.titlecolor = this.bannerList[e].titlecolor
				this.badescribecolor = this.bannerList[e].badescribecolor
				this.subheadingcolor = this.bannerList[e].subheadingcolor

				this.titlesize = this.bannerList[e].titlesize
				this.badescribesize = this.bannerList[e].badescribesize
				this.subheadingsize = this.bannerList[e].subheadingsize
			},
			goyuyue() {
				uni.switchTab({
					url: '/pages/index/index'
				});
			},
			goshop(){
				uni.navigateTo({
					url: '/staffB/onlineClass/index'
				})
				// uni.navigateTo({
				// 	url: '/staff/points_mall/points_mall'
				// })
				// uni.navigateTo({
				// 	url: '/staff/online_shopping_mall/online_shopping_mall'
				// })
			},
			// gofapiao(){
			// 	uni.navigateTo({
			// 		url: '/pagesB/my_invoice/my_invoice'
			// 	})
			// },
			// goorder(){
			// 	uni.navigateTo({
			// 		url: '/pagesB/order_list/order_list'
			// 	})
			// },
			goUser() {
				uni.switchTab({
					url: '/pages/my/my'
				});
			},
			// checkActivity() {
			// 	const id = this.bannerList[this.current]['project_class']
			// 	uni.navigateTo({
			// 		url: '/staffB/test_detail/test_detail?id=' + id
			// 	})
			// },


			// cutSwiper(dec) {
			// 	let newCurrent;
			// 	if (dec === 1) {
			// 		newCurrent = this.current - 1
			// 		if (newCurrent < 0) {
			// 			newCurrent = this.bannerList.length - 1
			// 		}
			// 	} else {
			// 		newCurrent = this.current + 1
			// 		if (newCurrent == this.bannerList.length) {
			// 			newCurrent = 0
			// 		}
			// 	}
			// 	this.current = newCurrent
			// },
		}
	}
</script>

<style scoped lang="scss">
	.msgBox {
		position: absolute;
		top: 10%;
		overflow: hidden;
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;

		view {
			margin: 20rpx 0;
		}
	}

	// .go-sub {
	// 	width: 100%;
	// 	height: 300rpx;
	// 	margin: 40rpx 0;
	// }

	// .dialog {
	// 	position: absolute;
	// 	width: 100%;
	// 	height: 100%;
	// 	left: 0;
	// 	top: 0;
	// 	z-index: 2;
	// }
	// .idcp {
	// 	position: absolute;
	// 	right: 20rpx;
	// 	top: 50%;
	// 	transform: translateY(-50%);
	// 	z-index: 3;

	// 	image {
	// 		width: 45rpx;
	// 		height: 50rpx;
	// 	}

	// 	.rotate {
	// 		transform: rotate(-180deg);
	// 	}
	// }

	::v-deep .u-swiper-wrap {
		height: 100%;

		swiper {
			height: 100% !important;
			margin: 20rpx;
			box-sizing: border-box;
		}

		.u-swiper-indicator {
			bottom: 660rpx !important;
		}

		.u-indicator-item-dot {
			background-color: #fff !important;
		}

		.u-indicator-item-dot-active {
			background-color: #ffa200 !important;
		}
	}

	// swiper {
	// 	height: 100%;
	// 	margin: 20rpx;
	// 	box-sizing: border-box;
	// 	swiper-item {
	// 		image {
	// 			width: 100%;
	// 			height: 100%;
	// 		}
	// 	}
	// }

	.container {
		position: relative;
		height: calc(100vh - 20rpx);
	}

	.plateBox {
		position: absolute;
		bottom: 1%;
		width: 100%;
		padding: 0 30rpx;
		box-sizing: border-box;

		.plate {
			width: 100%;
			display: flex;
			justify-content: center;
			border-radius: 10rpx;
			overflow: hidden;

			.plate-item {
				text-align: center;
				width: 49%;
				background-color: #F8FAF9;
				height: 320rpx;
				overflow: hidden;
				font-weight: bold;

				image {
					width: 100%;
					height: 100%;
				}
			}

			.centerG {
				width: 2%;
				padding: 20rpx;
				background-color: #ffffff;
				box-shadow: -1px 0px 0px 0px #fff;

				view {
					width: 1rpx;
					height: 100%;
					border: 1px #e9e9e9 solid;
				}
			}
		}

		.userInfo {
			background-color: #fff;
			width: 100%;
			padding: 20rpx 30rpx 40rpx 30rpx;
			margin-top: 20rpx;
			height: 280rpx;
			border-radius: 10rpx;
			overflow: hidden;

			.topBox {
				display: flex;
				align-items: center;
				height: 80rpx;
			}

			.bottomBox {
				display: flex;
				background-color: #efefef;
				border-radius: 5rpx;
				padding: 30rpx 0;

				view {
					display: flex;
					flex-direction: column;
					align-items: center;
					justify-content: space-around;
					width: 30%;
					height: 100rpx;
					margin: 0 auto;

					.num {
						font-size: 32rpx;
						font-weight: 700;
					}

					.msg {
						font-size: 25rpx;
						font-weight: 700;
					}
				}

				.centerBox {
					border-left: 4rpx #fefefe solid;
					border-right: 4rpx #fefefe solid;
				}
			}
		}
	}


	// .logo {
	// 	width: 100%;
	// 	height: 265rpx;
	// 	margin: 100rpx 0;
	// }
</style>
