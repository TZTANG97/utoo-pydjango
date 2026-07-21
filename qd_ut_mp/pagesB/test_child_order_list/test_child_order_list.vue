<template>
	<view class="container">
		<view class="list">
			<navigator :url="`/pagesB/test_child_order_detail/test_child_order_detail?id=${item.id}`" hover-class="none" class="item" v-for="(item, index) in list" :key="index">
				<view class="item-row">
					<text>子订单编号：{{ item['order_id'] }}</text>
				</view>
				<view class="item-row">
					<text>创建时间：{{ $alterTime(item['addTime']) }}</text>
				</view>
				<view class="item-row">
					<text>订单状态：{{ item['order_statusstr'] }}</text>
				</view>
			</navigator>
		</view>
		<my-loading :loading="loading" :isRefresh="is_refresh" :total="list.length"></my-loading>

		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import {
		fetchTestChildOrderListApi2
	} from '@/api/index.js'
	import MyLoading from "@/components/loading.vue"
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				ofId: '',
				list: [],
				page: 1,
				is_refresh: true,
				loading: false,
			};
		},
		onLoad({
			ofId = ''
		}) {
			if (ofId) this.ofId = ofId
			this.getList()
		},
		onReachBottom() {
			if (this.is_refresh) {
				this.page++;
				this.getList()
			}
		},
		methods: {
			getList() {
				this.loading = true
				fetchTestChildOrderListApi2({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
					ofId: this.ofId,
				}).then(res => {
					const { error, data } = res
					if (!error) {
						if (data.length !== 10) this.is_refresh = false
						this.list = [...this.list, ...data]
					} else {
						this.$tip(error)
					}
				}).finally(() => {
					this.loading = false
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
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