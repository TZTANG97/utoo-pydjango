<template>
	<view class="container">
		<view class="form">
			<view class="form-item">
				<view class="label must">
					企业名称：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" type="text" :disabled="disabled" maxlength="30"
						v-model="name" placeholder="请输入企业名称">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					注册地址国家：
				</view>
				<view class="control">
					<input class="disable" type="text" v-model="country" placeholder="请输入注册国家" :disabled="true">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					省/市/区：
				</view>
				<picker mode="region" @change="confirmAddress" v-if="!disabled">
					<view class="control areaId">
						<input :disabled="true" type="text" v-model="areaId" placeholder="请选择省/市/区">
						<uni-icons v-if="!disabled" type="bottom"></uni-icons>
					</view>
				</picker>
				<input v-else :class="disabled? 'disable': ''" :disabled="true" type="text" v-model="areaId"
					placeholder="请选择省/市/区">
			</view>

			<view class="form-item">
				<view class="label must">
					详细地址：
				</view>
				<view class="control detail-address">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="text" maxlength="50"
						v-model="address" placeholder="请输入详细地址">
					<image v-if="!disabled" @click="getLocationByMap" src="@/static/map.png" mode=""></image>
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					电话：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="number" maxlength="11"
						v-model="contractPhone" placeholder="请输入企业联系电话">
				</view>
			</view>
			<!-- 			<view class="form-item">
				<view class="label">
					开票付款信息：
				</view>
				<view class="control">
					{{ payInfo }}
				</view>
			</view> -->
			<view class="form-item">
				<view class="label must">
					纳税人识别号：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="text" maxlength="20"
						v-model="taxNum" placeholder="请输入纳税人识别号">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					企业开户银行：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="text" maxlength="50"
						v-model="bank" placeholder="请输入企业开户银行名称">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					企业银行账号：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="number" maxlength="19"
						v-model="bankCardNum" placeholder="请输入企业银行账号">
				</view>
			</view>
		</view>

		<view class="main-btn" @click="confirmCert" v-if="!disabled">
			确&nbsp;定
		</view>
		<view class="main-btn" v-else @click="clearAuthInfo">
			清&nbsp;空
		</view>
	</view>
</template>

<script>
	import {
		verifyField
	} from '@/utils/index'
	import {
		companyAuthApi,
		getPersonAuthInfoApi,
		clearAuthInfoApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
				name: '',
				country: '中国',
				areaId: '',
				address: '',
				contractPhone: '',
				// payInfo: '',
				taxNum: '',
				bank: '',
				bankCardNum: '',
				disabled: false,
				location: JSON.stringify({
					latitude: 40.042398,
					longitude: 116.378986,
				})
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
		onShow() {
			const chooseLocation = requirePlugin('chooseLocation');
			const location = chooseLocation.getLocation();
			if (location) {
				const {
					latitude,
					longitude,
					name
				} = location
				this.address = name
				this.location = JSON.stringify({
					latitude,
					longitude
				})
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


			// 获取企业认证信息
			getAuthInfo() {
				getPersonAuthInfoApi().then(({
					res,
					obj,
					resMsg
				}) => {
					if (res) {
						const {
							address,
							areaId,
							bank,
							bankCardNum,
							company_name,
							country,
							mobile,
							taxNum,
						} = obj
						this.name = company_name
						this.country = country
						this.areaId = areaId
						this.address = address
						this.contractPhone = mobile
						this.taxNum = taxNum
						this.bank = bank
						this.bankCardNum = bankCardNum
					} else {
						this.$toast(resMsg)
					}
				})
			},


			// 从地图选择详细的公司位置
			getLocationByMap() {
				wx.navigateTo({
					url: `plugin://chooseLocation/index?key=ALJBZ-K5F3Z-KQHX2-TOV43-QQEJK-Y4FWP&referer=优兔测试&location=${this.location}&category=公司`
				});
			},

			// 确定省市区
			confirmAddress(val) {
				const {
					detail: {
						value
					}
				} = val
				this.areaId = `${value[0]}/${value[1]}/${value[2]}`
			},

			// 确定认证
			confirmCert() {
				if (!this.name) return this.$toast('请输入企业名称')
				// if (!this.country) return this.$toast('请选择注册地址国家')
				if (!this.areaId) return this.$toast('请选择省市区')
				if (!this.address) return this.$toast('请输入详细地址')
				if (!this.contractPhone) return this.$toast('请输入企业联系电话')
				if (!verifyField('phoneNumber', this.contractPhone)) return this.$toast('企业联系电话格式不正确')
				// if (!this.payInfo) return this.$toast('请输入开票付款信息')
				if (!this.taxNum) return this.$toast('请输入纳税人识别号')
				if (!verifyField('taxpayerRegNmuber', this.taxNum)) return this.$toast('纳税人识别号格式不正确')
				if (!this.bank) return this.$toast('请输入企业开户行名称')
				if (!this.bankCardNum) return this.$toast('请输入企业银行账号')
				if (!verifyField('bank', this.bankCardNum)) return this.$toast('银行卡号格式不正确')
				companyAuthApi({
					name: this.name,
					country: '中国',
					areaId: this.areaId,
					address: this.address,
					contractPhone: this.contractPhone,
					taxNum: this.taxNum,
					bank: this.bank,
					bankCardNum: this.bankCardNum,
				}).then(res => {
					if (res.res) {
						const userInfo = uni.getStorageSync('userInfo')
						userInfo['userType'] = 2
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

	.detail-address {
		position: relative;

		image {
			position: absolute;
			right: 0;
			top: 50%;
			margin-top: -20rpx;
			width: 40rpx;
			height: 40rpx;
			z-index: 2;
		}
	}

	.areaId {
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