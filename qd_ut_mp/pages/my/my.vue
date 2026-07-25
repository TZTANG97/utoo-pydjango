<template>
	<view class="container syxHeight" :style="{ overflow: userInfo && userInfo.uType ? 'hidden' : 'auto' }">
		<image class="bg" src="@/static/my-bg.png" mode=""></image>
		<template v-if="!userInfo">
			<view class="guest-user">
				<view class="guest-hero">
					<text class="guest-hero__title">个人中心</text>
					<view class="guest-hero__row">
						<image class="guest-hero__avatar" src="@/static/head.png" mode="aspectFill" />
						<view class="guest-hero__meta">
							<view class="guest-hero__hi">Hi，欢迎来到愉兔检测</view>
							<view class="guest-hero__tip">登录后查看订单、积分与预约</view>
						</view>
					</view>
				</view>
				<view class="guest-sheet">
					<view class="guest-login" @click="viewMyProfile">注册 / 登录</view>
					<view class="guest-hint">检测预约 · 积分兑换 · 发票管理</view>
				</view>
			</view>
		</template>

		<template v-else-if="userInfo.uType">
			<view class="admin-user">
				<view class="admin-hero">
					<text class="admin-hero__title">个人中心</text>
					<view class="admin-hero__row" @click="viewMyProfile">
						<image class="admin-hero__avatar" v-if="userInfo['photo']" :src="userInfo['photo']" mode="aspectFill" />
						<image class="admin-hero__avatar" v-else src="@/static/head.png" mode="aspectFill" />
						<view class="admin-hero__meta" :class="{ 'is-center': !userInfo.mobile }">
							<view class="admin-hero__name">
								{{ userInfo.wx_nickname ? userInfo.wx_nickname : '没有昵称' }}
							</view>
							<view class="admin-hero__phone" v-if="userInfo.mobile">
								{{ userInfo.mobile }}
							</view>
						</view>
						<view class="admin-hero__logout" @click.stop="logOut">
							<image src="@/static/logout.png" mode=""></image>
							<text>退出</text>
						</view>
					</view>
				</view>

				<view class="admin-main" v-if="userInfo.userType != 5">
					<scroll-view scroll-y class="admin-side" :show-scrollbar="false">
						<view
							v-for="item in sideMenuList"
							:key="item.id"
							class="admin-side__item"
							:class="{ 'is-active': item.checked }"
							@click="menuItem(item)"
						>
							<text class="admin-side__name">{{ item.name }}</text>
							<text v-if="item.num >= 0" class="admin-side__num">{{ item.num }}</text>
						</view>
					</scroll-view>

					<scroll-view scroll-y class="admin-panel" :show-scrollbar="false">
						<view v-if="activeMenu" class="admin-panel__grid">
							<view
								v-for="(subItem, subInd) in activeMenu.childs"
								:key="subInd"
								class="admin-panel__cell"
							>
								<UtStatCard
									:title="subItem.name"
									:mark="subItem.icon"
									:count="statCardCount(subItem)"
									@click="cutMenu(subInd, subItem)"
								/>
							</view>
						</view>
					</scroll-view>
				</view>

				<view class="admin-scan" @click="$refs.scan.open()" v-if="userInfo && userInfo.uType">
					<image src="@/static/scan.png" mode=""></image>
				</view>

				<uni-popup ref="scan" type="bottom">
					<view class="scan-btns">
						<view class="title">扫码操作</view>
						<view class="btns-list">
							<view class="btn-item" @click="logInfo(1)">入库</view>
							<view class="btn-item" @click="logInfo(2)">领用</view>
							<view class="btn-item" @click="logInfo(3)">开始测试</view>
							<view class="btn-item" @click="logInfo(4)">完成测试</view>
							<view class="btn-item" @click="logInfo(5)">样品归还</view>
							<view class="btn-item" @click="logInfo(6)">样品寄回</view>
							<view class="btn-item" @click="logInfo(7)">样品留存</view>
							<view class="btn-item" @click="logInfo(8)">客户确认完成</view>
						</view>
					</view>
				</uni-popup>
			</view>
		</template>

		<template v-else>
			<view class="regular-user">
				<view class="regular-hero">
					<text class="regular-hero__title">个人中心</text>
					<view class="regular-hero__row" @click="viewMyProfile">
						<image class="regular-hero__avatar" v-if="userInfo['photo']" :src="userInfo['photo']" mode="aspectFill" />
						<image class="regular-hero__avatar" v-else src="@/static/head.png" mode="aspectFill" />
						<view class="regular-hero__meta">
							<view class="regular-hero__name">
								{{ userInfo.wx_nickname ? userInfo.wx_nickname : '没有昵称' }}
							</view>
							<view class="regular-hero__phone">
								{{ userInfo.mobile ? userInfo.mobile : '没有手机号' }}
							</view>
						</view>
						<view class="regular-hero__logout" @click.stop="logOut">
							<image src="@/static/logout.png" mode=""></image>
							<text>退出</text>
						</view>
					</view>
				</view>

				<view class="regular-sheet">
					<view class="regular-badge">
						<template v-for="item in 5">
							<image v-if="wcOrderCount >= (item + 1) * 10" :key="'bl' + item" src="@/static/badge-light.png" mode=""></image>
							<image v-else :key="'bd' + item" src="@/static/badge.png" mode=""></image>
						</template>
					</view>

					<view class="regular-stats">
						<view class="regular-stats__item" @click="cutMenu(0)">
							<view class="regular-stats__num">{{ userNum['orderCount'] }}</view>
							<view class="regular-stats__label">我的订单</view>
						</view>
						<view class="regular-stats__item regular-stats__item--mid" @click="cutMenu(3)">
							<view class="regular-stats__num">{{ userNum['fpCount'] }}</view>
							<view class="regular-stats__label">我的发票</view>
						</view>
						<view class="regular-stats__item" @click="cutMenu(5)">
							<view class="regular-stats__num">{{ userNum['yuyueCount'] }}</view>
							<view class="regular-stats__label">预约记录</view>
						</view>
					</view>

					<view class="regular-assets">
						<view class="regular-asset" @click="cutMenu(2)">
							<view class="regular-asset__label">我的积分</view>
							<view class="regular-asset__value">{{ dataObj.totalIntegral }}</view>
							<view class="regular-asset__btn">兑换</view>
						</view>
						<view class="regular-asset" @click="cutMenu(1)">
							<view class="regular-asset__label">
								<text>我的余额</text>
								<image @click.stop="checkBalance = false" v-if="checkBalance" src="@/static/eye.png" mode=""></image>
								<image @click.stop="checkBalance = true" v-else src="@/static/eye-close.png" mode=""></image>
							</view>
							<view class="regular-asset__value" v-if="checkBalance">{{ userNum['balance'].toFixed(2) }}</view>
							<view class="regular-asset__value" v-else>******</view>
							<view class="regular-asset__btn">充值</view>
						</view>
					</view>

					<view class="regular-tasks">
						<view class="regular-task" @click="taskFn(1)">
							<view class="regular-task__en">DAILYLOGIN</view>
							<view class="regular-task__zh">每日签到</view>
						</view>
						<view class="regular-task" @click="taskFn(2)">
							<view class="regular-task__en">MISSION</view>
							<view class="regular-task__zh">我的任务</view>
						</view>
						<view class="regular-task" @click="taskFn(3)">
							<view class="regular-task__en">FEEDBACK</view>
							<view class="regular-task__zh">意见反馈</view>
						</view>
					</view>

					<view class="regular-logout" @click="logOut">退出登录</view>
				</view>
			</view>
		</template>
		<u-popup v-model="show" mode="right">
			<view class="userBox">
				<view v-for="item,index in userList" v-if="(userInfo.userType == 1 && item.id !=1) || userInfo.userType != 1" :key="index"
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
		getOrderCount,
		signInIntegral
	} from '@/api/index.js'
	import UtStatCard from '@/components/UtStatCard.vue'
	export default {
		components: {
			UtStatCard
		},
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
						id: 4,
						name: '预约列表',
						checked: false,
						childs:[
							{
								id: '4-1',
								label: '预约列表',
								name: '预约列表',
								path: 'reservationList',
								pageB: true,
								icon: '预',
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
			const raw = uni.getStorageSync('userInfo')
			// 空字符串 / 非法值统一视为未登录，避免模板在多套 UI 间抖动
			this.userInfo = raw && typeof raw === 'object' ? raw : null
			if (!this.userInfo) {
				this.menusList = this.cateList
				return
			}
			// 0普通 1内部
			if (!this.userInfo.uType) {
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
						this.userNum = res.obj
						this.wcOrderCount = res.obj.wcOrderCount
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
			// 仅登录后拉订单统计；未登录调接口会触发「用户未登录」→ reLaunch 个人中心死循环闪烁
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
		computed: {
			sideMenuList() {
				const list = this.newMenuList || []
				const userType = this.userInfo && this.userInfo.userType
				if (userType == 3) return list
				return list.filter((_, index) => index != 2)
			},
			activeMenuIndex() {
				const list = this.newMenuList || []
				return list.findIndex((item) => item.checked)
			},
			activeMenu() {
				const idx = this.activeMenuIndex
				if (idx < 0) return null
				return this.newMenuList[idx] || null
			}
		},
		methods: {
			taskFn(type){
				if(type == 1){
					signInIntegral().then(res=>{
						if(res.res && res.resMsg == '签到成功'){
							this.getPoints()
						}
						this.$toast(res.resMsg)
					})
				}else{
					this.$toast('敬请期待！')
				}
			},
			getOrderCountFn() {
				getOrderCount().then(res => {
					if (res.res && res.obj) {
						const obj = res.obj
						const n = (v) => {
							const x = Number(v)
							return Number.isFinite(x) ? x : 0
						}
						if (obj.orderCountByManage != null && obj.orderCountByManage !== '' && this.newMenuList[2]) {
							this.newMenuList[2].num = n(obj.orderCountByManage)
							this.newMenuList[2].childs[0].num = n(obj.orderCountm)
							this.newMenuList[2].childs[1].num = n(obj.suborderCountm)
							this.newMenuList[2].childs[2].num = n(obj.orderchildCountm)
							this.newMenuList[2].childs[3].num = n(obj.suborderchildCountm)
							this.newMenuList[2].childs[4].num = n(obj.expsubChildpayListnum)
						}
						if (obj.orderCountAll != null && obj.orderCountAll !== '') {
							this.newMenuList[1].num = n(obj.orderCountAll)
							this.newMenuList[1].childs[0].num = n(obj.orderCount)
							this.newMenuList[1].childs[1].num = n(obj.suborderCount)
							this.newMenuList[1].childs[2].num = n(obj.orderchildCount)
							this.newMenuList[1].childs[3].num = n(obj.suborderchildCount)
						}
					}
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
				if (item && item.nb == 666) {
					this.show = true
				} else {
					// 内部用户
					if (this.userInfo['uType']) {
						const {
							path,
							type,
							all = '',
							pathB,
							pageB
						} = item
						console.log(pathB, 'pathB')
						if (pathB) {
							return uni.navigateTo({
								url: `/staffB/${path}/${path}?type=${type}&all=${all}`
							})
						} else if(pageB) {
							return uni.navigateTo({
								url: `/pagesB/${path}/${path}`
							})
						}else{
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
			},
			/** 避免模板里复杂三元写入属性，兼容 mp-weixin 编译 */
			statCardCount(subItem) {
				if (this.activeMenuIndex === 0) return null
				if (!subItem) return null
				if (subItem.num === 0 || subItem.num) return subItem.num
				return null
			}
		}
	}
</script>

<style lang="scss" scoped>
	.syxHeight {
		height: 100vh;
	}

	.regular-user {
		position: relative;
		z-index: 1;
		padding-bottom: calc(40rpx + env(safe-area-inset-bottom));

		.regular-hero {
			padding: 160rpx $ut-space-4 36rpx;
		}

		.regular-hero__title {
			display: block;
			font-size: 40rpx;
			font-weight: 600;
			color: #fff;
			margin-bottom: 28rpx;
		}

		.regular-hero__row {
			display: flex;
			align-items: center;
		}

		.regular-hero__avatar {
			width: 112rpx;
			height: 112rpx;
			border-radius: 50%;
			border: 4rpx solid rgba(255, 255, 255, 0.55);
			flex-shrink: 0;
			background: rgba(255, 255, 255, 0.2);
		}

		.regular-hero__meta {
			flex: 1;
			min-width: 0;
			margin-left: $ut-space-3;
		}

		.regular-hero__name {
			font-size: 34rpx;
			font-weight: 600;
			color: #fff;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}

		.regular-hero__phone {
			margin-top: 8rpx;
			font-size: 24rpx;
			color: rgba(255, 255, 255, 0.85);
		}

		.regular-hero__logout {
			flex-shrink: 0;
			display: flex;
			flex-direction: column;
			align-items: center;
			padding: 12rpx 16rpx;
			margin-left: $ut-space-2;
			border-radius: $ut-radius-md;
			background: rgba(255, 255, 255, 0.18);

			image {
				width: 36rpx;
				height: 36rpx;
			}

			text {
				margin-top: 4rpx;
				font-size: 22rpx;
				color: #fff;
			}
		}

		.regular-sheet {
			margin: 0 $ut-space-3;
			padding: $ut-space-4;
			border-radius: $ut-radius-lg;
			background: $ut-card;
			box-shadow: 0 -8rpx 24rpx rgba(31, 35, 41, 0.06);
		}

		.regular-badge {
			display: flex;
			justify-content: space-between;
			padding: 0 8rpx 8rpx;

			image {
				width: 72rpx;
				height: 72rpx;
				border-radius: 50%;
			}
		}

		.regular-stats {
			display: flex;
			margin-top: $ut-space-3;
			padding: $ut-space-3 0;
			border-radius: $ut-radius-md;
			background: $ut-bg;

			&__item {
				flex: 1;
				text-align: center;

				&--mid {
					border-left: 1rpx solid $ut-border;
					border-right: 1rpx solid $ut-border;
				}

				&:active {
					opacity: 0.85;
				}
			}

			&__num {
				font-size: 36rpx;
				font-weight: 700;
				color: $ut-primary;
			}

			&__label {
				margin-top: 8rpx;
				font-size: 22rpx;
				color: $ut-text-secondary;
			}
		}

		.regular-assets {
			display: flex;
			gap: $ut-space-3;
			margin-top: $ut-space-3;
		}

		.regular-asset {
			flex: 1;
			padding: $ut-space-3;
			border-radius: $ut-radius-md;
			background: linear-gradient(160deg, $ut-primary-soft 0%, #FFF8F2 100%);
			border: 1rpx solid rgba(233, 99, 2, 0.1);

			&:active {
				opacity: 0.9;
			}

			&__label {
				display: flex;
				align-items: center;
				justify-content: space-between;
				font-size: 22rpx;
				color: $ut-text-secondary;

				image {
					width: 28rpx;
					height: 28rpx;
				}
			}

			&__value {
				margin-top: 12rpx;
				font-size: 36rpx;
				font-weight: 700;
				color: $ut-text;
				overflow: hidden;
				text-overflow: ellipsis;
				white-space: nowrap;
			}

			&__btn {
				display: inline-block;
				margin-top: 16rpx;
				padding: 6rpx 22rpx;
				border-radius: 999rpx;
				background: $ut-primary;
				color: #fff;
				font-size: 22rpx;
			}
		}

		.regular-tasks {
			margin-top: $ut-space-3;
			border-radius: $ut-radius-md;
			overflow: hidden;
			border: 1rpx solid $ut-border;
		}

		.regular-task {
			display: flex;
			align-items: center;
			padding: 28rpx $ut-space-3;
			background: $ut-card;
			border-bottom: 1rpx solid $ut-border;

			&:last-child {
				border-bottom: none;
			}

			&:active {
				background: $ut-bg;
			}

			&__en {
				font-size: 24rpx;
				font-weight: 700;
				color: $ut-text;
				min-width: 200rpx;
			}

			&__zh {
				font-size: 26rpx;
				color: $ut-text-secondary;
			}
		}

		.regular-logout {
			margin-top: $ut-space-4;
			text-align: center;
			padding: 22rpx 0;
			border-radius: 999rpx;
			color: $ut-primary;
			border: 2rpx solid $ut-primary;
			font-weight: 600;
			background: $ut-card;

			&:active {
				background: $ut-primary-soft;
			}
		}
	}

	.guest-user {
		position: relative;
		z-index: 1;

		.guest-hero {
			padding: 160rpx $ut-space-4 36rpx;
		}

		.guest-hero__title {
			display: block;
			font-size: 40rpx;
			font-weight: 600;
			color: #fff;
			margin-bottom: 28rpx;
		}

		.guest-hero__row {
			display: flex;
			align-items: center;
		}

		.guest-hero__avatar {
			width: 112rpx;
			height: 112rpx;
			border-radius: 50%;
			border: 4rpx solid rgba(255, 255, 255, 0.55);
			flex-shrink: 0;
			background: rgba(255, 255, 255, 0.2);
		}

		.guest-hero__meta {
			margin-left: $ut-space-3;
		}

		.guest-hero__hi {
			font-size: 32rpx;
			font-weight: 600;
			color: #fff;
		}

		.guest-hero__tip {
			margin-top: 10rpx;
			font-size: 24rpx;
			color: rgba(255, 255, 255, 0.85);
		}

		.guest-sheet {
			margin: 0 $ut-space-3;
			padding: $ut-space-4;
			border-radius: $ut-radius-lg;
			background: $ut-card;
			box-shadow: 0 -8rpx 24rpx rgba(31, 35, 41, 0.06);
		}

		.guest-login {
			text-align: center;
			padding: 26rpx 0;
			border-radius: 999rpx;
			background: $ut-primary;
			color: #fff;
			font-size: 30rpx;
			font-weight: 600;

			&:active {
				opacity: 0.9;
			}
		}

		.guest-hint {
			margin-top: $ut-space-3;
			text-align: center;
			font-size: 22rpx;
			color: $ut-text-secondary;
		}
	}

	.admin-user {
		position: relative;
		height: 100%;
		display: flex;
		flex-direction: column;

		.admin-hero {
			position: relative;
			z-index: 1;
			padding: 160rpx $ut-space-4 36rpx;
		}

		.admin-hero__title {
			display: block;
			font-size: 40rpx;
			font-weight: 600;
			color: #fff;
			margin-bottom: 28rpx;
		}

		.admin-hero__row {
			display: flex;
			align-items: center;
		}

		.admin-hero__avatar {
			width: 112rpx;
			height: 112rpx;
			border-radius: 50%;
			border: 4rpx solid rgba(255, 255, 255, 0.55);
			flex-shrink: 0;
			background: rgba(255, 255, 255, 0.2);
		}

		.admin-hero__meta {
			flex: 1;
			min-width: 0;
			margin-left: $ut-space-3;
			display: flex;
			flex-direction: column;
			justify-content: center;

			&.is-center {
				justify-content: center;
			}
		}

		.admin-hero__name {
			font-size: 34rpx;
			font-weight: 600;
			color: #fff;
			max-width: 360rpx;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}

		.admin-hero__phone {
			margin-top: 8rpx;
			font-size: 24rpx;
			color: rgba(255, 255, 255, 0.85);
		}

		.admin-hero__logout {
			flex-shrink: 0;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			padding: 12rpx 16rpx;
			margin-left: $ut-space-2;
			border-radius: $ut-radius-md;
			background: rgba(255, 255, 255, 0.18);

			image {
				width: 36rpx;
				height: 36rpx;
			}

			text {
				margin-top: 4rpx;
				font-size: 22rpx;
				color: #fff;
			}

			&:active {
				background: rgba(255, 255, 255, 0.28);
			}
		}

		.admin-main {
			flex: 1;
			min-height: 0;
			display: flex;
			margin: 0 $ut-space-3 0;
			border-radius: $ut-radius-lg $ut-radius-lg 0 0;
			overflow: hidden;
			background: $ut-card;
			box-shadow: 0 -8rpx 24rpx rgba(31, 35, 41, 0.06);
		}

		.admin-side {
			width: 210rpx;
			height: 100%;
			background: $ut-bg;
			flex-shrink: 0;
		}

		.admin-side__item {
			position: relative;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			min-height: 128rpx;
			padding: $ut-space-2 12rpx;
			color: $ut-text-secondary;

			&.is-active {
				background: $ut-card;
				color: $ut-text;
				font-weight: 600;

				&::before {
					content: '';
					position: absolute;
					left: 0;
					top: 50%;
					transform: translateY(-50%);
					width: 6rpx;
					height: 40rpx;
					border-radius: 0 6rpx 6rpx 0;
					background: $ut-primary;
				}
			}
		}

		.admin-side__name {
			font-size: 26rpx;
			text-align: center;
			line-height: 1.35;
		}

		.admin-side__num {
			margin-top: 8rpx;
			font-size: 22rpx;
			color: $ut-primary;
			font-weight: 600;
		}

		.admin-panel {
			flex: 1;
			height: 100%;
			background: $ut-card;
		}

		.admin-panel__grid {
			display: flex;
			flex-wrap: wrap;
			padding: $ut-space-3 $ut-space-2 $ut-space-4;
			box-sizing: border-box;
		}

		.admin-panel__cell {
			width: 50%;
			padding: 8rpx;
			box-sizing: border-box;
		}

		.scan-btns {
			padding: 0 $ut-space-3 40rpx;
			background-color: $ut-card;
			border-top-left-radius: $ut-radius-lg;
			border-top-right-radius: $ut-radius-lg;

			.btns-list {
				margin-top: $ut-space-3;

				.btn-item {
					display: inline-block;
					width: 30%;
					height: 68rpx;
					text-align: center;
					line-height: 68rpx;
					color: #fff;
					background-color: $ut-primary;
					border-radius: $ut-radius-sm;

					&:nth-child(3n-1) {
						margin: 0 5%;
					}

					&:nth-child(n+4) {
						margin-top: $ut-space-3;
					}
				}
			}

			.title {
				font-size: 30rpx;
				padding: $ut-space-3 0;
				text-align: center;
				color: $ut-text;
				font-weight: 600;
			}
		}

		.admin-scan {
			position: fixed;
			right: $ut-space-4;
			bottom: calc(120rpx + env(safe-area-inset-bottom));
			width: 104rpx;
			height: 104rpx;
			border-radius: 50%;
			background-color: $ut-primary;
			display: flex;
			align-items: center;
			justify-content: center;
			z-index: 2;
			box-shadow: 0 10rpx 28rpx rgba(233, 99, 2, 0.4);

			image {
				width: 56rpx;
				height: 56rpx;
			}
		}
	}

	.bg {
		position: fixed;
		width: 100%;
		height: 420rpx;
		left: 0;
		top: 0;
		z-index: 0;
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
