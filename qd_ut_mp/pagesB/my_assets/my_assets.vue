<template>
	<view class="container">
		<view class="money">
			<!-- 			<view class="title">
				金额明细
			</view> -->

			<view class="detail-money">
				<view class="total-point">
					<view class="label">余额：</view>
					<view class="points">{{ format_with_Intl(amount) }}</view>
					<view class="control">
						<text @click="pay">充值</text>
						<!-- <text @click="withdraw">提现</text> -->
					</view>
				</view>
				<view class="expiring">
					<view class="label">待支付金额：</view>
					<view class="points">{{ format_with_Intl(arrearAmount) }}</view>
					<navigator class="control" url="/pagesB/repayment/repayment" hover-class="none">
						支付
					</navigator>
				</view>
				<view class="expiring">
					<view class="label">可开票金额：</view>
					<view class="points">{{ format_with_Intl(invoicingAmount) }}</view>
					<navigator class="control" url="/pagesB/make_invoice/make_invoice" hover-class="none">
						开票
					</navigator>
				</view>
			</view>
		</view>
		<view class="main">
			<view class="title-list">
				<uni-section>
					<uni-data-select :clear="false" v-model="value" :localdata="range"
						@change="search"></uni-data-select>
				</uni-section>
				<uni-datetime-picker class="datetime-picker" v-model="date" type="daterange" @change="changeDate" v-if="value < 3" />
				<input v-else type="text" @confirm="search" placeholder="请输入订单号" maxlength="30" v-model="keyWord" />
			</view>

			<view class="order-list">
				<template v-if="value < 3">
					<view class="item" v-for="(item, idx) in list" :key="idx">
						<view class="title">
							<text v-if="value === 1">{{ item.pa_num }}</text>
						</view>
						<view class="content">
							<view class="content-item">
								交易时间：{{ $alterTime(item.addTime) }}
							</view>
							<view class="content-item">
								交易金额：{{ item.money? item.money.toFixed(2) : '0.00'}}
							</view>
							<view class="content-item">
								交易方式：{{ payWayList[item.pay_way] }}
							</view>
							<view class="content-item">
								操作类型：{{ handleList[item.orderType - 0] }}
							</view>
							<view class="content-item" v-if="item.hzdPath">
								回执单：<text @click.stop="checkAnnex(item.hzdPath)">查看</text>
							</view>
							<view class="content-item">
								状态：{{ item.applyStatus }}
							</view>
							<view class="content-item">
								类型：{{ item.ptype }}
							</view>
							<view class="content-item" v-if="item.mark">
								驳回原因：{{ item.mark }}
							</view>
						</view>
					</view>
				</template>
				<template v-else-if="value === 3">
					<view class="item" v-for="(item, idx) in list" :key="idx">
						<view class="title">
							{{ item.orderId }}
						</view>
						<view class="content">
							<view class="content-item">
								申请时间：{{ $alterTime(item.addTime) }}
							</view>
							<view class="content-item">
								发票金额：{{ item.money? item.money.toFixed(2) : '0.00'}}
							</view>
							<view class="content-item">
								发票类型：{{ item['type'] === 1 ? '电子普通发票' : item['type'] == 3 ? '电子增值税专票' : item['type'] == 2 ? '纸质发票' : '' }}
							</view>
							<view class="content-item" v-if="item.info">
								发票资料：<text @click.stop="checkAnnex(item.info)">查看</text>
							</view>
							<view class="item-footer" v-if="item.status === 1">
								<view class="cancel-btn" @click.stop="cancelOrder(item.id)">
									取&nbsp;消
								</view>
							</view>
						</view>
					</view>
				</template>
				<template v-else>
					<view class="item" v-for="(item, idx) in list" :key="idx">
						<view class="title">
							{{ item.order_id }}
						</view>
						<view class="content">
							<view class="content-item">
								下单时间：{{ $alterTime(item.addTime) }}
							</view>
							<view class="content-item">
								下单金额：{{ item.totalPrice.toFixed(2) }}
							</view>
							<view class="content-item" v-if="order_status_list[item.order_status]">
								状态：{{ order_status_list[item.order_status] }}
							</view>
						</view>
					</view>
				</template>
			</view>
		</view>

		<view class="list">
			<my-loading :loading="loading" :total="list.length" :is-refresh="isRefresh"></my-loading>
		</view>

		<uni-popup ref="withdraw" type="center" @maskClick="closePopup">
			<view class="popup-container">
				<view class="title">
					提现
				</view>
				<view class="wrapper">
					<view class="item">
						<view class="label">
							<text>*</text>
							<text>提现金额：</text>
						</view>
						<input type="text" @blur="verifyMoney" v-model="money" placeholder="请输入提现金额" />
					</view>
					<view class="item">
						<view class="label">
							<text>*</text>
							<text>持卡人姓名：</text>
						</view>
						<input type="text" maxlength="20" v-model="bank_name" placeholder="请输入持卡人姓名" />
					</view>
					<view class="item">
						<view class="label">
							<text>*</text>
							<text>银行卡号：</text>
						</view>
						<input type="text" maxlength="20" v-model="bank_account" placeholder="请输入银行卡号" />
					</view>

					<view class="btn" @click="confirmWithdraw">
						确&nbsp;定
					</view>
				</view>
			</view>
		</uni-popup>

		<uni-popup ref="pay" type="center" @maskClick="closePopup">
			<view class="popup-container withdraw-container">
				<view class="title">
					线下支付
				</view>
				<view class="wrapper ">
					<view class="item">
						<view class="label">
							<text>*</text>
							<text>收款账号：</text>
						</view>
						<input :disabled="disabledInput" type="text" maxlength="20" v-model="receipt_account"
							placeholder="请输入收款账号" />
					</view>
					<view class="item">
						<view class="label">
							<text>*</text>
							<text>收款公司名称：</text>
						</view>
						<input :disabled="disabledInput" type="text" maxlength="20" v-model="receipt_company_name"
							placeholder="请输入收款公司名称" />
					</view>
					<view class="item">
						<view class="label">
							<text>*</text>
							<text>充值金额：</text>
						</view>
						<input type="text" maxlength="20" v-model="money" placeholder="请输入充值金额" @blur="verifyMoney" />
					</view>
					<view class="item">
						<view class="label">
							<text>*</text>
							<text>付款回执单：</text>
						</view>
						<view class="receipt" @click="uploadReceipt">
							<image v-if="receipt_url" class="receipt-img" :src="receipt_url" mode=""></image>
							<image v-else class="add-icon" src="@/static/add-icon.png" mode=""></image>
						</view>
					</view>

					<view class="btn" @click="confirmPay">
						确&nbsp;定
					</view>
				</view>
			</view>
		</uni-popup>
	</view>
