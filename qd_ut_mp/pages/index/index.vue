<template>
	<view class="book">
		<view class="book-search">
			<navigator class="book-search__box" url="/staffB/search/search" hover-class="none">
				<image class="book-search__icon" src="@/static/search.png" mode="aspectFit"></image>
				<input :disabled="true" class="book-search__input" type="text" placeholder="搜索实验 / 设备名称">
			</navigator>
		</view>

		<view class="book-body" :style="{ height: usable_heihgt + 'px' }">
			<scroll-view class="book-side" scroll-y :style="{ height: usable_heihgt + 'px' }">
				<view
					v-for="(item, idx) in cateList"
					:key="idx"
					class="book-side__item"
					:class="{ 'is-active': idx === cateIndex }"
					@click="changeCate(idx)"
				>
					<text class="book-side__name">{{ item['name'] }}</text>
				</view>
			</scroll-view>

			<scroll-view class="book-main" scroll-y :style="{ height: usable_heihgt + 'px' }">
				<template v-if="cateList && cateList[cateIndex] && cateList[cateIndex]['childList'].length">
					<view
						class="book-section"
						v-for="(item2, idx2) in cateList[cateIndex]['childList']"
						:key="idx2"
					>
						<view class="book-section__head">
							<view class="book-section__bar"></view>
							<text class="book-section__title">{{ item2['name'] }}</text>
						</view>
						<view class="book-grid">
							<view
								class="book-card"
								v-for="(item3, idx3) in item2['childList']"
								:key="idx3"
								@click="knowMore(item3.id)"
							>
								<view class="book-card__media">
									<image :src="item3.main_photo" mode="aspectFill"></image>
								</view>
								<text class="book-card__name">{{ item3.name }}</text>
							</view>
						</view>
					</view>
				</template>
				<view class="book-empty" v-else>
					<view class="book-empty__dot"></view>
					<text class="book-empty__text">暂无实验</text>
					<text class="book-empty__hint">换个分类试试</text>
				</view>
			</scroll-view>
		</view>
	</view>
</template>

