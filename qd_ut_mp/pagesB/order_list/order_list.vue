<template>
	<view class="container">
		<view class="search-header">
			<input type="text" v-model="key_words" placeholder="请输入关键词进行检索" maxlength="30">
			<view class="btn" @click="search">
				搜索
			</view>
		</view>

		<view class="order-status">
			<text @click="changeOrderStatus(idx)" :class="{ 'order-status-active': idx === selected_status }"
				v-for="(item, idx) in order_status_list" :key="idx">{{ item }}</text>
		</view>

		<view class="list">
			<view class="item" v-for="(item, idx3) in list" :key="idx3" @click="viewDetail(item.id)">
				<view class="item-row">
					<text>订单编号：{{ item.order_id }}</text>
				</view>
				<view class="item-row">
					<text>客户名称：{{ item['orderChildForms'][0]['goodsBrandName'] }}</text>
				</view>
				<view class="item-row">
					<text>样品名称：{{ item['orderChildForms'][0]['goodsName'] }}</text>
				</view>
				<view class="item-row" v-if="item['orderChildForms'][0]['goodsSpec']">
					<text>样品型号：{{ item['orderChildForms'][0]['goodsSpec'] }}</text>
				</view>
				<view class="item-row">
					<text>实验项目：{{ item['orderChildForms'][0]['experiment_project_name'] }}</text>
				</view>
				<view class="item-row">
					<text>实验分类：{{ item['orderChildForms'][0]['experiment_class_name'] }}</text>
				</view>
				<view class="item-row">
					<text>实付款金额：{{ item['xsskje']? item['xsskje'].toFixed(2) : '0.00' }}</text>
				</view>
				<view class="item-row">
					<text>下单金额：{{ item['totalPrice'] ? item['totalPrice'].toFixed(2) : '0.00' }}</text>
				</view>
				<view class="item-row">
					<text>订单状态：{{ item['order_statusstr'] }}</text>
				</view>
				<view class="item-row">
					<text>开票状态：{{ (item['iskp'] - 0) ? '完成' : '未完成' }}</text>
				</view>
				<view class="item-row">
					<text>付款状态：{{ (item['isfk'] - 0) ? '付款完成' : '待付款' }}</text>
				</view>
<!-- 				<template v-if="item['files'].length">
					<view class="item-row">
						<text>订单资料：</text>
					</view>
					<view class="item-row file" v-for="(file, idx4) in item['files']" :key="idx4"
						@click.stop="downloadFile(file['path'] + '/' + file['name'])">
						<text>{{ file['info'] }}</text>
					</view>
				</template> -->
				<template v-if="item['fpFiles'].length">
					<view class="item-row">
						<text>发票资料：</text>
					</view>
					<view class="item-row file" v-for="(file, idx2) in item['fpFiles']" :key="idx2"
						@click.stop="downloadFile(file['path'] + '/' + file['name'])">
						<text>{{ file['info'] }}</text>
					</view>
				</template>
				<view class="btns">
					<view class="btn" v-if="!(item['isfk'] - 0) && item['isUploadReceipt'] !== 1"
						@click.stop="pay(item)">
						支付
					</view>
					<view class="btn" v-if="(item['kpShow'] - 0) && item['invoiceType'] === 1"
						@click.stop="applyMakeInvoice(item['id'], item['dkpje'])">
						申请开票
					</view>
					<view class="btn" v-if="item['printYydShow']" @click.stop="saveFile(item.id)">
						下载预约单
					</view>

					<navigator v-if="item['ispjqx']" class="btn" :url="`/pagesB/evaluate/evaluate?id=${item['id']}`"
						hover-class="none">
						评价
					</navigator>

					<view v-if="item['fcShow'] == 1" class="btn" @click.stop="dtcOrder(1, item['id'])">
						再次测试
					</view>
					<view v-if="item['wcShow'] == 1" class="btn" @click.stop="dtcOrder(2, item['id'])">
						确认完成
					</view>
				</view>
			</view>
		</view>
		<my-loading :loading="loading" :isRefresh="is_refresh" :total="list.length"></my-loading>

		<u-toast ref="uToast" />
		<pay-way :money="money" ref="pay_way" @choosePayWayEvent="choosePayWay"></pay-way>
	</view>
</template>

