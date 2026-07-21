<template>
	<view class="container">
		<view class="form">
			<view class="form-item">
				<view class="label">
					公司/学校：
				</view>
				<view class="control">
					<input :disabled="disabled" type="text" maxlength="30" v-model="company_name"
						placeholder="请输入公司名称或学校名称">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					姓名：
				</view>
				<view class="control">
					<input :disabled="disabled" type="text" maxlength="8" v-model="trueName" placeholder="请输入姓名">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					手机号：
				</view>
				<view class="control">
					<input :disabled="disabled" type="number" maxlength="11" v-model="mobile" placeholder="请输入手机号">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					电子邮件：
				</view>
				<view class="control">
					<input :disabled="disabled" type="text" maxlength="35" v-model="email" placeholder="请输入电子邮件">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					身份证号：
				</view>
				<view class="control">
					<input :disabled="disabled" type="text" maxlength="18" v-model="idcard" placeholder="请输入身份证号">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					省/市/区：
				</view>
				<picker v-if="!disabled" mode="region" @change="confirmAddress">
					<view class="control area-id">
						<input :disabled="true" type="text" v-model="area_id" placeholder="请选择省/市/区">
						<uni-icons type="bottom"></uni-icons>
					</view>
				</picker>
				<input v-else :disabled="disabled" type="text" v-model="area_id" placeholder="请选择省/市/区">
			</view>
			<view class="form-item">
				<view class="label must">
					收货地址：
				</view>
				<view class="control area-id">
					<input :disabled="disabled" type="text" maxlength="50" v-model="addreddInfo" placeholder="请输入收货地址">
				</view>
			</view>
			<view class="wx-address" @click="getAddressForWx" v-if="!disabled">
				使用微信收货地址
			</view>
		</view>

		<view class="main-btn" @click="confirmCert" v-if="!disabled">
			确&nbsp;定
		</view>
		<view class="main-btn" @click="clearAuthInfo" v-else>
			清&nbsp;空
		</view>
	</view>
</template>

<script>
	import {
		personAuthApi,
		getPersonAuthInfoApi,
		clearAuthInfoApi
	} from '@/api/index.js'
	import {
		verifyField
	} from '@/utils/index'
	export default {
		data() {
			return {
				// 是否禁用，如果只是展示就禁用
				disabled: false,
				company_name: '',
				trueName: '',
				mobile: '',
				email: '',
				idcard: '',
				area_id: '',
				addreddInfo: '',
			};
		},
		onLoad({
			get_data = ''
		}) {
			if (get_data) {
				this.getAuthInfo()
				this.disabled = true
			}
		},
		methods: {
			// 清空认证信息
			clearAuthInfo() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否确定清空账号信息？',
					success({
						confirm
					}) {
						if (confirm) {
							clearAuthInfoApi().then(({
								res,
								resMsg
							}) => {
								if (res) {
									resMsg = '清空成功'
								}
								that.$toast(res.resMsg)
								const userInfo = uni.getStorageSync('userInfo');
								userInfo['userType'] = 1
								uni.setStorageSync('userInfo', userInfo)
								uni.removeStorageSync('is_identify')
								setTimeout(() => {
									uni.navigateBack()
								}, 1200)
							})
						}
					}
				})
			},


			// 获取个人认证信息
			getAuthInfo() {
				getPersonAuthInfoApi().then(({
					res,
					obj,
					resMsg
				}) => {
					if (res) {
						const {
							address,
							area_id,
							company_name,
							email,
							idcard,
							mobile,
							trueName
						} = obj
						this.company_name = company_name
						this.trueName = trueName
						this.mobile = mobile
						this.email = email
						this.idcard = idcard
						this.area_id = area_id
						this.addreddInfo = address
					} else {
						this.$toast(resMsg)
					}
				})
			},


			// 从微信获取收货地址
			getAddressForWx() {
				const that = this
				uni.chooseAddress({
					success({
						provinceName,
						cityName,
						countyName,
						detailInfo
					}) {
						that.addreddInfo = provinceName + cityName + countyName + detailInfo
					},
					fail() {
						that.$toast('获取失败，请重试！')
					}
				})
			},

			// 确定省市区
			confirmAddress(val) {
				const {
					detail: {
						value
					}
				} = val
				this.area_id = `${value[0]}/${value[1]}/${value[2]}`
			},

			// 确定认证
			confirmCert() {
				if (!this.trueName) return this.$toast('请输入姓名')
				if (!this.mobile) return this.$toast('请输入手机号')
				if (!verifyField('phoneNumber', this.mobile)) return this.$toast('手机号格式不正确')
				if (!this.email) return this.$toast('请输入邮箱')
				if (!verifyField('email', this.email)) return this.$toast('邮箱格式不正确')
				if (this.idcard) {
					if (!verifyField('idCard', this.idcard)) return this.$toast('身份证格式不正确')
				}
				if (!this.addreddInfo) return this.$toast('请输入收货地址')

				personAuthApi({
					company_name: this.company_name,
					trueName: this.trueName,
					mobile: this.mobile,
					email: this.email,
					idcard: this.idcard,
					area_id: this.area_id,
					addreddInfo: this.addreddInfo,
				}).then(res => {
					if (res.res) {
						const userInfo = uni.getStorageSync('userInfo')
						userInfo['userType'] = 1
						uni.setStorageSync('userInfo', userInfo)
						uni.setStorageSync('is_identify', 1)
						uni.redirectTo({
							url: '/staffB/success/success?title=信息完善成功'
						})
					} else {
						this.$toast(res.resMsg)
					}
				})

			}
		}
	}
</script>

<style lang="scss" scoped>
	@import "@/layout/form-item.scss";

	input {
		color: #8A8A8A;
	}

	.wx-address {
		text-align: right;
		margin-top: 20rpx;
		color: $primary;
	}

	.area-id {
		position: relative;
	}

	uni-icons {
		position: absolute;
		right: 0;
		top: 50%;
		transform: translateY(-50%)
	}


	.main-btn {
		margin-bottom: 50rpx;
	}

	.container {
		padding: 0 30rpx;
	}
</style>