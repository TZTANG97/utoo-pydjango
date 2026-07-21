<template>
	<view class="container">
		<view class="search-header">
			<input type="text" v-model="key_words" placeholder="请输入姓名" maxlength="30">
			<!-- <input type="text" v-model="key_words" placeholder="请输入手机号" maxlength="30"> -->
			<view class="btn" @click="search">
				搜索
			</view>
		</view>
		<view class="list">
			<view class="item" v-for="(item, index) in list" :key="index"
				@click="viewDetail(item.id, item.order_type,item)">
				<view class="item-row">
					<text>订单号：{{ item.order_num || '' }}</text>
				</view>
				<view class="item-row">
					<text>咨询时间：{{ $alterTime(item.addTime) || '' }}</text>
				</view>
				<view class="item-row">
					<text>测试分类：{{ item.className || '' }}</text>
				</view>
				<view class="item-row">
					<text>姓名：{{ item.userName || '' }}</text>
				</view>
				<view class="item-row">
					<text>手机号：{{ item.mobile || '' }}</text>
				</view>
				<view class="item-row">
					<text>公司名：{{ item.company_name || '' }}</text>
				</view>
				<view class="item-row">
					<text>咨询详情：{{ item.content || '' }}</text>
				</view>
				<view class="item-row">
					<text>客服人员：{{ item.syUserName || '' }}</text>
				</view>
				<view class="item-row">
					<text>状态：{{ statusFn(item.status) }}</text>
				</view>
			</view>
		</view>
		<my-loading :loading="loading" :isRefresh="is_refresh" :total="list.length"></my-loading>

		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import {
		list,
	} from '@/api/reservationList.js'
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
			};
		},
		onLoad({
			type = '6',
			date
		}) {
			this.type = type
		},
		onShow() {
			this.list = []
			this.page = 1
			this.is_refresh = true
			this.getList()
		},
		onReachBottom() {
			if (this.is_refresh) {
				this.page++;
				this.getList()
			}
		},
		methods: {
			statusFn(status){
				if(status == 0){
					return '未回复'
				}else if(status == 1){
					return '已处理'
				}else if(status == 2){
					return '已生成订单'
				}else{
					return '已取消'
				}
			},
			// 查看详情
			viewDetail(id, type, item) {
				uni.navigateTo({
					url: '/pagesB/reservationDetial/reservationDetial?id=' + id + '&order_id=' + item.order_id
				})
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
					request = list({
						draw: 1,
						start: (this.page - 1) * 10,
						length: 10,
						order_id: this.key_words,
						// order_status: this.selected_status
					})
				} else {
					request = list({
						draw: 1,
						start: (this.page - 1) * 10,
						length: 10,
						order_id: this.key_words,
						// order_status: this.selected_status
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