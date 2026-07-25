<template>
	<view class="detail" v-if="showData">
		<view class="detail-hero">
			<swiper class="detail-hero__swiper" :indicator-dots="true" indicator-active-color="#E96302" indicator-color="rgba(0,0,0,0.15)">
				<swiper-item v-for="(item, idx) in showData['manage_photos']" :key="idx">
					<image :src="item" mode="aspectFill"></image>
				</swiper-item>
			</swiper>
		</view>

		<view class="detail-body">
			<view class="detail-name" v-if="showData.name">{{ showData.name }}</view>
			<view class="detail-cta" @click="sub">预约实验</view>

			<view class="detail-section">
				<view class="detail-section__head">
					<view class="detail-section__bar"></view>
					<text class="detail-section__title">实验介绍</text>
				</view>
				<view class="detail-section__content">
					<rich-text :nodes="showData['app_project_details']"></rich-text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import {
		fetchProjectIntroduceApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
				id: '',
				showData: null,
				special_type:0
			};
		},
		onLoad({
			id
		}) {
			this.id = id
			this.getDetail()
		},
		onPullDownRefresh() {
			fetchProjectIntroduceApi(this.id).then(({
				res,
				resMsg,
				obj
			}) => {
				if (res) {
					obj['manage_photos'].forEach(item => {
						item = item? item.replace(/\\/g, '/') : ''
					})
					obj['app_project_details'] = obj['app_project_details']? obj['app_project_details'].replace(/\<img/gi, '<img style="max-width:100%;height:auto" ') : ''
					this.showData = obj
				} else {
					this.$toast(`${resMsg},请刷新重试！`)
				}
			}).finally(_ => {
				uni.stopPullDownRefresh()
			})
		},
		methods: {

			// 获取详情
			getDetail() {
				fetchProjectIntroduceApi(this.id).then(({
					res,
					resMsg,
					obj
				}) => {
					if (res) {
						this.special_type = obj.special_type
						obj['manage_photos'].forEach(item => {
							item = item? item.replace(/\\/g, '/') : ''
						})
						obj['app_project_details'] = obj['app_project_details']? obj['app_project_details'].replace(/\<img/gi, '<img style="max-width:100%;height:auto"') : ''
						this.showData = obj
					} else {
						this.$toast(`${resMsg},请刷新重试！`)
					}
				})
			},

			// 登录之后才能预约
			sub() {
				const token = uni.getStorageSync('token');
				if (token) {
					// 发起预约
					uni.navigateTo({
						url: '/staffB/sub/sub?id=' + this.id+`|${this.special_type}`
					})

				} else {
					uni.navigateTo({
						url: '/pages/login/login'
					})
				}
			},
		}
	}
</script>

<style lang="scss" scoped>
	.detail {
		min-height: 100vh;
		background: $ut-bg;
		padding-bottom: calc(40rpx + env(safe-area-inset-bottom));
		box-sizing: border-box;
	}

	.detail-hero {
		padding: $ut-space-3 $ut-space-3 0;

		&__swiper {
			width: 100%;
			height: 520rpx;
			border-radius: $ut-radius-lg;
			overflow: hidden;
			background: $ut-card;
			box-shadow: 0 8rpx 24rpx rgba(31, 35, 41, 0.08);

			image {
				width: 100%;
				height: 100%;
				display: block;
			}
		}
	}

	.detail-body {
		margin: $ut-space-3;
		padding: $ut-space-4;
		border-radius: $ut-radius-lg;
		background: $ut-card;
		box-shadow: 0 8rpx 24rpx rgba(31, 35, 41, 0.06);
	}

	.detail-name {
		font-size: 34rpx;
		font-weight: 700;
		color: $ut-text;
		line-height: 1.4;
		margin-bottom: $ut-space-3;
	}

	.detail-cta {
		text-align: center;
		padding: 26rpx 0;
		border-radius: 999rpx;
		background: linear-gradient(135deg, #FF8A3D 0%, $ut-primary 100%);
		color: #fff;
		font-size: 30rpx;
		font-weight: 600;
		box-shadow: 0 10rpx 24rpx rgba(233, 99, 2, 0.35);

		&:active {
			opacity: 0.92;
			transform: scale(0.99);
		}
	}

	.detail-section {
		margin-top: $ut-space-4;

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
		}

		&__title {
			font-size: 28rpx;
			font-weight: 700;
			color: $ut-text;
		}

		&__content {
			font-size: 26rpx;
			line-height: 1.7;
			color: $ut-text-secondary;
			word-break: break-word;
		}
	}
</style>

<style lang="scss">
	page {
		background-color: $ut-bg;
	}
</style>
