<template>
	<view class="container">
		<view class="list">
			<view class="item" v-for="(item, index) in list" :key="index">
				<view class="item-row">
				</view>
				<view class="item-row">
					<text>子订单编号：{{ item['orderId'] }}</text>
				</view>
				<view class="item-row">
					<text>产品名称：{{ item['goodsName'] }}</text>
				</view>
				<view class="item-row">
					<text>产品型号：{{ item['goodsSpec']? item['goodsSpec'] : '无'}}</text>
				</view>
				<view class="item-row">
					<text>产品品牌：{{ item['goodsBrandName'] }}</text>
				</view>
				<view class="item-row">
					<text>数量：{{ item['goodsNums'] }}</text>
				</view>
				<view class="item-row">
					<text>实验测试项目：{{ item['experiment_project_name'] }}</text>
				</view>
				<view class="item-row">
					<text>实验测试分类：{{ item['experiment_class_name'] }}</text>
				</view>
				<view class="item-row">
					<text>实验测试金额：{{ item['goodsPrice'].toFixed(2) }}</text>
				</view>
				<view class="item-row">
					<text>标准测试金额：{{ item['reference_price'].toFixed(2) }}</text>
				</view>
				<view class="item-row">
					<text>总价：{{ (item['goodsNums'] * item['goodsPrice']).toFixed(2) }}</text>
				</view>
			</view>
		</view>

		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import {
		getOrderProductListApi,
		fetchSubChildOrderListApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
				id: '',
				list: [],
				type: ''
			};
		},
		onLoad({
			id = '',
			type = '6'
		}) {
			if (id) this.id = id
			// 6获取实验订单产品列表
			// 8获取实验分包订单产品列表
			this.type = type
			this.getDetail()
		},
		methods: {
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

			getDetail() {
				this.loading = true
				let request;
				if (this.type == 6) {
					request = getOrderProductListApi({
						draw: 1,
						start: 0,
						length: -1,
						ofId: this.id
					})
				} else {
					request = fetchSubChildOrderListApi({
						draw: 1,
						start: 0,
						length: -1,
						ofId: this.id
					})
				}

				request.then(res => {
					if (!res.error) {
						this.list = res.data
					} else {
						thsi.$toast(res.error)
					}
				}).finally(() => {
					this.loading = false
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
	.file {
		color: $primary;
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