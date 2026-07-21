<template>
	<view class="time-line">
		<text>历史操作记录</text>
		<text v-if="showType" style="color: #f39800;font-weight: 700;padding: 10rpx 0;font-size: 25rpx;">测试进度请点击子订单进入查看</text>
		<view class="lv-content">
			<u-time-line class="u-time-lines">
				<u-time-line-item nodeTop="10" class="lv-content-item" v-for="(item, index) in logs" :key="index">
					<template v-slot:node>
						<view class="u-node"></view>
					</template>
					<template v-slot:content>
						<view class="u-order-time">
							<view>{{ $u.timeFormat(item[timeKey], 'yyyy-mm-dd') }}</view>
							<view>{{ $u.timeFormat(item[timeKey], 'hh:MM:ss') }}</view>
						</view>
						<view>
							<view class="u-order-desc" v-if="item.log_user">操作人: {{ item.log_user.trueName }}</view>
							<view class="u-order-desc">
								操 作：
								<u-parse :html="item.log_info"></u-parse>
							</view>
						</view>
					</template>
				</u-time-line-item>
			</u-time-line>
		</view>
		<view class="empty" v-if="!logs.length">暂无操作记录</view>
	</view>
</template>

<script>
	export default {
		name: "timeLine",
		props: {
			logs: {
				type: Array,
				default: () => []
			},
			timeKey: {
				type: String,
				default: 'addTime'
			},
			type:{
				type: Boolean,
			}
		},
		watch:{
			type:{
				deep:true,
				immediate:true,
				handler(val){
					this.showType = val
					
				}
			}
		},
		data() {
			return {
				val:false,
				showType:false
			};
		},
		mounted() {
			console.log(this.type,'type')
			console.log(this.logs,'6666')
		}
	}
</script>

<style lang="scss" scoped>
	.time-line {
		background-color: #fff;
		border-radius: 20rpx;
		padding: 0 30rpx;
		margin-top: 20rpx;

		.u-node {
			width: 15rpx;
			height: 15rpx;
			// border-image: linear-gradient(0deg, #ffceb2, #fff5da) 10 10;
			// background: linear-gradient(0deg, #089fe5 0%, $primary 100%);
			background-color: $primary;
			box-shadow: 0px 3px 5px 0px rgba(183, 71, 42, .7);
			border-radius: 50%;
		}

		.u-order-desc {
			font-size: 24rpx;
			margin-bottom: 12rpx;
			color: #000000;
			font-size: 24rpx;
			opacity: 0.85;
		}

		.u-order-time {
			color: #000000;
			text-align: center;
			opacity: 0.85;
			position: absolute;
			left: -220rpx;
			view {
				font-size: 24rpx;
			}
		}

		.lv-content {
			padding: 30rpx 0 60rpx 180rpx;
			border-radius: 20rpx;
		}

		.lv-content-item {
			position: relative;
		}

		text {
			font-size: 32rpx;
			color: #333333;
			display: block;
			padding: 30rpx 0;
		}
	}
</style>
