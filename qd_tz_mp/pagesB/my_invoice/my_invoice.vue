<template>
	<view class="container">
		<view class="money">
			<view class="wrapper">
				<view class="total-point">
					<view class="label">可开票金额：</view>
					<view class="points">{{ invoicingAmount }}</view>
					<view class="control" @click="makeInvoice">
						开票
					</view>
				</view>
			</view>
			
			<view class="wrapper">
				<view class="total-point">
					<view class="label">发票信息：</view>
					<view class="invoice-header">
						发票抬头： {{ invoice_header }}
					</view>
					<view class="tax-num">
						企业税号：{{ tax_num }}
					</view>
<!-- 					<view class="control" @click="makeInvoice">
						添加开票信息
					</view> -->
				</view>
			</view>
		</view>

		<view class="header">
			<uni-section>
				<uni-data-select :clear="false" v-model="value" :localdata="range" @change="search"></uni-data-select>
			</uni-section>
			<input type="text" @confirm="search" placeholder="请输入订单号" maxlength="30" v-model="keyWord" />
		</view>

		<view class="order-list">
			<view class="item" v-for="(item, idx) in list" :key="idx">
				<view class="title" v-if="!value">
					<view>{{ $alterTime(item.addTime) }}</view>
					<view class="status" :class="item['status'] === 3 || item['status'] === 5? 'canceied' : ''">
						{{ invoice_status[item['status'] + ''] }}
					</view>
				</view>
				<view class="content">
					<template v-if="value">
						<view class="content-item">
							关联订单：{{ item.orderId }}
						</view>
						<view class="content-item">
							开票时间：{{ $alterTime(item.invoice_date)}}
						</view>
						<view class="content-item">
							发票金额：{{ item.money? item.money.toFixed(2) : '0.00'}}
						</view>
					</template>
					<template v-else>
						<view class="content-item">
							发票编号：{{ item.invoice_num }}
						</view>
						<view class="content-item">
							发票抬头：{{ item.invoice_title }}
						</view>
						<view class="content-item">
							发票金额：{{ item.invoice_money? item.invoice_money.toFixed(2) : '0.00'}}
						</view>
					</template>

					<view class="content-item">
						发票类型：{{ item['type'] === 1 ? '电子普通发票' : item['type'] == 3 ? '电子增值税专票' : item['type'] == 2 ? '纸质发票' : '' }}
					</view>
				</view>

				<view class="handle" v-if="item['status'] === 1">
					<view @click="cancelInvoice(item.id, idx)">取&nbsp;消</view>
				</view>
			</view>
		</view>

		<view class="list">
			<my-loading :loading="loading" :total="list.length" :is-refresh="isRefresh"></my-loading>
		</view>
	</view>
</template>

<script>
	import {
		fetchinvoiceListApi,
		cancelInvoiceApi,
		fetchInvoiceDetailListApi,
		fetchUserBandInfoApi
	} from '@/api/index.js'
	import MyLoading from "@/components/loading.vue"
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
				keyWord: '',
				invoicingAmount: '',
				invoice_status: {
					'1': '开票中',
					'2': '退票中',
					'3': '已作废',
					'4': '已开票',
					'5': '已取消',
				},
				value: 0,
				invoice_header: '',
				tax_num: '',
				range: [{
						value: 0,
						text: "申请记录"
					},
					{
						value: 1,
						text: "明细记录"
					}
				],
			}
		},
		onShow() {
			fetchUserBandInfoApi().then(res => {
				if (res.res) {
					const { 
						obj: {
							invoice_title,
							taxNum
						}
					} = res
					this.invoice_header = invoice_title
					this.tax_num = taxNum
				}
			})
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

			format_with_Intl(num = 0) {
				let str = parseFloat(num).toFixed(2);
				let parts = str.split(".");
				let integerPart = parts[0];
				integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				return `${integerPart}.${parts[1]}`;
			},

			// 开票
			makeInvoice() {
				uni.navigateTo({
					url: '/pagesB/make_invoice/make_invoice'
				})
			},

			// 取消开票
			cancelInvoice(id, idx) {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否确认取消开票？',
					success({
						confirm
					}) {
						if (confirm) {
							cancelInvoiceApi({
								invoiceId: id
							}).then(res => {
								if (res.res) {
									that.$toast('取消成功')
									that.list[idx]['status'] = 3
								} else {
									that.$toast(res.resMsg)
								}
							})
						}
					}
				})
			},

			search() {
				this.page = 1
				this.isRefresh = true
				this.list = []
				this.getList()
			},

			getList() {
				this.loading = true
				let request;
				if (this.value) {
					request = fetchInvoiceDetailListApi({
						draw: 1,
						start: (this.page - 1) * 10,
						orderId: this.keyWord,
						length: 10,
						type: 2,
					})
				} else {
					request = fetchinvoiceListApi({
						start: (this.page - 1) * 10,
						length: 10,
						orderId: this.keyWord,
						draw: 1,
						type: 2,
					})
				}
				request.then(res => {
					if (res.res) {
						let data;
						if (this.value) {
							data = res.obj.data
						} else {
							data = res.obj.data.data
							let stayApplyMoney = res.obj.stayApplyMoney
							this.invoicingAmount = this.format_with_Intl(stayApplyMoney)
						}
						this.list = [...this.list, ...data]
						if (data.length !== 10) this.isRefresh = false
					} else {
						this.$toast(res.resMsg)
						this.isRefresh = false
					}
				}).finally(_ => {
					this.loading = false
				})
			},
		}
	}
</script>

<style scoped lang="scss">
	/deep/.uni-section .uni-section-header {
		width: 200rpx;
		padding: 0;
	}

	.canceied {
		color: #878787 !important;
	}


	.handle {
		display: flex;
		flex-direction: row-reverse;
		color: $primary;
		padding: 20rpx 0;
	}

	.order-list {
		overflow: hidden;

		.item {
			background-color: #fff;
			margin: 0 20rpx;
			padding: 0 20rpx;

			&:nth-child(n+1) {
				margin-top: 30rpx;
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
			border-top: 1rpx solid #F2F2F2;
			border-bottom: 1rpx solid #F2F2F2;

			.content-item {
				&:nth-child(n+1) {
					margin-top: 10rpx;
				}
			}
		}
	}

	.header {
		display: flex;
		align-items: center;
		box-sizing: border-box;
		border-bottom: 1rpx solid #F2F2F2;
		padding: 10rpx 30rpx 30rpx;
		background-color: #fff;

		input {
			flex: 1;
			height: 70rpx;
			border: 1px solid #e5e5e5;
			box-sizing: border-box;
			padding: 0 20rpx;
			border-radius: 7rpx;
			margin-left: 20rpx;
		}

	}

	.money {
		display: flex;
		padding: 40rpx 0;
		.wrapper {
			
		}
		background-color: #fff;

		.wrapper {
			width: 50%;

			.control {
				margin: 30rpx 0 0 30rpx;
				color: $primary;
			}

			.label {
				margin-left: 30rpx;
			}
			
			.invoice-header, .tax-num {
				font-size: 24rpx;
				color: #8c8c8c;
				margin-left: 30rpx;
				height: 36rpx;
			}
			
			.invoice-header {
				margin-top: 10rpx;
			}

			.points {
				font-size: 55rpx;
				font-weight: bold;
				color: $primary;
				margin: 10rpx 0 0 30rpx;
			}
		}
	}
</style>

<style>
	page {
		background-color: #F2F2F2;
	}
</style>