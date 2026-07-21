<template>
	<view class="container">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					订单状态
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ status_list[orderData['order_status']] }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单编号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.order_id }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					来源单号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.parentOf? orderData.parentOf.order_id: '无' }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="orderData.testClass">
				<view class="group-label">
					订单类型
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.testClass.name }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					客户公司
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.company?orderData.company.name : '无' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					所属公司
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.supplierUser.company_name }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					审核主管
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.saleManagerUser.userName }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					销售人员
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.saleUser.userName }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					制单人员
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.addUser.userName }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="orderData.testUser">
				<view class="group-label">
					测试人员
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.testUser.userName }}
					</view>
				</view>
			</view>

			<view class="group-item">
				<view class="group-label">
					下单时间
				</view>
				<view class="group-content">
					<view class="text-content" v-if="orderData">
						{{ $alterTime(orderData.addTime, false) }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					预计收货时间
				</view>
				<view class="group-content">
					<view class="text-content" v-if="orderData">
						{{ $alterTime(orderData.delivery_time, false) }}
					</view>
				</view>
			</view>

			<view class="group-item">
				<view class="group-label">
					客户账号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.customUser? orderData.customUser.mobile : '无' }}
					</view>
				</view>
			</view>

			<view class="group-item" v-if="mobile">
				<view class="group-label">
					联系电话
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.mobile }}
					</view>
				</view>
			</view>

			<view class="group-item" v-if="reverso">
				<view class="group-label">
					样品是否回收
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ reverso == 1 ? '是' : '否' }}
					</view>
				</view>
			</view>

			<view class="group-item" v-if="orderData.send_address">
				<view class="group-label">
					样品寄送地址
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ orderData.send_address }}
					</view>
				</view>
			</view>

			<view class="group-item">
				<view class="group-label">
					是否云视频
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ is_video? '是' : '否' }}
					</view>
				</view>
			</view>


			<template v-if="files.length">
				<view class="group-item" style="border-bottom: none;">
					<view class="group-label">
						订单资料
					</view>
					<view class="group-content">
						<u-icon size="28" name="arrow-down"></u-icon>
					</view>
				</view>
				<view class="files-list">
					<view class="file-item" v-for="(item, index) in files" :key="index"
						@click="preImage(index, 'files')">
						<text style="color: #E96302;">{{ item.info }}</text>
					</view>
				</view>
			</template>

			<template v-if="testFiles.length">
				<view class="group-item" style="border-bottom: none;">
					<view class="group-label">
						测试资料
					</view>
					<view class="group-content">
						<u-icon size="28" name="arrow-down"></u-icon>
					</view>
				</view>
				<view class="files-list">
					<view class="file-item" v-for="(item, index) in testFiles" :key="index"
						@click="preImage(index, 'testFiles')">
						<text style="color: #E96302;">{{ item.info }}</text>
					</view>
				</view>
			</template>

			<view class="group-item" style="border-bottom: none;" v-if="orderData.msg">
				<view class="group-label">
					订单备注
				</view>
				<view class="group-content">
					<view class="all-mark">
						{{ orderData.msg }}
					</view>
				</view>
			</view>
		</view>

		<view class="detail-box" v-if="roleName!='R类人员'">
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
								<!-- <view class="u-order-desc">操作人: {{ item.log_user }}</view> -->
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

		<u-popup mode="right" width="60%" v-model="showMenus">
			<view class="menus-list" v-if="orderData && roleName!='R类人员' && roleName!='H类用户'">

				<template v-if="orderData.order_status != 0 && orderData.order_status !== 50">
					<navigator :url="`/staff/edit_child_order/edit_child_order?id=${id}`" hover-class="none" class="btn"
						v-if="id_list.includes(syUser.userId) && isDisabled && !isType">
						编辑
					</navigator>

					<view class="btn" v-show="id_list.includes(syUser.userId) && !isType"
						@click="sampleAOGandCancel(0)">取消订单
					</view>

					<view class="btn" v-show="orderData.order_status == 20 && !isType" @click="cancelApply">
						取消审核申请
					</view>

					<view class="btn" v-show="orderData.order_status == 5 && !isType" @click="submitApply">
						提交审核
					</view>

					<template
						v-if="orderData.order_status === 20 && (syUser.userId == orderData.sale_manager || isshqx)">
						<view class="btn" @click="audit(1)">
							审核通过
						</view>
						<view class="btn" @click="audit(2)">
							审核驳回
						</view>
					</template>
				</template>

				<view class="btn" @click="yyyspFn" v-show="orderData.order_status >= 36 && is_video === 1 && video_show && !isType">
					预约云视频
				</view>

				<template v-if="orderData.order_status >= 30 && !isType">
					<view class="btn" v-show="ypdhShow" @click="logInfo(1)">
						样品到货
					</view>
					<view class="btn" v-show="yplyShow" @click="logInfo(2)">
						样品领用
					</view>
					<view class="btn" v-show="kscsShow" @click="logInfo(3)">
						开始测试
					</view>
					<view class="btn" v-show="cswcShow" @click="logInfo(4)">
						测试完成
					</view>
					<view class="btn" v-show="ypghShow" @click="logInfo(5)">
						样品归还
					</view>
					<view class="btn" v-show="ypjhShow" @click="logInfo(6)">
						样品寄回
					</view>
					<view class="btn" v-show="yplcShow" @click="logInfo(7)">
						样品留存
					</view>
					<!-- <view class="btn" v-show="ypfcShow" @click="logInfo(8)">
						样品复测
					</view> -->
				</template>
				<navigator v-if="!isType" hover-class="none" class="btn"
					:url="`/staff/child_product_list/child_product_list?id=${id}`">
					产品列表
				</navigator>
			</view>
		</u-popup>
		<!-- 选择子订单列表 -->
		<u-popup v-model="show" mode="center" width="100%" border-radius="20rpx" :mask-close-able="false" :closeable="true">
			<view style="padding: 20rpx;">
				<view style="padding: 20rpx;border-bottom: 1px #ccc solid;">选择子订单</view>
				<scroll-view scroll-y="true" style="height: 100%;">
					<view style="text-align: center;margin: 30rpx;" v-if="cpList.length == 0">暂无数据</view>
					<view class="list" v-if="cpList.length != 0">
						<view class="item" v-for="(item, index) in cpList" :key="index">
							<view class="item-row"
								style="display: flex;justify-content: space-between;padding: 0 20rpx;align-items: center;">
								<text></text>
								<u-checkbox-group>
									<u-checkbox v-model="item.checked"></u-checkbox>
								</u-checkbox-group>
							</view>
							<view class="item-row">
								<text>产品名称：{{ item['goods_name'] }}</text>
							</view>
							<view class="item-row" v-if="item['goods_spec']">
								<text>产品型号：{{ item['goods_spec'] }}</text>
							</view>
							<view class="item-row">
								<text>产品品牌：{{ item['goods_brand_name'] }}</text>
							</view>
							<view class="item-row">
								<text>数量：{{ item['goods_nums'] }}</text>
							</view>
							<view class="item-row">
								<text>实验测试项目：{{ item['experiment_project_name'] }}</text>
							</view>
							<view class="item-row" v-if="item['experiment_class_name']">
								<text>实验测试分类：{{ item['experiment_class_name'] }}</text>
							</view>
						</view>
					</view>
				</scroll-view>
				<view class="confrim-btn" style="margin-top: 20rpx;display: flex;justify-content: center;">
					<view @click="cpBtn" style="border-radius: 10rpx;padding: 20rpx 0;background-color: #e96302; width: 100%;color: #fff;text-align: center;">
						确定
					</view>
				</view>
			</view>
		</u-popup>
		<!-- 预约云视频 -->
		<u-popup v-model="yypSshow" mode="center" width="80%" :mask-close-able="false" border-radius="20rpx" :closeable="true">
			<view style="padding: 20rpx;">
				<view style="padding: 20rpx;border-bottom: 1px #ccc solid;margin-bottom: 20rpx;">预约云视频</view>
				<view class="group">
					<view class="group-item">
						<view class="group-label">
							预约云视频时间
						</view>
						<view class="group-content" @click="showCalendar = true">
							<view class="text-content">
								{{ yypDate ? yypDate : '请选择时间' }}
							</view>
						</view>
					</view>
					<view class="group-item">
						<view class="group-label">
							预约云视频会议号
						</view>
						<view class="group-content">
							<view class="text-content">
								<input v-model="yypCode" style="text-align: right;" placeholder="请输入会议号" />
							</view>
						</view>
					</view>
				</view>

				<view style="margin-top: 20rpx;display: flex;justify-content: center;">
					<view @click="yypOk" style="border-radius: 10rpx;padding: 20rpx 0;background-color: #e96302; width: 100%;color: #fff;text-align: center;">
						确定
					</view>
				</view>
			</view>
		</u-popup>

		<!-- 操作列表 -->
		<view class="go-left" @click="showMenus = true">
			<image src="@/static/go-left.png" mode=""></image>
		</view>
		<u-toast ref="uToast" />
		<!-- 选择日期 -->
		<u-calendar btn-type="warning" @change="confirmDate" max-date="2222-01-01" active-bg-color="#E96302 !important"
			v-model="showCalendar" mode="date"></u-calendar>
	</view>
