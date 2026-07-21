<template>
	<view class="container">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					流水编号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.czNum }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					<text>{{accType == 11 ? '转账账户' : '交易账户'}}</text>
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ userObj.userName }}

					</view>
				</view>
			</view>
			<view class="group-item" v-if="accType == 11">
				<view class="group-label">
					<text>转入账户</text>
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ inuser.userName }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					账户类型
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ account.accountType == 1 ? '人民币账户' : '美元账户' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					交易金额
				</view>
				<view class="group-content">
					<view class="text-content">
						{{account.accountType == 1 ? '￥' : '$'}}{{ orderData.logAmount }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="accType == 2">
				<view class="group-label">
					银行名称
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.bankName }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="accType == 2">
				<view class="group-label">
					银行卡号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.cardNum }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					交易时间
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ $alterTime(orderData.addTime) }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					交易备注
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.pdLogInfo ? orderData.pdLogInfo : '无' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					交易状态
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ statusFn(orderData.logStatus) }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="photo">
				<view class="group-label">
					交易凭证
				</view>
				<view class="group-content">
					<view class="text-content">
						<img style="width: 200rpx;height: 200rpx;" :src="photo.path+'/'+photo.name" alt="" />
					</view>
				</view>
			</view>
		</view>
		<view class="syxBtn">
			<button v-if="btnShow" @click="closeFn()">取消申请</button>
			<button v-if="btnShow1" @click="upLoadFn(orderData.id,2)">上传打款凭证</button>
			<button v-if="btnShow3" @click="paymentsOk(orderData.id)">确认收款成功</button>
		</view>

		<view class="detail-box">
			<text>历史操作记录</text>
			<view class="lv-content">
				<u-time-line class="u-time-lines">
					<u-time-line-item nodeTop="10" class="lv-content-item" v-for="(item, index) in logs_list"
						:key="index">
						<template v-slot:node>
							<view class="u-node"></view>
						</template>
						<template v-slot:content>
							<view class="u-order-time">
								<view>
									{{ $alterTime(item.addTime).slice(0, 10) }}
								</view>
								<view>
									{{ $alterTime(item.addTime).slice(10) }}
								</view>
							</view>
							<view>
								<view class="u-order-desc" v-if="item.logUserId">操作人: {{ item.logUserId }}</view>

								<view class="u-order-desc">
									操 作：
									<u-parse :html="item.logInfo"></u-parse>
								</view>
							</view>
						</template>
					</u-time-line-item>
				</u-time-line>
			</view>
			<view class="empty" v-if="!logs_list.length">暂无操作记录</view>
			<view style="height: 1rpx;"></view>
		</view>
		<u-modal v-model="show" :show-cancel-button='true' @confirm="confirm" ref="uModal" :async-close="true"
			:content="type == 1 ? '是否确定取消申请？' : '确定要确认收款成功吗？'"></u-modal>
		<upload-progress ref="prg"></upload-progress>
	</view>
</template>

