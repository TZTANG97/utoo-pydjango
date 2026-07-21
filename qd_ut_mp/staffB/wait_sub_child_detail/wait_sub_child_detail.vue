<template>
	<view class="container" v-if="my_data">
		<!-- 分成信息 -->
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					订单编号
				</view>
				<view class="group-content">
					{{ my_data.order_id }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					来源订单
				</view>
<!-- 				<navigator style="color: #E96302;"
					:url="`/test/check_pending_test_sub_order_detail/check_pending_test_sub_order_detail?id=${my_data.parentOf.id}`"
					hover-class="none" v-if="my_data.parentOf">
					{{ my_data.parentOf.order_id }}
				</navigator> -->
				<view v-if="my_data.parentOf">
					{{ my_data.parentOf.order_id }}
				</view>

				<view class="group-content" v-else>
					自主订单
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					销售主管
				</view>
				<view class="group-content">
					{{ my_data.saleManagerUser.userName }}
				</view>
			</view>
			<view class="group-item" v-if="my_data.saleUser">
				<view class="group-label">
					采购人员
				</view>
				<view class="group-content">
					{{ my_data.saleUser.userName }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					制单人员
				</view>
				<view class="group-content">
					{{ my_data.addUser.userName }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					实验分包公司名称
				</view>
				<view class="group-content">
					{{ my_data.stock_company_name }}
				</view>
			</view>
			<view v-if="isFlag" class="group-item">
				<view class="group-label">
					实验分包总价
				</view>
				<view class="group-content">
					{{ my_data.totalPrice? my_data.totalPrice.toFixed(2) : '0.00'}}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					下单时间
				</view>
				<view class="group-content">
					{{ my_data.order_time ? $alterTime(my_data.order_time).slice(0, 10) : '' }}
				</view>
			</view>

			<view class="group-item">
				<view class="group-label">
					预计发货时间
				</view>
				<view class="group-content">
					{{ $alterTime(my_data.delivery_time).slice(0, 10) }}
				</view>
			</view>
			<view v-if="isFlag" class="group-item">
				<view class="group-label">
					订单币种
				</view>
				<view class="group-content">
					{{ my_data.currency_type === 1? '人民币' : '美元' }}
				</view>
			</view>
			<view v-if="isFlag" class="group-item">
				<view class="group-label">
					付款方式
				</view>
				<view class="group-content">
					{{ my_data.paytype.name }}
				</view>
			</view>
			<view v-if="isFlag" class="group-item">
				<view class="group-label">
					付款状态
				</view>
				<view class="group-content">
					{{ pay_status.find(e => e.key === my_data.pay_status).value }}
				</view>
			</view>
			<view v-if="isFlag" v-for="(item, index) in collectionTimes" :key="index">
				<view class="group-item">
					<view class="group-label">
						预计付款时间
					</view>
					<view class="group-content">
						{{ $alterTime(item.time, false) }}
					</view>
				</view>
				<view v-if="isFlag" class="group-item">
					<view class="group-label">
						预计付款金额
					</view>
					<view class="group-content">
						<text>{{ item.price.toFixed(2) }}</text>
					</view>
				</view>
				<view v-if="item.bill">
					<view class="group-item" style="color: #E96302 !important;">
						<view class="group-label">实际付款时间</view>
						<view class="group-content" style="color: #E96302 !important;">
							<view class="text-content">{{ $alterTime(item.bill.billDate, false) }}</view>
						</view>
					</view>
					<view class="group-item" style="color: #E96302;">
						<view class="group-label">实际付款金额</view>
						<view class="group-content" style="color: #E96302 !important;">
							<view class="text-content">
								<text>{{ item.bill.money.toFixed(2) }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>
			<view v-if="isFlag" class="group-item">
				<view class="group-label">
					是否开票
				</view>
				<view class="group-content">
					{{ my_data.invoiceType === 1 ? '是' : '否' }}
				</view>
			</view>

			<view v-if="isFlag" v-for="(item, index) in openBills" :key="index">
				<view class="group-item">
					<view class="group-label">开票时间</view>
					<view class="group-content">
						<view class="text-content">{{ $alterTime(item.billDate, false) }}</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">开票金额</view>
					<view class="group-content">
						<view class="text-content">
							<text>{{ item.money.toFixed(2) }}</text>
						</view>
					</view>
				</view>
			</view>

			<view class="group-item" v-if="my_data.invoiceType == 1&&isFlag">
				<view class="group-label">
					进项开票类型
				</view>
				<view class="group-content">
					{{ my_data.inBillType? my_data.inBillType.name : '未知'}}
				</view>
			</view>
			<view class="group-item" v-if="my_data.invoiceType == 1&&isFlag">
				<view class="group-label">
					税率
				</view>
				<view class="group-content">
					{{ my_data.taxes }}
				</view>
			</view>

			<view class="group-item" style="border-bottom: none;" v-if="files.length !== 0">
				<view class="group-label">
					订单资料
				</view>
				<view class="group-content">
					<u-icon size="28" name="arrow-down"></u-icon>
				</view>
			</view>
			<view class="files-list" v-if="files.length !== 0">
				<view class="file-item" @click="preFile(index)" v-for="(item, index) in files" :key="index">
					<text style="color: #E96302;">{{ item.info }}</text>
				</view>
			</view>
			<view class="group-item" style="border-bottom: none;" v-if="my_data.msg">
				<view class="group-label">
					订单备注
				</view>
				<view class="group-content">
					<view class="all-mark">
						{{ my_data.msg }}
					</view>
				</view>
			</view>

			<view class="group-item">
				<view class="group-label">
					订单状态
				</view>
				<view class="group-content">
					{{ order_status[my_data.order_status] }}
				</view>
			</view>

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
								<view>{{ $u.timeFormat(item.addTime, 'yyyy-mm-dd') }}</view>
								<view>{{ $u.timeFormat(item.addTime, 'hh:MM:ss') }}</view>
							</view>
							<view>
								<view class="u-order-desc" v-if="item.log_user">操作人: {{ item.log_user.trueName }}</view>
								<view class="u-order-desc">
									操 作：
									<u-parse :html="item.log_info"></u-parse>
								</view>
							</view>
						</template>
					</u-time-line-item>
				</u-time-line>
			</view>
			<view class="empty" v-if="!logs_list.length">暂无操作记录</view>
			<view style="height: 1rpx;"></view>
		</view>

		<!-- 左拉图标 -->
		<view class="go-left" @click="showMenus = true">
			<image src="@/static/go-left.png" mode=""></image>
		</view>

		<u-popup width="60%" mode="right" v-model="showMenus">
			<view class="menus-list" v-if="my_data">
				<view class="btn" @click="editOrder" v-show="my_data.order_status && isDisabled && !isType">
					编辑
				</view>

				<view class="btn" v-show="(my_data.order_status == 5 || my_data.order_status == 10) && !isType" @click="cancelOrder">
					取消订单
				</view>

				<view class="btn" v-show="my_data.order_status == 20 && !isType" @click="cancelApply">
					取消审核申请
				</view>

				<view class="btn" v-show="my_data.order_status == 5 && !isType" @click="submitApply">
					提交审核
				</view>

				<template v-if="my_data.order_status === 20 && (syUser.userId == my_data.sale_manager || isshqx) && !isType">
					<view class="btn" @click="audit(1)">
						付款审核通过
					</view>
					<view class="btn" @click="audit(2)">
						付款审核驳回
					</view>
				</template>

				<view class="btn" v-show="my_data.order_status == 30 && !isType" @click="uploadData('下单')">
					确认已下单
				</view>


				<template v-if="my_data.order_status >= 30">
					<view class="btn" v-show="(!my_data.pay_status || my_data.pay_status === 36) && isAskPay && !isType"
						@click="putInPay">
						申请付款
					</view>

					<template v-if="my_data.pay_status === 32 && (syUser.userId == my_data.sale_manager || isshqx) && isType">
						<view class="btn" @click="handle(2)">
							付款审核通过
						</view>
						<view class="btn" @click="handle(3)">
							付款审核拒绝
						</view>
					</template>

					<view class="btn" v-show="my_data.pay_status === 33 && !isType" @click="putInPay">
						重新发起付款申请
					</view>
				</template>

				<view class="btn" v-show="my_data.pay_status === 34 && viewReciveBtn && !isType" @click="uploadData('付款')">
					上传付款信息
				</view>

				<view class="btn" v-show="my_data.order_status >= 30 && viewKpBtn && !isType" @click="uploadData('开票')">
					上传发票信息
				</view>




				<navigator v-if="!isType" hover-class="none" class="btn"
					:url="`/staff/child_product_list/child_product_list?type=8&id=${id}`">
					产品列表
				</navigator>
			</view>
		</u-popup>


		<u-toast ref="uToast" />
		<collection :keyWord="keyWord" :show.sync="showCollection" @getValue="submitData"></collection>
	</view>
</template>

<script>
	import {
		fetchCheckPendingTestSubChildOrderDetailApi,
		checkTestSubChildOrderStatusApi,
		cancelTestSubChildOrderApi,
		putInPayTestSubChildOrderApi,
		saleOrderOpenBillApi,
		confirmOrderTestSubChildOrderApi,
		shipmentsTestSubChildOrderApi,
		subChildAuditApi,
		cancelSubChildApplyApi,
		subChildSubmitApplyApi
	} from '@/api/index.js'
	// 上传发票/收款组件
	import collection from '../collection.vue'
	export default {
		components: {
			collection
		},
		data() {
			return {
				id: '',
				my_data: null,
				// 收款金额和时间
				collectionTimes: null,
				order_type_list: [{
						id: 1,
						label: '销售订单'
					},
					{
						id: 2,
						label: '采购订单'
					},
					{
						id: 3,
						label: '校准订单'
					},
					{
						id: 4,
						label: '维修订单'
					},
					{
						id: 5,
						label: '采购订单'
					},
					{
						id: 6,
						label: '实验订单'
					},
					{
						id: 7,
						label: '库存销售订单'
					},
					{
						id: 8,
						label: '实验分包订单'
					},
					{
						id: 9,
						label: '实验分包子订单'
					},
				],
				order_status: {
					0: "已取消",
					5: "订单未发起审核",
					10: "已驳回",
					20: "待审核",
					30: "已审核",
					35: "已下单",
					36: "样品到货",
					37: "样品领用",
					38: "测试中",
					39: "测试完成",
					41: "样品归还",
					42: "样品寄回",
					43: "样品留存",
					45: "已发货",
					46: "已入库",
					50: "已完成"
				},
				logs_list: [],
				showMenus: false,
				pay_status: [{
						key: 0,
						value: '未申请'
					},
					{
						key: 32,
						value: '待审核'
					},
					{
						key: 33,
						value: '已驳回'
					},
					{
						key: 34,
						value: '已审核'
					},
					{
						key: 36,
						value: '已付款'
					},
					{
						key: 38,
						value: '已完成'
					}
				],
				files: [],
				isAskPay: false,
				isshqx: false,
				viewReciveBtn: false,
				viewKpBtn: false,
				showCollection: false,
				keyWord: '',
				openBills: [],
				isDisabled: false,
				video_show: false,
        isFlag: false,
				isType:null
			};
		},
		onLoad(options) {
			let {
				id,
				type
			} = options
			if(type) this.isType = type
			if (!id) return this.$tip2('缺少订单ID')
			this.id = id
			this.getDetail()
			uni.$on('isEdit', () => {
				this.getDetail()
			})
			console.log(this.syUser,'syUsersyUser')
		},
		onUnload() {
			uni.$off('isEdit');
		},
		methods: {

			// 提交审核
			submitApply() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确认发起审核申请？',
					success(res) {
						if (res.confirm) {
							subChildSubmitApplyApi({
								id: that.id
							}).then(res => {
								if (res.res) {
									that.$tip('发起成功')
									that.showMenus = false
									that.getDetail()
								} else {
									that.$tip(res.resMsg)
								}
							})
						}
					}
				})
			},

			// 取消审核申请
			cancelApply() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否确认取消审核申请？',
					success(res) {
						if (res.confirm) {
							cancelSubChildApplyApi({
								id: that.id
							}).then(res => {
								if (res.res) {
									that.$tip('申请已取消')
									that.showMenus = false
									that.getDetail()
								} else {
									that.$tip(res.resMsg)
								}
							})
						}
					}
				})
			},


			// 审核通过/驳回
			audit(type) {
				const that = this
				uni.showModal({
					title: '提示',
					content: `确定审核${type == 1? '通过' : '驳回' }？`,
					success(res) {
						if (res.confirm) {
							subChildAuditApi({
								id: that.id,
								type
							}).then(res => {
								if (res.res) {
									that.$tip(`审核已${type == 1? '通过' : '驳回'}`)
									that.showMenus = false
									that.getDetail()
								} else {
									that.$tip(res.resMsg)
								}
							})
						}
					}
				})
			},

			// 厂家已发货
			shipments() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否确认已发货?',
					success(res) {
						if (res.confirm) {
							shipmentsTestSubChildOrderApi({
								orderStatus: 45,
								id: that.id
							}).then(res => {
								if (res.res) {
									that.$tip('发货成功')
									that.showMenus = false
									that.getDetail()
								} else {
									that.$tip(res.resMsg)
								}
							})
						}
					},
				})
			},

			// 上传之后提交
			async submitData({
				money,
				date,
				fileList
			}) {
				let result = null

				if (this.keyWord == '下单') {
					result = await confirmOrderTestSubChildOrderApi({
						ofId: this.id,
						accessoryId: fileList
					})
				} else {
					result = await saleOrderOpenBillApi({
						money,
						ofId: this.id,
						billDate: date,
						accessoryId: fileList,
						// 1开票 2付款
						type2: this.keyWord == '开票' ? '1' : '2',
					})
				}

				if (result.res) {
					this.$tip(`${this.keyWord}成功`)
					this.showCollection = false
					this.showMenus = false
					this.getDetail()
				} else {
					this.$tip(result.resMsg)
				}
			},

			// 上传操作
			uploadData(keyWord) {
				this.keyWord = keyWord
				this.showCollection = true
			},

			// 申请付款
			putInPay() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否确定发起付款申请?',
					success(res) {
						if (res.confirm) {
							putInPayTestSubChildOrderApi({
								type: '1',
								ofId: that.id
							}).then(res => {
								if (res.res) {
									that.$tip('申请成功')
									that.showMenus = false
									that.getDetail()
								} else {
									that.$tip(res.resMsg)
								}
							})
						}
					},
				})
			},

			// 取消订单
			cancelOrder() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否取消此订单?',
					success(res) {
						if (res.confirm) {
							cancelTestSubChildOrderApi({
								type: '2',
								id: that.id
							}).then(res => {
								if (res.res) {
									that.$tip('订单已取消')
									that.showMenus = false
									that.getDetail()
								} else {
									that.$tip(res.resMsg)
								}
							})
						}
					},
				})
			},

			// 编辑订单
			editOrder() {
				checkTestSubChildOrderStatusApi({
					id: this.id
				}).then(res => {
					if (res.res) {
						uni.navigateTo({
							url: '/staff/edit_sub_child_order/edit_sub_child_order?id=' +
								this.id
						})
					}
				})
			},


			preFile(index) {
				let list = this.files.map(e => e.path + '/' + e.name)
				this.$preFile(index, list)
			},
			// 审核操作
			handle(type) {
				let that = this
				uni.showModal({
					title: '提示',
					content: `确定${type === 2? '同意' : '拒绝'}该申请？`,
					success(res) {
						if (res.confirm) {
							putInPayTestSubChildOrderApi({
								type,
								ofId: that.id
							}).then(res => {
								if (res.res) {
									that.$tip(`审核已${type === 2? '同意' : '拒绝'}`)
									that.showMenus = false
									that.getDetail()
								} else {
									that.$tip(res.resMsg)
								}
							})
						}
					},
				})
			},

			// 获取详情
			getDetail() {
				fetchCheckPendingTestSubChildOrderDetailApi({
					id: this.id,
				}).then(res => {
					if (res.res) {
						let {
							of,
							collectionTimes,
							logs,
							childs,
							files,
							isAskPay,
							isshqx,
							viewReciveBtn,
							viewKpBtn,
							openBills,
							isDisabled,
							video_show
						} = res.obj
            this.isFlag = res.obj.isFlag
						this.video_show = video_show
						this.isDisabled = isDisabled
						this.openBills = openBills
						this.viewKpBtn = viewKpBtn
						this.viewReciveBtn = viewReciveBtn
						this.isshqx = isshqx;
						this.my_data = of;
						this.isAskPay = isAskPay
						this.collectionTimes = collectionTimes
						this.logs_list = logs
						this.files = files
					} else {
						this.$tip(res.resMsg)
					}
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/group.scss';

	.menus-list {
		.btn {
			width: 260rpx;
			height: 65rpx;
			line-height: 65rpx;
			background-color: $primary;
			color: #FFF;
			text-align: center;
			margin: 30rpx auto 0;
			box-sizing: border-box;
			padding: 0 25rpx;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}
	}

	.go-left {
		position: fixed;
		right: 0;
		top: 40%;
		background-color: #FFF;
		border-top-left-radius: 7rpx;
		border-bottom-left-radius: 40rpx;
		padding-left: 10rpx;

		image {
			width: 60rpx;
			height: 65rpx;
			vertical-align: middle;
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
<style>
	page {
		background-color: #f2f2f2;
	}
</style>
