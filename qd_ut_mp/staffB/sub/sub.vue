<template>
	<view class="container">
		<view class="form">
			<view class="form-item">
				<view class="label must">
					姓名：(请务必与寄件人一致)
				</view>
				<view class="control">
					<input type="text" maxlength="30" v-model="name" placeholder="请输入姓名">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					手机号：(请务必与寄件手机号一致)
				</view>
				<view class="control">
					<input type="number" maxlength="11" v-model="mobile" placeholder="请输入手机号">
				</view>
			</view>
<!-- 			<view class="form-item">
				<view class="label">
					公司名称：
				</view>
				<view class="control">
					<input type="text" maxlength="35" v-model="company_name" placeholder="请输入公司名称">
				</view>
			</view> -->
			<view class="form-item">
				<view class="label must">
					样品回收：（ps：样品寄回默认到付）
				</view>
				<view class="control">
					<switch color="#E96302" @change="swichChange"
						style="transform:scale(0.6);margin-left: -25rpx;" />
				</view>
			</view>

			<template v-if="recycle">
				<view class="form-item">
					<view class="label must">
						收件人名称：
					</view>
					<view class="control">
						<input maxlength="30" v-model="addresseeName" placeholder="请输入收件人名称">
					</view>
				</view>
				<view class="form-item">
					<view class="label must">
						收件人联系方式：
					</view>
					<view class="control">
						<input maxlength="11" v-model="addresseeMobile" placeholder="请输入收件人联系方式">
					</view>
				</view>
				<view class="form-item">
					<view class="label must">
						回收地址：
					</view>
					<view class="control">
						<input maxlength="30" v-model="address" placeholder="请输入回收地址">
					</view>
				</view>
			</template>

			<view class="form-item">
				<view class="label must">
					云视频：（ps：根据实际测试时长结算）
				</view>
				<view class="control">
					<switch color="#E96302" @change="cloud_video = !cloud_video"
						style="transform:scale(0.6);margin-left: -25rpx;" />
				</view>
			</view>

			<view class="form-item">
				<view class="label must">
					线下到场：（ps：提前2个工作日预约时间）
				</view>
				<view class="control">
					<switch color="#E96302" @change="is_arrive = !is_arrive"
									style="transform:scale(0.6);margin-left: -25rpx;" />
				</view>
			</view>

			<view class="form-item">
				<view class="label must">
					我要上机：（ps：到场后全程在工程师指导下进行）
				</view>
				<view class="control">
					<switch color="#E96302" @change="is_on = !is_on"
									style="transform:scale(0.6);margin-left: -25rpx;" />
				</view>
			</view>

			<view class="form-item">
				<view class="label">
					上传资料
				</view>
				<view class="control">
					<view class="data-list">
						<view class="data-item" v-for="item in dataList" :key="item.id">
							<text>{{ item.info }}</text>
							<image @click="deleteData(item.id)" src="@/static/delete.png" mode=""></image>
						</view>
					</view>
					<view class="upload-btn" v-if="dataList.length < 5" @click="uploadSubData">上传</view>
				</view>
			</view>

			<view class="form-item">
				<view class="label">
					实验需求：
				</view>
				<view class="tipText">
					1.如有指定所需的放大倍数/标尺，请填写）
				</view>
				<view class="tipText">
					2.默认拍摄图片数量6一10张，如需增加或减少张数请填写，基于默认收费标准按张数对应增收或优惠）
				</view>
				<view class="tipText">
					3.如有测试重点关注事项，请填写或点击上传资料）
				</view>
				<view class="tipText">
					4.云视频/线下到场请按需填写您想要的时间，客服会提前2个工作日与您具体确认。关注“愉免检测“公众号会提前24小时和15分钟分别发送通知，若逾期10分钟未上线/到场则视为放弃）
				</view>
				<view class="tipText">
					5.根据不同测试项目，请按个人实际需求填写）
				</view>
				<view class="control">
					<textarea v-model="consult_text" placeholder="请输入实验需求" maxlength="300" />
				</view>
			</view>
		</view>
		<view class="main-btn" @click="nextStep" v-if="isYuYue === true">
			下一步
		</view>
		<view class="main-btn" @click="confirmSubmit" v-else>
			确&nbsp;定
		</view>
	</view>
</template>

