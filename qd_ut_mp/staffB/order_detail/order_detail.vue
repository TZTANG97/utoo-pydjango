<template>
	<view class="container" v-if="my_data">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					订单编号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.order_id }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="my_data.testClass">
				<view class="group-label">
					订单类型
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.testClass.name }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					制单人员
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.addUser.userName }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="my_data.customUser">
				<view class="group-label">
					客户账号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.customUser.mobile }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					所属公司
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.supplierUser.company_name }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					录入订单时间
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ $alterTime(my_data.addTime, false) }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					下单时间
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ $alterTime(my_data.order_time, false) }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					总价
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.totalPrice.toFixed(2) }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					销售主管
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.saleManagerUser.userName }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					销售人员
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.saleUser.userName }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					客户名称
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.company.name? my_data.company.name : '暂无' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单币种
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.currency_type == '1'? '人民币' : '美元' }}
					</view>
				</view>
			</view>
			<view class="group-item" @click="showDevide = true" v-if="roleName!='R类人员'">
				<view class="group-label">
					分成信息
				</view>
				<view class="group-content">
					查看
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					预计收货时间
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ $alterTime(my_data.delivery_time, false) }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					付款方式
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.paytype.name }}
					</view>
				</view>
			</view>
			<view v-for="(item, index) in collectionTimes" :key="index">
				<view class="group-item">
					<view class="group-label">
						预计收款时间
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ $alterTime(item.time, false) }}
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						预计收款金额
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ item.price.toFixed(2) }}
						</view>
					</view>
				</view>
				<view v-if="item.bill">
					<view class="group-item" style="color: #E96302 !important;">
						<view class="group-label">实际收款时间</view>
						<view class="group-content" style="color: #E96302 !important;">
							<view class="text-content">{{ $alterTime(item.bill.billDate, false) }}</view>
						</view>
					</view>
					<view class="group-item" style="color: #E96302;">
						<view class="group-label">实际收款金额</view>
						<view class="group-content" style="color: #E96302 !important;">
							<view class="text-content">
								<text>{{ item.bill.money.toFixed(2) }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>



			<view class="group-item">
				<view class="group-label">
					是否开票
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.invoiceType == 1? '是' : '否' }}
					</view>
				</view>
			</view>

			<view v-if="openBills.length">
				<view v-for="(item, index) in openBills" :key="index">
					<view class="group-item" style="color: #E96302 !important;">
						<view class="group-label">开票时间</view>
						<view class="group-content" style="color: #E96302 !important;">
							<view class="text-content">{{ $alterTime(item.billDate) }}</view>
						</view>
					</view>
					<view class="group-item" style="color: #E96302;">
						<view class="group-label">开票金额</view>
						<view class="group-content" style="color: #E96302 !important;">
							<view class="text-content">
								<text>{{ item.money.toFixed(2) }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>


			<view class="group-item" v-if="my_data.invoiceType == 1">
				<view class="group-label">
					出项开票类型
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.outBillType? my_data.outBillType.name : '未知'}}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="my_data.invoiceType == 1">
				<view class="group-label">
					税率
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.taxes }}
					</view>
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
				<view class="file-item" v-for="(item, index) in files" :key="index" @click="preImage(index)">
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
					<view class="text-content">
						{{ ORDER_STATUS[my_data.order_status] }}
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

		<!-- 分成信息 -->
		<u-popup mode="center" width="80%" border-radius="20" v-model="showDevide" closeable>
			<view class="popup-wrapper">
				<view class="popup-hint">
					<text>分成信息</text>
				</view>
				<view class="popup-main">
					<view class="popup-item">
						<view class="popup-label">
							毛利分成：
						</view>
						<view class="popup-content">
							<view v-for="(item, index) in scaleList" :key="index">
								<view v-if="cUserName == item.userName || !cUserName">
									<text>{{ item.userName }}：</text>
									<text>{{ item.scale }}%</text>
								</view>
							</view>
						</view>
					</view>
					<view class="popup-item">
						<view class="popup-label">
							成本分成：
						</view>
						<view class="popup-content">
							<view v-for="(item, index) in salecbscaleList" :key="index">
								<view v-if="cUserName == item.userName || !cUserName">
									<text>{{ item.userName }}：</text>
									<text>{{ item.scale }}</text>
								</view>
							</view>
						</view>
					</view>
				</view>
			</view>
		</u-popup>

		<u-popup mode="right" width="60%" v-model="showMenus">
			<view class="menus-list" v-if="my_data">

				<view class="btn"
					v-if="(my_data.order_status == 5 || my_data.order_status == 10 || my_data.order_status == 20 || my_data.order_status == 30) && roleName!='R类人员' && roleName != 'H类用户'"
					@click="cancelOrder">
					取消订单
				</view>
				<navigator :url="`/staff/edit_sub_order/edit_sub_order?id=${id}`" hover-class="none" class="btn"
					v-if="(my_data.order_status == 5 || my_data.order_status == 10 || my_data.order_status == 20) && syUser.userType !== '系统管理员' && isDisabled  && roleName!='R类人员' && roleName != 'H类用户'">
					编辑
				</navigator>

				<navigator :url="`/staff/edit_sub_order/edit_sub_order?id=${id}`" hover-class="none" class="btn"
					v-if="my_data.order_status > 0 && syUser.userType === '系统管理员' && isDisabled  && roleName!='R类人员' && roleName != 'H类用户'">
					编辑
				</navigator>


				<view class="btn" v-if="my_data.order_status === 20  && roleName!='R类人员' && roleName != 'H类用户'"
					@click="cancelAuditApplication">
					取消审核申请
				</view>

				<view class="btn" v-if="my_data.order_status === 5  && roleName!='R类人员' && roleName != 'H类用户'"
					@click="submitAudit">
					提交审核
				</view>

				<navigator
					:url="`/staff/add_em_sub_son_order/add_em_sub_son_order?id=${id}&class_id=${my_data.class_id}`"
					hover-class="none" class="btn"
					v-if="my_data.order_status == 0 && isOut && roleName!='R类人员' && roleName != 'H类用户'">
					创建实验分包子订单
				</navigator>

				<template
					v-if="my_data.order_status == 20 && (syUser.userId == my_data.sale_manager || isshqx) && roleName!='R类人员' && roleName != 'H类用户'">
					<view class="btn" @click="auditOrder(1)">
						审核通过
					</view>
					<view class="btn" @click="auditOrder(2)">
						审核驳回
					</view>
				</template>


				<template
					v-if="my_data.order_status == 30 || my_data.is_evaluate == 1 && roleName!='R类人员' && roleName != 'H类用户'">
					<view class="btn" v-if="viewKpBtn && !my_data.is_online == 0 && roleName != 'R类人员'"
						@click="middleHandleFun('开票')">
						开票
					</view>
					<view class="btn" v-if="viewReciveBtn && roleName != 'R类人员' && roleName != 'H类用户'"
						@click="middleHandleFun('收款')">
						收款
					</view>
				</template>


				<template v-if="my_data.order_status == 67  && roleName!='R类人员' && roleName != 'H类用户'">
					<view class="btn" @click="cancelOrder">
						取消订单
					</view>
					<view class="btn" @click="confirmCommunicateForClinet">
						已和客户沟通确认
					</view>
				</template>
				<view class="btn"
					v-if="(my_data.order_status == 5 || my_data.order_status == 20 || my_data.order_status == 30 || my_data.order_status == 67) && (syUser.userId == my_data.saleUser.id || syUser.userId == my_data.addUser.id) && isfcbl  && roleName!='R类人员' && roleName != 'H类用户'"
					@click="editDevideInfo">
					调整分成比例
				</view>

				<view class="btn" v-if="!my_data.cost_settle == 0  && roleName!='R类人员' && roleName != 'H类用户'"
					@click="settlement">
					所有成本已结清
				</view>

				<navigator :url="`/staff/product_list/product_list?id=${id}&type=8`" hover-class="none" class="btn">
					产品列表
				</navigator>

				<navigator :url="`/staff/child_order/child_order?id=${id}&type=8`" hover-class="none" class="btn">
					子订单
				</navigator>
























				<!-- 				<navigator :url="`/staff/edit_order/edit_order?id=${id}`" hover-class="none" class="btn"
					v-show="(my_data.order_status === 5 || my_data.order_status === 10 || my_data.order_status === 20) && syUser.userType !== '系统管理员' && isDisabled && isType && roleName != 'R类人员'">
					编辑订单
				</navigator>

				<navigator :url="`/staff/edit_order/edit_order?id=${id}`" hover-class="none" class="btn"
					v-show="my_data.order_status && syUser.userType === '系统管理员' && isDisabled && isType">
					编辑订单
				</navigator> -->





				<!-- 				<navigator :url="`/staff/edit_order/edit_order?id=${id}`" hover-class="none" class="btn"
					v-show="my_data.order_status == 66 && isType">
					编辑订单
				</navigator> -->



				<!-- <view class="btn" @click="cancelOrder(2)"
					v-show="(my_data.order_status === 5 || my_data.order_status === 10 || my_data.order_status === 20 || my_data.order_status === 30) && !isType && roleName != 'R类人员'">
					取消订单
				</view>

				<view class="btn" v-show="my_data.order_status === 20 && isType && roleName != 'R类人员'" @click="cancelAudit">
					取消审核申请
				</view>

				<view class="btn" v-show="my_data.order_status === 5 && isType && roleName != 'R类人员'" @click="submitAudit">
					提交审核
				</view>

				<navigator :url="`/staff/add_em_sub_order/add_em_sub_order?id=${id}&class_id=${my_data.class_id}`"
					hover-class="none" class="btn" v-show="my_data.order_status && isOut && isType && roleName != 'R类人员'">
					创建实验子订单
				</navigator>

				<template v-if="my_data.order_status === 20 && (syUser.userId === my_data.sale_manager || isshqx) && roleName != 'R类人员'">
					<view class="btn" @click="audit(1)">审核通过</view>
					<view class="btn" @click="audit(2)">审核驳回</view>
				</template>

				<template v-if="(my_data.order_status === 30 || my_data.is_evaluate === 1) && isType && roleName != 'R类人员'">
					<view class="btn" v-show="viewKpBtn && !my_data.is_online && roleName != 'R类人员'" @click="setKeyWord('开票')">
						开票
					</view>
					<view class="btn" v-show="viewReciveBtn && roleName != 'R类人员'" @click="setKeyWord('收款')">
						收款
					</view>
				</template>

				<template v-if="my_data.order_status === 67 && isType && roleName != 'R类人员'">
					<view class="btn" @click="cancelOrder(2)">
						取消订单
					</view>
					<view class="btn" @click="communicateConfirm">
						已和客户沟通确认
					</view>
				</template>

				<view class="btn" @click="adjustDevide"
					v-show="(my_data.order_status === 67 || my_data.order_status === 5 || my_data.order_status === 20 || my_data.order_status === 30) && (syUser.userId === my_data.saleUser.id || syUser.userId === my_data.addUser.id) && isfcbl && isType && roleName != 'R类人员'">
					调整分成比例
				</view>

				<view v-show="!my_data.cost_settle && isType && roleName != 'R类人员'" class="btn" @click="settlementCost">
					所有成本已结清
				</view> -->

				<!-- 				<navigator v-if="isType" :url="`/staff/child_order/child_order?id=${id}`" hover-class="none"
					class="btn">
					子订单
				</navigator>

				<navigator v-if="isType" :url="`/staff/product_list/product_list?id=${id}`" hover-class="none"
					class="btn">
					产品列表
				</navigator> -->
			</view>
		</u-popup>

		<!-- 操作列表 -->
		<view class="go-left" @click="showMenus = true" v-if="isType">
			<image src="@/static/go-left.png" mode=""></image>
		</view>
		<u-toast ref="uToast" />
		<!-- 开票/收款 -->
		<collection :keyWord="keyWord" :show.sync="show" @getValue="submitInfo"></collection>
		<!-- 评价客户 -->
		<rate-customers :show.sync="showRateCustomers" @getValue="submitRate"></rate-customers>

		<!-- 分成比例 -->
		<devide-into @confirmDevideList="updateDevide" :show.sync="showEditDevide" :backUpList="backUpList"
			:ml="scaleList" :cb="salecbscaleList" :showMl="true" :showCb="true" :cbUnit="false">
		</devide-into>
	</view>