</template>

<script>
	import MyLoading from "@/components/loading.vue"
	import {
		fetchMyAssetsApi,
		withdrawApi,
		uploadFileApi,
		offlinePayApi,
		// 获取记录
		fetchHistoryApi,
		// 获取开票记录
		fetchInvoiceDetailListApi,
		// 获取待处理订单
		fetchAssetsListApi,
		// 待支付，待申请
		fetchNoPayOrderListApi,
		// 取消开票
		cancelInvoiceApi
	} from '@/api/index.js'
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				list: [],
				isRefresh: true,
				page: 1,
				loading: false,
				selectedIdx: 0,
				amount: 0,
				arrearAmount: 0,
				invoicingAmount: 0,
				keyWord: '',
				order_status_list: {
					"0": "已取消",
					"5": "采购成本未确认",
					"10": "已驳回",
					"20": "待审核",
					"30": "已审核",
					"40": "已确认",
					"49": "所有成本未结清",
					"50": "已完成",
					"35": "已下单",
					"45": "已发货",
					"46": "已入库",
					"66": "待平台确认",
					"67": "已和客户沟通确认"
				},
				money: '',
				bank_name: '',
				bank_account: '',
				// 已上传回执单路径
				receipt_url: '',
				receipt_url_id: '',
				receipt_account: '',
				receipt_company_name: '',
				value: 0,
				range: [{
						value: 0,
						text: '全部记录'
					},
					{
						value: 1,
						text: '充值记录'
					},
					{
						value: 2,
						text: '支付记录'
					},
					{
						value: 3,
						text: '开票记录'
					},
					{
						value: 4,
						text: '待处理订单'
					},
					{
						value: 5,
						text: '待申请发票'
					},
					{
						value: 6,
						text: '待支付订单'
					}
				],
				disabledInput: false,
				payWayList: {
					1: '支付宝',
					2: '微信',
					3: '线下支付',
					4: '余额支付'
				},
				handleList: {
					1: '充值',
					2: '支付',
					3: '支付',
					4: '提现',
				},
				date: []
			}
		},
		onLoad() {
			this.getList()
			this.getMoney()

			const da = uni.getStorageSync('defaultAccount');
			if (da) {
				this.disabledInput = true
				this.receipt_account = da['bankCardNum']
				this.receipt_company_name = da['company_name']
			}
		},
		onReachBottom() {
			if (this.isRefresh) {
				this.page++
				this.getList()
			}
		},
		methods: {
			
			changeDate(e) {
				this.date = e
				this.search()
			},

			checkAnnex(url) {
				uni.navigateTo({
					url: `/pagesB/webview?src=${url}`
				})
			},

			// 取消订单
			cancelOrder(id) {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定取消订单',
					success({
						confirm
					}) {
						if (confirm) {
							cancelInvoiceApi({
								invoiceId: id
							}).then(res => {
								that.$toast(res.resMsg)
								if (res.res) {
									const idx = that.list.findIndex(item => item.id === id)
									that.$set(that.list[idx], 'status', -1)
								}
							})
						}
					}
				})
			},

			format_with_Intl(num = 0) {
				let str = parseFloat(num).toFixed(2);
				let parts = str.split(".");
				let integerPart = parts[0];
				integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				return `${integerPart}.${parts[1]}`;
			},


			// 确认支付
			confirmPay() {
				if (!this.receipt_account) return this.$toast('请填写收款账号')
				if (!this.receipt_company_name) return this.$toast('请填写收款公司名称')
				if (!this.money) return this.$toast('请填写充值金额')
				if (!this.receipt_url_id) return this.$toast('请上传回执单')
				offlinePayApi({
					money: this.money,
					file_id: this.receipt_url_id,
					pay_way: 3,
				}).then(res => {
					if (res.res) {
						this.$refs['pay'].close()
						this.closePopup()
						this.$toast('充值申请已提交')
					} else {
						this.$toast(res.resMsg)
					}
				})
			},

			// 上传回执单
			uploadReceipt() {
				const that = this
				uni.chooseImage({
					count: 1,
					sizeType: ['compressed'],
					success(res) {
						uni.compressImage({
							src: res.tempFilePaths[0],
							quality: 70,
							success(res) {
								uploadFileApi({
									filePath: res.tempFilePath,
									reqUrl: '/experimentOrder/uploadChildData.ajax',
									name: 'orderdata',
									formData: {
										type: '7'
									}
								}).then(res => {
									if (res.res) {
										const {
											path,
											name,
											id
										} = res.obj
										that.receipt_url = path + '/' + name
										that.receipt_url_id = id
									} else {
										that.$toast('上传失败')
									}
								}).finally(_ => {
									uni.hideLoading()
								})
							}
						})
					}
				});
			},

			// 确认提现
			confirmWithdraw() {
				if (!this.money) this.$toast('请输入提现金额')
				if (!this.bank_name) return this.$toast('请输入持卡人姓名')
				if (!this.bank_account) return this.$toast('请输入银行卡号')
				withdrawApi({
					money: this.money,
					bankNum: this.bank_account,
					accountName: this.bank_name,
				}).then(res => {
					if (res.res) {
						this.$refs['withdraw'].close()
						this.closePopup()
						this.$toast('提现申请已提交')
						this.getMoney()
					} else {
						this.$toast(res.resMsg)
					}
				})
			},

			closePopup() {
				this.money = ''
				this.bank_name = ''
				this.bank_account = ''
				this.receipt_url = ''
				this.receipt_url_id = ''
				// this.receipt_account = ''
				// this.receipt_company_name = ''
			},

			// 失去焦点校验金额
			verifyMoney() {
				const money = parseFloat(this.money.trim())
				if (isNaN(money)) return this.money = ''
				this.money = money.toFixed(2)
			},

			// 充值
			pay() {
				uni.navigateTo({
					url: '/pagesB/balance_recharge/balance_recharge'
				})
				// this.$refs['popup'].close()
				// this.$refs['pay'].open()
			},

			// 提现
			withdraw() {
				// this.$refs['popup'].close()
				this.$refs['withdraw'].open()
			},

			search() {
				this.page = 1
				this.isRefresh = true
				this.list = []
				this.getList()
			},

			// 获取余额，欠款金额等
			getMoney() {
				fetchMyAssetsApi().then(res => {
					if (res.res) {
						const {
							arrearAmount,
							invoicingAmount,
							amount
						} = res.obj
						this.amount = amount.toFixed(2)
						this.arrearAmount = arrearAmount.toFixed(2)
						this.invoicingAmount = invoicingAmount.toFixed(2)
					}
				})
			},


			getList() {
				this.loading = true
				let request;

				if (this.value < 3) {
					request = fetchHistoryApi({
						draw: 1,
						start: (this.page - 1) * 10,
						length: 10,
						startTime: this.date.length? `${this.date[0]} 00:00:00` : '',
						endTime: this.date.length? `${this.date[1]} 00:00:00` : '',
						type: this.value,
					})
				} else if (this.value === 3) {
					request = fetchInvoiceDetailListApi({
						draw: 1,
						start: (this.page - 1) * 10,
						length: 10,
						orderId: this.keyWord,
						type: 2,
					})
				} else if (this.vlaue === 4) {
					request = fetchAssetsListApi({
						draw: 1,
						start: (this.page - 1) * 10,
						length: 10,
						order_id: this.keyWord,
						type: 5
					})

				} else {
					request = fetchNoPayOrderListApi({
						draw: 1,
						start: (this.page - 1) * 10,
						length: 10,
						order_id: this.keyWord,
						type: this.value === 5 ? 5 : 1
					})
				}

				request.then(res => {
					if (res.res) {
						const {
							obj: {
								data
							}
						} = res
						this.list = [...this.list, ...data]
						if (data.length !== 10) {
							this.isRefresh = false
						}
					} else {
						this.$toast(res.resMsg)
					}
				}).finally(_ => {
					this.loading = false
				})
			},

			cutList(idx) {
				if (this.selectedIdx === idx) return
				this.selectedIdx = idx
				this.page = 1
				this.isRefresh = true
				this.list = []
				this.getList()
			},
		}
	}
