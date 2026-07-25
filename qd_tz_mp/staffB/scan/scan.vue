<template>
	<view class="container">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					<span style="color: #f00;">*</span>
					<span>样品ID</span>
				</view>
				<view class="group-content">
					<span v-if="sample_id">{{ sample_id.split('_')[1] }}</span>
					<!-- <image v-if="!id" @click="scan(1)" src="@/static/f-scan.png" mode=""></image> -->
					<image @click="scan(1)" src="@/static/f-scan.png" mode=""></image>
				</view>
			</view>

			<view class="group-item" v-if="type == 1 || type == 5"
				@click="chooseLocation? chooseLocation = false : chooseLocation = true">
				<view class="group-label">
					选择存放位置
				</view>
				<view class="group-content">
					{{ chooseLocation? '是' : '否' }}
				</view>
			</view>

			<view class="group-item" v-if="type == 3">
				<view class="group-label">
					<span>实验平台</span>
				</view>
				<view class="group-content">
					<span v-if="line_id">{{ line_name }}</span>
					<!-- <image v-if="!id" @click="scan(3)" src="@/static/f-scan.png" mode=""></image> -->
					<image @click="scan(3)" src="@/static/f-scan.png" mode=""></image>
				</view>
			</view>


			<template v-if="(type == 1 || type == 5)? chooseLocation : type != 3 && type != 4 && type != 8">
				<view class="group-item">
					<view class="group-label">
						仓库名称
					</view>
					<view class="group-content">
						<input type="text" :disabled="true" v-model="store_name">
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						库存位置
					</view>
					<view class="group-content">
						<input type="text" :disabled="true" v-model="store">
						<image @click="scan(2)" src="@/static/f-scan.png" mode=""></image>
					</view>
				</view>
			</template>

			<template v-if="type == 2">
<!--				<view class="group-item">-->
<!--					<view class="group-label">-->
<!--						<span style="color: #f00;">*</span>-->
<!--						<span>预计完成时间</span>-->
<!--					</view>-->
<!--					<view class="group-content">-->
<!--						<input type="number" placeholder="请输入预计完成时间" v-model="finish_time">-->
<!--					</view>-->
<!--				</view>-->
<!--				<view class="group-item">-->
<!--					<view class="group-label">-->
<!--						<span style="color: #f00;">*</span>-->
<!--						<span>时间类型</span>-->
<!--					</view>-->
<!--					<view class="group-content" @click="time_type == 1? time_type = 2 : time_type = 1">-->
<!--						<view class="text-content">-->
<!--							{{ time_type === 1? '小时' : '天' }}-->
<!--						</view>-->
<!--					</view>-->
<!--				</view>-->
			</template>
			<template v-if="type == 6">
				<view class="group-item">
					<view class="group-label">
						<span style="color: #f00;">*</span>
						<span>快递单号</span>
					</view>
					<view class="group-content">
						<input type="text" placeholder="请输入快递单号" v-model="express_no">
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						<span style="color: #f00;">*</span>
						<span>快递公司</span>
					</view>
					<view class="group-content">
						<input type="text" placeholder="请输入快递公司" v-model="express_name" />
					</view>
				</view>
			</template>
			<template v-if="type == 7">
				<template v-if="handle === 1">
					<view class="group-item" @click="lcNewLocation? lcNewLocation = false : lcNewLocation = true">
						<view class="group-label">
							是否选择位置信息
						</view>
						<view class="group-content">
							{{ lcNewLocation? '是' : '否' }}
						</view>
					</view>
					<template v-if="lcNewLocation">
						<view class="group-item">
							<view class="group-label">
								<span style="color: #f00;">*</span>
								<span>新仓库名称</span>
							</view>
							<view class="group-content">
								<input type="text" :disabled="true" v-model="new_store_name">
							</view>
						</view>
						<view class="group-item">
							<view class="group-label">
								<span style="color: #f00;">*</span>
								<span>新库存位置</span>
							</view>
							<view class="group-content">
								<input type="text" :disabled="true" v-model="new_store">
								<image @click="scan(4)" src="@/static/f-scan.png" mode=""></image>
							</view>
						</view>
					</template>
				</template>
				<view class="group-item">
					<view class="group-label">
						操作
					</view>
					<view class="group-content" @click="handle === 1? handle = 2 : handle = 1 ">
						<div class="text-content">
							{{ handle === 1? '样品留存' : '样品报废' }}
						</div>
						<image src="@/static/switch.png" mode=""></image>
					</view>
				</view>
			</template>

			<template v-if="type == 8">
				<view class="group-item">
					<view class="group-label">
						<span>上传图片</span>
					</view>
					<view class="group-content">
						<img v-if="subUrl" style="width: 50px; height: 50px; margin-right: 10px" :src="subUrl" />
						<view @click="uploadImage">上传</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						<span>描述</span>
					</view>
					<view class="group-content">
						<input type="text" placeholder="请输入用户确认描述" v-model="submitMark" />
					</view>
				</view>
			</template>

			<view class="group-item" v-if="type == 2">
				<view class="group-label">
					<span>预约云视频时间</span>
				</view>
				<view class="group-content">
					<uni-datetime-picker v-model="setting_time" type="datetime" />
				</view>
			</view>
			<view class="group-item" v-if="type == 2">
				<view class="group-label">
					<span>腾讯视频会议号</span>
				</view>
				<view class="group-content">
					<input type="text" placeholder="请输入会议号" v-model="meeting_num">
				</view>
			</view>
		</view>
		<view class="main-btn" @click="submit">
			提&nbsp;交
		</view>
	</view>