<script>
	import {
		fetchOrderListApi,
		fetchPDFUrlApi,
		balanceRepaymentApi,
		fetchOrderPrePayId,
		getFinishChildOrderListApi,
		fetchMyPointsApi,
	} from '@/api/index.js'
	import MyLoading from "@/components/loading.vue"
	import PayWay from '../pay_way.vue'
	export default {
		components: {
			MyLoading,
			PayWay
		},
		data() {
			return {
				list: [],
				page: 1,
				is_refresh: true,
				loading: false,
				key_words: '',
				order_status_list: [
					'全部',
					'待支付',
					'待实验',
					'实验中',
					'已完成',
					// '售后',
				],
				selected_status: 0,
				ofId: '',
				money: 0
			};
		},
		onLoad() {
			// 监听评价的完成
			uni.$_on('finishEval', id => {
				const idx = this.list.findIndex(item => item.id === id - 0)
				this.$set(this.list[idx], 'ispjqx', false)
			})
		},
		onShow() {
			this.page = 1
			this.list = []
			this.getList()
		},
		onReachBottom() {
			if (this.is_refresh) {
				this.page++;
				this.getList()
			}
		},
		methods: {
			dtcOrder(type, id) {
				getFinishChildOrderListApi({
					type,
					id
				}).then(res => {
					if (res.res) {
						if (!res.obj.length) {
							this.$toast('没有可操作的子订单')
						} else {
							uni.setStorageSync('childList', JSON.stringify(res.obj))
							uni.navigateTo({
								url: '/pagesB/anew_test/anew_test?type=' + type
							})
						}
					} else {
						this.$toast('没有可操作的子订单')
					}
				})
			},

			async choosePayWay(flag, integral_num, money) {
				this.$refs['pay_way']['$refs']['pay_way'].close()
				this.$refs['pay_way'].popupShow = false
				// 1微信 0余额 
				console.log(flag, 'flag')
				if (flag == 'abc') {
					this.money = 0
					return
				} else if (flag) {
					if (money) {
						console.log('我是微信支付0元')
						balanceRepaymentApi({
							ofId: this.ofId,
							useIntegral: integral_num,
							pay_way: 2
						}).then(res => {
							this.$tip(res.res ? '支付成功' : res.resMsg)
							if (res.res) {
								this.list = []
								this.page = 1
								this.is_refresh = true
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
						console.log('我是微信支付')
						const result = await wx.login(),
							that = this;
						fetchOrderPrePayId({
							ofId: this.ofId,
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
								wx.requestPayment({
									timeStamp: timeStamp + '',
									nonceStr,
									package: `prepay_id=${prepayId}`,
									signType: 'RSA',
									paySign,
									success(res) {
										that.$tip('支付成功！')
										that.list = []
										that.page = 1
										that.is_refresh = true
										that.getList()
										that.money = 0
										fetchMyPointsApi().then(res => {
											if (res.res) {
												uni.setStorageSync('totalIntegral', res.obj
													.totalIntegral);
											}
										})
									},
									fail(e) {
										console.log(e, '支付失败')
										uni.hideLoading()
										that.$tip('支付失败，请重试！')
									}
								})
							} else {
								that.$tip('支付失败，请重试！')
							}
						})
					}

				} else {
					console.log('我是余额支付')
					balanceRepaymentApi({
						ofId: this.ofId,
						useIntegral: integral_num,
						pay_way: 4
					}).then(res => {
						this.$tip(res.res ? '支付成功' : res.resMsg)
						if (res.res) {
							this.list = []
							this.page = 1
							this.is_refresh = true
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

			},

			// 下载
			downloadFile(path) {
				const that = this
				uni.setClipboardData({
					data: path,
					success() {
						that.$toast('链接已复制，请打开浏览器下载！');
					}
				});
			},

			// 申请开票
			applyMakeInvoice(id, dkpje) {
				uni.navigateTo({
					url: `/pagesB/confirm_make_invoice/confirm_make_invoice?id=${id}&money=${dkpje}&type=2`
				})
			},

			// 订单支付
			pay(item) {
				this.ofId = item.id
				let xsskje = item.xsskje ? item.xsskje : 0
				let totalPrice = item.totalPrice ? item.totalPrice : 0
				this.money = (totalPrice * 100 - xsskje * 100) / 100

				this.$refs['pay_way'].popupShow = true
				// this.$refs['pay_way']['$refs']['pay_way'].open()
			},

			// 保存文件
			saveFile(id) {
				fetchPDFUrlApi({
					id
				}).then(res => {
					if (res.res) {
						const that = this
						const {
							url
						} = res.obj
						uni.setClipboardData({
							data: url,
							success(res) {
								uni.hideLoading()
								that.$tip('链接已复制，请打开浏览器下载！')
							}
						});
					} else {
						this.$tip('下载失败，请重试！')
					}
				})
			},


			// 查看详情
			viewDetail(id) {
				uni.navigateTo({
					url: '/pagesB/order_detail/order_detail?id=' + id
				})
			},

			// 更改选中的子订单状态
			changeOrderStatus(idx) {
				if (this.selected_status === idx) return
				this.selected_status = idx
				this.page = 1
				this.is_refresh = true
				this.list = []
				this.getList()
			},


			search() {
				this.list = []
				this.page = 1
				this.is_refresh = true
				this.getList()
			},
			getList() {
				this.loading = true
				fetchOrderListApi({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
					keywords: this.key_words,
					type: this.selected_status
				}).then(res => {
					console.log(res,'res')
					if (res.res) {
						const {
							obj: {
								data
							}
						} = res
						if (data.length !== 10) this.is_refresh = false
						data.forEach(item => {
							item.page = 0;
							item.isRefresh = true;
							item.first_child = [];
							item.first_child[0] = item.orderChildForms[0] || [];
						});
						this.list = [...this.list, ...data]
					} else {
						this.$tip(res.resMsg)
					}
				}).finally(() => {
					this.loading = false
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/search.scss';

	// 新增订单按钮
	@import '@/layout/add-order-btn.scss';

	// .popup-container {
	// 	background-color: #fff;
	// 	border-radius: 10rpx;
	// 	padding: 0 30rpx;

	// 	.item-list {
	// 		padding-bottom: 20rpx;
	// 		image {
	// 			width: 70rpx;
	// 			height: 70rpx;
	// 		}

	// 		text {
	// 			margin-left: 20rpx;
	// 			font-weight: bold;
	// 			vertical-align: text-top;
	// 		}

	// 		.pay-item:nth-child(n+2) {
	// 			margin-top: 20rpx;
	// 		}
	// 	}

	// 	.title {
	// 		padding: 20rpx 0;
	// 		font-weight: bold;
	// 		text-align: center;
	// 	}
	// }





	.file {
		color: $primary;
	}

	.btns {
		display: flex;
		flex-direction: row-reverse;
		flex-wrap: wrap;
		margin-bottom: 20rpx;

		.btn {
			position: relative;
			height: 70rpx;
			border-radius: 40rpx;
			text-align: center;
			line-height: 70rpx;
			border: 3rpx solid $primary;
			color: $primary;
			margin: 20rpx 20rpx 0 0;
			padding: 0 40rpx;
			background-color: transparent;
			z-index: 2;
		}
	}

	.order-status-active {
		border-bottom: 4rpx solid $primary;
	}


	.order-status {
		text {
			display: inline-block;
			padding: 15rpx 20rpx;
			box-sizing: border-box;
		}
	}

	.check-more {
		display: flex;
		align-items: center;
		justify-content: center;
		padding-bottom: 10rpx;
		color: #999;

		.more-icon {
			width: 25rpx !important;
			height: 25rpx !important;
			margin-left: 10rpx;
		}
	}

	.child-list {
		padding: 0 10rpx 20rpx;

		.child-item {
			display: flex;
			margin-top: 20rpx;
			padding: 10rpx 0;
			box-shadow: 0 0 3rpx #999;

			&:first-child {
				margin-top: 0;
			}

			.child-info {
				width: 450rpx;
				margin-left: 20rpx;
				font-size: 26rpx;

				view {
					width: 100%;
					margin-top: 10rpx;

					&:first-child {
						margin-top: 0;
					}
				}
			}
		}

		image {
			width: 200rpx;
			height: 200rpx;
			vertical-align: middle;
			border-radius: 5rpx;
		}
	}

	.list {
		overflow: hidden;

		.item-row {
			height: 60rpx;
			line-height: 60rpx;
			box-sizing: border-box;
			padding: 0 20rpx;
			width: 100%;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;

			&:first-child {
				height: 80rpx;
				line-height: 80rpx;
				background-color: $primary;
				color: #FFF;
			}
		}


		.item {
			margin-top: 20rpx;
			background-color: #FFF;
			border-radius: 5rpx;
			overflow: hidden;
		}
	}



	.loading {
		text-align: center;
		color: #999;
		margin: 20rpx 0;
	}

	.container {
		padding: 0 25rpx;
	}
</style>
<style>
	page {
		background-color: #f2f2f2;
	}
</style>