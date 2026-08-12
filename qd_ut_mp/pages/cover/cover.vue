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
			this.startCountdown()
			getXcxBanner().then(res => {
				const banner = res && res.obj && res.obj.banner
				if (banner && banner.path && banner.name) {
					this.url = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/' + banner.path + '/' + banner.name
				}
			}).catch(() => {
				// 体验版未配合法域名等会导致失败；倒计时仍继续，避免白屏卡死
			})
		},
		methods: {
			startCountdown() {
				if (this.timer) return
				this.timer = setInterval(() => {
					if (this.num <= 0) {
						this.go()
					} else {
						this.num--
					}
				}, 1000)
			},
			go() {
				clearInterval(this.timer)
				this.timer = null
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