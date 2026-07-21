<template>
	<view class="container" v-if="order_data">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					子订单编号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ order_data['order_id'] }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					来源单号
				</view>
				<view class="group-content">
					<view class="text-content">
						<span>{{ order_data['parentOf']? order_data['parentOf']['order_id'] : '暂无' }}</span>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单状态
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ order_data['order_statusstr'] }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					预计收货时间
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ order_data['delivery_time']? $alterTime(order_data['delivery_time']) : '' }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="order_data.order_type == 10">
				<view class="group-label">
					订单类型
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ order_data['testClass']['name'] }}
					</view>
				</view>
			</view>
			<template v-if="order_data['files'].length">
				<view class="group-item">
					<view class="group-label">
						测试数据
					</view>
					<view class="group-content">
						<view class="text-content">
							<u-icon size="28" name="arrow-down"></u-icon>
						</view>
					</view>
				</view>
				<view class="files-list">
					<view class="file-item" v-for="(item, index) in order_data['files']" :key="index"
						@click="preImage(index)">
						<text style="color: #3C8BDB;">{{ item.info }}</text>
					</view>
				</view>
			</template>
		</view>

		<view class="btns">
			<navigator class="btn"
				:url="`/pagesB/test_child_order_product_list/test_child_order_product_list?id=${id}&order_type=${order_data['order_type']}`"
				hover-class="none">
				产品列表
			</navigator>
		</view>
		<u-toast ref="uToast" />

		<time-line :logs="order_data['logs']"></time-line>
	</view>
</template>

<script>
	import {
		timeLine
	} from '../timeLine.vue'
	import {
		fetchTestChildOrderDetailApi
	} from '@/api/index.js'
	export default {
		components: {
			timeLine
		},
		data() {
			return {
				id: '',
				order_data: null
			}
		},
		onLoad({
			id = ''
		}) {
			if (id) {
				this.id = id
			}
			this.getDetail()
		},
		methods: {
			preImage(index) {
				let list = this.order_data['files'].map(e => e.path + '/' + e.name)
				this.$preFile(index, list)
			},

			// 获取详情
			getDetail() {
				fetchTestChildOrderDetailApi({
					id: this.id
				}).then(res => {
					if (res.res) {
						const {
							logs = [], files = []
						} = res.obj
						this.order_data = res.obj.of
						this.order_data.logs = logs
						this.order_data.files = files
					} else {
						thsi.$toast(res.resMsg)
					}
				})
			}
		}
	}
</script>

<style scoped lang="scss">
	@import '@/layout/group.scss';

	.btns {
		display: flex;
		flex-direction: row-reverse;
		flex-wrap: wrap;
		margin-bottom: 20rpx;

		.btn {
			height: 70rpx;
			border-radius: 40rpx;
			text-align: center;
			line-height: 70rpx;
			margin-right: 20rpx;
			padding: 0 40rpx;
			background-color: $primary;
			color: #fff;
			margin-top: 20rpx;
		}
	}

	.primary {
		color: $primary !important;
	}
</style>

<style>
	page {
		background-color: #f2f2f2;
	}
</style>
