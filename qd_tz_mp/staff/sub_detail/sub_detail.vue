<template>
	<view class="container" v-if="my_data">
		<!-- 分成信息 -->
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
			<view class="group-item" v-if="my_data.order_status !== 5 && my_data.order_status !== 67">
				<view class="group-label">
					毛利润
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ bfb.toFixed(2) + '%' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单类型
				</view>
				<view class="group-content">
					<view class="text-content">
						<span>{{ my_data['testClass']['name'] }}</span>
					</view>
				</view>
			</view>
			<view class="group-item" v-if="my_data.addUser">
				<view class="group-label">
					制单人员
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.addUser.userName }}
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
						{{ my_data.currency_type == 1? '人民币' : '美元' }}
					</view>
				</view>
			</view>
			<view class="group-item" @click="show_divide = true" v-if="roleName!='R类人员' && flag">
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
						{{ my_data.paytype? my_data.paytype.name : '暂无' }}
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
				<view v-if="item.onlinebill">
					<view class="group-item" style="color: #E96302 !important;">
						<view class="group-label">实际收款时间</view>
						<view class="group-content" style="color: #E96302 !important;">
							<view class="text-content">{{ $alterTime(item.onlinebill.billDate, false) }}</view>
						</view>
					</view>
					<view class="group-item" style="color: #E96302;">
						<view class="group-label">实际收款金额</view>
						<view class="group-content" style="color: #E96302 !important;">
							<view class="text-content">
								<text>{{ item.onlinebill.money.toFixed(2) }}</text>
							</view>
						</view>
					</view>
				</view>
				<view v-if="item.bill&&!item.onlinebill">
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
			<view class="group-item" style="align-items: start !important;">
				<view class="group-label">
					样品是否回收
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.reverso_context == 1? '是' : '否' }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="my_data.reverso_context == 1">
				<view class="group-label">
					收件人姓名
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.addressee_name ? my_data.addressee_name : '无' }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="my_data.reverso_context == 1">
				<view class="group-label">
					收件人电话
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.addressee_mobile ? my_data.addressee_mobile : '无' }}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="my_data.reverso_context == 1">
				<view class="group-label">
					样品回收地址
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ my_data.send_address ? my_data.send_address : '无' }}
					</view>
				</view>
			</view>
			<!-- <view v-if="yspAndDhList.length">
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
			</view> -->

			<view class="group-item" style="border-bottom: none;">
				<view class="group-label">
					订单资料
				</view>
				<view class="group-content">
					<u-icon size="28" name="arrow-down"></u-icon>
				</view>
			</view>
			<view class="files-list" v-if="files.length !== 0">
				<!-- @click="preImage(index)" -->
				<view class="file-item" v-for="(item, index) in files" :key="index" @click="preImage(index)">
					<text style="color: #E96302;">{{ item.info }}</text>
					<!-- <web-view :src="item.path + '/' + item.name"></web-view> -->
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

			<view v-for="(item, index) in openBills" :key="index">
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

		</view>

		<!--  v-if="roleType != userList['H_USER']['roleName']" -->
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
		<u-popup mode="center" width="80%" border-radius="20" v-model="show_divide" closeable>
			<view class="popup-wrapper">
				<view class="popup-hint">
					<text>分成信息</text>
				</view>
				<view class="popup-main">
					<view class="popup-item">
						<view class="popup-label">
							利润分成：
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
				</view>
			</view>
		</u-popup>


		<u-popup mode="right" width="60%" v-model="showMenus">
			<view class="menus-list" v-if="my_data">
				<view class="btn"
							v-if="(my_data.order_status == 5 || my_data.order_status == 10 || my_data.order_status == 20 || my_data.order_status == 30) && !isType && roleName!='R类人员' && roleName != 'H类用户'"
							@click="cancelOrder">
					取消订单
				</view>
				<navigator :url="`/staff/edit_sub_order/edit_sub_order?id=${id}`" hover-class="none" class="btn"
									 v-if="(my_data.order_status == 5 || my_data.order_status == 10 || my_data.order_status == 20) && syUser.userType !== '系统管理员' && isDisabled && !isType && roleName!='R类人员' && roleName != 'H类用户'">
					编辑
				</navigator>

				<navigator :url="`/staff/edit_sub_order/edit_sub_order?id=${id}`" hover-class="none" class="btn"
									 v-if="my_data.order_status > 0 && syUser.userType === '系统管理员' && isDisabled && !isType && roleName!='R类人员' && roleName != 'H类用户'">
					编辑
				</navigator>


				<view class="btn"
							v-if="my_data.order_status === 20 && !isType && roleName!='R类人员' && roleName != 'H类用户'"
							@click="cancelAuditApplication">
					取消审核申请
				</view>

				<view class="btn" v-if="my_data.order_status === 5 && !isType && roleName!='R类人员' && roleName != 'H类用户'"
							@click="submitAudit">
					提交审核
				</view>

				<navigator
						:url="`/staff/add_em_sub_son_order/add_em_sub_son_order?id=${id}&class_id=${my_data.class_id}`"
						hover-class="none" class="btn"
						v-if="my_data.order_status != 0 && isOut && !isType && roleName!='R类人员' && roleName != 'H类用户'">
					创建实验分包子订单
				</navigator>
				<!-- {{my_data.order_status != 0}},{{isOut}},{{!isType}},{{roleName!='R类人员'}},{{roleName != 'H类用户'}} -->

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
						v-if="(my_data.order_status == 30 || my_data.is_evaluate == 1) && !isType && roleName!='R类人员' && roleName != 'H类用户'">
					<view class="btn" v-if="viewKpBtn && my_data.is_online == 0" @click="middleHandleFun('开票')">
						开票
					</view>
					<view class="btn" v-if="viewReciveBtn" @click="middleHandleFun('收款')">
						收款
					</view>
				</template>


				<template v-if="my_data.order_status == 67 && !isType && roleName!='R类人员' && roleName != 'H类用户'">
					<view class="btn" @click="cancelOrder">
						取消订单
					</view>
					<view class="btn" @click="confirmCommunicateForClinet">
						已和客户沟通确认
					</view>
				</template>
				<view class="btn"
							v-if="(my_data.order_status == 5 || my_data.order_status == 20 || my_data.order_status == 30 || my_data.order_status == 67) && (syUser.userId == my_data.saleUser.id || syUser.userId == my_data.addUser.id) && isfcbl && !isType && roleName!='R类人员' && roleName != 'H类用户' && flag"
							@click="editDevideInfo">
					调整分成比例
				</view>

				<view class="btn" v-if="my_data.cost_settle == 0 && !isType && roleName!='R类人员' && roleName != 'H类用户'"
							@click="settlement">
					所有成本已结清
				</view>

				<!-- <view class="btn">
					增加关联订单
				</view>

				<view class="btn">
					更多信息
				</view>

				<view class="btn" v-show="isyyd">
					生成预约单
				</view> -->

				<view class="btn" @click="addRelatedOrders" v-if="!isType">
					增加关联订单
				</view>
				<view class="btn" @click="appointmentFn" v-show="isyyd && !isType">
					生成预约单
				</view>

				<navigator v-if="!isType" :url="`/staff/product_list/product_list?id=${id}&type=8`" hover-class="none"
									 class="btn">
					产品列表
				</navigator>

				<navigator v-if="!isType" :url="`/staff/child_order/child_order?id=${id}&type=8`" hover-class="none"
									 class="btn">
					子订单
				</navigator>
			</view>
		</u-popup>

		<!-- 打开操作列表 -->
		<view class="go-left" @click="showMenus = true">
			<image src="@/static/go-left.png" mode=""></image>
		</view>
		<u-toast ref="uToast" />

		<!-- 分成比例 -->
		<devide-into @confirmDevideList="confirmUpdateDevide" :show.sync="showEditDevide" :backUpList="backUpList"
								 :lr="scaleList" :showLr="true">
		</devide-into>

		<!-- 评价客户 -->
		<rate-client :show.sync="showRateClient" @getValue="submitRate"></rate-client>

		<!-- 开票/收款 -->
		<collection :keyWord="keyWord" :show.sync="show" @getValue="submitInfo"></collection>
		<!-- 生成预约单 -->
		<appointment @appointmentClose="appointmentClose" :appointmentList="appointmentList"
								 :show.sync="showAppointment">

		</appointment>
		<!-- 增加关联订单 -->
		<relatedOrders :show.sync="showRelatedOrders" @relatedOrdersClose="relatedOrdersClose"></relatedOrders>
	</view>
