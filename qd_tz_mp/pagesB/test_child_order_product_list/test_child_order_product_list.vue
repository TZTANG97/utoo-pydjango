<template>
	<view class="container">
		<view class="list">
			<view class="item" v-for="(item, index) in list" :key="index">
				<view class="item-row">
				</view>
				<view class="item-row">
					<text>客户名称：{{ item['goods_brand_name'] }}</text>
				</view>
				<view class="item-row">
					<text>样品名称：{{ item['goods_name'] }}</text>
				</view>
				<view class="item-row">
					<text>样品型号：{{ item['goods_spec'] }}</text>
				</view>
				<view class="item-row">
					<text>样品数量：{{ item['goods_nums'] }}</text>
				</view>
				<view class="item-row">
					<text>实验项目：{{ item['experiment_project_name'] }}</text>
				</view>
				<view class="item-row" v-if="order_type == 10">
					<text>实验分类：{{ item['experiment_class_name'] }}</text>
				</view>
				<view class="item-row">
					<text>状态：{{ item['orderStautsStr'] }}</text>
				</view>

				<template v-if="item['testFiles'].length">
					<view class="item-row">
						<text>订单资料：</text>
					</view>
					<view class="item-row file" v-for="(file, idx) in item['testFiles']" :key="index"
						@click.stop="downloadFile(file['path'] + '/' + file['name'])">
						<text>{{ file['info'] }}</text>
					</view>
				</template>

				<view class="btns">
					<navigator v-if="item['ispcfc']" :url="`/pagesB/anew_test/anew_test?id=${item.id}`" class="btn">
						再次测试
					</navigator>
					<view v-if="item['ispcqr']" class="btn" @click="confirmComplete(item.id)">
						确认完成
					</view>
				</view>
			</view>
		</view>

		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import {
		confirmCompleteApi,
		fetchTestChildOrderDetailApi,
	} from '@/api/index.js'
	export default {
		data() {
			return {
				id: '',
				list: [],
				order_type: ''
			};
		},
		onLoad({
			id = '',
			order_type = ''
		}) {
			if (id) this.id = id
			if (order_type) this.order_type = order_type
			this.getDetail()
		},
		methods: {
			// 确认完成
			confirmComplete(id) {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确认完成订单？',
					success({
						confirm
					}) {
						if (confirm) {
							confirmCompleteApi({
								id
							}).then(res => {
								if (res.res) {
									that.$tip('订单已完成')
									that.getDetail()
								} else {
									that.$tip(res.resMsg)
								}
							})
						}
					}
				})

			},


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
				fetchTestChildOrderDetailApi({
					id: this.id
				}).then(res => {
					if (res.res) {
						this.list = res.obj.childs
					} else {
						thsi.$toast(res.resMsg)
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

	.btns {
		display: flex;
		flex-direction: row-reverse;
		flex-wrap: wrap;
		margin: 20rpx 0;

		.btn {
			position: relative;
			height: 70rpx;
			border-radius: 40rpx;
			text-align: center;
			line-height: 70rpx;
			border: 3rpx solid $primary;
			color: $primary;
			margin-right: 20rpx;
			padding: 0 40rpx;
			background-color: transparent;
			z-index: 2;
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