<template>
	<view class="container">
		<view class="search-header">
			<input type="text" v-model="key_words" placeholder="请输入订单号" maxlength="30">
			<view class="btn" @click="search">
				搜索
			</view>
		</view>
		<view class="list" v-if="type == 111 || type == 222">
			<view class="item" v-for="(item, index) in list" :key="index" @click="viewDetail(item.id, item.order_type)">
				<view class="item-row">
					<text>订单编号：{{ item.order_id }}</text>
				</view>
				<view class="item-row" v-if="item.company.name">
					<text>客户企业名称：{{ item.company.name }}</text>
				</view>
				<view class="item-row">
					<text>所属公司名称：{{ item.supplierUser.company_name }}</text>
				</view>
				<view class="item-row">
					<text>销售主管：{{ item.saleManagerUser.userName }}</text>
				</view>
				<view class="item-row">
					<text>销售人员：{{ item.saleUser.userName }}</text>
				</view>
				<view class="item-row">
					<text>订单总价：{{ item.totalPrice.toFixed(2) }}</text>
				</view>
				<view class="item-row">
					<text>是否开票：{{ item.invoiceType === 1? '是' : '否' }}</text>
				</view>
				<view class="item-row">
					<text>下单时间：{{ item.delivery_time? $alterTime(item.delivery_time, false): '' }}</text>
				</view>
				<view class="item-row">
					<text>录入订单时间：{{ item.addTime? $alterTime(item.addTime, false) : '' }}</text>
				</view>
				<view class="item-row">
					<text>订单状态：{{ ORDER_STATUS[item.order_status] }}</text>
				</view>
			</view>
		</view>
		<view v-if="type == 333 || type == 444 || type == 555">
			<view class="group" v-for="(item, index) in list" :key="index" @click="viewDetail(item['id'])">
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
<!--				<view class="group-item">-->
<!--					<view class="group-label">-->
<!--						所属公司-->
<!--					</view>-->
<!--					<view class="group-content">-->
<!--						{{ item.stock_company_name || item.supplierUser.company_name || '无' }}-->
<!--					</view>-->
<!--				</view>-->
				<view class="group-item">
					<view class="group-label">
						客户企业名称
					</view>
					<view class="group-content">
						{{ item.customerName || item.company.name || '暂无' }}
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						状态
					</view>
					<view class="group-content">
						{{ ORDER_STATUS[item.order_status] }}
					</view>
				</view>
			</view>
		</view>
		<!-- 		<view class="noData" v-if="list.length == 0">
			暂无数据...
		</view> -->
		<my-loading :loading="isLoading" :isRefresh="isRefresh" :total="list.length"></my-loading>
		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import MyLoading from "@/components/loading.vue"
	import {
		ORDER_STATUS,
	} from '@/constant/status.js'
	import {
		getAuditOrderList,
	} from '@/api/index.js'
	import {
		getAuditOrderList1
	} from '@/api/staffB.js'
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				page: 1,
				loading: false,
				ORDER_STATUS,
				type: 0,
				list: [],
				key_words: '',
				isRefresh: true,
				isLoading: false,
				page: 1,
			}
		},
		onLoad(data) {
			console.log(data, 'data')
			this.type = data.type
			uni.setNavigationBarTitle({
				title: data.type == 111 ? '待审核实验订单' : data.type == 222 ? '待审核实验分包订单' : data.type == 333 ?
					'待审核实验子订单' : data.type == 444 ? '待审核实验分包子订单' : '待审核付款实验分包子订单'
			})
			this.getAuditOrderListFn()
		},
		onReachBottom() {
			if (this.isRefresh) {
				this.page++;
				this.getAuditOrderListFn()
			}
		},
		methods: {
			// 查看详情
			viewDetail(id, type) {
				console.log(id, type, '6666666')
				// 实验订单
				if (this.type == 111) {
					uni.navigateTo({
						url: '/staff/order_detail/order_detail?id=' + id + '&type=111'
					})
				} else if (this.type == 222) {
					// 实验分包订单
					uni.navigateTo({
						url: '/staff/sub_detail/sub_detail?id=' + id + '&type=222'
					})
				} else if (this.type == 333) {
					// 实验子订单
					uni.navigateTo({
						url: '/staff/child_detail/child_detail?id=' + id + '&type=333'
					})
				} else if (this.type == 444) {
					// 实验分包子订单
					uni.navigateTo({
						url: '/staff/sub_child_detail/sub_child_detail?id=' + id + '&type=444'
					})
				} else if (this.type == 555) {
					// 待付款审核实验分包子订单
					uni.navigateTo({
						url: '/staffB/wait_sub_child_detail/wait_sub_child_detail?id=' + id + '&type=555'
					})
				}
			},
			getAuditOrderListFn() {
				this.isLoading = true
				let data = {
					orderId: this.key_words,
					orderType: this.type == 111 ? 6 : this.type == 222 ? 8 : this.type == 333 ? 10 : 9,
					draw: '10',
					length: 10,
					start: (this.page - 1) * 10,
				}
				if (this.type == 555) {
					getAuditOrderList1(data.orderId, data.orderType, data.draw, data.length, data.start).then(res => {
						if (res.res) {
							if (res.obj.data.length !== 10) this.isRefresh = false
							this.list = [...this.list, ...res.obj.data]
						} else {
							this.$tip(res.error)
						}
					}).finally(() => {
						this.isLoading = false
					})
				} else {
					getAuditOrderList(data.orderId, data.orderType, data.draw, data.length, data.start).then(res => {
						if (res.res) {
							if (res.obj.data.length !== 10) this.isRefresh = false
							this.list = [...this.list, ...res.obj.data]
						} else {
							this.$tip(res.error)
						}
					}).finally(() => {
						this.isLoading = false
					})
				}
				// getAuditOrderList(data.orderId, data.orderType, data.draw, data.length, data.start).then(res => {
				// 	if (res.res) {
				// 		if (res.obj.data.length !== 10) this.isRefresh = false
				// 		this.list = [...this.list, ...res.obj.data]
				// 	} else {
				// 		this.$tip(res.error)
				// 	}
				// }).finally(() => {
				// 	this.isLoading = false
				// })
			},
			search() {
				// this.list.splice(0, this.list.length)
				this.list = []
				this.page = 1
				this.isRefresh = true
				this.getAuditOrderListFn()
			},
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/group.scss';
	@import '@/layout/search.scss';

	.noData {
		text-align: center;
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
