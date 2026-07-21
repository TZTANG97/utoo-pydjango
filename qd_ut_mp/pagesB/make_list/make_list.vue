<template>
	<view class="container">
		<view class="example-body">
			<uni-datetime-picker v-model="datetimerange" type="datetimerange" rangeSeparator="至" @change="change" />
		</view>

		<view class="list">
			<view class="item" v-for="(item, idx) in list" :key="idx" @click="viewDetail(item.id)">
				<view class="title">
					<view>{{ $alterTime(item.addTime) }}</view>
					<view class="status" :class="status_list[item['status']]['type']">
						{{ status_list[item['status']]['val'] }}
					</view>
				</view>
				<view class="content">
					<view class="content-item">
						申请内容：{{ item.testName }}
					</view>
					<view class="content-item">
						备注：{{ item.content }}
					</view>
				</view>
				<view class="btns">
					<view class="btn" v-if="item.is_cancel" @click.stop="cancelSub(item.id)">
						取消预约
					</view>
				</view>
			</view>
		</view>
		<my-loading :loading="loading" :is-refresh="isRefresh" :total="list.length"></my-loading>
	</view>
</template>

<script>
	import MyLoading from "@/components/loading.vue"
	import {
		fetchMyMakeOrderListApi,
		cancelConsultApi
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
				datetimerange: ["", ""],
				status_list: [{
						type: 'warning',
						val: '待回复'
					},
					{
						type: 'success',
						val: '已回复'
					},
					{
						type: 'success',
						val: '已生成'
					}, {
						type: 'info',
						val: '已取消'
					}
				],
				type: true
			}
		},
		onLoad() {
			this.getList()
		},
		onPullDownRefresh() {
			this.type = true
			this.list = []
			this.page = 1
			this.getList()
		},
		onReachBottom() {
			if (this.isRefresh) {
				this.page++
				this.getList()
			}
		},
		methods: {

			cancelSub(id) {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定取消预约吗？',
					success({
						confirm
					}) {
						if (confirm) {
							cancelConsultApi(id).then(res => {
								that.$toast(res.resMsg)
								if (res.res) {
									const idx = that.list.findIndex(item => item.id === id)
									that.$set(that.list[idx], 'is_cancel', 0)
									that.$set(that.list[idx], 'status', 3)
								}
							})
						}
					}
				})
			},


			// 查看详情
			viewDetail(id) {
				uni.navigateTo({
					url: `/pagesB/make_detail/make_detail?id=${id}`
				})
			},

			change(e) {
				this.page = 1
				this.isRefresh = true
				this.list = []
				if (!e.length) {
					this.datetimerange = ["", ""]
				}
				this.getList()
			},

			getList() {
				this.loading = true
				fetchMyMakeOrderListApi({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
					startime: this.datetimerange[0] == undefined ? '' : this.datetimerange[0],
					endtime: this.datetimerange[1] == undefined ? '' : this.datetimerange[1],
				}).then(res => {
					if (res.res) {
						const {
							data
						} = res.obj
						if (data.length !== 10) {
							this.isRefresh = false
						}
						this.list = [...this.list, ...data]
						if (this.type) {
							setTimeout(() => {
								uni.stopPullDownRefresh();
								this.type = false
							}, 500)
						}
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
	.btns {
		display: flex;
		flex-direction: row-reverse;
		flex-wrap: wrap;

		.btn {
			position: relative;
			height: 70rpx;
			border-radius: 40rpx;
			text-align: center;
			line-height: 70rpx;
			border: 3rpx solid $primary;
			color: $primary;
			padding: 0 40rpx;
			background-color: transparent;
			z-index: 2;
		}
	}
	.example-body {
		position: fixed;
		left: 0;
		top: 0;
		z-index: 20;
		width: 100%;
		padding: 10px;
		background-color: #fff;
	}

	.list {
		margin: 139rpx 30rpx 0;

		.item {
			background-color: #fff;
			padding: 0 20rpx 20rpx;

			&:nth-child(n+2) {
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
			display: flex;
			justify-content: space-between;
			border-bottom: 1rpx solid #F2F2F2;
			padding: 20rpx 0;
		}

		.content {
			padding: 20rpx 0;

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