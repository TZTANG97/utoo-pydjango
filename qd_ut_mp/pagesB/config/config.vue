<template>
	<view class="container">
		<view class="code">{{ code }}</view>
		<button @click="copy" v-if="code">复制</button>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				code: ''
			}
		},
		onLoad() {
			this.getCode()
		},
		methods: {
			getCode() {
				const that = this
				wx.login({
					success(res) {
						that.code = res.code
					}
				})
			},
			copy() {
				wx.setClipboardData({
					data: this.code,
					success(res) {
						wx.showToast({
							icon: 'none',
							title: '复制成功'
						})
					}
				})
			}
		}
	}
</script>

<style scoped>
	.container {
		text-align: center;
	}

	.code {
		margin: 20rpx 0;
	}
</style>