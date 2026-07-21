<template>
	<view class="container">
		<view class="form-item">
			<view class="label">
				{{ loginWay? '账号' : '手机号' }}：
			</view>
			<view class="control">
				<input type="text" v-model="phoneNumber" maxlength="11"
					:placeholder="`请输入${ loginWay? '账号' : '手机号' }`">
			</view>
		</view>
		<view class="form-item" v-if="loginWay">
			<view class="label">
				密码：
			</view>
			<view class="control">
				<input type="password" v-model="password" maxlength="20" placeholder="请输入密码">
			</view>
		</view>
		<view class="form-item" v-else>
			<view class="label">
				验证码：
			</view>
			<view class="control" style="position: relative;">
				<text @click="getCode" class="code">{{ text }}</text>
				<input type="number" v-model="code" maxlength="6" placeholder="请输入验证码">
			</view>
		</view>

		<view class="sup-login flex-between">
			<text v-if="loginWay" @click="switchLoginWay(false)">验证码登录</text>
			<text v-else @click="switchLoginWay(true)">密码登录</text>
			<navigator url="/staffB/forget_password/forget_password" hover-class="none">
				找回密码
			</navigator>
		</view>

		<view class="main-btn empty-btn" @click="login">
			登&nbsp;录
		</view>

		<view class="get-phone-number-com">
			<button class="main-btn login-for-wx" type="default" open-type="getPhoneNumber"
				@getphonenumber="fastLoginForWx">手机号快捷登录</button>
		</view>

		<!-- 		<view class="register">
			快速注册
		</view> -->
	</view>
</template>

<script>
	import {
		verifyField
	} from '@/utils/index.js';
	import {
		// 密码登录
		loginForPwdApi,
		// 获取验证码
		getCodeApi,
		// 验证码登录
		loginForCodeApi,
		// 一键登录
		fastLoginApi, fetchUserListApi
	} from '@/api/loign.js'
	export default {
		data() {
			return {
				// 判断登录方式
				loginWay: true,
				phoneNumber: '',
				password: '',
				code: '',
				// 是否正在获取验证码
				text: '获取验证码',
				timer: null
			};
		},
		methods: {
			// 获取验证码
			getCode() {
				if (this.text != '获取验证码') return
				if (!this.phoneNumber) return this.$toast('请输入手机号')
				if (!verifyField('phoneNumber', this.phoneNumber)) return this.$toast('手机号格式不正确');
				getCodeApi(this.phoneNumber).then(res => {
					if (res.res) {
						this.$toast('验证码已发送')
						let s = 60;
						this.text = `${s}s`
						this.timer = setInterval(() => {
							s--;
							if (s) {
								this.text = `${s}s`
							} else {
								clearInterval(this.timer)
								this.timer = null
								this.text = '获取验证码'
							}
						}, 1000)
					} else {
						this.$toast(res.resMsg)
					}
				})
			},

			// 切换登录方式
			switchLoginWay(mode) {
				this.loginWay = mode
				if (this.loginWay) {
					this.code = ''
				} else {
					this.password = ''
				}
			},

			// 登录
			login() {
				if (!this.phoneNumber) return this.$toast(`请输入${this.loginWay? '账号' : '手机号'}`);
				if(!this.loginWay && !verifyField('phoneNumber', this.phoneNumber)) return this.$toast('手机号格式不正确');
				if (this.loginWay) {
					if (!this.password) return this.$toast('请输入密码');
					loginForPwdApi({
						loginName: this.phoneNumber,
						password: this.password
					}).then(res => {
						if (res.res) {
							res.obj.wx_nickname = decodeURI(res.obj.wx_nickname)
							uni.setStorageSync('userInfo', res.obj)
							uni.setStorageSync('token', res.obj['token'])
							if(res.obj['uType']) {
								uni.setStorageSync('uType', res.obj['uType'])
							}
							fetchUserListApi().then(res => {
								if(res.res) {
									uni.setStorageSync("userList", res.obj)
								}
							})
							uni.switchTab({
								url: '/pages/my/my'
							})
							uni.$emit('checkAuth')
						} else {
							this.$toast(res.resMsg)
						}
					})
				} else {
					if (!this.code) return this.$toast('请输入验证码');
					loginForCodeApi(this.phoneNumber, this.code).then(res => {
						if (res.res) {
							res.obj.wx_nickname = decodeURI(res.obj.wx_nickname)
							uni.setStorageSync('userInfo', res.obj)
							uni.setStorageSync('token', res.obj['token'])
							if(res.obj['uType']) {
								uni.setStorageSync('uType', res.obj['uType'])
							}
							fetchUserListApi().then(res => {
								if(res.res) {
									uni.setStorageSync("userList", res.obj)
								}
							})
							uni.switchTab({
								url: '/pages/my/my'
							})
							uni.$emit('checkAuth')
						} else {
							this.$toast(res.resMsg)
						}
					})
				}


			},


			// 微信一键登录
			async fastLoginForWx({
				detail: {
					errMsg,
					code = ''
				}
			}) {
				if (errMsg === 'getPhoneNumber:ok') {
					let result = await fastLoginApi(code)
					if (result.res) {
						result.obj['photo'] = result.obj['photo'].replace('\\', '/')
						result.obj.wx_nickname = decodeURI(result.obj.wx_nickname)
						uni.setStorageSync('userInfo', result.obj)
						uni.setStorageSync('token', result.obj['token'])
						fetchUserListApi().then(res => {
							if(res.res) {
								uni.setStorageSync("userList", res.obj)
							}
						})
						// 判断是不是内部账号
						if(result.obj['uType']) {
							uni.setStorageSync('uType', result.obj['uType'])
						}
						uni.switchTab({
							url: '/pages/my/my'
						})
						uni.$emit('checkAuth')
					} else {
						this.$toast(result.resMsg)
					}
				}
			}
		}
	}
</script>

<style lang="scss" scoped>
	@import "@/layout/form-item.scss";

	.code {
		position: absolute;
		right: 0;
		top: 50%;
		transform: translateY(-50%);
		color: $primary;
		z-index: 9;
	}

	.register {
		margin-top: 30rpx;
		text-align: center;
		color: $primary;
	}

	.get-phone-number-com {
		position: relative;

		&::after {
			display: block;
			position: absolute;
			content: '最多使用';
			right: 0;
			top: -7rpx;
			width: 100rpx;
			height: 45rpx;
			text-align: center;
			border-bottom-right-radius: 25rpx;
			border-top-left-radius: 25rpx;
			line-height: 45rpx;
			font-size: 20rpx;
			color: #fff;
			background-color: #ED9E1C;
		}
	}

	.login-for-wx {
		background-color: $primary !important;
		color: #fff;
		font-size: 28rpx;
	}

	.sup-login {
		color: $primary;
		margin-top: 15rpx;
		// padding: 0 10rpx;
	}

	.main-btn {
		width: 650rpx;
	}

	.container {
		padding: 0 30rpx;
	}
</style>