</template>

<script>
	import {
		fetchTestChildOrderDetailApi,
		sampleAOGandCancelApi,
		testOrderChildOrderTestApi,
		scanOperateApi,
		childAuditApi,
		cancelChildApplyApi,
		childSubmitApplyApi,
		cancelOperatExperimentChild
	} from '@/api/index.js'
	import {
		experimentChildOrderList,
		addVideoInfo
	} from '@/api/staffB.js'
	export default {
		data() {
			return {
				showMenus: false,
				id: '',
				logs_list: [],
				files: [],
				status_list: {
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
				orderData: null,
				childOrderData: null,
				testFiles: [],
				line: null,
				reverso: 0,
				isshqx: false,
				isDisabled: false,
				id_list: [],
				video_show: false,
				isType: null,
				roleName: '',
				ypdhShow:false,
				yplyShow:false,
				kscsShow:false,
				cswcShow:false,
				ypghShow:false,
				ypjhShow:false,
				yplcShow:false,
				ypfcShow:false,
				is_video:null,
				show: false,
				cpList: [],
				showCalendar: false,
				yypDate: '',
				yypCode: '',
				cpId: null,
				yypSshow: false,
				order_id:null
			};
		},
		onLoad({
			id,
			type,
			order_id
		}) {
			const userType = uni.getStorageSync('userInfo')
			this.roleName = userType.roleName
			if (type) this.isType = type
			if (!id) return this.$tip2('缺少订单ID')
			this.id = id
			this.order_id = order_id
			this.getDetail()
		},
		onShow() {
			this.getDetail()
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
							childSubmitApplyApi({
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
			// 选择子列表
			cpBtn() {
				let arr = []
				this.cpId = null
				this.cpList.forEach(item => {
					if (item.checked) arr.push(true)
				})
				if (arr.length == 0) return this.$toast('请选择一条数据！')
				if (arr.length != 1) return this.$toast('只能选择一条数据！')
				this.cpList.forEach(item => {
					if (item.checked) this.cpId = item.id
				})
				this.show = false
				this.yypSshow = true
			},
			// 预约云视频
			yypOk() {
				let that= this
				let data = {
					ofId:this.id,
					childids:this.cpId,
					setting_time:this.yypDate,
					meeting_num:this.yypCode,
				}
				addVideoInfo(data).then(res=>{
					console.log(res,'res')
					if (res.res) {
						that.$tip('预约成功')
						that.yypSshow = false
						that.getDetail()
					} else {
						that.$tip(res.resMsg)
					}
				})
			},
			yyyspFn() {
				experimentChildOrderList(this.id).then(res => {
					res.data.forEach(item => {
						item.checked = false
					})
					this.cpList = res.data
					this.show = true
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
							cancelChildApplyApi({
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

			// 审核 通过/驳回
			audit(type) {
				const that = this
				uni.showModal({
					title: '提示',
					content: `确定审核${type == 1? '通过' : '驳回' }？`,
					success(res) {
						if (res.confirm) {
							childAuditApi({
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

			// 修改实验状态
			updateTestStatus(status) {
				const that = this
				uni.showModal({
					title: '提示',
					content: `确定${status === 1? '开始' : '完成'}测试？`,
					success({
						confirm
					}) {
						if (confirm) {
							testOrderChildOrderTestApi({
								type: status,
								id: that.id
							}).then(({
								res,
								resMsg
							}) => {
								if (res) {
									resMsg = '操作成功'
									that.showMenus = false
									that.getDetail()
								}
								that.$toast(resMsg)
							})
						}
					}
				})
			},
			// 确定时间
			confirmDate(e) {
				this.yypDate = e.result
			},
			logInfo(type) {
				let params = {
					type,
					id: this.id
				}

				// if (type === 3) {
				// 	params['line_id'] = this.line.id
				// 	params['line_name'] = this.line.line_num
				// }

				let result = []
				for (let k in params) {
					result.push(`${k}=${params[k]}`)
				}

				uni.navigateTo({
					url: `/staffB/scan/scan?${result.join('&')}`,
				})
			},


			// 样品到货和取消订单
			sampleAOGandCancel(type) {
				const that = this
				uni.showModal({
					title: '提示',
					content: `确定${type? '样品到货' : '取消订单'}？`,
					success({
						confirm
					}) {
						if (confirm) {
							cancelOperatExperimentChild(that.id).then(({
								res,
								resMsg
							}) => {
								if (res) {
									resMsg = '操作成功'
									that.showMenus = false
									that.getDetail()
								}
								that.$toast(resMsg)
							})
							// sampleAOGandCancelApi({
							// 	id: that.id,
							// 	type
							// })
						}
					}
				})
			},

			preImage(idx, k) {
				let list = this[k].map(e => e.path + '/' + e.name)
				this.$preFile(idx, list)
			},

			// 获取详情
			getDetail() {
				this.showMenus = false
				fetchTestChildOrderDetailApi({
					id: this.id
				}).then(res => {
					if (res.res) {
						let {
							of: mainData,
							logs,
							files,
							testFiles,
							obj,
							line,
							reverso,
							isshqx,
							testUser,
							addUser,
							saleManaUser,
							is_video,
							saleUser,
							usersadmin,
							isDisabled,
							video_show
						} = res.obj
						this.video_show = video_show
						this.is_video = is_video
						this.isDisabled = isDisabled
						this.id_list.push(testUser?.id)
						this.id_list.push(addUser?.id)
						this.id_list.push(saleManaUser?.id)
						this.id_list.push(saleUser?.id)
						this.id_list.push(usersadmin?.id)
						this.ypdhShow = res.obj.ypdhShow,
						this.yplyShow = res.obj.yplyShow,
						this.kscsShow = res.obj.kscsShow,
						this.cswcShow = res.obj.cswcShow,
						this.ypghShow = res.obj.ypghShow,
						this.ypjhShow = res.obj.ypjhShow,
						this.yplcShow = res.obj.yplcShow,
						this.ypfcShow = res.obj.ypfcShow,

						this.isshqx = isshqx
						this.orderData = mainData
						this.childOrderData = obj
						this.logs_list = logs
						this.files = files
						this.testFiles = testFiles
						this.line = line
						this.reverso = reverso
					} else {
						this.$tip(res.resMsg)
					}
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/popup.scss';
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
		// border-image: linear-gradient(0deg, #ffceb2, #fff5da) 10 10;
		// background: linear-gradient(0deg, #089fe5 0%, #19d59a 100%);
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
	.list {
		overflow: hidden;

		.item-row {
			height: 60rpx;
			line-height: 60rpx;
			box-sizing: border-box;
			padding: 0 20rpx;
			width: 100%;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;

			&:first-child {
				height: 80rpx;
				line-height: 80rpx;
				background-color: $primary;
				color: #FFF;
			}
		}
	}

	.item {
		margin-top: 20rpx;
		background-color: #FFF;
		border-radius: 5rpx;
		overflow: hidden;
	}
</style>
<style>
	page {
		background-color: #f2f2f2;
	}
	.u-btn--warning {
		border-color: #e96302 !important;
		background-color: #e96302 !important;
	}
	@import '@/layout/popup.scss';
</style>