</script>


<style>
	page {
		background-color: #F2F2F2;
	}
</style>
<style scoped lang="scss">
	/deep/.uni-section {
		margin-right: 20rpx;
		.uni-section-header {
			padding: 0;
			width: 188rpx;
		}
	}

	/deep/.my-loading {
		.wrapper {
			padding: 100rpx 0;
		}
	}
	
	/deep/.uni-date {
		height: 70rpx;
		flex: 1;
	}

	.btn {
		color: #FFF;
		background-color: #E96302;
		border-radius: 10rpx;
		padding: 17rpx 15rpx;
		text-align: center;
		margin-top: 50rpx;
	}



	.popup-container {
		height: 620rpx;
		background-color: #fff;
		width: 550rpx;
		border-radius: 10rpx;
		padding: 0 30rpx;

		.item:nth-child(n+1) {
			margin-top: 30rpx;

			input {
				margin-top: 10rpx;
			}
		}

		.title {
			padding: 20rpx 0;
			font-weight: bold;
			text-align: center;
		}

		input {
			border-bottom: 1rpx solid #C0C0C0;
		}
	}

	.withdraw-container {
		height: 850rpx;

		.receipt {
			display: flex;
			align-items: center;
			justify-content: center;
			width: 150rpx;
			height: 150rpx;
			border-radius: 10rpx;
			border: 4rpx dotted #666;
			margin-top: 10rpx;
			vertical-align: middle;

			.receipt-img {
				width: 100%;
				height: 100%;
			}


			.add-icon {
				width: 75rpx;
				height: 75rpx;
			}
		}
	}


	.order-list {
		overflow: hidden;

		.item-footer {
			height: 70rpx;
			text-align: right;
			line-height: 70rpx;

			.cancel-btn {
				display: inline-block;
				vertical-align: middle;
				color: $primary;
				border: 1rpx solid $primary;
				border-radius: 50rpx;
				padding: 0 40rpx;
				font-size: 26rpx;
			}
		}

		.item {
			background-color: #fff;
			margin: 0 20rpx;

			&:nth-child(n+1) {
				margin-top: 25rpx;
			}

			.status {
				color: $primary;
			}

			.success {
				color: #67C23A !important;
			}

			.info {
				color: #5D5D5D !important;
			}
		}

		.title {
			height: 70rpx;
			background-color: $primary;
			color: #fff;
			line-height: 70rpx;
			padding: 0 20rpx;
		}

		.content {
			padding: 20rpx;

			.content-item {
				&:nth-child(n+1) {
					margin-top: 10rpx;
				}
			}
		}
	}

	.money {
		background-color: #fff;

		.title {
			text-align: center;
			padding: 20rpx 0;
			font-size: 30rpx;
			font-weight: bold;
		}
	}

	.slider-active {
		left: 207rpx !important;
	}

	.title-item-active {
		&::after {
			display: block;
			content: '';
			height: 5rpx;
			margin-top: 5rpx;
			background-color: $primary;
		}
	}

	.title-list {
		display: flex;
		align-items: center;
		padding: 15rpx 30rpx;
		background-color: #fff;

		input {
			background-color: #fff;
			box-sizing: border-box;
			padding: 0 20rpx;
			border-radius: 7rpx;
			border: 1px solid #e5e5e5;
			height: 70rpx;
			flex: 1;
		}
	}

	.detail-money {
		display: flex;
		flex-wrap: wrap;

		.control {
			margin: 30rpx 0 0 30rpx;
			color: $primary;

			text {
				&:nth-child(n+2) {
					margin-left: 30rpx;
				}
			}
		}

		&>view {
			width: 50%;
			padding: 40rpx 0;
		}

		.label {
			margin-left: 30rpx;

		}

		.points {
			font-size: 55rpx;
			font-weight: bold;
			color: $primary;
			margin: 10rpx 0 0 30rpx;
		}
	}
</style>