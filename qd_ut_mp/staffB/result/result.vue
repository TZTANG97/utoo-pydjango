<template>
	<view class="content">
		<image src="@/static/success.png" mode=""></image>
		<view>{{ title }}</view>
		<view v-if="showBtn" class="btn" @click="goBack">返回</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				title: '操作成功',
				showBtn: false
			};
		},
		onLoad(options) {
			let { title } = options
			if(title) this.title = title
			if(title !== '登录成功') {
				this.showBtn = true
			}
		},
		methods: {
			goBack() {
				uni.navigateBack({
					delta: 1,
					fail() {
						uni.switchTab({
							url: '/pages/index/index'
						})
					}
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
.content{
	text-align: center;
	padding-top: 100rpx;
	view {
		margin-top: 10rpx;
		font-size: 30rpx;
	}
	image {
		width: 100rpx;
		height: 100rpx;
	}
	.btn {
		width: 400rpx;
		height: 65rpx;
		border-radius: 10rpx;
		background-color: $primary;
		line-height: 65rpx;
		text-align: center;
		color: #fff;
		margin: 100rpx auto;
	}
}
</style>
