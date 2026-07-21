<template>
	<view class="container">
		<view class="header">
			<input type="text" @confirm="search" placeholder="请输入订单号" maxlength="30" v-model="keyWord" />
		</view>

		<view class="list">
			<view class="item" v-for="(item, idx) in list" :key="idx">
				<view class="title">
					<view>{{ item.order_id }}</view>
					<view class="status">{{ status_list[item['status']]['val'] }}</view>
				</view>
				<view class="content">
					<view class="content-item">
						产品名称：{{ item['orderChildForms'][0]['goodsName'] }}
					</view>
					<view class="content-item">
						实验项目：{{ item['orderChildForms'][0]['experiment_project_name'] }}
					</view>
					<view class="content-item">
						实验分类：{{ item['orderChildForms'][0]['experiment_class_name'] }}
					</view>
					<view class="content-item">
						下单金额：{{ item['totalPrice'] ? item['totalPrice'].toFixed(2) : '0.00' }}
					</view>
					<view class="content-item">
						付款状态：{{ (item['isfk'] - 0) ? '支付完成' : '待支付' }}
					</view>
				</view>
				<view class="handle">
					<view @click="openChooseList(item)">支&nbsp;付</view>
				</view>
			</view>
		</view>
		<u-toast ref="uToast" />
		<my-loading :loading="loading" :is-refresh="isRefresh" :total="list.length"></my-loading>
		<pay-way :money="money" ref="pay_way" @choosePayWayEvent="choosePayWay"></pay-way>
	</view>
</template>

<script>
	import MyLoading from "@/components/loading.vue"
	import PayWay from '../pay_way.vue'
	import {
		fetchRepaymentListApi,
		// 余额还款
		balanceRepaymentApi,
		// 微信在线还款
		repaymentApi,
		fetchMyPointsApi,
	} from '@/api/index.js'
	export default {
		components: {
			MyLoading,
			PayWay
		},
		data() {
			return {
				page: 1,
				isRefresh: true,
				loading: false,
				list: [],
				keyWord: '',
				order_id: '',
				money: 0
			}
		},
		onLoad() {
			this.getList()
		},
		onReachBottom() {
			if (this.isRefresh) {
				this.page++
				this.getList()
			}
		},
		methods: {
			async choosePayWay(e, integral_num, money) {
				let that = this;
				this.$refs['pay_way']['$refs']['pay_way'].close()
				this.$refs['pay_way'].popupShow = false
				if (e == 'abc') {
					this.money = 0
					return
				} else if (e) {
					if (money) {
						balanceRepaymentApi({
							ofId: this.order_id,
							useIntegral: integral_num,
							pay_way: 2
						}).then(res => {
						that.$tip(res.res ? '支付成功' : res.resMsg)
						if (res.res) {
							this.getList()
							this.money = 0
							fetchMyPointsApi().then(res => {
								if (res.res) {
									uni.setStorageSync('totalIntegral', res.obj.totalIntegral);
								}
							})
						}
						})
					} else {
						const result = await wx.login()

						repaymentApi({
							ofId: this.order_id,
							code: result.code,
							useIntegral: integral_num
						}).then(res => {
							if (res.res) {
								const {
									timeStamp,
									prepayId,
									paySign,
									nonceStr,
								} = res.obj
								// uni.showLoading()
								wx.requestPayment({
									timeStamp: timeStamp + '',
									nonceStr,
									package: `prepay_id=${prepayId}`,
									signType: 'RSA',
									paySign,
									success(res) {
										that.$tip('支付成功！')
										that.getList()
										this.money = 0
										fetchMyPointsApi().then(res => {
											if (res.res) {
												uni.setStorageSync('totalIntegral', res.obj
													.totalIntegral);
											}
										})
									},
									fail(e) {
										that.$tip('支付失败，请重试！')
									},
									complete() {
										uni.hideLoading()
									}
								})
							} else {
								this.$tip('支付失败，请重试！')
							}
						})
					}

				} else {

					balanceRepaymentApi({
						ofId: this.order_id,
						useIntegral: integral_num,
						pay_way: 4
					}).then(res => {
						that.$tip(res.res ? '支付成功' : res.resMsg)
						if (res.res) {
							this.getList()
							this.money = 0
							fetchMyPointsApi().then(res => {
								if (res.res) {
									uni.setStorageSync('totalIntegral', res.obj.totalIntegral);
								}
							})
						}
					})
				}
				this.money = 0

			},

			// 使用余额支还款
			openChooseList(item) {
				let xsskje = item.xsskje ? item.xsskje : 0
				let totalPrice = item.totalPrice ? item.totalPrice : 0
				this.money = (totalPrice * 100 - xsskje * 100) / 100
				this.order_id = item.id
				// this.$refs['pay_way']['$refs']['pay_way'].open()
				this.$refs['pay_way'].popupShow = true
			},

			search() {
				this.page = 1
				this.isRefresh = true
				this.list = []
				this.getList()
			},

			makeInvoice(id, m) {
				uni.navigateTo({
					url: `/pagesB/confirm_make_invoice/confirm_make_invoice?id=${id}&m=${m}`
				})
			},

			getList() {
				this.loading = true
				fetchRepaymentListApi({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
					keywords: this.keyWord,
					type: '1'
				}).then(res => {
					if (res.res) {
						if (res.obj.data.length !== 10) {
							this.isRefresh = false
						}
						this.list = [...this.list, ...res.obj.data]
					} else {
						this.$toast(res.resMsg)
					}
				}).finally(_ => {
					this.loading = false
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
	.header {
		position: fixed;
		left: 0;
		width: 100%;
		box-sizing: border-box;
		border-bottom: 1rpx solid #F2F2F2;
		height: 80rpx;
		padding: 10rpx 30rpx;
		background-color: #fff;

		input {
			height: 60rpx;
			background-color: #E9E9E9;
			box-sizing: border-box;
			padding: 0 20rpx;
			border-radius: 5rpx;
		}

	}

	.handle {
		display: flex;
		flex-direction: row-reverse;
		color: $primary;
		padding: 20rpx 0;
	}

	.list {
		margin: 80rpx 30rpx 0;
		overflow: hidden;

		.item {
			background-color: #fff;
			padding: 0 20rpx;

			&:nth-child(n+1) {
				margin-top: 25rpx;
			}

			.status {
				color: $primary;
			}
		}

		.title {
			display: flex;
			justify-content: space-between;
			padding: 20rpx 0;
		}

		.content {
			padding: 20rpx 0;
			border-bottom: 1rpx solid #F2F2F2;
			border-top: 1rpx solid #F2F2F2;

			.content-item {
				&:nth-child(n+1) {
					margin-top: 10rpx;
				}
			}
		}
	}

	.container {
		overflow: hidden;
	}
</style>

<style>
	page {
		background-color: #F2F2F2;
	}
</style>