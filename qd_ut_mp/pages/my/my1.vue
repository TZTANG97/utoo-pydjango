<template>
	<view class="container syxHeight" :style="{overflow : userInfo.uType ? 'hidden' : 'auto'}">
		<image class="bg" v-if="!userInfo || userInfo.uType" src="@/static/my-bg.png" mode=""></image>
		<template v-if="!userInfo">
			<view class="header flex-center">
				<view class="label">
					<text>Hi，</text>
					<text>欢迎来到愉兔检测</text>
				</view>
				<image class="head" src="@/static/head.png" mode="" />
			</view>
			<view class="login-btn" @click="viewMyProfile">
				注册/登录
			</view>
		</template>

		<template v-else-if="userInfo.uType">
			<view class="admin-user">
				<text class="myUser">个人中心</text>
				<view class="header flex-center" @click="viewMyProfile">
					<image class="head" v-if="userInfo['photo']" :src="userInfo['photo']" mode="" />
					<image class="head" v-else src="@/static/head.png" mode="" />
					<view class="user-info flex-between"
						:style="{ 'justify-content': !userInfo.mobile? 'center' : '' }">
						<view class="user-name">
							{{ userInfo.wx_nickname? userInfo.wx_nickname : '没有昵称'}}
						</view>
						<view class="user-phone">
							{{ userInfo.mobile? userInfo.mobile : ''}}
						</view>
					</view>
					<view class="log-out" style="font-size: 40rpx;" @click.stop="logOut">
						<!-- <image src="@/static/logout.png" mode=""></image> -->
						退出
					</view>
				</view>
				<!-- :style="{height:visibleHeight * 2 +'rpx'}" -->
				<view class="main" style="height: 100%;" v-if="userInfo.userType != 5">
					<view class="menus-list">
						<view class="menuItem" @click="menuItem(item)"
							:style="{background:item.checked ? '#fff' : '#f6f6f6'}" v-for="(item,index) in newMenuList"
							:key="index" v-if="userInfo.userType != 3 && index != 2 || userInfo.userType == 3">
							{{item.name}} <br>
							{{item.num >= 0 ? item.num : ''}}
						</view>
					</view>
					<view class="menus-Box" v-for="(item,index) in newMenuList" :key="index" v-if="item.checked">
						<view v-for="(subItem,subInd) in item.childs" :key="subInd" @click="cutMenu(subInd, subItem)">
							<view v-if="!userInfo['uType']" class="span">{{subItem.icon}}</view>
							<view v-else class="span">{{subItem.icon}}</view>
							<!-- <image v-else class="span" src="@/static/我的订单.png" mode=""></image> -->

							<view v-if="!userInfo['uType']" class="text">{{subItem}}</view>
							<view v-else class="text">{{subItem.name}} <text v-if="index != 0">({{subItem.num}})</text>
							</view>
						</view>
					</view>

				</view>

				<view class="scan" @click="$refs.scan.open()" v-if="userInfo && userInfo.uType">
					<image src="@/static/scan.png" mode=""></image>
				</view>


				<uni-popup ref="scan" type="bottom">
					<view class="scan-btns">
						<view class="title">
							扫码操作
						</view>
						<view class="btns-list">
							<view class="btn-item" @click="logInfo(1)">
								入库
							</view>
							<view class="btn-item" @click="logInfo(2)">
								领用
							</view>
							<view class="btn-item" @click="logInfo(3)">
								开始测试
							</view>
							<!-- 扫码确认即可完成 -->
							<view class="btn-item" @click="logInfo(4)">
								完成测试
							</view>
							<view class="btn-item" @click="logInfo(5)">
								样品归还
							</view>
							<view class="btn-item" @click="logInfo(6)">
								样品寄回
							</view>
							<view class="btn-item" @click="logInfo(7)">
								样品留存
							</view>
						</view>
					</view>
				</uni-popup>
			</view>
		</template>

		<template v-else>
			<view class="regular-user">
				<view class="regular-user-header" @click="viewMyProfile">
					<image v-if="userInfo['photo']" :src="userInfo['photo']" mode="" />
					<image v-else src="@/static/head.png" mode="" />
					<view class="nick-name">
						{{ userInfo.wx_nickname? userInfo.wx_nickname : '没有昵称'}}
					</view>
					<view class="user-mobile">
						{{ userInfo.mobile? userInfo.mobile : '没有手机号' }}
					</view>
				</view>
				<view class="badge">
					<template v-for="item in 5">
						<image v-if="wcOrderCount >= item + 1" src="@/static/badge-light.png" mode=""></image>
						<image v-else src="@/static/badge.png" mode=""></image>
					</template>
				</view>
				<view class="main-menu">
					<view class="main-menu-item" @click="cutMenu(0)">
						<view class="num">{{ userNum['orderCount'] }}</view>
						<view class="label">我的订单</view>
					</view>
					<view class="main-menu-item" @click="cutMenu(3)">
						<view class="num">{{ userNum['fpCount'] }}</view>
						<view class="label">我的发票</view>
					</view>
					<view class="main-menu-item" @click="cutMenu(5)">
						<view class="num">{{ userNum['yuyueCount'] }}</view>
						<view class="label">预约记录</view>
					</view>
				</view>
				<view class="sub-menu">
					<view class="sub-menu-item" @click="cutMenu(2)">
						<view class="label">
							我的积分
						</view>
						<view class="money">
							<text>{{ dataObj.totalIntegral }}</text>
							<br>
							<view class="btn">
								兑换
							</view>
						</view>
					</view>
					<view class="sub-menu-item" @click="cutMenu(1)">
						<view class="label">
							<text>我的余额</text>
							<image @click.stop="checkBalance = false" v-if="checkBalance" src="@/static/eye.png"
								mode="">
							</image>
							<image @click.stop="checkBalance = true" v-else src="@/static/eye-close.png" mode="">
							</image>
						</view>
						<view class="money">
							<text v-if="checkBalance">{{ userNum['balance'].toFixed(2) }}</text>
							<text v-else>******</text>
							<br>
							<view class="btn">
								充值
							</view>
						</view>
					</view>
				</view>
				<view class="make-task">
					<view class="label">
						<text>DISCOVERY</text>
						<text>探索任务</text>
					</view>
					<image src="@/static/right.png" mode=""></image>
				</view>

				<view class="log-out" @click="logOut">
					退出登录
				</view>
			</view>
		</template>
		<u-popup v-model="show" mode="right">
			<view class="userBox">
				<view v-for="(item,index) in userList" v-if="(userInfo.userType == 1 && item.id !=1) || userInfo.userType != 1" :key="index"
					class="userItem" @click="cutMenu(index,item)">
					<view><span>—</span><span>—</span></view>
					<span>{{item.name}}</span>
				</view>
			</view>
		</u-popup>
	</view>
