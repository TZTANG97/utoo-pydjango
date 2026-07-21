<template>
	<view class="container">
		<view class="form-item">
			<input v-model="phone" type="number" maxlength="11"
				placeholder="请输入手机号">
		</view>
		<view class="form-item code">
			<input v-model="code" type="number" maxlength="6" placeholder="请输入验证码">
			<view class="get-code" @click="getCode">
				{{ btnText }}
			</view>
		</view>

		<view class="main-btn" @click="verifyPhone">
			确&nbsp;定
		</view>
	</view>
</template>

<script>
	import {
		fetchCodeApi,
		verifyCodeApi
	} from '@/api/forget_password.js'
	import {
		verifyField
	} from '@/utils/index.js'
	export default {
		data() {
			return {
				btnText: '获取验证码',
				cooling: false,
				timer: null,
				phone: '',
				code: ''
			}
		},
		onLoad() {
		},
		methods: {
			// 验证手机号
			verifyPhone() {
				if (!this.phone) return this.$toast('请输入手机号')
				if (!verifyField('phoneNumber', this.phone)) return this.$toast('手机号格式不正确')
				if (!this.code) return this.$toast('请输入验证码')

				verifyCodeApi({
					phone: this.phone,
					code: this.code
				}).then(({
					res,
					resMsg
				}) => {
					if (res) {
						uni.redirectTo({
							url: `/staffB/set_password/set_password?mobile=${this.phone}`
						})
					} else {
						this.$toast(resMsg)
					}
				})

			},


			// 获取验证码
			getCode() {
				if (this.cooling) return
				if (!this.phone) return this.$toast('请输入手机号')
				if (!verifyField('phoneNumber', this.phone)) return this.$toast('手机号格式不正确')
				fetchCodeApi(this.phone).then(({
					res,
					resMsg
				}) => {
					if (res) {
						this.$toast('验证码已发送')
						this.cooling = true
						let time = 60
						this.btnText = `${time}s`
						this.timer = setInterval(() => {
							time--;
							if (!time) {
								clearInterval(this.timer)
								this.btnText = '获取验证码'
								this.cooling = false
							} else {
								this.btnText = `${time}s`
							}
						}, 1000)
					} else {
						this.$toast(resMsg)
					}
				})
			},
		}
	}
</script>

<style scoped lang="scss">
	@import "@/layout/form-item.scss";

	.code {
		position: relative;
		margin-top: 40rpx !important;
	}

	.get-code {
		position: absolute;
		right: 0;
		top: 50%;
		transform: translateY(-50%);
		font-size: 25rpx;
		z-index: 2;
		color: $primary;
	}

	.container {
		padding: 0 30rpx;
	}
</style>