<script>
	import {
		accountDetailxcx,
		passApi,
		logStatusNew,
		pass1Api
	} from '@/api/staffB.js'
	import uploadProgress from '../uploadProgress'
	import {
		uploadFileApi
	} from '@/api/index.js'
	export default {
		components: {
			uploadProgress
		},
		data() {
			return {
				orderData: {},
				logs_list: [],
				photo: {},
				userObj: {},
				btnShow: false,
				btnShow1: false,
				show: false,
				accountAdd: 0,
				id: null,
				btnShow3: false,
				type: 1,
				account:{}
			}
		},
		onLoad(data) {
			this.id = data.id
			this.accountDetailxcxFn(data.id)
		},
		methods: {
			// 取消操作
			confirm() {
				if (this.type == 1) {
					passApi(this.orderData.id).then(res => {
						if (res.res) {
							this.$toast('取消成功')
							this.btnShow = false
							this.accountDetailxcxFn(this.id)
						} else {
							this.$tip(res.error)
						}
					})
				} else {
					pass1Api(this.orderData.id).then(res => {
						if (res.res) {
							this.$toast('操作成功')
							this.btnShow3 = false
							this.accountDetailxcxFn(this.id)
						} else {
							this.$tip(res.error)
						}
					})
				}

				this.show = false
			},
			closeFn(id) {
				this.type = 1
				this.show = true
			},
			// 上传打款凭证
			upLoadFn(id, type) {
				const that = this
				uni.chooseImage({
					count: 1,
					sizeType: ['compressed'],
					success(res) {
						console.log(res, 'res')
						const filePath = res.tempFilePaths[0]
						uni.showLoading({
							title: '上传中...',
							mask: true,
							iocn: 'none'
						})
						uploadFileApi({
							filePath,
							reqUrl: '/logStatusNew.ajax',
							name: 'order_status',
							formData: {
								id: id
							}
						}).then(data => {
							if (data.res) {
								that.$toast('上传成功')
								// this.photo = res.obj
								that.accountDetailxcxFn(that.id)
								// that.dataList.push({
								// 	id,
								// 	info,
								// 	path: path + '/' + name
								// })
							} else {
								that.$toast('上传失败')
							}
						}).finally(_ => {
							uni.hideLoading()
						})
					}
				})

			},
			// 确认收款成功
			paymentsOk(id) {
				this.type = 2
				this.show = true
			},
			// 按钮判断展示
			dataFn(obj) {
				if (obj.logStatus == 2) {
					if (obj.accType == 1) {
						if (this.accountAdd == 2) {
							this.btnShow = true
						}
					} else if (obj.accType == 2) {
						if (this.accountAdd == 2) {
							this.btnShow = true
						}
					} else if (obj.accType == 12 || obj.accType == 17) {
						if (this.accountAdd == 2) {
							this.btnShow = true
						}
					}
				}
				if (obj.accType == 1) {
					if (obj.logStatus == 3) {
						if (this.accountAdd == 2) {
							this.btnShow = true
						}
					}
					this.btnShow1 = true
				}
				if (obj.accType == 2) {
					if (obj.logStatus == 4) {
						if (this.accountAdd == 2) {
							this.btnShow = true
						}
					}
					this.btnShow1 = true
				}
				if (obj.logStatus == 5) {
					if (obj.accType == 10) {
						this.btnShow3 = false
					} else {
						this.btnShow3 = true
					}
				}
			},
			accountDetailxcxFn(data) {
				accountDetailxcx(data).then(res => {
					console.log(res, 'res')
					if (res.res) {
						this.account = res.obj.account
						this.accountAdd = res.obj.accountAdd
						this.accType = res.obj.accType
						this.logs_list = res.obj.Logs
						this.orderData = res.obj.obj
						this.userObj = res.obj.user
						this.photo = res.obj.photo
						this.dataFn(res.obj.obj)
					}
				})
			},
			// 状态
			statusFn(data) {
				if (data == -1) return '已驳回'
				if (data == -2) return '已取消'
				if (data == 1) return '交易成功'
				if (data == 2) return '待审核'
				if (data == 3) return '待打款'
				if (data == 4) return '待付款'
				if (data == 5) return '待确认'
			},
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/popup.scss';
	@import '@/layout/group.scss';

	.syxBtn {
		display: flex;
		background-color: #f2f2f2;
		padding: 30rpx 0;

		button {
			padding: 10rpx 20rpx;
			margin: 0 16rpx;
			background: #e96302;
			color: #fff;
			font-size: 30rpx;
			height: 60rpx;
			line-height: 44rpx;
			border-radius: 23rpx;
		}
	}

	.u-node {
		width: 15rpx;
		height: 15rpx;
		background-color: $primary;
		box-shadow: 0px 3px 5px 0px rgba(183, 71, 42, .7);
		border-radius: 50%;
	}

	.u-order-desc {
		font-size: 24rpx;
		margin-bottom: 12rpx;
		color: #000000;
		font-size: 24rpx;
		opacity: 0.85;
	}

	.u-order-time {
		color: #000000;
		font-size: 24rpx;
		text-align: center;
		opacity: 0.85;
		position: absolute;
		left: -220rpx;
	}

	.lv-content {
		padding: 30rpx 0 60rpx 180rpx;
		border-radius: 20rpx;
	}

	.lv-content-item {
		position: relative;
	}

	.detail-box {
		background-color: #fff;
		border-radius: 20rpx;
		padding: 0 30rpx;
		margin-top: 20rpx;

		text {
			font-size: 32rpx;
			color: #333333;
			display: block;
			padding: 30rpx 0;
		}
	}
</style>