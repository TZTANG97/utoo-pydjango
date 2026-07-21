<template>
	<view class="container">
		<view class="search-header">
			<input type="text" v-model="key_words" placeholder="请输入关键词进行检索" maxlength="30">
			<view class="btn" @click="search">
				搜索
			</view>
		</view>
		<view class="list">
			<view class="item" v-for="(item, index) in list" :key="index">
				<view class="item-row">
					<text>订单编号：{{ item['orderId'] }}</text>
				</view>
				<view class="item-row">
					<text>产品名称：{{ item['goodsName'] }}</text>
				</view>
				<view class="item-row">
					<text>客户名称：{{ item['goodsBrandName'] }}</text>
				</view>
				<view class="item-row">
					<text>样品型号：{{ item['goodsSpec'] }}</text>
				</view>
				<view class="item-row">
					<text>样品数量：{{ item['goodsNums'] }}</text>
				</view>
				<view class="item-row">
					<text>实验项目：{{ item['experiment_project_name'] }}</text>
				</view>
				<view class="item-row">
					<text>实验分类：{{ item['experiment_class_name'] }}</text>
				</view>
				<view class="item-row">
					<text>总价：{{ item['reference_price']? item['reference_price'].toFixed(2) : '0.00' }}</text>
				</view>
			</view>
		</view>
		<my-loading :loading="loading" :isRefresh="is_refresh" :total="list.length"></my-loading>

		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import {
		fetchTestChildOrderListApi
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
				key_words: ''
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
			search() {
				this.list = []
				this.page = 1
				this.is_refresh = true
				this.getList()
			},
			getList() {
				this.loading = true
				fetchTestChildOrderListApi({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
					ofId: this.ofId,
					order_id: this.key_words
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
	@import '@/layout/search.scss';
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