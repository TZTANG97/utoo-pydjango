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
						支付时间：{{ $alterTime(item.addTime) }}
					</view>
					<view class="content-item">
						可开票金额：{{ item.money? item.money.toFixed(2) : '0.00' }}
					</view>
				</view>
				<view class="handle">
					<view @click="makeInvoice(item.id, item.money)">开&nbsp;票</view>
				</view>
			</view>
		</view>
		<my-loading :loading="loading" :is-refresh="isRefresh" :total="list.length"></my-loading>
	</view>
</template>

<script>
	import MyLoading from "@/components/loading.vue"
	import {
		fetchTrueMakeInvoiceListApi
	} from '@/api/index.js'
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				page: 1,
				isRefresh: true,
				loading: false,
				list: [],
				keyWord: ''
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

			search() {
				this.page = 1
				this.isRefresh = true
				this.list = []
				this.getList()
			},

			makeInvoice(id, m) {
				uni.navigateTo({
					url: `/pagesB/confirm_make_invoice/confirm_make_invoice?id=${id}&money=${m}&type=1`
				})
			},

			getList() {
				this.loading = true
				fetchTrueMakeInvoiceListApi({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
					orderId: this.keyWord,
					startime: '',
					endtime: '',
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