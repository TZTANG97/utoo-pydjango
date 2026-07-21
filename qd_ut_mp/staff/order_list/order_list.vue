<template>
	<view class="container">
		<view class="search-header">
			<input type="text" v-model="key_words" placeholder="请输入关键词进行检索" maxlength="30">
			<view class="btn" @click="search">
				搜索
			</view>
		</view>

		<view class="order-status">
			<text @click="changeOrderStatus(item['id'])" :class="{ 'order-status-active': item.id === selected_status }"
				v-for="(item, idx) in order_status_list" :key="idx">{{ item['label'] }}</text>
		</view>

		<view class="list">
			<view class="item" v-for="(item, index) in list" :key="index" @click="viewDetail(item.id, item.order_type,item)">
				<view class="item-row">
					<text>订单编号：{{ item.order_id }}</text>
				</view>
				<view class="item-row">
					<text>客户企业名称：{{ item.customerName || '暂无' }}</text>
				</view>
<!--				<view class="item-row">-->
<!--					<text>所属公司名称：{{ item.supplierName || '' }}</text>-->
<!--				</view>-->
				<view class="item-row">
					<text>销售主管：{{ item.managerName ? item.managerName : '' }}</text>
				</view>
				<view class="item-row">
					<text>销售人员：{{ item.saleUserName ? item.saleUserName : '' }}</text>
				</view>
				<view class="item-row">
					<text>订单总价：{{ item.totalPrice.toFixed(2) }}</text>
				</view>
				<view class="item-row">
					<text>是否开票：{{ item.invoiceType === 1? '是' : '否' }}</text>
				</view>
				<view class="item-row">
					<text>下单时间：{{ item.order_time? $alterTime(item.order_time, false): '' }}</text>
				</view>
				<view class="item-row">
					<text>录入订单时间：{{ item.addTime? $alterTime(item.addTime, false) : '' }}</text>
				</view>
				<view class="item-row">
					<text>订单状态：{{ ORDER_STATUS[item.order_status] }}</text>
				</view>
			</view>
		</view>
		<my-loading :loading="loading" :isRefresh="is_refresh" :total="list.length"></my-loading>

		<u-toast ref="uToast" />

		<navigator :url="`/staff/edit${type==6? '' : '_sub'}_order/edit${type==6? '' : '_sub'}_order`" hover-class="none" class="add-icon">
			<image src="@/static/add.png" mode=""></image>
		</navigator>
	</view>
</template>

<script>
	import {
		adminFetchTestOrderListApi,
		adminFetchTestSubOrderListApi
	} from '@/api/index.js'
	import {
		ORDER_STATUS
	} from '@/constant/status.js'
	import MyLoading from "@/components/loading.vue"
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				list: [],
				page: 1,
				is_refresh: true,
				loading: false,
				key_words: '',
				ORDER_STATUS,
				order_status_list: [
					{
						id: '',
						label: '全部'
					},
					{
						id: '20',
						label: '待审核'
					},
					{
						id: '30',
						label: '已审核'
					},
					{
						id: '10',
						label: '已驳回'
					},
					{
						id: '50',
						label: '已完成'
					}
				],
				selected_status: '',
				type: ''
			};
		},
		onLoad({
			type = '6',
			date
		}) {
			console.log(type,'type')
			console.log(date,'date')
			this.type = type
			this.getList()
		},
		onReachBottom() {
			if (this.is_refresh) {
				this.page++;
				this.getList()
			}
		},
		methods: {
			// 查看详情
			viewDetail(id, type,item) {
				console.log(item,'item')
				// 实验订单
				if (this.type == 6) {
					uni.navigateTo({
						url: '/staff/order_detail/order_detail?id=' + id + '&order_id=' + item.order_id
					})
				} else {
					// 实验分包订单
					uni.navigateTo({
						url: '/staff/sub_detail/sub_detail?id=' + id + '&order_id=' + item.order_id
					})
				}
			},

			// 更改选中的子订单状态
			changeOrderStatus(id) {
				if (this.selected_status === id) return
				this.selected_status = id
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
				let request;
				if (this.type == 6) {
					request = adminFetchTestOrderListApi({
						draw: 1,
						start: (this.page - 1) * 10,
						length: 10,
						order_id: this.key_words,
						order_status: this.selected_status
					})
				} else {
					request = adminFetchTestSubOrderListApi({
						draw: 1,
						start: (this.page - 1) * 10,
						length: 10,
						order_id: this.key_words,
						order_status: this.selected_status
					})
				}
				request.then(res => {
					if (!res.error) {
						const {
							data
						} = res
						if (data.length !== 10) this.is_refresh = false
						this.list = [...this.list, ...data]
					} else {
						this.$tip(res.error)
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
	}

	.item {
		margin-top: 20rpx;
		background-color: #FFF;
		border-radius: 5rpx;
		overflow: hidden;
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
