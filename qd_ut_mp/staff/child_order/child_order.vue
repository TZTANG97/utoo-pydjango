<template>
	<view class="container">
		<view class="search-header" v-if="all">
			<input type="text" v-model="key_words" placeholder="请输入订单号" maxlength="30">
			<view class="btn" @click="search">
				搜索
			</view>
		</view>

		<view class="group" v-for="(item, index) in list" :key="index"
			@click="viewDetail(item)">
			<view class="group-hint">
				子订单-{{ index + 1 }}
			</view>
			<view class="group-item">
				<view class="group-label">
					子订单编号
				</view>
				<view class="group-content">
					{{ item.order_id }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					创建时间
				</view>
				<view class="group-content">
					{{ $alterTime(item.order_time, false) }}
				</view>
			</view>
			<view class="group-item" v-if="type == 6">
				<view class="group-label">
					客户企业名称
				</view>
				<view class="group-content">
<!--					{{ item.supplierName || item.supplierUser.company_name || '无' }}-->
					{{ item.customerName || ((item.company && item.company.name) ? item.company.name : '暂无') || '暂无' }}
				</view>
			</view>
			<template v-else>
				<view class="group-item">
					<view class="group-label">
						进货公司
					</view>
					<view class="group-content">
						{{ item.stock_company_name || '' }}
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						进货总价
					</view>
					<view class="group-content">
						{{ item.totalPrice.toFixed(2) }}
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						订单类型
					</view>
					<view class="group-content">
						{{ item.currency_type === 1? '人民币' : '美元' }}
					</view>
				</view>
			</template>
			<view class="group-item">
				<view class="group-label">
					状态
				</view>
				<view class="group-content">
					{{ order_status[item.order_status] }}
				</view>
			</view>
		</view>

		<my-loading :loading="isLoading" :isRefresh="isRefresh" :total="list.length"></my-loading>
		<view style="height: 0.1rpx;">
		</view>
		<u-toast ref="uToast" />
	</view>
</template>
<script>
	import {
		fetchTestChildOrderListApi2,
		fetchTestSubChildOrder,
		adminFetchTestChildOrderListApi,
		adminFetchTestSubChildOrderListApi
	} from '@/api/index.js';
	import MyLoading from "@/components/loading.vue"
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				id: '',
				type: '',
				list: [],
				page: 1,
				isRefresh: true,
				isLoading: false,
				key_words: '',
				selected_status: 0,
				order_status: {
					0: "已取消",
					5: "订单未发起审核",
					10: "已驳回",
					20: "待审核",
					30: "已审核",
					35: "已下单",
					36: "样品到货",
					37: "样品领用",
					38: "测试中",
					39: "测试完成",
					41: "样品归还",
					42: "样品寄回",
					43: "样品留存",
					45: "已发货",
					46: "已入库",
					50: "已完成"
				},
				// 是否获取所有的子订单
				all: false,
			}
		},
		onLoad({
			id = '',
			type = '6',
			// 获取全部
			all = ''
		}) {
			this.id = id
			this.type = type
			if (all) {
				this.all = true
			}

			// uni.$on('isEdit', () => {
			// 	this.GetChildList()
			// })

			// this.GetChildList()
		},
		onShow() {
      this.page = 1
      this.isRefresh = true
			this.list = []
			this.GetChildList()
		},

		onUnload() {
			uni.$off('isEdit')
		},

		onReachBottom() {
			if (this.isRefresh) {
				this.page++;
				this.GetChildList()
			}
		},
		methods: {
			search() {
				this.list = []
				this.page = 1
				this.isRefresh = true
				this.GetChildList()
			},

			// 更改选中的子订单状态
			changeOrderStatus(idx) {
				if (this.selected_status === idx) return
				this.selected_status = idx
				this.page = 1
				this.isRefresh = true
				this.list = []
				this.GetChildList()
			},

			// 查看详情
			viewDetail(item) {
				console.log(item.order_id,'item')
				console.log(item.id,'item')
				if (this.type == 6) {
					uni.navigateTo({
						url: '/staff/child_detail/child_detail?id=' + item.id + '&order_id=' + item.order_id
					})
				} else {
					uni.navigateTo({
						url: '/staff/sub_child_detail/sub_child_detail?id=' + item.id + '&order_id=' + item.order_id
					})
				}
			},

			// 搜索
			// search() {
			// 	this.list.splice(0, this.list.length)
			// 	this.page = 1
			// 	this.isRefresh = true
			// 	this.GetChildList()
			// },

			// 获取子订单
			GetChildList() {
				this.isLoading = true
				let request;

				if(this.all) {
					if(this.type == 6) {
						request = adminFetchTestChildOrderListApi({
							draw: 1,
							start: (this.page - 1) * 10,
							length: 10,
							// 搜索的订单id
							order_id: this.key_words
						})
					} else {
						request = adminFetchTestSubChildOrderListApi({
							draw: 1,
							start: (this.page - 1) * 10,
							length: 10,
							// 搜索的订单id
							order_id: this.key_words
						})
					}
				} else {
					if (this.type == 6) {
						request = fetchTestChildOrderListApi2({
							draw: 1,
							start: (this.page - 1) * 10,
							length: 10,
							ofId: this.id,
						})
					} else {
						request = fetchTestSubChildOrder({
							draw: 1,
							start: (this.page - 1) * 10,
							length: 10,
							ofId: this.id,
						})
					}
				}
				request.then(res => {
					if (!res.error) {
						if (res.data.length !== 10) this.isRefresh = false
						this.list = [...this.list, ...res.data]
					} else {
						this.$tip(res.error)
					}
				}).finally(() => {
					this.isLoading = false
				})
			}
		}
	}
</script>
<style scoped lang="scss">
	@import '@/layout/group.scss';
	@import '@/layout/search.scss';

	.container {
		padding: 0 25rpx;
	}

	.order-status-active {
		border-bottom: 4rpx solid $primary;
	}


	.order-status {
		padding: 0 30rpx;

		text {
			display: inline-block;
			padding: 15rpx 20rpx;
			box-sizing: border-box;
		}
	}

	.group {
		margin-top: 20rpx;
	}

	.list-status {
		color: #999;
		text-align: center;
		margin: 15rpx 0;
	}
</style>
