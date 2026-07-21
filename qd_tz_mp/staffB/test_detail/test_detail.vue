<template>
	<view class="container" v-if="showData">
		<swiper class="swiper" :indicator-dots="true">
			<swiper-item v-for="(item, idx) in showData['manage_photos']" :key="idx">
				<image :src="item" mode="widthFix"></image>
			</swiper-item>
		</swiper>
		<view class="main-btn" @click="sub">
			预约实验
		</view>
		<view class="title flex-center">
			实验介绍
		</view>
		<view class="test-decs">
			<rich-text :nodes="showData['app_project_details']"></rich-text>
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
	.title {
		margin-top: 30rpx;
		color: #838487;
		justify-content: center;
		font-size: 32rpx;

		&::before,
		&::after {
			display: block;
			content: '';
			width: 70rpx;
			height: 3rpx;
			background-color: #838487;
		}

		&::before {
			margin-right: 20rpx;
		}

		&::after {
			margin-left: 20rpx;
		}
	}

	.main-btn {
		margin-bottom: 40rpx;
	}

	.test-decs {
		margin-top: 15rpx;
		color: #A1A3A6;
		font-size: 26rpx;
	}

	.container {
		padding: 0 56rpx;
	}



	.swiper {
		width: 100%;
		height: 747rpx;
		margin-top: 20rpx;
		swiper-item {
			position: relative;
		}

		image {
			position: absolute;
			left: 50%;
			top: 50%;
			transform: translate(-50%, -50%);
		}
	}


	.container {
		overflow: hidden;
	}
</style>
