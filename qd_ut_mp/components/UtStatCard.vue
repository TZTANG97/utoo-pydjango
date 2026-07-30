<!-- 愉兔统计/入口卡片：个人中心等页面复用 -->
<template>
	<view class="ut-stat-card" @click="$emit('click')">
		<view class="ut-stat-card__mark">
			<text>{{ displayMark }}</text>
		</view>
		<view class="ut-stat-card__body">
			<text class="ut-stat-card__title">{{ title }}</text>
			<text v-if="showCount" class="ut-stat-card__count">{{ count }}</text>
		</view>
	</view>
</template>

<script>
	export default {
		name: 'UtStatCard',
		props: {
			title: {
				type: String,
				default: ''
			},
			count: {
				type: [Number, String],
				default: null
			},
			mark: {
				type: String,
				default: ''
			}
		},
		computed: {
			displayMark() {
				if (this.mark) return String(this.mark).slice(0, 1)
				return String(this.title || '').slice(0, 1) || '·'
			},
			showCount() {
				return this.count !== null && this.count !== undefined && this.count !== ''
			}
		}
	}
</script>

<style lang="scss" scoped>
	.ut-stat-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 100%;
		min-height: 188rpx;
		padding: $ut-space-3 $ut-space-2;
		background: $ut-card;
		border-radius: $ut-radius-md;
		border: 1rpx solid $ut-border;
		box-sizing: border-box;

		&:active {
			background: $ut-primary-soft;
			border-color: rgba(233, 99, 2, 0.35);
		}
	}

	.ut-stat-card__mark {
		width: 72rpx;
		height: 72rpx;
		border-radius: $ut-radius-md;
		background: $ut-primary-soft;
		display: flex;
		align-items: center;
		justify-content: center;

		text {
			font-size: 32rpx;
			font-weight: 600;
			color: $ut-primary;
			line-height: 1;
		}
	}

	.ut-stat-card__body {
		margin-top: $ut-space-2;
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 100%;
	}

	.ut-stat-card__title {
		font-size: 24rpx;
		color: $ut-text;
		text-align: center;
		line-height: 1.35;
		max-width: 100%;
	}

	.ut-stat-card__count {
		margin-top: 6rpx;
		font-size: 28rpx;
		font-weight: 600;
		color: $ut-primary;
		line-height: 1.2;
	}
</style>
