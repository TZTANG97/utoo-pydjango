<template>
	<!-- 列表loading组件 -->
	<view class="my-loading">
		<view v-if="loading">
			<view class="show-my-loading">
				<u-loading mode="flower"></u-loading>
				<text>努力加载中...</text>
			</view>
		</view>
		<view v-else>
			<view v-if="!isRefresh" class="wrapper">
				<view v-if="total > 0" style="padding: 20rpx 0;">没有更多数据了~</view>
				<view v-else style="padding: 100rpx 0;">暂无数据</view>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		name: "listLoading",
		props: {
			loading: {
				type: Boolean,
				default: false
			},
			isRefresh: {
				type: Boolean,
				default: true
			},
			total: {
				type: Number,
				default: 0
			}
		}
	}
</script>

<style scoped>
	.my-loading {
		color: #999;
		font-size: 26rpx;
		min-height: 79rpx;
	}

	.show-my-loading {
		padding: 20rpx 0;
	}

	.show-my-loading text {
		margin-left: 10rpx;
	}

	.wrapper,
	.show-my-loading {
		text-align: center;
		vertical-align: middle;
	}
</style>
