<template>
	<view class="container">
		<view class="form-item">
			<input v-model="pwd" type="password" maxlength="20" placeholder="请输入密码" />
		</view>
		<view class="form-item">
			<input v-model="confirmPwd" type="password" maxlength="20" placeholder="请再次输入密码" />
		</view>
		<view class="main-btn" @click="confirmUpdatePwd">
			确&nbsp;定
		</view>
	</view>
</template>

<script>
	import {
		setPwdApi
	} from '@/api/set_password.js'
	export default {
		data() {
			return {
				phone: '',
				pwd: '',
				confirmPwd: ''
			}
		},
		onLoad({
			mobile = ''
		}) {
			this.phone = mobile
		},
		methods: {
			confirmUpdatePwd() {
				if (!this.pwd) return this.$toast('请输入密码')
				if (!this.confirmPwd) return this.$toast('请再次输入密码')
				if (this.pwd != this.confirmPwd) return this.$toast('两次密码输入不一致')
				setPwdApi({
					phone: this.phone,
					pwd: this.pwd,
					confirmPwd: this.confirmPwd
				}).then(({
					res,
					resMsg
				}) => {
					if (res) {
						this.$toast('设置成功')
						const userInfo = uni.getStorageSync('userInfo');
						if (!userInfo) {
							setTimeout(() => {
								uni.reLaunch({
									url: "/pages/login/login"
								})
							}, 1200)
						} else {
							setTimeout(() => {
								uni.navigateBack({
									delta: 1
								})
							}, 1200)
						}
					} else {
						this.$toast(resMsg)
					}
				})
			}
		}
	}
</script>

<style scoped lang="scss">
	@import "@/layout/form-item.scss";

	.container {
		padding: 0 30rpx;
	}
</style>