</template>

<script>
	import {
		scanOperateApi,
		confirmsave,
		isFlag
	} from '@/api/index.js'
	export default {
		data() {
			return {
				id: '',
				type: '',
				sample_id: '',
				store: '',
				finish_time: '',
				line_id: '',
				line_name: '',
				new_store: '',
				new_store_name: '',
				new_store_id: '',
				express_no: '',
				express_name: '',
				time_type: 1,
				store_name: '',
				store_id: '',
				handle: 1,
				chooseLocation: false,
				lcNewLocation: false,
				showCalendar:false,
				setting_time:null,
				meeting_num:null,
				submitMark: '',
				subUrl: '',
				subId: ''
			}
		},
		onLoad({
			type,
			id = '',
			line_id = '',
			line_name = ''
		}) {
			this.type = type - 0

			// 如果有id，说明是从订单跳转过来的
			if (id) {
				// 没什么意意义，就是单传的判断一下
				this.id = id
				// this.sample_id = 'childId_' + id

				if(this.type === 3) {
					this.line_id = line_id
					this.line_name = line_name
				}
			}
		},
		methods: {
			uploadImage() {
				if(!this.sample_id) {
					if (!this.sample_id) return this.$toast('请扫描样品二维码')
					return
				}
				let _this = this;
				const token = uni.getStorageSync('token')
				uni.chooseImage({
					count: 1,
					sourceType: ['album', 'camera'],
					success: (chooseRes) => {
						console.log(chooseRes)
						const tempFilePath = chooseRes.tempFilePaths
						let num = 0;
						uni.showLoading()
						tempFilePath.forEach((item, index) => {
							// 上传图片（自动使用 multipart/form-data 格式）
							let uploadFile = uni.uploadFile({
								url: `${_this.$baseUrl}/experimentChildOrder/uploadPhone.ajax`, //仅为示例，非真实的接口地址
								filePath: item, // 本地临时文件路径
								name: 'photo', // 后端接收文件的参数名（需与后端一致）
								success: (uploadRes) => {
									uni.hideLoading()
									let res = JSON.parse(uploadRes.data);
									console.log(res)
									if(res.res) {
										_this.subUrl = res.obj.url
										_this.subId = res.obj.id;
									} else {
										uni.showToast({
											title: '图片上传失败，请重试',
											icon: 'none'
										})
									}
								},
								header: {
									token,
									uniapp: 'true'
								},
								fail: (err) => {
									uni.hideLoading()
									console.error('上传失败', err);
								}
							});
							console.log(uploadFile)
						})
					}
				});

			},


			scan(val) {
				const that = this
				uni.scanCode({
					success(res) {
						console.log(res);
						if (res.errMsg) {
							switch (val) {
								case 1:
									that.sample_id = res.result;
									// 当type=8时，调用isFlag接口验证
									if (that.type === 8) {
										isFlag({ childId: res.result.split('_')[1] }).then(res => {
											if (!res.res) {
												// 验证失败，提示信息并清空sample_id
												that.$toast(res.resMsg)
												that.sample_id = ''
											}
										})
									}
									break;
								case 2:
									let [store_id, store_name, store] = res.result.split(';')
									that.store_id = store_id
									that.store_name = store_name
									that.store = store
									break;
								case 3:
									let [line_id, line_name] = res.result.split(';')
									that.line_id = line_id
									that.line_name = line_name
									break;
								default:
									let [new_store_id, new_store_name, new_store] = res.result.split(';')
									that.new_store_id = new_store_id
									that.new_store_name = new_store_name
									that.new_store = new_store
							}
						} else {
							that.$toast('二维码无效，请重试！')
						}
					},
					fail(err) {
						if (err.errMsg !== 'scanCode:fail cancel') {
							that.$toast('二维码无效，请重试！')
						}
					},
				})
			},

			removeBOM(str) {
				// UTF-8 BOM is represented by the Unicode character \uFEFF
				if (str.charCodeAt(0) === 0xFEFF) {
					return str.slice(1);
				}
				return str;
			},

			submit() {
				console.log(this.setting_time,'.setting_time')
				console.log(this.meeting_num,'.meeting_num')
				let params = {
					type: this.type,
					childId: this.sample_id,
				}

				if(this.setting_time)params.setting_time = this.setting_time
				if(this.meeting_num)params.meeting_num = this.meeting_num

				console.log(params,'params')
				if (!this.sample_id) return this.$toast('请扫描样品二维码')
				if (this.chooseLocation && (this.type == 1 || this.type == 5)) {
					if (!this.store_id) return this.$toast('请扫码库存位置二维码')
					params['storePosId'] = this.removeBOM(this.store_id)
					params['isPosition'] = 1
				} else {
					params['storePosId'] = this.store_id ? this.removeBOM(this.store_id) : ''
					params['isPosition'] = 0
				}


				if (this.type == 2) {
					params['finish_time'] = 0;
					params['time_type'] = 3;
				}

				if (this.type == 3) {
					// if (!this.line_id) return this.$toast('请扫描实验平台二维码')
					params['lineId'] = this.removeBOM(this.line_id)
				}

				if (this.type == 6) {
					if (!this.express_no) return this.$toast('请输入快递单号')
					if (!this.express_name) return this.$toast('请输入快递公司名称')
					params['expressNo'] = this.express_no
					params['expressName'] = this.express_name
				}

				if (this.type == 7) {
					if (this.handle === 1 && this.lcNewLocation) {
						params['isPosition'] = 1
						if (!this.new_store_id) return this.$toast('请扫码新的库存位置二维码')
						params['newStorePosId'] = this.removeBOM(this.new_store_id)
					}
					params['key'] = this.handle
				}
				if(this.type == 8) {
					if(!this.subUrl) {
						uni.showToast({
							title: '请先上传图片',
							icon: 'none'
						})
						return
					}
					let params1 = {
						childId: this.sample_id.split('_')[1],
						mark: this.submitMark,
						ids: this.subId
					}
					confirmsave(params1).then(res => {
						if (res.res) {
							uni.redirectTo({
								url: `/staffB/result/result?title=操作成功`
							})
						} else {
							this.$toast(res.resMsg)
						}
					})
				} else {
					scanOperateApi(params).then(res => {
						if (res.res) {

							// 如果存在id，则证明是从订单页面过来的。
							if (this.id) {
								uni.$_emit('refersh')
							}

							uni.redirectTo({
								url: `/staffB/result/result?title=操作成功`
							})
						} else {
							this.$toast(res.resMsg)
						}
					})
				}

			},
			// 打开日历选择器
			chooseDate() {
				this.showCalendar = true
			},
		}
	}
</script>

<style scoped lang="scss">
	@import '@/layout/group.scss';

	.main-btn {
		margin-top: 20rpx;
	}

	.group-content {
		image {
			width: 55rpx;
			height: 55rpx;
			vertical-align: middle;
			margin-left: 15rpx;
		}
	}

	input {
		text-align: right;
	}

	.container {
		padding: 0 20rpx;
	}
	/deep/ .uni-datetime-picker--btn{
		background-color: #3C8BDB;
	}
	/deep/ .uni-calendar-item__weeks-box .uni-calendar-item--checked {
		background-color: #3C8BDB;
	}
</style>
