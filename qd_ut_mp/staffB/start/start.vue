<template>
	<view class="container">
		<view class="cover" :class="{'close-page': close}">
			<image style="width: 100%;height: 100%" src="../static/start.png" mode=""></image>
			<view class="skip" @click="goHome">
				<text>跳过&nbsp;{{ duration }}s</text>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				close: false,
				timer: null,
				duration: 4
			}
		},
		onLoad() {
			this.timer = setInterval(() => {
				this.duration--
				if (!this.duration) {
					this.goHome()
				}
			}, 1000)
		},
		methods: {
			goHome() {
				clearInterval(this.timer)
				this.close = true
				setTimeout(() => {
					uni.switchTab({
						url: '/pages/test_sub/test_sub'
					})
				}, 500)
			}
		},
	}
</script>

<style scoped>
	.container {
		display: flex;
		height: 100vh;
		align-items: center;
	}

	.cover {
		position: relative;
		overflow: hidden;
		transition: all .3s ease-out;
		width: 100vw;
		height: 100vh;
	}

	.skip {
		display: inline-block;
		position: absolute;
		z-index: 2;
		right: 30rpx;
		bottom: 40rpx;
		color: #fff;
		border: 2rpx solid #fff;
		border-radius: 30rpx;
		padding: 8rpx 23rpx;
	}

	.close-page {
		animation: closeAmt .45s linear forwards;
	}

	@keyframes closeAmt {

		20% {
			height: 60vh;
			border-radius: 50%;
		}

		30% {
			height: 100vw;
			border-radius: 50%;
		}

		40% {
			border-radius: 50%;
			height: 100vw;
		}

		50% {
			border-radius: 50%;
			height: 100vw;
		}

		60% {
			border-radius: 50%;
			height: 100vw;
			transform: scale(0.75);
		}

		70% {
			border-radius: 50%;
			height: 100vw;
			transform: scale(0.7);
		}

		80% {
			border-radius: 50%;
			height: 100vw;
			transform: scale(0.5);
		}

		90% {
			border-radius: 50%;
			height: 100vw;
			transform: scale(0.25);
		}

		100% {
			border-radius: 50%;
			height: 100vw;
			transform: scale(0);
			display: none;
		}
	}
</style>