</template>

<script>
	import {
		checkAuthApi
	} from '@/api/common.js'
	import {
		loginForCodeApi
	} from '@/api/loign'
	import {
		fetchDefaultAccountApi,
		scanOperateApi,
		getUserNumberApi,
		getIntegralConvertRatio,
		fetchMyPointsApi,
		getOrderCount
	} from '@/api/index.js'
	export default {
		data() {
			return {
				pageHeight: 0,

				// 实验列表和实验列表共用一个页面
				// 子订单也是共用一个页面
				cateList: [{
						label: '实验订单',
						path: 'order_list',
						type: 6
					},
					{
						label: '实验分包订单',
						path: 'order_list',
						type: 8
					},
					{
						label: '实验子订单',
						path: 'child_order',
						type: 6,
						all: 1
					},
					{
						label: '实验分包子订单',
						path: 'child_order',
						type: 8,
						all: 1
					}
				],
				newMenuList: [{
						id: 1,
						name: '我的数据',
						checked: true,
						childs: [{
								id: '1-1',
								name: '账户资金',
								icon: '账',
								path: 'accountFunds',

								type: '',
								all: '',
								nb: '666'
							},
							{
								id: '1-2',
								name: '数字化运营中心',
								icon: '运',
								path: 'digitalOperationsCenter',
								pathB: true,
								type: '',
								all: ''
							},
						]
					},
					{
						id: 2,
						name: '我的实验',
						checked: false,
						num: 0,
						childs: [{
								id: '2-1',
								label: '实验订单',
								name: '实验订单',
								path: 'order_list',
								type: 6,
								icon: '实',
								num: 0
							},
							{
								id: '2-2',
								label: '实验分包订单',
								name: '实验分包订单',
								path: 'order_list',
								type: 8,
								icon: '分',
								num: 0
							},
							{
								id: '2-3',
								label: '实验子订单',
								name: '实验子订单',
								path: 'child_order',
								type: 6,
								all: 1,
								icon: '子',
								num: 0
							},
							{
								id: '2-4',
								label: '实验分包子订单',
								name: '实验分包子订单',
								path: 'child_order',
								type: 8,
								all: 1,
								icon: '子',
								num: 0
							}
						]
					},
					{
						id: 3,
						name: '我的审核',
						checked: false,
						num: 0,
						childs: [{
								id: '3-1',
								label: '实验订单',
								name: '实验订单',
								path: 'pendingReview',
								pathB: true,
								type: 111,
								icon: '待',
								num: 0
							},
							{
								id: '3-2',
								label: '实验分包订单',
								name: '实验分包订单',
								path: 'pendingReview',
								pathB: true,
								type: 222,
								icon: '待',
								num: 0
							},
							{
								id: '3-3',
								label: '实验子订单',
								name: '实验子订单',
								path: 'pendingReview',
								pathB: true,
								type: 333,
								icon: '待',
								num: 0
							},
							{
								id: '3-4',
								label: '实验分包子订单',
								name: '实验分包子订单',
								path: 'pendingReview',
								pathB: true,
								type: 444,
								icon: '待',
								num: 0
							},
							{
								id: '3-5',
								label: '待审核付款实验分包子订单',
								name: '待审核付款实验分包子订单',
								path: 'pendingReview',
								pathB: true,
								type: 555,
								icon: '待',
								num: 0
							}
						]
					},
					{
						id: 5,
						name: '提案改善',
						checked: false,
						childs:[
							{
								id: '5-1',
								label: '提案改善',
								name: '提案改善',
								path: 'proposal',
								pageB: true,
								icon: '提',
							}
						]
					},
				],
				menusList: [],
				userInfo: null,
				normalUser: [
					'我的订单',
					'我的资产',
					'我的积分',
					'我的发票',
					'我的预约',
				],
				userNum: {
					balance: 0,
					fpCount: 0,
					orderCount: 0,
					totalIntegral: 0,
					yuyueCount: 0,
				},
				checkBalance: false,
				wcOrderCount: 0,
				integralConvertRatio: 0,
				dataObj: {
					totalIntegral: 0,
					expireIntegral: 0
				},
				visibleHeight: 0,
				show: false,
				userList: [{
						id: 1,
						name: '账户资金',
						path: 'accountFunds',
						pathB: true,
						type: 'b',
						all: '',
					},
					{
						id: 2,
						name: '订单资金详情',
						path: 'accountFunds',
						pathB: true,
						type: 'a',
						all: '',
					},
					{
						id: 3,
						name: '明细列表',
						pathB: true,
						path: 'accountFunds',
						type: 'c',
						all: '',
					},
					{
						id: 4,
						name: '充值申请',
						pathB: true,
						path: 'accountFunds',
						type: 'd',
						all: '',
					},
					{
						id: 5,
						name: '提现申请',
						pathB: true,
						path: 'accountFunds',
						type: 'e',
						all: '',
					},
					{
						id: 6,
						name: '转账申请',
						pathB: true,
						path: 'accountFunds',
						type: 'f',
						all: '',
					},
					{
						id: 7,
						name: '借贷款申请',
						pathB: true,
						path: 'accountFunds',
						type: 'g',
						all: '',
					}
				],
				bgHeight: 0
			};
		},
		onShow() {
			this.userInfo = uni.getStorageSync('userInfo');
			console.log(this.userInfo,'userInfo')
			// 0普通 1内部
			if (this.userInfo && !this.userInfo.uType) {
				this.menusList = this.normalUser
				if (!uni.getStorageSync('defaultAccount')) {
					// 获取默认收款账户
					fetchDefaultAccountApi().then(res => {
						if (res.res) {
							uni.setStorageSync('defaultAccount', res.obj)
						}
					})
				}
				getUserNumberApi().then(res => {
					if (res.res) {
						// uni.setStorageSync('totalIntegral', res.obj.totalIntegral);
						this.userNum = res.obj
						this.wcOrderCount = Math.floor(res.obj.wcOrderCount / 5)
					}
				})
				getIntegralConvertRatio().then(res => {
					if (res.res) {
						uni.setStorageSync('integralConvertRatio', res.obj.integral_convert_ratio)
					}

				})
				this.getPoints()
			} else {
				this.menusList = this.cateList
			}
			this.getOrderCountFn()
		},
		onLoad() {
			uni.$on('checkAuth', () => {
				checkAuthApi().then(res => {
					if (res.res) {
						if (!res.obj['is_identify']) {
							uni.showModal({
								title: '提示',
								content: '是否去完善信息？',
								success({
									confirm
								}) {
									if (confirm) {
										uni.navigateTo({
											url: '/staffB/choose_identity/choose_identity'
										})
									}
								}
							})
						} else {
							uni.setStorageSync('is_identify', res.obj['is_identify'])
						}
					}
				})
			})
			const that = this
			uni.getSystemInfo({
				success(res) {
					const {
						windowHeight
					} = res
					that.pageHeight = windowHeight
				}
			})

		},
		methods: {
			getOrderCountFn() {
				getOrderCount().then(res => {
					if (res.res) {
						// const data = uni.getStorageSync('userInfo')
						if (res.obj.orderCountByManage >= 0 && this.newMenuList[2]) {
							this.newMenuList[2].num = res.obj.orderCountByManage
							this.newMenuList[2].childs[0].num = res.obj.orderCountm
							this.newMenuList[2].childs[1].num = res.obj.suborderCountm
							this.newMenuList[2].childs[2].num = res.obj.orderchildCountm
							this.newMenuList[2].childs[3].num = res.obj.suborderchildCountm
							this.newMenuList[2].childs[4].num = res.obj.expsubChildpayListnum
						}
						if (res.obj.orderCountAll) {
							this.newMenuList[1].num = res.obj.orderCountAll
							this.newMenuList[1].childs[0].num = res.obj.orderCount
							this.newMenuList[1].childs[1].num = res.obj.suborderCount
							this.newMenuList[1].childs[2].num = res.obj.orderchildCount
							this.newMenuList[1].childs[3].num = res.obj.suborderchildCount
						}
					}
					console.log(res, 'res')
				})
			},
			// 打印样品信息
			async logInfo(type = '') {
				uni.navigateTo({
					url: `/staffB/scan/scan?type=${type}`
				})
				return

				const scan_result = await this.scanQrCode()
				if (!scan_result) return this.$toast('二维码无效')
				scanOperateApi({
					type,
					childId: scan_result['result']
				}).then(res => {
					if (res.res) {
						this.$toast(res.resMsg)
					} else {
						this.$toast(res.resMsg)
					}
				})
			},

			// 扫一扫
			async scanQrCode() {
				return new Promise((resolve, reject) => {
					uni.scanCode({
						success(res) {
							resolve(res)
						},
						fail(err) {
							reject(false)
						},
					})
				})
			},

			// 切换菜单
			cutMenu(idx, item) {
				console.log(item, 'item')
				if (item && item.nb == 666) {
					this.show = true
				} else {
					// 内部用户
					if (this.userInfo['uType']) {
						const {
							path,
							type,
							all = '',
							pathB
						} = item
						console.log(pathB, 'pathB')
						if (pathB) {
							return uni.navigateTo({
								url: `/staffB/${path}/${path}?type=${type}&all=${all}`
							})
						} else {
							return uni.navigateTo({
								url: `/staff/${path}/${path}?type=${type}&all=${all}`
							})
						}

					}

					// 外部用户
					switch (idx) {
						case 0:
							uni.navigateTo({
								url: '/pagesB/order_list/order_list'
							})
							break;

						case 1:
							uni.navigateTo({
								url: '/pagesB/my_assets/my_assets'
							})
							break;


						case 2:
							uni.navigateTo({
								url: '/pagesB/points/points?dataObj=' + JSON.stringify(this.dataObj)
							})
							break;

						case 3:
							uni.navigateTo({
								url: '/pagesB/my_invoice/my_invoice'
							})
							break;

						default:
							uni.navigateTo({
								url: '/pagesB/make_list/make_list'
							})
					}
				}

			},

			// 查看订单
			viewOrder(path) {
				uni.navigateTo({
					url: `/test/${path}/${path}`
				})
			},


			// 进个人中心
			viewMyProfile() {
				if (this.userInfo) {
					uni.navigateTo({
						url: '/staffB/my-profile/my-profile'
					})
				} else {
					uni.navigateTo({
						url: '/pages/login/login'
					})
				}
			},
			// 退出登录
			logOut() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定退出？',
					success({
						confirm
					}) {
						console.log(confirm, 'confirm')
						if (confirm) {
							that.userInfo = null
							uni.removeStorageSync('userInfo')
							uni.removeStorageSync('userList')
							uni.removeStorageSync('token')
							uni.removeStorageSync('uType')
							// uType: 0普通用户  1内部用户
							uni.removeStorageSync('is_identify')
							uni.removeStorageSync('defaultAccount')
							uni.switchTab({
								url: '/pages/index/index'
							})
							that.newMenuList[0].checked = true
							that.newMenuList[1].checked = false
							that.newMenuList[2].checked = false
						}
					}
				})
			},
			// 获取积分
			getPoints() {
				fetchMyPointsApi().then(res => {
					if (res.res) {
						const {
							obj: {
								totalIntegral,
								expireIntegral,
								expireDate
							}
						} = res
						this.dataObj = {
							totalIntegral: totalIntegral,
							expireIntegral: expireIntegral
						}
						uni.setStorageSync('totalIntegral', totalIntegral);
					} else {
						this.$toast(res.resMsg)
					}
				})
			},
			menuItem(data) {
				this.newMenuList.forEach(item => {
					if (data.id == item.id) {
						item.checked = true
					} else {
						item.checked = false
					}
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
	.syxHeight {
		height: 100vh;
	}

	.regular-user {
		// overflow: hidden;
		padding: 0 30rpx;

		.make-task {
			display: flex;
			justify-content: space-between;
			align-items: center;
			padding: 40rpx 0;
			margin-top: 20rpx;

			.label {
				text:nth-child(1) {
					font-size: 40rpx;
					font-weight: bold;
				}

				text:nth-child(2) {
					color: #B4B5B5;
					margin-left: 20rpx;
					font-size: 24rpx;
				}
			}

			image {
				width: 30rpx;
				height: 30rpx;
			}
		}

		.sub-menu {
			display: flex;
			justify-content: space-between;
			margin-top: 20rpx;

			.sub-menu-item {
				display: flex;
				flex-direction: column;
				justify-content: space-between;
				width: 48%;
				border-radius: 15rpx;
				background-color: #F8FAF9;
				padding: 20rpx;

				.money {
					text {
						display: block;
						font-weight: bold;
						font-size: 40rpx;
						max-width: 191rpx;
						margin-top: 10rpx;
					}
				}

				.btn {
					display: inline-block;
					padding: 5rpx 23rpx;
					background-color: $primary;
					border-radius: 30rpx;
					color: #fff;
					margin-top: 10rpx;
				}

				.label {
					display: flex;
					justify-content: space-between;
					color: #B4B5B5;
					font-size: 24rpx;

					image {
						width: 30rpx;
						height: 30rpx;
					}
				}
			}
		}

		.main-menu {
			display: flex;
			justify-content: space-around;
			align-items: center;
			margin-top: 30rpx;
			background-color: #F8FAF9;
			border-radius: 10rpx;
			height: 200rpx;

			.main-menu-item {
				text-align: center;
			}

			.num {
				font-size: 40rpx;
				font-weight: bold;
			}

			.label {
				color: #B4B5B5;
				font-size: 24rpx;
				margin-top: 10rpx;
			}
		}

		.badge {
			display: flex;
			justify-content: space-around;
			margin-top: 40rpx;

			image {
				width: 90rpx;
				height: 90rpx;
				border-radius: 50%;
			}
		}

		.log-out {
			text-align: center;
			padding: 20rpx 0;
			border-radius: 45rpx;
			margin: 100rpx auto 30rpx;
			background-color: #fff;
			color: $primary;
			border: 2rpx solid $primary;
		}

		.regular-user-header {
			width: 400rpx;
			height: 400rpx;
			border-radius: 50%;
			border: 2rpx solid #efefef;
			margin: 100rpx auto 0;
			text-align: center;

			image {
				width: 120rpx;
				height: 120rpx;
				border-radius: 50%;
				border: 2rpx solid #efefef;
				margin-top: 60rpx;
			}

			.nick-name,
			.user-mobile {
				margin-top: 10rpx;
				font-size: bold;
			}
		}
	}

	.admin-user {
		position: relative;
		height: 100%;

		.myUser {
			position: absolute;
			font-size: 45rpx;
			top: -80rpx;
			left: 50rpx;
			color: #fff;
		}

		.scan-btns {
			padding: 0 20rpx;
			height: 400rpx;
			background-color: #fff;
			border-top-left-radius: 30rpx;
			border-top-right-radius: 30rpx;

			.btns-list {
				margin-top: 30rpx;

				.btn-item {
					display: inline-block;
					width: 30%;
					height: 65rpx;
					text-align: center;
					line-height: 65rpx;
					color: #fff;
					background-color: $primary;
					border-radius: 5rpx;

					&:nth-child(3n-1) {
						margin: 0 5%;
					}

					&:nth-child(n+4) {
						margin-top: 30rpx;
					}
				}
			}

			.title {
				font-size: 30rpx;
				padding: 15rpx 0;
				text-align: center;
			}
		}

		.scan {
			position: fixed;
			right: 50rpx;
			bottom: 80rpx;
			width: 100rpx;
			height: 100rpx;
			border-radius: 50%;
			background-color: $primary;
			text-align: center;
			line-height: 100rpx;
			z-index: 2;

			image {
				width: 65rpx;
				height: 65rpx;
				vertical-align: middle;
			}
		}

		.cate-item {
			width: 50%;
			text-align: center;
			overflow: hidden;

			&:nth-child(n+3) {
				margin-top: 40rpx
			}


			image {
				display: block;
				margin: 0 auto 10rpx;
				width: 110rpx;
				height: 110rpx;
			}
		}

		.menus-item-active {
			position: relative;
			background-color: #fff;

			&::before {
				display: block;
				position: absolute;
				content: '';
				width: 8rpx;
				height: 40rpx;
				left: 0;
				top: 50%;
				margin-top: -20rpx;
				background-color: $primary;
			}
		}

		.main {
			display: flex;
			margin-top: 50rpx;

			.menus-list {
				width: 35%;
				background-color: #f6f6f6;

				.menuItem {
					display: flex;
					flex-direction: column;
					justify-content: center;
					align-items: center;
					width: 100%;
					height: 140rpx;
					background-color: #f6f6f6;
				}
			}

			.menus-Box {
				width: 65%;
				background-color: #fff;

				&>view {
					display: inline-block;
					width: 50%;
					height: 180rpx;
					margin-top: 40rpx;
					text-align: center;
					vertical-align: top;

					.span {
						font-size: 60rpx;
						color: #e96302;
					}

					.text {
						color: #000;
						margin-top: 10rpx;
					}
				}
			}

			// .menus-list {
			// 	margin-top: 40rpx;
			// 	padding: 0 40rpx;

			// 	.menus-item {
			// 		display: flex;
			// 		justify-content: space-between;
			// 		height: 100rpx;
			// 		vertical-align: middle;

			// 		text {
			// 			margin-left: 10rpx;
			// 		}

			// 		image {
			// 			width: 35rpx;
			// 			height: 35rpx;
			// 		}
			// 	}
			// }

			.menus-detail-cate {
				width: 75%;
				flex-wrap: wrap;
				// 解决flex换行时间距过大
				align-content: flex-start;
				overflow-y: scroll;
				padding: 40rpx 0;
			}
		}


	}

	.header {
		width: 100%;
		height: 200rpx;
		padding: 0 40rpx;
		color: #fff;
		margin-top: 170rpx;
		justify-content: space-between;

		.head {
			width: 150rpx;
			height: 150rpx;
			border-radius: 50%;
		}



		.label {
			text {
				display: block;
			}

			font-size: 52rpx;
		}

		.user-info {
			align-items: flex-start;
			flex-grow: 1;
			height: 53%;
			flex-direction: column;
			margin-left: 20rpx;

			.user-name {
				font-size: 38rpx;
				font-weight: bold;
			}
		}

		.log-out {
			image {
				width: 50rpx;
				height: 50rpx;
			}
		}
	}

	.bg {
		position: fixed;
		width: 100%;
		height: 420rpx;
		left: 0;
		top: 0;
		z-index: -1;
	}


	.login-btn {
		text-align: center;
		margin: 190rpx 40rpx 0;
		padding: 20rpx 0;
		border-radius: 45rpx;
		background-color: $primary;
		color: #fff;
	}


	// .container {
	// 	// overflow: hidden;
	// 	overflow-y: auto;
	// }

	.userBox {
		width: 440rpx;
		display: flex;
		flex-wrap: wrap;
		padding: 200rpx 20rpx 0 20rpx;

		.userItem {
			display: flex;
			align-items: center;
			flex-direction: column;
			width: 200rpx;
			height: 200rpx;

			view {
				display: flex;
				flex-direction: column;
				align-items: center;
				border: 10rpx #f39800 solid;
				border-radius: 8rpx;
				width: 80rpx;
				padding-bottom: 40rpx;
				padding-top: 4rpx;
				margin-top: 20rpx;
				margin-bottom: 20rpx;

				&>span {
					height: 15rpx;
					color: #f39800;
					font-weight: 900;
					font-size: 38rpx;
				}
			}
		}
	}
</style>
