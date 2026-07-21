<template>
	<view class="container">
		<view class="get-phone-number-com">
			<button class="main-btn login-for-wx" type="default" open-type="getPhoneNumber"
				@getphonenumber="fastLoginForWx">授权绑定手机号</button>
			<view class="info">
				授权手机号绑定，便于后续扫码登录及获取服务消息
			</view>
		</view>
	</view>
</template>

<script>
	import {
		getUserInfoApi
	} from '@/api/loign.js'
	import {
		checkCardIsExpired
	} from '@/api/index'
	export default {
		data() {
			return {
				openid: '',
				ticket: ''
			}
		},
		onLoad({
			openid = '',
			ticket = ''
		}) {
			this.ticket = ticket
			this.openid = openid
			checkCardIsExpired({
				ticket
			}).then(res => {
				if (res.res) {
					// 判断小程序是否已登录
					const token = uni.getStorageSync('token');
					if (token) {
						uni.redirectTo({
							url: `/staffB/fill_info/fill_info?openid=${this.openid}&ticket=${this.ticket}`
						})
					}
				} else {
					uni.switchTab({
						url: '/pages/index/index'
					})
				}
			})
		},
		methods: {
			async fastLoginForWx({
				detail: {
					errMsg,
					code = ''
				}
			}) {
				if (errMsg === 'getPhoneNumber:ok') {
					const result = await getUserInfoApi({
						openid: this.openid,
						code,
						ticket: this.ticket
					})
					const {
						res,
						obj = ''
					} = result
					if (res) {
						result.obj['photo'] = result.obj['photo'].replace('\\', '/')
						result.obj.wx_nickname = decodeURI(result.obj.wx_nickname)
						uni.setStorageSync('userInfo', result.obj)
						uni.setStorageSync('token', result.obj['token'])
						// 判断是不是内部账号
						if (result.obj['uType']) {
							uni.setStorageSync('uType', result.obj['uType'])
						}
						
						uni.redirectTo({
							url: `/staffB/fill_info/fill_info?openid=${this.openid}&mobile=${obj}&ticket=${this.ticket}`
						})
					} else {
						this.$toast(result.resMsg ? result.resMsg : '授权失败')
					}
				} else {
					this.$toast('授权失败，请重试！')
				}
			}
		}
	}
</script>

<style scoped lang="scss">
	
	.info {
		color: #C2C2C2;
		font-size: 24rpx;
		margin-top: 20rpx;
		text-align: center;
	}
	
	.get-phone-number-com {
		margin: 150px auto 0;
	}

	.login-for-wx {
		background-color: $primary !important;
		color: #fff;
		font-size: 28rpx;
	}

	.main-btn {
		width: 650rpx;
	}

	.container {
		padding: 0 30rpx;
	}
</style>