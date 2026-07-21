<template>
	<view class="container">
		<view class="row flex-between" @click="modifyHead">
			<view class="label">
				头像
			</view>
			<view class="content flex-between">
				<image v-if="userInfo && userInfo['photo']" :src="userInfo['photo']" mode="" />
				<image v-else src="@/static/head.png" mode="" />
				<uni-icons type="forward" class="right"></uni-icons>
			</view>
		</view>
		<view class="row flex-between">
			<view class="label">
				手机号
			</view>
			<view class="content flex-between">
				<text
					class="hidden">{{ userInfo? userInfo['mobile'].replace(/(\d{3})\d{5}(\d{3})/, '$1****$2') : '' }}</text>
			</view>
		</view>
		<view class="row flex-between" @click="updateNickName">
			<view class="label">
				昵称
			</view>
			<view class="content flex-between">
				<text class="hidden">{{ userInfo['wx_nickname'] }}</text>
				<uni-icons type="forward" class="right"></uni-icons>
			</view>
		</view>
		<navigator url="../forget_password/forget_password" hover-class="none" class="row flex-between">
			<view class="label">
				修改密码
			</view>
			<view class="content">
				<uni-icons type="forward" class="right"></uni-icons>
			</view>
		</navigator>
		<view class="row flex-between" @click="viewAuthInfo" v-if="userInfo && !userInfo['uType']">
			<view class="label">
				账号信息
			</view>
			<view class="content">
				<uni-icons type="forward" class="right"></uni-icons>
			</view>
		</view>
		<view class="row flex-between" v-if="userInfo.uType == 0" @click="viewInvoiceInfo">
			<view class="label">
				发票信息
			</view>
			<view class="content">
				<uni-icons type="forward" class="right"></uni-icons>
			</view>
		</view>
		<!-- <template v-if="userInfo && userInfo['uType']"> -->
		<view class="row flex-between" v-if="userInfo['is_bind_account'] != 1" @click="bindAccount">
			<view class="label" style="flex-grow: 1;">
				账号绑定
			</view>
			<view class="content">
				<uni-icons type="forward" class="right"></uni-icons>
			</view>
		</view>
		<view class="row flex-between" @click="relieveBind" v-else>
			<view class="label">
				解除绑定
			</view>
			<view class="content">
				<uni-icons type="forward" class="right"></uni-icons>
			</view>
		</view>
		<!-- </template> -->


		<uni-popup ref="inputDialog" type="dialog">
			<uni-popup-dialog :before-close="true" ref="inputClose" mode="input" title="修改昵称" placeholder="请输入新的昵称"
				@confirm="dialogInputConfirm" @close="closePopup"></uni-popup-dialog>
		</uni-popup>
	</view>
</template>

<script>
	import {
		checkAuthApi
	} from '@/api/common.js'
	import {
		setNickNameApi
	} from '@/api/my_profile.js'
	import {
		uploadFileApi,
		bindWxAccountApi,
		relieveBindWxAccountApi,
		getbindstatus
	} from '@/api/index.js'
	export default {
		data() {
			return {
				userInfo: null,
			};
		},
		onShow() {
			getbindstatus().then(res=>{
				this.userInfo.is_bind_account = res.obj.is_bind
			})
		},
		onLoad() {
			this.userInfo = uni.getStorageSync('userInfo');
			console.log(this.userInfo,'userInfo')
		},
		methods: {

			// 解绑
			relieveBind() {
				relieveBindWxAccountApi().then(res => {
					if (res.res) {
						this.userInfo['is_bind_account'] = 0
						uni.setStorageSync('userInfo', this.userInfo)
					}
					this.$toast(res.res ? '解绑成功' : res.resMsg)
				})
			},

			// 账号绑定
			async bindAccount() {
				const loginResult = await uni.login()
				if (loginResult.errMsg !== 'login:ok') return this.$toast('绑定失败，请重试！')
				const result = await bindWxAccountApi({
					dlcode: loginResult.code
				})
				const {
					res,
					obj = ''
				} = result
				if (res) {
					this.$toast('绑定成功')
					this.userInfo['is_bind_account'] = 1
					uni.setStorageSync('userInfo', this.userInfo)
				} else {
					this.$toast(result.resMsg ? result.resMsg : '绑定失败')
				}
			},

			// 查看发票信息
			viewInvoiceInfo() {
				uni.navigateTo({
					url: '/pagesB/invoice_list/invoice_list'
				})
			},

			// 判断是否认证
			viewAuthInfo() {
				checkAuthApi().then(({
					res,
					obj,
					resMsg
				}) => {
					if (res) {
						if (!obj['is_identify']) {
							uni.navigateTo({
								url: '/staffB/choose_identity/choose_identity'
							})
						} else {
							const userType = uni.getStorageSync('userInfo')['userType'];
							// 1个人 2企业
							// get_data：获取认证数据展示
							let url = '/staffB/personal_cert/personal_cert?get_data=1'
							if (userType === 2) {
								url = '/staffB/enterprise_cert/enterprise_cert?get_data=1'
							}
							uni.navigateTo({
								url
							})
						}
					} else {
						this.$toast(resMsg)
					}
				})
			},


			// 确定新昵称
			dialogInputConfirm(val) {
				if (val.length > 15) {
					return this.$toast('昵称长度超出限制')
				}
				setNickNameApi(val).then(({
					res,
					resMsg
				}) => {
					if (res) {
						resMsg = '设置成功'
						this.$refs.inputDialog.close()
						this.userInfo['wx_nickname'] = val
						uni.setStorageSync('userInfo', this.userInfo)
					}
					this.$toast(resMsg)
				})
			},

			// 关闭popup
			closePopup() {
				this.$refs.inputDialog.close()
			},

			// 更改昵称
			updateNickName() {
				this.$refs.inputDialog.open()
			},
			// 更改头像
			modifyHead() {
				const that = this
				uni.chooseImage({
					count: 1,
					sizeType: ['compressed'],
					success(res) {
						uni.compressImage({
							src: res.tempFilePaths[0],
							quality: 70,
							success(res) {
								uploadFileApi({
									filePath: res.tempFilePath,
									reqUrl: '/wx/updatePhone.ajax',
									name: 'photo'
								}).then(res => {
									if (res.res) {
										that.userInfo['photo'] = res.obj['url']
										uni.setStorageSync('userInfo', that.userInfo)
									} else {
										that.$toast('上传失败')
									}
								}).finally(_ => {
									uni.hideLoading()
								})
							}
						})
					}
				});
			}
		}
	}
</script>

<style lang="scss" scoped>
	@import "@/layout/row.scss";

	.auth-btn {
		background-color: transparent !important;
		border: none !important;
		font-size: 28rpx;
		color: #6C6C6C;
		padding: 0 !important;
		text-align: left;

		&::after {
			border: none !important;
		}
	}

	/deep/.uni-icons {
		font-size: 40rpx !important;
	}
</style>