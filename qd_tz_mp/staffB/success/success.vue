<template>
	<view class="container">
		<image src="@/static/success.png" mode=""></image>
		<view class="title">
			{{ title }}
		</view>
		<navigator open-type="navigateBack" hover-class="none" :delta="1" class="main-btn">
			确&nbsp;定
		</navigator>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				title: ''
			};
		},
		onLoad({
			title = ''
		}) {
			this.title = decodeURI(title)
		},
	}
</script>

<style lang="scss" scoped>
	.main-btn {
		border-radius: 10rpx;
		width: 350rpx;
	}

	.title {
		font-size: 35rpx;
	}

	.container {
		text-align: center;
	}

	image {
		width: 100rpx;
		height: 100rpx;
		margin: 50rpx 0 35rpx;
	}
</style>