<template>
	<view class="container syxHeight">
		<img style="max-width: 100%;max-height: 100%;width: 100%;height: 100%;" :src="url" alt="" />
		<view class="tg" @click="go">跳过{{num}}</view>
	</view>
</template>

<script>
	import {
		getXcxBanner
	} from '@/api/index.js'
	export default {
		data() {
			return {
				url: 'https://qgongye.oss-cn-shanghai.aliyuncs.com/',
				num: 5,
				timer: null
			}
		},
		onLoad() {
			getXcxBanner().then(res => {
				this.url = this.url + res.obj.banner.path + '/' + res.obj.banner.name
				this.timer = setInterval(() => {
					if (this.num == 0) {
						clearInterval(this.timer)
						uni.switchTab({
							url: '/pages/test_sub/test_sub'
						});
					} else {
						this.num--
					}
				}, 1000)
			})

		},
		methods: {
			go() {
				clearInterval(this.timer)
				uni.switchTab({
					url: '/pages/test_sub/test_sub'
				});
			}
		}
	}
</script>

<style>
	.syxHeight {
		position: relative;
		height: 100vh;
		text-align: center;
	}

	.tg {
		position: absolute;
		bottom: 10%;
		right: 8%;
		border: 1rpx #ccc solid;
		background-color: #fff;
		color: #000;
		padding: 8rpx 20rpx;
		border-radius: 30rpx;
	}
</style>