</template>

<script>
	import {
		fetchCheckPendingTestOrderDetailApi,
		cancelTestOrderApi,
		settlementTestOrderCostApi,
		submitAuditTestOrderApi,
		cancelAuditTestOrderApi,
		// 收款/开票
		saleOrderOpenBillApi,
		// 评价客户
		evaluateClientApi,
		// 订单审核通过/审核驳回
		handleCheckPendingTestOrderApi,
		communicateConfirmForClientApi,
		// 获取分成人员列表
		fetchDevideUserListApi,
		updateDevideInfoApi,
		changeOrderPayStatusApi,
		fetchPDFUrlApi
	} from '@/api/index.js'
	import {
		orderdetaildptxcx
	} from '@/api/staffB.js'
	import collection from '../collection'
	import rateCustomers from '../rateCustomers'
	import devideInto from '../devideInto.vue'
	import loading from "@/components/loading.vue"
	import {
		ORDER_STATUS
	} from '@/constant/status.js'
	export default {
		components: {
			collection,
			rateCustomers,
			devideInto,
			loading
		},
		data() {
			return {
				showMenus: false,
				id: '',
				my_data: null,
				// 毛利率
				bfb: 0,
				// 收款金额和时间
				collectionTimes: null,
				showDevide: false,
				salecbscaleList: [],
				scaleList: [],
				backUpList: [],
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
				logs_list: [],
				files: [],
				ORDER_STATUS,
				openBills: [],
				isfcbl: false,
				evaluate: false,
				viewKpBtn: '',
				viewReciveBtn: '',
				isshqx: false,
				show: false,
				keyWord: '',
				showRateCustomers: false,
				showEditDevide: false,
				isDisabled: false,
				isyyd: false,
				isOut: false,
				isType: null,
				roleName: ''
			};
		},
		onLoad({
			id,
			type
		}) {
			const userType = uni.getStorageSync('userInfo')
			this.roleName = userType.roleName
			console.log(this.roleName, 'roleName')
			console.log(type, 'type')
			if (type) this.isType = type
			if (!id) return this.$tip2('缺少订单ID')
			this.id = id
			this.getDetail()
			uni.$on('isEdit', () => {
				this.getDetail()
			})

		},
		onUnload() {
			uni.$off('isEdit')
		},
		methods: {
			viewPDF(type) {
				uni.showLoading()
				fetchPDFUrlApi({
					id: this.id
				}).then(res => {
					if (res.res) {
						const {
							url
						} = res.obj

						const that = this
						uni.downloadFile({
							url,
							success(res) {
								uni.hideLoading()
								uni.openDocument({
									filePath: res.tempFilePath,
									showMenu: true,
									fileType: 'pdf'
								})
							},
							fail() {
								uni.hideLoading()
								that.$toast('PDF预加载失败，请重试！')
							}
						})
					} else {
						uni.hideLoading()
						this.$tip(res.resMsg)
					}
				}).catch(_ => {
					uni.hideLoading()
				})
			},

			// 修改订单的支付状态
			changePayStatus() {
				changeOrderPayStatusApi({
					id: this.id
				}).then(res => {
					this.$tip(res.res ? '支付成功' : '支付失败')
				})
			},

			// 调整分成比例
			updateDevide({
				ml,
				cb
			}) {
				let totalDevide = 0
				totalDevide = ml.reduce((val, e) => {
					if (!this.$isTrue(e.scale) || !e.userId) {
						this.$tip('毛利分成人员和分成比例不能为空')
						throw new Error('')
					}
					return val + (e.scale - 0)
				}, 0)

				cb.forEach(item => {
					if (!item.userId || !this.$isTrue(item.scale)) {
						this.$tip('成本分成人员和分成比例不能为空')
						throw new Error('')
					}
				})

				if (totalDevide !== 100) return this.$tip('毛利分成总和必须等于100%')

				updateDevideInfoApi({
					id: this.id,
					user_scale_info: ml.map(item => `${item.userId}_${item.scale}`).join(','),
					salecb_user_scale_info: cb.map(item => `${item.userId}_${item.scale}`).join(','),
				}).then(res => {
					if (res.res) {
						this.salecbscaleList = cb
						this.scaleList = ml
						this.showEditDevide = false
						this.showMenus = false
					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			// 调整分成准备工作
			async adjustDevide() {
				if (!this.backUpList.length) {
					const result = await fetchDevideUserListApi()
					if (result.res) {
						this.backUpList = result.obj
					} else {
						this.$tip('获取分成人员失败，请重试！')
					}
				}
				this.showEditDevide = true
			},

			// 确认沟通
			communicateConfirm() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否确认已和客户确认？',
					success(res) {
						if (res.confirm) {
							communicateConfirmForClientApi({
								id: that.id,
								type: 'confirm'
							}).then(res => {
								if (res.res) {
									that.$tip('确认成功')
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

			// 审核
			audit(type) {
				const that = this
				uni.showModal({
					title: '提示',
					content: `确定审核${type == 1? '通过' : '驳回' }？`,
					success(res) {
						if (res.confirm) {
							handleCheckPendingTestOrderApi({
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

			// 提交评价
			submitRate({
				star,
				rateContent
			}) {
				evaluateClientApi({
					ofId: this.id,
					point: star,
					content: rateContent,
				}).then(res => {
					if (res.res) {
						this.$tip('评价成功')
						this.showRateCustomers = false
						this.showMenus = false
						this.getDetail()
					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			// 提交 收款/发票信息
			submitInfo({
				money,
				date,
				fileList
			}) {
				saleOrderOpenBillApi({
					// 0收款1开票
					type: this.keyWord == '开票' ? '1' : '0',
					money,
					billDate: date,
					accessoryId: fileList,
					ofId: this.id,
					// 1开票 2收款
					type2: this.keyWord == '开票' ? '1' : '2',
				}).then(res => {
					if (res.res) {
						this.$tip(`${this.keyWord}成功`)
						this.show = false
						this.showMenus = false
						this.getDetail()
					} else {
						this.$tip(res.resMsg)
					}
				})
			},


			// 收款
			setKeyWord(title) {
				this.keyWord = title
				this.show = true
			},



			// 取消审核申请
			cancelAudit() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否确认取消审核申请？',
					success(res) {
						if (res.confirm) {
							cancelAuditTestOrderApi({
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

			// 提交审核
			submitAudit() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否确认提交审核申请？',
					success(res) {
						if (res.confirm) {
							submitAuditTestOrderApi({
								id: that.id
							}).then(res => {
								if (res.res) {
									that.$tip('申请已提交')
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

			// 成本已结清
			settlementCost() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '是否进行所有成本已结清操作？',
					success(res) {
						if (res.confirm) {
							settlementTestOrderCostApi({
								id: that.id
							}).then(res => {
								if (res.res) {
									that.$tip('结算成功')
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

			// 取消订单
			cancelOrder(type) {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定取消？',
					success(res) {
						if (res.confirm) {
							cancelTestOrderApi({
								id: that.id,
								type
							}).then(res => {
								if (res.res) {
									that.$tip('取消成功')
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


			preImage(index) {
				let list = this.files.map(e => e.path + '/' + e.name)
				this.$preFile(index, list)
			},

			// 获取详情
			getDetail() {
				orderdetaildptxcx(this.id).then(res => {
					if (res.res) {
						let {
							of: mainData,
							openBills,
							bfb,
							collectionTimes,
							logs,
							files,
							salecbscaleList,
							scaleList,
							isfcbl,
							evaluate,
							viewKpBtn,
							viewReciveBtn,
							isshqx,
							isDisabled,
							isOut,
							isyyd = false
						} = res.obj
						this.isOut = isOut
						this.isyyd = isyyd
						this.isDisabled = isDisabled
						this.isshqx = isshqx
						this.viewKpBtn = viewKpBtn
						this.viewReciveBtn = viewReciveBtn
						this.evaluate = evaluate
						this.isfcbl = isfcbl
						this.my_data = mainData
						this.openBills = openBills
						this.bfb = bfb
						this.collectionTimes = collectionTimes
						this.logs_list = logs
						this.files = files

						this.salecbscaleList = salecbscaleList
						this.scaleList = scaleList
					} else {
						this.$tip(res.resMsg)
					}
				})
			}
		},
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
		border-bottom-left-radius: 7rpx;
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