<script>
	import {
		fetchCateListApi,
		fetchProjectIntroduceApi
	} from '@/api/index.js'
	import MyLoading from "@/components/loading"
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				testList: [],
				usable_heihgt: 0,
				cateList: [],
				cateIndex: 0,
			}
		},
		onLoad() {
			const that = this
			uni.getSystemInfo({
				success(res) {
					// header 约 112rpx（搜索区）
					that.usable_heihgt = res.windowHeight - (res.screenWidth / 750) * 112
				}
			})
			fetchCateListApi().then(res => {
				if (res.res) {
					this.cateList = res.obj
					this.cateList.forEach(item2 => {
						this.testList = [...this.testList, ...item2.childList]
					})
				}
			})
		},
		methods: {
			changeCate(idx) {
				if (this.cateIndex === idx) return
				this.cateIndex = idx
			},
			knowMore(id) {
				uni.navigateTo({
					url: `/staffB/test_detail/test_detail?id=${id}`
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
	.book {
		min-height: 100%;
		background: $ut-bg;
		display: flex;
		flex-direction: column;
	}

	.book-search {
		padding: $ut-space-2 $ut-space-3 $ut-space-3;
		background: linear-gradient(180deg, #FFF7F0 0%, $ut-bg 100%);

		&__box {
			position: relative;
			display: flex;
			align-items: center;
			height: 72rpx;
			padding: 0 $ut-space-3 0 72rpx;
			background: $ut-card;
			border-radius: 999rpx;
			border: 1rpx solid rgba(233, 99, 2, 0.12);
			box-shadow: 0 8rpx 20rpx rgba(233, 99, 2, 0.08);
		}

		&__icon {
			position: absolute;
			left: 28rpx;
			top: 50%;
			transform: translateY(-50%);
			width: 32rpx;
			height: 32rpx;
			opacity: 0.55;
		}

		&__input {
			flex: 1;
			height: 72rpx;
			font-size: 26rpx;
			color: $ut-text;
			background: transparent;
		}
	}

	.book-body {
		display: flex;
		flex: 1;
		min-height: 0;
		background: $ut-card;
		border-radius: $ut-radius-lg $ut-radius-lg 0 0;
		overflow: hidden;
		box-shadow: 0 -6rpx 20rpx rgba(31, 35, 41, 0.04);
	}

	.book-side {
		width: 200rpx;
		flex-shrink: 0;
		background: $ut-bg;

		&__item {
			position: relative;
			min-height: 112rpx;
			padding: $ut-space-3 16rpx;
			display: flex;
			align-items: center;
			justify-content: center;
			box-sizing: border-box;

			&.is-active {
				background: $ut-card;

				&::before {
					content: '';
					position: absolute;
					left: 0;
					top: 50%;
					transform: translateY(-50%);
					width: 6rpx;
					height: 44rpx;
					border-radius: 0 6rpx 6rpx 0;
					background: $ut-primary;
				}

				.book-side__name {
					color: $ut-primary;
					font-weight: 700;
				}
			}

			&:active:not(.is-active) {
				background: rgba(233, 99, 2, 0.06);
			}
		}

		&__name {
			font-size: 24rpx;
			line-height: 1.4;
			text-align: center;
			color: $ut-text-secondary;
		}
	}

	.book-main {
		flex: 1;
		min-width: 0;
		background: $ut-card;
		padding: $ut-space-3 $ut-space-3 40rpx;
		box-sizing: border-box;
	}

	.book-section {
		margin-bottom: $ut-space-4;

		&__head {
			display: flex;
			align-items: center;
			margin-bottom: $ut-space-3;
		}

		&__bar {
			width: 8rpx;
			height: 28rpx;
			border-radius: 8rpx;
			background: linear-gradient(180deg, #FF8A3D 0%, $ut-primary 100%);
			margin-right: 12rpx;
			flex-shrink: 0;
		}

		&__title {
			font-size: 28rpx;
			font-weight: 700;
			color: $ut-text;
		}
	}

	.book-grid {
		display: flex;
		flex-wrap: wrap;
		margin: 0 -8rpx;
	}

	.book-card {
		width: 50%;
		padding: 0 8rpx;
		margin-bottom: $ut-space-3;
		box-sizing: border-box;

		&:active {
			opacity: 0.88;
		}

		&__media {
			width: 100%;
			height: 160rpx;
			border-radius: $ut-radius-md;
			overflow: hidden;
			background: $ut-bg;
			border: 1rpx solid $ut-border;
			box-shadow: 0 4rpx 12rpx rgba(31, 35, 41, 0.04);

			image {
				width: 100%;
				height: 100%;
				display: block;
			}
		}

		&__name {
			margin-top: 12rpx;
			padding: 0 4rpx;
			font-size: 24rpx;
			line-height: 1.35;
			color: $ut-text;
			overflow: hidden;
			text-overflow: ellipsis;
			display: -webkit-box;
			-webkit-box-orient: vertical;
			-webkit-line-clamp: 2;
			text-align: center;
		}
	}

	.book-empty {
		padding: 120rpx 0;
		display: flex;
		flex-direction: column;
		align-items: center;

		&__dot {
			width: 72rpx;
			height: 72rpx;
			border-radius: 50%;
			background: $ut-primary-soft;
			margin-bottom: $ut-space-3;
			position: relative;

			&::after {
				content: '';
				position: absolute;
				left: 50%;
				top: 50%;
				width: 28rpx;
				height: 4rpx;
				border-radius: 4rpx;
				background: $ut-primary;
				transform: translate(-50%, -50%);
			}
		}

		&__text {
			font-size: 28rpx;
			color: $ut-text;
			font-weight: 600;
		}

		&__hint {
			margin-top: 8rpx;
			font-size: 22rpx;
			color: $ut-text-secondary;
		}
	}
</style>

<style lang="scss">
	page {
		background-color: $ut-bg;
	}
</style>