<script>
	import {
		verifyField
	} from '@/utils/index'
	import {
		subTestApi,
		getPersonAuthInfoApi,
		uploadFileApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
				id: '',
				name: '',
				mobile: '',
				company_name: '',
				consult_text: '',
				recycle: false,
				address: '',
				addresseeName: '',
				addresseeMobile: '',
				cloud_video: false,
				is_arrive: false,
				is_on: false,
				dataList: [],
				isYuYue:false,
				data:{},
				special_type:null
			};
		},
		onLoad({
			id
		}) {
			let data = id.split("|")[0]
			if (data) {
				this.id = data
				this.mobile = uni.getStorageSync('userInfo')['mobile']
				getPersonAuthInfoApi().then(res => {
					if (res.res) {
						const {
							mobile,
							trueName,
							userType,
							company_name
						} = res.obj
						this.addresseeMobile = mobile
						this.addresseeName = trueName

						if (userType === 2) {
							this.addresseeName = company_name
						}
					}
				})
			}
			let boo = id.split("|")[1]
			this.special_type = boo
			if(Boolean(boo == 1) == true){
				this.isYuYue = true
			}else{
				this.isYuYue = false
			}
		},
		methods: {
			swichChange(data) {
				this.recycle = data.detail.value
				if (!data.detail.value) {
					this.address = ''
					this.addresseeName = ''
					this.addresseeMobile = ''
				}
			},

			// 删除上传的资料
			deleteData(id) {
				const idx = this.dataList.findIndex(item => item.id === id)
				this.dataList.splice(idx, 1)
			},

			// 上传预约资料
			uploadSubData() {
				// 限制一下大小10M
				// 10000000
				const that = this
				uni.chooseImage({
					count: 1,
					sizeType: ['compressed'],
					success(res) {
						const filePath = res.tempFilePaths[0]
						uni.showLoading({
							title: '上传中...',
							mask: true,
							iocn: 'none'
						})
						uploadFileApi({
							filePath,
							reqUrl: '/experimentOrder/uploadChildData.ajax',
							name: 'orderdata',
							formData: {
								type: '7'
							}
						}).then(res => {
							if (res.res) {
								const { id, info ,name, path } = res.obj
								that.dataList.push({
									id,
									info,
									path: path + '/' + name
								})
							} else {
								that.$toast('上传失败')
							}
						}).finally(_ => {
							uni.hideLoading()
						})
					}
				})


			},

			// 确定提交
			confirmSubmit() {
				const reg = /^1[3-9]\d{9}$/
				if (!this.id) return this.$toast('缺少实验ID')
				if (!this.name) return this.$toast('请输入姓名')
				if (!this.mobile) return this.$toast('请输入手机号')
				if (!verifyField('phoneNumber', this.mobile)) return this.$toast('手机号格式不正确')
				if (this.recycle) {
					if (!this.address) return this.$toast('回收地址不能为空')
					if (!this.addresseeName) return this.$toast('收件人名称不能为空')
					if (!this.addresseeMobile) return this.$toast('收件人联系方式不能为空')
					if (!verifyField('phoneNumber', this.addresseeMobile)) return this.$toast('收件人联系方式格式错误')
				}
				let obj = {
					sampleInformationList: null,
				};
				let str = JSON.stringify(obj);
				let codeStr = encodeURIComponent(str);
				subTestApi({
					sampleInformationList: codeStr,
					userName: this.name,
					mobile: this.mobile,
					company_name: this.company_name,
					content: this.consult_text,
					class_id: this.id,
					recycle: this.recycle,
					address: this.address,
					addresseeName: this.addresseeName,
					addresseeMobile: this.addresseeMobile,
					is_video: this.cloud_video,
					is_arrive: this.is_arrive,
					is_on: this.is_on,
					order_list: this.dataList.map(item => item.id).join()
				}).then(({
					res,
					resMsg
				}) => {
					// resMsg = '预约成功，稍后会有专属业务员会向您致电，敬请接听！'
					this.$toast(resMsg)
					if (res) {
						setTimeout(() => {
							uni.navigateBack()
						}, 1200)
					}
				})
			},
			nextStep(){
				const reg = /^1[3-9]\d{9}$/
				if (!this.id) return this.$toast('缺少实验ID')
				if (!this.name) return this.$toast('请输入姓名')
				if (!this.mobile) return this.$toast('请输入手机号')
				if (!verifyField('phoneNumber', this.mobile)) return this.$toast('手机号格式不正确')
				if (this.recycle) {
					if (!this.address) return this.$toast('回收地址不能为空')
					if (!this.addresseeName) return this.$toast('收件人名称不能为空')
					if (!this.addresseeMobile) return this.$toast('收件人联系方式不能为空')
					if (!verifyField('phoneNumber', this.addresseeMobile)) return this.$toast('收件人联系方式格式错误')
				}
				this.data = {
					userName: this.name,
					mobile: this.mobile,
					company_name: this.company_name,
					content: this.consult_text,
					class_id: this.id,
					recycle: this.recycle,
					address: this.address,
					addresseeName: this.addresseeName,
					addresseeMobile: this.addresseeMobile,
					is_video: this.cloud_video,
					is_arrive: this.is_arrive,
					is_on: this.is_on,
					order_list: this.dataList.map(item => item.id).join()
				}
				uni.navigateTo({
					url: '/staffB/sampleInfo/sampleInfo?data=' + JSON.stringify(this.data) + '&special_type='+this.special_type
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
	@import "@/layout/form-item.scss";


	.data-item {
		display: flex;
		align-items: center;
		margin-top: 15rpx;

		text {
			display: block;
			width: 400rpx;
			text-overflow: ellipsis;
			overflow: hidden;
			color: $primary;
		}

		image {
			width: 30rpx;
			height: 30rpx;
			margin-left: 20rpx;
		}
	}


	.upload-btn {
		color: $primary;
		margin-top: 15rpx;
	}

	textarea {
		width: 100%;
		height: 300rpx;
		border: 1rpx solid #F0F0F0;
		border-radius: 10rpx;
		margin-top: 10rpx;
		box-sizing: border-box;
		padding: 10rpx;
	}


	.container {
		padding: 0 30rpx 50rpx;
	}

	.tipText {
		margin-bottom: 10rpx;
		line-height: 32rpx;
		font-size: 24rpx;
		color: #999999;
	}
</style>