</template>

<script>
import {
	fetchCheckPendingTestSubOrderDetailApi,
	settlementTestSubOrderApi,
	fetchDevideUserListApi,
	// 保存分成比例
	adjustDevideApi,
	communicateConfirmForClientApi,
	cancelTestSubOrderApi,
	evaluateClientApi,
	saleOrderOpenBillApi,
	cancelTestSubOrderAuditApplicationApi,
	handleCheckPendingTestSubOrderApi,
	submitAuditForTestSubOrderApi,
	fetchPDFUrlApi
} from '@/api/index.js'
import {
	addressList,
	geranateYydForm,
	addRelevanceOrder_dpt
} from '@/api/staffB.js'
import devideInto from '../devideInto.vue'
import rateClient from '../rateCustomers.vue'
import collection from '../collection'
import appointment from '../appointment.vue'
import relatedOrders from '../relatedOrders.vue'
import {
	ORDER_STATUS
} from '@/constant/status.js'
export default {
	components: {
		devideInto,
		rateClient,
		collection,
		appointment,
		relatedOrders
	},
	data() {
		return {
			id: '',
			ORDER_STATUS,
			showMenus: false,
			my_data: null,
			// 毛利率
			bfb: 0,
			files: [],
			// 收款金额和时间
			collectionTimes: null,
			order_type_list: {
				1: '销售订单',
				2: '采购订单',
				3: '校准订单',
				4: '维修订单',
				5: '采购订单',
				6: '实验订单',
				7: '库存销售订单',
				8: '实验分包订单',
				9: '实验分包子订单',
			},
			logs_list: [],
			scaleList: [],
			show_divide: false,
			openBills: [],
			isOut: false,
			isshqx: false,
			viewKpBtn: false,
			viewReciveBtn: false,
			evaluate: false,
			isfcbl: false,
			backUpList: [],
			showEditDevide: false,
			showRateClient: false,
			// 用来区分开票还是收款
			keyWord: '',
			show: false,
			isDisabled: false,
			isyyd: false,
			isType: null,
			roleName: '',
			yspAndDhList: [],
			showAppointment: false,
			appointmentList: [],
			showRelatedOrders: false,
			order_id: '',
			flag:false
		};
	},
	onLoad({
					 id,
					 type,
					 order_id
				 }) {
		const userType = uni.getStorageSync('userInfo')
		this.flag = userType.flag
		this.roleName = userType.roleName
		console.log(this.roleName, 'this.roleName')
		if (type) this.isType = type
		console.log(this.isType, !this.isType, 'isType')
		if (!id) return this.$tip2('缺少订单ID')
		this.id = id
		if (order_id) this.order_id = order_id
		// this.getDetail()
		// uni.$on('isEdit', () => {
		// 	this.getDetail()
		// })
	},
	onUnload() {
		uni.$off('isEdit')
	},
	onShow() {
		this.showMenus = false
		this.getDetail()
		uni.$on('isEdit', () => {
			this.getDetail()
		})
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

		// 提交审核
		submitAudit() {
			const that = this
			uni.showModal({
				title: '提示',
				content: '是否确认提交审核？',
				success(res) {
					if (res.confirm) {
						submitAuditForTestSubOrderApi({
							id: that.id,
						}).then(res => {
							if (res.res) {
								that.$tip('审核已提交')
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
		cancelAuditApplication() {
			const that = this
			uni.showModal({
				title: '提示',
				content: '是否确认取消审核申请？',
				success(res) {
					if (res.confirm) {
						cancelTestSubOrderAuditApplicationApi({
							id: that.id,
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

		// 审核订单
		auditOrder(type) {
			// 1通过2拒绝
			const that = this
			uni.showModal({
				title: '提示',
				content: `是否确定${type == 1? '通过' : '驳回'}订单？`,
				success(res) {
					if (res.confirm) {
						handleCheckPendingTestSubOrderApi({
							id: that.id,
							type
						}).then(res => {
							if (res.res) {
								that.$tip(`订单已${type == 1? '通过' : '驳回'}`)
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

		// 提交收款信息或者开票信息
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

		middleHandleFun(keyWord) {
			this.keyWord = keyWord
			this.show = true
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
					this.showRateClient = false
					this.showMenus = false
					this.getDetail()
				} else {
					this.$tip(res.resMsg)
				}
			})
		},

		// 取消订单
		cancelOrder() {
			const that = this
			uni.showModal({
				title: '提示',
				content: '是否取消此订单？',
				success(res) {
					if (res.confirm) {
						cancelTestSubOrderApi({
							id: that.id,
							type: '2'
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

		// 已和客户沟通确认
		confirmCommunicateForClinet() {
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

		// 确定修改分成信息
		confirmUpdateDevide({
													lr
												}) {
			let totalDevide = 0
			totalDevide = lr.reduce((val, e) => {
				if (!this.$isTrue(e.scale) || !e.userName) {
					this.$tip('分成人员和分成比例不能为空')
					throw new Error('')
				}
				return val + (e.scale - 0)
			}, 0)

			if (totalDevide !== 100) return this.$tip('利润分成总和必须等于100%')

			adjustDevideApi({
				id: this.id,
				user_scale_info: lr.map(item => `${item.userId}_${item.scale}`).join(','),
			}).then(res => {
				if (res.res) {
					this.scaleList = lr
					this.showEditDevide = false
				} else {
					this.$tip(res.resMsg)
				}
			})
		},

		// 调整分成比例
		async editDevideInfo() {
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
		// 添加关联订单
		addRelatedOrders() {
			this.showRelatedOrders = true
		},
		relatedOrdersClose(val, data) {
			let obj = {
				order_id: this.order_id,
				rSelect: val,
				rOrderId: data
			}
			addRelevanceOrder_dpt(obj).then(res => {
				if (res.res) {
					this.showRelatedOrders = false
					this.$tip('增加关联订单成功')
					this.showMenus = false
					this.getDetail()
				} else {
					this.$tip(res.resMsg)
				}
			})
		},
		// 生成预约单
		appointmentFn() {
			addressList().then(res => {
				if (res.res) {
					this.appointmentList = res.obj
					this.showAppointment = true
				}
			})
		},
		// 确认生成预约单
		appointmentClose(id) {
			let data = {
				id: this.id,
				test_address_id: id
			}
			geranateYydForm(data).then(res => {
				if (res.res) {
					this.showAppointment = false
					this.$tip('生成预约单成功')
					this.showMenus = false
					this.getDetail()
				} else {
					this.$tip(res.resMsg)
				}
			})
		},

		// 结算
		settlement() {
			const that = this
			uni.showModal({
				title: '提示',
				content: '是否进行所有成本已结清操作?',
				success(res) {
					if (res.confirm) {
						settlementTestSubOrderApi({
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


		preImage(index) {
			let list = this.files.map(e => e.path + '/' + e.name)
			this.$preFile(index, list)
		},
		// 获取详情
		getDetail() {
			fetchCheckPendingTestSubOrderDetailApi({
				id: this.id
			}).then(res => {
				if (res.res) {
					let {
						of: main,
						bfb,
						collectionTimes,
						logs,
						files,
						scaleList,
						openBills,
						isOut,
						isshqx,
						viewKpBtn,
						viewReciveBtn,
						evaluate,
						isfcbl,
						yspAndDhList,
						isDisabled,
						isyyd
					} = res.obj
					this.isfcbl = isfcbl
					this.isyyd = isyyd
					this.evaluate = evaluate
					this.viewKpBtn = viewKpBtn
					this.viewReciveBtn = viewReciveBtn
					this.my_data = main
					this.isshqx = isshqx
					this.bfb = bfb
					this.isOut = isOut
					this.openBills = openBills
					this.collectionTimes = collectionTimes
					this.logs_list = logs
					this.files = files
					this.isDisabled = isDisabled
					this.yspAndDhList = yspAndDhList
					// if (this.roleType == this.userList['H_USER']['roleName']) {
					// scaleList = scaleList.filter(item => item['userId'] === this.syUser['id'])
					// }
					this.scaleList = scaleList
					console.log(this.my_data.order_status, 'order_status')
					console.log(this.my_data.is_evaluate, 'is_evaluate')
					console.log(this.my_data.is_online, 'is_online')
					console.log(this.isType, 'isType')
					console.log(this.roleName, 'roleName')
					console.log(this.viewKpBtn, 'viewKpBtn')
					console.log(this.viewReciveBtn, 'viewReciveBtn')
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
</style>
<style>
page {
	background-color: #f2f2f2;
}
</style>
