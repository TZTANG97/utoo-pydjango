<template>
	<view class="container">
		<view class="group" v-if="order_data">
			<view class="group-item">
				<view class="group-label">
					订单编号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ order_data['order_id'] }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单类型
				</view>
				<view class="group-content">
					<view class="text-content">
						<span>{{ order_data['testClass']['name'] }}</span>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					总价
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ order_data['totalPrice'] ? order_data['totalPrice'].toFixed(2) : '0.00' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					下单时间
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ $alterTime(order_data['order_time']) }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					预计收货时间
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ $alterTime(order_data['delivery_time']) }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					是否开票
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ order_data['invoiceType'] ? '是' : '否' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					开票状态
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ (order_data['iskp'] - 0) ? '完成' : '未完成' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单状态
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ order_data['order_statusstr'] }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					付款状态
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ (order_data['isfk'] - 0) ? '付款完成' : '待付款' }}
					</view>
				</view>
			</view>
			<view v-for="(item, idx) in order_data['collectionTimes']" :key="idx">
				<view class="group-item">
					<view class="group-label">
						预计付款时间
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ $alterTime(item['time'], false) }}
						</view>
					</view>
				</view>
				<view class="group-item" v-if="item.bill||item.onlinebill">
					<view class="group-label primary">
						实际付款时间
					</view>
					<view class="group-content">
						<view v-if="item.bill" class="text-content primary">
							{{ $alterTime(item['bill']['billDate'])}}
						</view>
            <view v-if="item.onlinebill" class="text-content primary">
              {{$alterTime(item['onlinebill']['billDate'])}}
            </view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						预计付款金额
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ (item['price'] - 0).toFixed(2) }}
						</view>
					</view>
				</view>
        <view class="group-item realy" v-if="item.onlinebill">
          <view class="group-label primary">
            实际付款金额
          </view>
          <view class="group-content">
            <view class="text-content primary">
              {{ (item['onlinebill']['money'] * 1).toFixed(2) }}
            </view>
          </view>
        </view>
				<view class="group-item realy" v-if="item.bill&&!item.onlinebill">
					<view class="group-label primary">
						实际付款金额
					</view>
					<view class="group-content">
						<view class="text-content primary">
							{{ (item['bill']['money'] * 1).toFixed(2) }}
						</view>
					</view>
				</view>
			</view>
			<template v-if="order_data['hzdpath']">
				<view class="group-item">
					<view class="group-label">
						回执单
					</view>
					<view class="group-content">
						<view class="text-content" @click="preHzd">
							查看
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						回执单状态
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ hzdStatusList[order_data['isUploadReceipt']] }}
						</view>
					</view>
				</view>
				<view class="group-item" v-if="yydUrl">
					<view class="group-label">
						预约单
					</view>
					<view class="group-content">
						<view class="text-content file-name" @click="downloadFile(yyrUrl)">
							{{ order_data['order_id'] }}
						</view>
					</view>
				</view>
			</template>
			<view v-if="yspAndDhList.length">
				<view v-for="(item, index) in yspAndDhList" :key="index">
					<view class="group-item" v-if="item.hyh">
						<view class="group-label">云视频会议号</view>
						<view class="group-content">
							<view class="text-content">{{ item.hyh }}</view>
						</view>
					</view>
					<view class="group-item" v-if="item.jhdh">
						<view class="group-label">样品寄回单号</view>
						<view class="group-content">
							<view class="text-content">
								<text>{{ item.jhdh }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>

			<!-- 			<template v-if="order_data['files']">
				<view class="group-item">
					<view class="group-label">
						订单资料
					</view>
					<view class="group-content">
						<view class="text-content">
							<image class="file-icon" src="../static/file-down.png" mode=""></image>
						</view>
					</view>
				</view>
				<view class="group-item" v-for="(item,idx) in order_data['files']" :key="idx"
					@click="downloadFile(item['path'] + '/' + item['name'])">
					<view class="group-label file-name">
						{{ item['info'] }}
					</view>
				</view>
			</template> -->


		</view>

		<view class="btns" v-if="order_data">
			<view class="btn" v-if="!(order_data['isfk'] - 0) && order_data['isUploadReceipt'] !== 1" @click="pay">
				支付
			</view>
			<navigator
				:url="`/pagesB/confirm_make_invoice/confirm_make_invoice?id=${order_data['id']}&money=${order_data['dkpje']}&type=2`"
				hover-class="none" class="btn" v-if="(order_data['kpShow'] - 0) && order_data['invoiceType'] === 1">
				申请开票
			</navigator>
			<view class="btn" v-if="order_data['printYydShow']" @click.stop="saveFile">
				下载预约单
			</view>
			<navigator class="btn" :url="`/pagesB/child_order_list/child_order_list?ofId=${id}`" hover-class="none">
				产品列表
			</navigator>
			<navigator class="btn" :url="`/pagesB/test_child_order_list/test_child_order_list?ofId=${id}`"
				hover-class="none">
				子订单
			</navigator>

			<navigator v-if="order_data['ispjqx']" class="btn" :url="`/pagesB/evaluate/evaluate?id=${id}`"
				hover-class="none">
				评价
			</navigator>
		</view>
		<u-toast ref="uToast" />
		<time-line v-if="order_data" :type="true" :logs="order_data['logs']"></time-line>
		<pay-way :money="money"  ref="pay_way" @choosePayWayEvent="choosePayWay"></pay-way>
	</view>
</template>

<script>
	import {
		timeLine
	} from '../timeLine.vue'
	import {
		fetchOrderDetailApi,
		fetchPDFUrlApi,
		balanceRepaymentApi,
		fetchOrderPrePayId,
		fetchMyPointsApi
	} from '@/api/index.js'
	import PayWay from '../pay_way.vue'
	export default {
		components: {
			timeLine,
			PayWay
		},
		data() {
			return {
				id: '',
				order_data: null,
				hzdStatusList: ['未上传', '待审核', '审核通过', '审核驳回'],
				yydUrl: '',
				money: 0,
				yspAndDhList:[],
			}
		},
		onLoad({
			id = ''
		}) {
			if (id) {
				this.id = id
			}
			this.getDetail()
			// 监听评价的完成
			uni.$_on('finishEval', id => {
				this.order_data['ispjqx'] = false
			})
		},
		methods: {
			async choosePayWay(flag, integral_num, money) {
				console.log(this.$refs['pay_way'], '66666')
				this.$refs['pay_way']['$refs']['pay_way'].close()
				this.$refs['pay_way'].popupShow = false
				if (flag == 'abc') {
					this.money = 0
					return
				} else if (flag) {
					if (money) {
						balanceRepaymentApi({
							ofId: this.id,
							useIntegral: integral_num,
							pay_way: 2
						}).then(res => {
							this.$tip(res.res ? '支付成功' : res.resMsg)
							if (res.res) {
								this.getDetail()
								this.money = 0
								fetchMyPointsApi().then(res => {
									if (res.res) {
										uni.setStorageSync('totalIntegral', res.obj.totalIntegral);
									}
								})
							}
						})
					} else {
						const result = await wx.login(),
							that = this;
						fetchOrderPrePayId({
							ofId: this.id,
							code: result.code,
							useIntegral: integral_num
						}).then(res => {
							if (res.res) {
								const {
									timeStamp,
									prepayId,
									paySign,
									nonceStr,
								} = res.obj
								wx.requestPayment({
									timeStamp: timeStamp + '',
									nonceStr,
									package: `prepay_id=${prepayId}`,
									signType: 'RSA',
									paySign,
									success(res) {
										that.getDetail()
										that.$tip('支付成功！')
										this.money = 0
										fetchMyPointsApi().then(res => {
											if (res.res) {
												uni.setStorageSync('totalIntegral', res.obj
													.totalIntegral);
											}
										})
									},
									fail(e) {
										that.$tip('支付失败，请重试！')
									}
								})
							} else {
								this.$tip('支付失败，请重试！')
							}
						})
					}

				} else {
					balanceRepaymentApi({
						ofId: this.id,
						useIntegral: integral_num,
						pay_way: 4
					}).then(res => {
						this.$tip(res.res ? '支付成功' : res.resMsg)
						if (res.res) {
							this.getDetail()
							this.money = 0
							fetchMyPointsApi().then(res => {
								if (res.res) {
									uni.setStorageSync('totalIntegral', res.obj.totalIntegral);
								}
							})
						}
					})
				}



			},


			// 下载
			downloadFile(path) {
				const that = this
				uni.setClipboardData({
					data: path,
					success() {
						that.$toast('链接已复制，请打开浏览器下载！');
					}
				});
			},

			// 订单支付
			pay() {
				let xsskje = this.order_data.xsskje ? this.order_data.xsskje : 0
				let totalPrice = this.order_data.totalPrice ? this.order_data.totalPrice : 0
				this.money = (totalPrice * 100 - xsskje * 100) / 100
				// this.$refs['pay_way']['$refs']['pay_way'].open()
				this.$refs['pay_way'].popupShow = true
				return
				const that = this
				uni.showModal({
					title: '提示',
					content: '确认支付？',
					success({
						confirm
					}) {
						if (confirm) {
							balanceRepaymentApi({
								ofId: that.id
							}).then(res => {
								that.$tip(res.res ? '支付成功' : res.resMsg)
								if (res.res) {
									that.getDetail()
								}
							})
						}
					}
				})
			},

			// 保存文件
			saveFile() {
				fetchPDFUrlApi({
					id: this.order_data['id']
				}).then(res => {
					if (res.res) {
						const that = this
						const {
							url
						} = res.obj
						uni.setClipboardData({
							data: url,
							success(res) {
								uni.hideLoading()
								that.$tip('链接已复制，请打开浏览器下载！')
							}
						});
					} else {
						this.$tip('下载失败，请重试！')
					}
				})
			},

			// 查看回执单
			preHzd() {
				uni.previewImage({
					urls: [this.order_data['hzdpath']],
					longPressActions: {
						itemList: ['保存图片'],
					}
				});
			},

			// 获取详情
			getDetail() {
				fetchOrderDetailApi({
					id: this.id
				}).then(res => {
					if (res.res) {
						const {
							collectionTimes,
							logs,
							hzdpath,
							files,
							yydUrl,
							yspAndDhList
						} = res.obj
						this.order_data = res.obj.of
						this.order_data.collectionTimes = collectionTimes
						this.order_data.logs = logs
						this.order_data.hzdpath = hzdpath
						this.order_data.files = files
						this.yydUrl = yydUrl
						this.yspAndDhList = yspAndDhList
					} else {
						this.$tip(res.resMsg)
					}
				})
			}
		}
	}
</script>

<style scoped lang="scss">
	@import '@/layout/group.scss';

	.file-name {
		color: $primary;
	}

	.file-icon {
		width: 40rpx;
		height: 40rpx;
	}

	.btns {
		display: flex;
		flex-direction: row-reverse;
		flex-wrap: wrap;
		margin-bottom: 20rpx;

		.btn {
			height: 70rpx;
			border-radius: 40rpx;
			text-align: center;
			line-height: 70rpx;
			margin-right: 20rpx;
			padding: 0 40rpx;
			background-color: $primary;
			color: #fff;
			margin-top: 20rpx;
		}
	}

	.primary {
		color: $primary !important;
	}
</style>

<style>
	page {
		background-color: #f2f2f2;
	}
</style>
