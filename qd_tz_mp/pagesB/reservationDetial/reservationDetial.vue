<template>
	<view class="container">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					实验测试分类：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'classNameList', '实验测试分类', 'classId')">
						{{ swapIdgetValue('classNameList', 'name', 'classId') }}
						<u-icon size="28" v-if="detail && (detail.status == 0 || detail.status == 1)"
							name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					姓名：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail.userName || ''}}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					手机号：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail.mobile || ''}}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					公司名：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail.company_name || ''}}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					客服人员：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail.syUserName || ''}}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					咨询详情
				</view>
				<view class="group-content">
					<view class="text-content">
						<textarea :disabled="detail.status != 0 && detail.status != 1" v-model="detail.content"
							placeholder="请输入咨询详情" maxlength="120" />
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					备注
				</view>
				<view class="group-content">
					<view class="text-content">
						<textarea :disabled="detail.status != 0 && detail.status != 1" v-model="detail.remark"
							placeholder="请输入备注" maxlength="120" />
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					用户上传资料：
				</view>
				<view class="group-content">
					<view class="text-content">
						<!-- 	<image style="width: 35rpx;height: 35rpx;margin-right: 10rpx;vertical-align: middle;"
							src="@/static/img/upload.png" mode=""></image> -->
						<!-- <text>上传</text> -->
					</view>
				</view>
			</view>
			<view class="files-list" v-if="files.length !== 0">
				<view class="file-item" v-for="(item, index) in files" :key="index" @click="preImage(index)">
					<text style="color: #3C8BDB;">{{ item.info }}</text>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					样品寄回地址
				</view>
				<view class="group-content">
					<view class="text-content">
						<textarea :disabled="detail.status != 0 && detail.status != 1" v-model="detail.send_address"
							placeholder="请输入回收地址" maxlength="120" />
					</view>
				</view>
			</view>
			<view class="group-item" style="align-items: start !important;">
				<view class="group-label">
					样品是否回收：
				</view>
				<view class="group-content">
					<view class="text-content">
						<u-switch :disabled="detail.status != 0 && detail.status != 1" @change="reversoSwitch"
							v-model="reverso_context" active-color="#3C8BDB" size="28">
						</u-switch>
					</view>
				</view>
			</view>
			<template v-if="detail.reverso_context">
				<view class="group-item">
					<view class="group-label">
						收件人姓名
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ detail.addressee_name }}
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						收件人电话
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ detail.addressee_mobile }}
						</view>
					</view>
				</view>
			</template>
			<view class="group-item">
				<view class="group-label">
					所属公司：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('company_name', 'companyList', '所属公司', 'companyId')">
						{{ swapIdgetValue('companyList', 'company_name', 'companyId') }}
						<u-icon size="28" v-if="detail && (detail.status == 0 || detail.status == 1)"
							name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					销售主管：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('userName', 'saleBossList', '销售主管', 'purchaseBossId')">
						{{ swapIdgetValue('saleBossList', 'userName', 'purchaseBossId') }}
						<u-icon size="28" v-if="detail && (detail.status == 0 || detail.status == 1)"
							name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					预计收货时间：
				</view>
				<view class="group-content">
					<view class="text-content" @click="chooseDate('delivery_time')">
						{{ delivery_time || '请选择收货时间' }}
						<u-icon size="28" v-if="detail && (detail.status == 0 || detail.status == 1)"
							name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					预计收款时间：
				</view>
				<view class="group-content">
					<view class="text-content" @click="chooseDate('collection_time')">
						{{ collection_time || '请选择收款时间' }}
						<u-icon size="28" v-if="detail && (detail.status == 0 || detail.status == 1)"
							name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单类型：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'orderTypeList', '订单类型', 'order_type')">
						{{ swapIdgetValue('orderTypeList', 'name', 'order_type') }}
						<u-icon size="28" v-if="detail && (detail.status == 0 || detail.status == 1)"
							name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					实验测试地址：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'testAddressList', '实验测试地址', 'test_address')">
						{{ swapIdgetValue('testAddressList', 'name', 'test_address') }}
						<u-icon size="28" v-if="detail && (detail.status == 0 || detail.status == 1)"
							name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					公司汇款账户：
				</view>
				<view class="group-content">
					<view class="text-content"
						@click="select('name', 'companyAccountList', '公司汇款账户', 'company_account')">
						{{ swapIdgetValue('companyAccountList', 'name', 'company_account') }}
						<u-icon size="28" v-if="detail && (detail.status == 0 || detail.status == 1)"
							name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					是否开票：
				</view>
				<view class="group-content">
					<view class="text-content">
						<u-switch :disabled="detail.status != 0 && detail.status != 1" v-model="invoiceType"
							active-color="#3C8BDB" size="28">
						</u-switch>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					是否云视频：
				</view>
				<view class="group-content">
					<view class="text-content">
						<u-switch :disabled="detail.status != 0 && detail.status != 1" v-model="is_video"
							active-color="#3C8BDB" size="28">
						</u-switch>
					</view>
				</view>
			</view>

			<!-- 样品信息 -->
			<view class="list">
				<view class="item" v-for="(item, index) in childsyp" :key="index">
					<view class="item-row">
						<text>样品信息-数量：{{ item.sample_num || 0 }}</text>
					</view>
					<view class="item-row">
						<text>样品名称/类型：{{ item.sample_name || '' }}</text>
					</view>
					<view class="item-row">
						<text>主要成分：{{ item.main_component || '' }}</text>
					</view>
					<view class="item-row">
						<text>是否含磁：{{ item.is_magnetic == 0 ? '是' : '否'}}</text>
					</view>
					<view class="item-row">
						<text>是否喷金：{{ item.is_gold_spraying == 0 ? '是' : '否'}}</text>
					</view>
					<view class="item-row">
						<text>{{ item.sampleAttributeManageList[0].sttribute_name || '' }}：{{item.sampleAttributeManageList[0].attributeListsanji[0].sttribute_name || ''}}</text>
					</view>
				</view>
			</view>

			<!-- 子订单 -->
			<view class="group child-order" style="margin-bottom: 0;" v-for="(item, index) in childOrderList"
				:key="index">
				<view class="group-item">
					<view class="group-label">
						产品名称：
					</view>
					<view class="group-content">
						<view class="text-content" @click="chooseProduct(item.newAdd, index)">
							{{ item.goods_name? item.goods_name : '请选择产品名称' }}
							<u-icon size="28" v-if="item.newAdd" name="arrow-right"></u-icon>
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						产品型号：
					</view>
					<view class="group-content">
						<view class="text-content" @click="chooseProductModel(item, index)">
							{{ item.goods_spec? item.goods_spec : '请选择产品型号' }}
							<u-icon v-if="detail && (detail.status == 0 || detail.status == 1)" size="28"
								name="arrow-right"></u-icon>
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						产品品牌：
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ item.goodsBrandName? item.goodsBrandName : '请选择产品品牌' }}
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						数量：
					</view>
					<view class="group-content">
						<view class="text-content">
							<input :disabled="isNum && detail.status != 0 && detail.status != 1" @input="getTotal(true)"
								class="child-order-input" type="digit" v-model.number.lazy="item.goods_nums" set
								placeholder="请输入数量">
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						设备名称：
					</view>
					<view class="group-content">
						<view class="text-content" @click="experimentName(item, index)">
							{{ item.names  ? item.names : '请选择设备名称' }}
							<u-icon v-if="detail && (detail.status == 0 || detail.status == 1)" size="28"
								name="arrow-right"></u-icon>
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						实验测试分类：
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ item.experiment_class_name? item.experiment_class_name : '暂无' }}
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						实际测试金额：
					</view>
					<view class="group-content">
						<view class="text-content">
							<input :disabled="detail.status != 0 && detail.status != 1" class="child-order-input"
								@input="getTotal" type="text" v-model.lazy="item.goods_price">
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						标准测试金额：
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ item.reference_price? (item.reference_price).toFixed(2) : '0.00' }}
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						样品信息：
					</view>
					<!-- <view class="group-content">
						<view class="text-content">
							{{ item.sample_id? item.sample_id : '0.00' }}
						</view>
					</view> -->
					<view class="group-content">
						<view class="text-content" @click="sampleName(item, index)">
							{{ item.sample_name  ? item.sample_name : '请选择样品信息' }}
							<u-icon v-if="detail && (detail.status == 0 || detail.status == 1)" size="28"
								name="arrow-right"></u-icon>
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						总价：
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ (item.goods_nums * Number(item.goods_price)).toFixed(2) == 'NaN' ? '0.00' : (item.goods_nums * Number(item.goods_price)).toFixed(2) }}
						</view>
					</view>
				</view>
				<view class="group-item" style="padding: 15rpx 10rpx;"
					v-if="detail && (detail.status == 0 || detail.status == 1)">
					<view class="group-label">
						操作：
					</view>
					<view class="group-content">
						<view class="confirm1" v-if="index == childOrderList.length - 1" @click="addFn">
							新&nbsp;增
						</view>
						<view class="confirm1" v-if="childOrderList.length != 1" @click="deleteFn(index)">
							删&nbsp;除
						</view>
					</view>
				</view>

			</view>


			<view class="btnBox" v-if="detail.status == 0 || detail.status == 1">
				<view class="confirm" @click="submitData">
					保&nbsp;存
				</view>
				<view class="confirm" @click="saveExpGoodsFn">
					新增产品
				</view>
				<view class="confirm" @click="saveExpProjectFn">
					新增实验项目
				</view>
				<view class="confirm" @click="cancelConsultFn">
					取消咨询
				</view>
				<view class="confirm" @click="saveOrderFn">
					生成订单
				</view>
			</view>



			<!-- 公用弹框-完整数据 -->
			<popup-bottom :show.sync="showcheckBox" :list.sync="checkBoxList" :title="checkBoxTitle"
				:showKey="checkBoxKeyName" @getValue="confirmValue"></popup-bottom>


			<!-- 公用弹框-分页加载 -->
			<popup-bottom :loadable="true" :loading="productLoading" :is-refresh.sync="productIsRefresh"
				:show.sync="showDynamicPopup" :list.sync="productList" title="选择产品" showKey="goods_name"
				@getMoreOrSearch="getGoodsList" @getValue="confirmProduct" :page.sync="productPage"></popup-bottom>

			<!-- 分页加载-获取设备名称 -->
			<popup-bottom :loadable="true" :loading="testLoading" :is-refresh="testIsRefresh"
				:show.sync="showTestProjectPopup" :list.sync="testList" title="选择设备名称" show-key="name"
				@getMoreOrSearch="getTestProjectList" @getValue="confirmTestProject"
				:page.sync="testPage"></popup-bottom>



			<!-- 分页加载-样品信息 -->
			<popup-bottom :loadable="true" :loading="sampleLoading" :is-refresh="sampleIsRefresh"
				:show.sync="sampleProjectPopup" :list.sync="sampleList" title="选择样品信息" show-key="sample_name"
				@getMoreOrSearch="getsampleProjectList" @getValue="confirmsample"
				:page.sync="samplePage"></popup-bottom>

			<!-- 仅适用于选择产品型号 -->
			<popup-bottom :show.sync="showChooseProductModel" :list.sync="productModelList" title="选择型号"
				@getValue="confirmProductModel"></popup-bottom>

			<!-- 选择日期 -->
			<u-calendar btn-type="warning" @change="confirmDate" max-date="2222-01-01"
				active-bg-color="#3C8BDB !important" v-model="showCalendar" mode="date"></u-calendar>


			<!-- 添加子订单图标 -->
			<!-- <view class="add-order"
			@click="showDynamicPopup = true, currentSelectedChildOrderIndex = childOrderList.length">
			<image src="@/static/add.png" mode=""></image>
		</view> -->

			<!-- 分成信息 -->
			<!-- <devide-into :cbUnit="false" :showMl="true" :showCb="true" :cb="cb" :ml="ml" :backUpList="cbList"
			:show.sync="showDevideInfo" @confirmDevideList="confirmDevideInfo"></devide-into> -->

			<u-toast ref="uToast" />
		</view>
	</view>
</template>

<script>
	// 弹框组件
	import popupBottom from '../popupBottom.vue'
	// import devideInto from '../devideInto.vue'
	// import uploadProgress from '../uploadProgress'
	import {
		consultDetail,
		queryAll3,
		addressList,
		accountList,
		updateConsult,
		saveOrder,
		cancelConsult,
		submitExperimentGoods,
		sbList,
		querySampleList
	} from '@/api/reservationList.js'
	import {
		// 详情
		fetchEditTestOrderDetailApi,
		// 采购人员列表/销售主管列表
		fetchBunListApi,
		// 税率
		fetchTaxRateListApi,
		// 付款方式
		fetchPurchasePayWayApi,
		// 所属公司列表
		fetchCompanyListApi,
		// 发票
		fetchInvoiceTypeListApi,
		// 客户列表
		fetchClientListApi,
		// 产品列表
		fetchTestSubGoodsListApi,
		// 根据所选sku获取价钱
		fetchPriceApi,
		// 提交编辑功能
		saveTestOrderApi,
		// 获取测试实验项目
		fetchTestProductGoodsListApi,
		// 新增实验订单
		addTestOrderApi,
		// 订单类型
		queryAll
	} from '@/api/index.js'
	export default {
		components: {
			popupBottom,
			// devideInto,
			// uploadProgress
		},
		data() {
			return {
				orderTypeList: [{
						id: 1,
						name: '分包订单'
					},
					{
						id: 2,
						name: '实验订单'
					},
				],
				testAddressList: [],
				companyAccountList: [],
				test_address: null,
				company_account: null,
				classNameList: [],
				className: null,
				classId: null,
				id: '',
				detail: null,
				// 采购人员
				purchasePersonnelId: -1,
				// 采购主管id
				purchaseBossId: -1,
				// 客户id
				clientId: -1,

				// 所属公司id
				companyId: -1,

				// 总价,可以修改的
				totalPrice: 0,
				// 不可修改的，用来比较
				disabledTotalPrice: 0,
				sampleList: [],
				// 发票类型ID
				invoiceId: -1,

				// 付款ID
				payId: -1,

				// 币种
				currencyId: -1,

				// 税率
				taxeId: -1,

				// 是否开票
				invoiceType: false,

				// 样品回收
				reverso_context: false,

				// 禁用开关
				disabledSwitch: false,

				// 日历开关
				showCalendar: false,

				// 给那个值设置日历
				setDateForKey: '',

				// 下单时间
				collection_time: '',
				// 发货时间
				delivery_time: '',

				// 备注
				msg: '',

				// 子订单列表
				childOrderList: [],


				// 币种列表
				currencyList: [{
						id: 1,
						label: '人民币'
					},
					{
						id: 2,
						label: '美元'
					}
				],
				// 客户列表
				clientList: [],
				// 发票列表
				invoiceList: [],
				// 所属公司列表
				companyList: [],
				// 付款列表
				payList: [],
				// 税率列表
				taxRateList: [],
				// 采购人员列表
				purchasePersonnelList: [],
				// 销售主管列表
				saleBossList: [],

				// 付款时间列表
				payDateList: [],

				// 订单资料列表
				files: [],


				checkBoxTitle: '',
				showcheckBox: false,
				checkBoxList: [],
				checkBoxKeyName: '',
				checkEchoKey: '',



				// 此处的执行索引可以优化，通过冒泡设置当前选中的订单
				// 显示动态弹框
				showDynamicPopup: false,
				// 产品列表
				productList: [],
				productPage: 1,
				productIsRefresh: true,
				productLoading: false,




				// 选择产品型号
				showChooseProductModel: false,
				// 产品型号列表
				productModelList: [],
				currentSelectedChildOrderIndex: -1,

				// 当前的编辑订单是否是审核之后的编辑
				isDisabled: false,




				// 获取实验项目列表
				showTestProjectPopup: false,

				sampleProjectPopup: false,
				testLoading: false,
				sampleLoading: false,
				testIsRefresh: true,
				sampleIsRefresh: false,
				testList: [],
				testPage: 1,
				samplePage: 1,
				mlList: [],
				ml: [],
				cbList: [],
				cb: [],
				showDevideInfo: false,
				queryAllList: [],
				order_type: '',
				isNum: false,
				send_address: '',
				addressee_name: '',
				addressee_mobile: '',
				childsyp: [],
				is_video: false,
				experimentList: [],
				experimentId: null,
				syuser_id: '',
				zcMobile: ''
			}
		},
		onLoad(options) {
			let {
				id
			} = options

			let title = '预约详情'

			uni.setNavigationBarTitle({
				title
			})

			// 获取一些必要的基本数据
			const rquestArr = [this.getPurchaseCompanyList(), this.getInvoiceList(), this.getCompanyList(),
				this.getPayList(), this.getTaxRateList(), this.getpurchasePersonnelList(1), this
				.getpurchasePersonnelList(-1), this.queryAllFn(),
			]
			this.isNum = false
			if (id) {
				this.id = id
				this.getDetail()
			}
			Promise.all(rquestArr).catch(err => {
				this.$tip2('数据拉取失败')
			})
			queryAll3(3).then(res => {
				this.classNameList = res.obj
			})
			// 实验测试地址
			addressList().then(res => {
				res.obj.forEach(item => {
					item.name = item.true_name + ' ' + item.mobile + ' ' + item.address
				})
				this.testAddressList = res.obj
			})
			// 公司汇款账户
			accountList().then(res => {
				res.obj.forEach(item => {
					item.name = item.company_name + ' ' + item.bankCardNum + ' ' + item.bank
				})
				this.companyAccountList = res.obj
			})
		},
		onShow() {
			this.testList = []
			this.testPage = 1
			this.getTestProjectList()

			this.productList = []
			this.productPage = 1
			this.getGoodsList()
		},
		methods: {
			addFn() {
				this.childOrderList.push({
					newAdd: true,
					goods_id: '',
					goods_spec: '',
					goods_nums: 1,
					experiment_project_id: '',
					experiment_project_name: '',
					experiment_class_id: '',
					experiment_class_name: '',
					goods_price: '0.00',
					reference_price: '',
					sample_id: '',
				})
			},
			deleteFn(index) {
				this.childOrderList.splice(index, 1)
			},
			// 获取订单类型
			queryAllFn() {
				queryAll().then(res => {
					this.queryAllList = res.obj
				})
			},
			// 获取总值
			getTotal(num) {
				let total = 0
				let arr = JSON.parse(JSON.stringify(this.childOrderList))
				arr.forEach(e => {
					if (num) {
						let data = e.goods_nums.toString().split(".")[1]
						let data2 = e.goods_nums.toString().split(".")[0]
						let str = Number(data2)
						if (data) {
							if (data.length == 1) {
								str = Number(data2) + Number('0.' + data)
							} else {
								str = Number(data2) + Number('0.' + data[0])
							}
						}
						e.goods_nums = str
						total += str * Number(e.goods_price);
					} else {
						total += e.goods_nums * Number(e.goods_price);
					}
				})
				this.$nextTick(() => {
					this.childOrderList = arr
				})
				this.disabledTotalPrice = this.totalPrice = total
			},

			// 确定分成信息
			// 校验数据
			// 关闭弹框
			confirmDevideInfo({
				ml = [],
				cb = []
			}) {
				let total = 0
				ml.forEach(e => {
					if (!this.$isTrue(e.scale) || !e.userName) {
						this.$tip('分成人员和分成比例不能为空')
						throw new Error('')
					} else {
						total += e.scale - 0
					}
				})

				if (total !== 100) {
					return this.$tip('毛利分成比例总和必须是100%')
				}

				total = 0
				cb.forEach(e => {
					if (!this.$isTrue(e.scale) || !e.userName) {
						this.$tip('分成人员和分成比例不能为空')
						throw new Error('')
					} else {
						total += e.scale - 0
					}
				})
				this.ml = ml
				this.cb = cb

				this.showDevideInfo = false
			},


			// 确定实验项目
			confirmTestProject(e) {
				console.log(e, 'eeeee')
				let {
					// 项目名称
					project_name,
					// 分类名称
					class_name,
					// 测试金额
					test_price,
					id,
					class_id
				} = e

				this.childOrderList[this.currentSelectedChildOrderIndex]['experiment_project_name'] = project_name
				this.childOrderList[this.currentSelectedChildOrderIndex]['experiment_class_name'] = class_name
				this.childOrderList[this.currentSelectedChildOrderIndex]['experiment_class_id'] = class_id
				this.childOrderList[this.currentSelectedChildOrderIndex]['names'] = project_name + ` (${class_name})`
				this.childOrderList[this.currentSelectedChildOrderIndex]['goods_price'] = (test_price).toFixed(2)
				this.childOrderList[this.currentSelectedChildOrderIndex]['reference_price'] = test_price
				this.childOrderList[this.currentSelectedChildOrderIndex]['experiment_project_id'] = id
				this.getTotal()
				this.getTotal(true)
				this.showTestProjectPopup = false
			},
			confirmsample(e) {
				this.childOrderList[this.currentSelectedChildOrderIndex]['sample_name'] = e.sample_name
				this.childOrderList[this.currentSelectedChildOrderIndex]['sample_id'] = e.id
				this.sampleProjectPopup = false
			},

			// 获取实验项目
			getTestProjectList(project_name = '') {
				console.log('666666')
				this.testLoading = true

				sbList({
					draw: '1',
					start: (this.testPage - 1) * 10,
					length: '10',
					project_name
				}).then(res => {
					this.testPage++
					if (!res.error) {
						if (res.data.length !== 10) {
							this.testIsRefresh = false
						}
						res.data.forEach(item => {
							let name1 = ''
							let name2 = ''
							if (item.project_name) name1 = item.project_name
							if (item.class_name) name2 = ` (${item.class_name})`
							item.name = name1 + name2
						})
						this.testList = [...this.testList, ...res.data]
					} else {
						this.$tip(res.error)
					}
				}).finally(_ => {
					this.testLoading = false
				})
			},
			getsampleProjectList() {
				this.sampleLoading = true
				querySampleList({
					consultId: this.detail.id
				}).then(res => {
					this.sampleList = res.obj
				}).finally(_ => {
					this.sampleLoading = false
				})
				console.log(this.sampleList, 'this.sampleList')
			},

			// 提交数据
			submitData() {
				let obj = {
					id: this.detail.id,
					class_id: this.classId,
					userName: this.detail.userName,
					mobile: this.detail.mobile,
					company_name: this.detail.company_name,
					content: this.detail.content,
					remark: this.detail.remark,
					syUserName: this.detail.syUserName,
					supplier_name: this.companyId == -1 ? '' : this.companyId + '',
					sale_manager: this.purchaseBossId,
					delivery_time_str: this.delivery_time,
					collection_time_str: this.collection_time,
					order_type: this.order_type,
					send_address: this.detail.send_address,
					reverso_context: this.reverso_context ? 'ON' : 'OFF',
					addressee_name: this.detail.addressee_name,
					addressee_mobile: this.detail.addressee_mobile,
					test_address_id: this.test_address,
					company_account_id: this.company_account,
					invoiceType: this.invoiceType ? 'ON' : 'OFF',
					is_video: this.is_video ? 1 : 0,
					// childsyp:JSON.parse(JSON.stringify(this.childsyp)),
					// childOrderList:JSON.parse(JSON.stringify(this.childOrderList))
				}
				var flagnum = true;
				for (var i = 0; i < this.childOrderList.length; i++) {
					var divId = this.childOrderList[i].goods_nums;
					var reg = /(^[1-9]\d*(\.\d{1})?$)|(^0(\.\d{1})?$)/;
					if (!reg.test(divId)) {
						flagnum = false;
						break;
					}
				}
				if (!flagnum) return this.$tip('数量不能为空或填写错误（小数点后一位）!');

				// 判断订单总价与所有产品价格总和是否相等
				var goodsTotalP = 0;
				var goodsTotalNum = 0;
				for (var i = 0; i < this.childOrderList.length; i++) {
					var goodsPrice = Number(this.childOrderList[i].goods_price)
					var goodsNums = this.childOrderList[i].goods_nums
					goodsTotalP += parseFloat(goodsPrice) * parseFloat(goodsNums);
					goodsTotalNum += parseFloat(goodsNums);
				}
				goodsTotalP = parseFloat(goodsTotalP).toFixed(2);
				goodsTotalNum = parseFloat(goodsTotalNum).toFixed(1);
				obj.totalPrice = goodsTotalP;
				obj.goods_amount = goodsTotalNum;

				var formData = obj;
				var goodsData = this.getAllAddGoods();
				var dataAry = new Array();
				dataAry.push(formData);
				if (this.syuser_id == "" || this.syuser_id == "null") return this.$tip("所属公司没有关联账号,请去所属公司管理里进行关联");

				// var syUserId = $("#syuser_id").val();
				// if(syUserId==""||syUserId=="null") return this.$tip('所属公司没有关联账号,请去所属公司管理里进行关联');

				let canshu = dataAry.concat(goodsData);
				updateConsult(canshu).then(res => {
					if (res.res) {
						this.$tip('保存成功')
						setTimeout(() => {
							uni.navigateBack();
						}, 1500)
					}else{
						this.$tip(res.resMsg)
					}
				})
			},
			// 新增产品
			saveExpGoodsFn() {
				uni.navigateTo({
					url: '/pagesB/reservationDetial/saveExpGoods?id=' + this.detail.id
				})
			},
			// 新增实验项目
			saveExpProjectFn() {
				uni.navigateTo({
					url: '/pagesB/reservationDetial/saveExpProject?id=' + this.detail.id
				})
			},
			// 取消咨询
			cancelConsultFn() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定取消？',
					success(res) {
						if (res.confirm) {
							cancelConsult({
								id: that.detail.id
							}).then(res => {
								if (res.res) {
									that.$tip('取消成功！')
									setTimeout(() => {
										uni.navigateBack();
									}, 1500)
								}
							})
						}
					}
				})

			},
			// 生成订单
			saveOrderFn() {
				let obj = {
					id: this.detail.id,
					class_id: this.classId,
					userName: this.detail.userName,
					mobile: this.detail.mobile,
					company_name: this.detail.company_name,
					content: this.detail.content,
					remark: this.detail.remark,
					syUserName: this.detail.syUserName,
					supplier_name: this.companyId == -1 ? '' : this.companyId + '',
					sale_manager: this.purchaseBossId,
					delivery_time_str: this.delivery_time,
					collection_time_str: this.collection_time,
					order_type: this.order_type,
					send_address: this.detail.send_address,
					reverso_context: this.reverso_context ? 'ON' : 'OFF',
					addressee_name: this.detail.addressee_name,
					addressee_mobile: this.detail.addressee_mobile,
					test_address_id: this.test_address,
					company_account_id: this.company_account,
					invoiceType: this.invoiceType ? 'ON' : 'OFF',
					is_video: this.is_video ? '1' : '0',
					zxcontent: this.detail.content
				}
				var flagnum = true;
				for (var i = 0; i < this.childOrderList.length; i++) {
					var divId = this.childOrderList[i].goods_nums;
					var reg = /(^[1-9]\d*(\.\d{1})?$)|(^0(\.\d{1})?$)/;
					if (!reg.test(divId)) {
						flagnum = false;
						break;
					}
				}
				console.log(this.companyId,'this.companyId')
				if(!this.companyId || this.companyId == -1 || this.companyId == null) return this.$tip('请选择所属公司！');
				if (!flagnum) return this.$tip('数量不能为空或填写错误（小数点后一位）!');
				if (!this.order_type) return this.$tip('请选择生成订单类型!');
				if (this.childOrderList.length < 1) return this.$tip('实验分包订单至少选择一个产品才可提交!');

				// 判断订单总价与所有产品价格总和是否相等
				var goodsTotalP = 0;
				var goodsTotalNum = 0;
				for (var i = 0; i < this.childOrderList.length; i++) {
					var goodsPrice = Number(this.childOrderList[i].goods_price)
					var goodsNums = this.childOrderList[i].goods_nums
					goodsTotalP += parseFloat(goodsPrice) * parseFloat(goodsNums);
					goodsTotalNum += parseFloat(goodsNums);
				}
				goodsTotalP = parseFloat(goodsTotalP).toFixed(2);
				goodsTotalNum = parseFloat(goodsTotalNum).toFixed(1);
				obj.totalPrice = goodsTotalP;
				obj.goods_amount = goodsTotalNum;

				var formData = obj;
				var goodsData = this.getAllAddGoods();



				if (this.zcMobile == "") this.$tip('该用户未注册，请联系用户注册会员!');
				if (this.zcMobile != this.detail.mobile) this.$tip('请修改手机号为注册手机号!');

				var ypAry = new Array();
				this.childsyp.forEach(item => {
					ypAry.push(item.id)
				})

				let go = true
				for (var i = 0; i < goodsData.length; i++) {
					for (const key in goodsData[i]) {
						if(key != 'sample_id'){
							if(goodsData[i][key] == '' || goodsData[i][key] == null) {
								go = false
							}
						}
					}
				}
				if (!go) return this.$tip('请补充产品信息后再提交！');


				var ypflag0 = true;
				for (var y = 0; y < ypAry.length; y++) {
					var ypflag = false;
					for (var i = 0; i < goodsData.length; i++) {
						if (ypAry[y] == goodsData[i].sample_id) {
							ypflag = true;
						}
					}
					if (!ypflag) {
						ypflag0 = false;
						break;
					}
				}
				if (!ypflag0) return this.$tip('产品列表未关联所有的样品信息!');


				let dataAry = new Array();
				dataAry.push(formData);
				if (this.syuser_id == "" || this.syuser_id == null) return this.$tip("所属公司没有关联账号,请去所属公司管理里进行关联");

				var canshu = dataAry.concat(goodsData);
				saveOrder(canshu).then(res => {
					if (res.res) {
						this.$tip('生成成功')
						setTimeout(() => {
							uni.navigateBack();
						}, 1500)
					}else{
						this.$tip(res.resMsg)
					}
				})
			},
			// 数据处理
			getAllAddGoods() {
				var goodsData = new Array();
				for (var i = 0; i < this.childOrderList.length; i++) {
					var goods = {};
					var goodsId = this.childOrderList[i].goods_id
					var goodSpec = this.childOrderList[i].goods_spec
					var goodNums = this.childOrderList[i].goods_nums
					var experiment_project_id = this.childOrderList[i].experiment_project_id
					var experiment_project_name = this.childOrderList[i].experiment_project_name
					var experiment_class_id = this.childOrderList[i].experiment_class_id
					var experiment_class_name = this.childOrderList[i].experiment_class_name
					var goodsPrice = Number(this.childOrderList[i].goods_price)
					var bzcsj = this.childOrderList[i].reference_price
					var sample_id = this.childOrderList[i].sample_id

					goods.goods_id = goodsId;
					goods.goods_spec = goodSpec;
					goods.goods_nums = goodNums;
					goods.experiment_project_id = experiment_project_id;
					goods.experiment_project_name = experiment_project_name;
					goods.experiment_class_id = experiment_class_id;
					goods.experiment_class_name = experiment_class_name;
					goods.goods_price = goodsPrice;
					goods.reference_price = bzcsj;
					goods.sample_id = sample_id;
					goodsData.push(goods);
				}
				return goodsData;
			},

			// 删除新增子订单
			deleteChildOrder(index) {
				if (this.childOrderList.length == 1) return this.$tip('最后一个子订单不能删除')
				let that = this
				uni.showModal({
					title: "提示",
					content: '您确定删除该订单吗？',
					success(e) {
						if (e.confirm) {
							that.childOrderList.splice(index, 1)
							that.getTotal()
							that.getTotal(true)
						}
					}
				})
			},

			// 确定产品型号
			confirmProductModel(e) {
				this.childOrderList[this.currentSelectedChildOrderIndex].goods_spec = e
				this.childOrderList[this.currentSelectedChildOrderIndex].goods_nums = 1
				this.showChooseProductModel = false
			},

			// 设备名称
			experimentName(item, index) {
				if (this.detail.status != 0 && this.detail.status != 1) return
				this.currentSelectedChildOrderIndex = index
				this.showTestProjectPopup = true
			},

			// 样品信息
			sampleName(item, index) {
				if (this.detail.status != 0 && this.detail.status != 1) return
				// if(this.childsyp.length > 0) this.consultId = this.childsyp[index].consult_id
				this.currentSelectedChildOrderIndex = index
				this.sampleProjectPopup = true
			},

			// 选择产品型号
			chooseProductModel(item, currentSelectedChildOrderIndex) {
				if (this.detail.status != 0 && this.detail.status != 1) return
				this.currentSelectedChildOrderIndex = currentSelectedChildOrderIndex
				console.log(item, 'item')
				if (item.id) {
					// 添加时的修改
					if (item.expGoods.goods_model == '') {
						this.productModelList = []
					} else {
						this.productModelList = item.expGoods.goods_model.split(',')
					}

				} else {
					this.productModelList = []
					item.goodsSpecList.forEach(subItem => {
						if (subItem) this.productModelList.push(subItem)
					})
					// this.productModelList = item.goodsSpecList
				}
				this.showChooseProductModel = true
			},

			// 确定产品
			confirmProduct(e) {
				let {
					id,
					goods_name,
					goods_model,
					goods_brand_name,
					goods_brand_id,
				} = e

				let obj = {
					goods_id: id,
					newAdd: true,
					goods_name: goods_name,
					// 型号
					goodsSpec: '',
					goodsSpecList: goods_model.split(','),
					// 品牌名称
					goodsBrandName: goods_brand_name,
					goodsBrandId: goods_brand_id,
					goods_nums: 1,
					// 实验测试项目名称
					experiment_project_name: '',
					// 实验测试分类名称
					experiment_class_name: '',
					experiment_class_id: '',
					experiment_project_id: '',
					// 实际测试金额
					goodsPrice: 0,
					// 标准测试金额
					reference_price: 0
				}

				this.$set(this.childOrderList, this.currentSelectedChildOrderIndex, obj)
				this.showDynamicPopup = false
			},

			// 选择产品
			chooseProduct(isNew, index) {
				if (this.detail.status != 0 && this.detail.status != 1) return
				if (!isNew) return
				this.currentSelectedChildOrderIndex = index
				this.showDynamicPopup = true
			},

			// 删除
			deleteFile(id, index) {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定删除该资料吗？',
					success(e) {
						if (e.confirm) {
							that.files.splice(index, 1)
						}
					}
				})
			},

			// 预览
			preImage(index) {
				let list = this.files.map(item => item.path + '/' + item.name)
				this.$preFile(index, list)
			},


			// 上传订单资料
			uploadFile() {
				this.$uploadFile2(this.$refs['prg']).then(res => {
					this.files.push(res)
				})
			},

			// 获取子订单
			getGoodsList(keyWord = '') {
				this.productLoading = true

				fetchTestSubGoodsListApi({
					draw: '1',
					start: (this.productPage - 1) * 10,
					length: '10',
					goods_name: keyWord,
				}).then(res => {
					this.productPage++
					if (!res.error) {
						if (res.data.length != 10) this.productIsRefresh = false
						this.productList = [...this.productList, ...res.data]
					} else {
						this.$tip(res.error)
					}
				}).finally(_ => {
					this.productLoading = false
				})
			},


			// 设置key，并打开日历选择器
			chooseDate(keyName) {
				if (this.detail.status != 0 && this.detail.status != 1) return
				this.setDateForKey = keyName
				this.showCalendar = true
			},

			// 确定时间
			confirmDate(e) {
				if (isNaN(this.setDateForKey)) {
					// 下单时间，发货时间
					this[this.setDateForKey] = e.result
				} else {
					// 预计付款时间
					this.payDateList[this.setDateForKey] = e.result
				}
			},

			// 发票开关
			invoiceSwitch(e) {
				if (!e) {
					this.invoiceId = -1
					this.taxeId = -1
				}
			},
			// 样品回收开关
			reversoSwitch(e) {
				if (!e) {
					this.send_address = ''
					this.addressee_name = ''
					this.addressee_mobile = ''
				}
			},


			// 根据id获取值并回显
			// 数组名称，展示的名称，组件内的哪个值跟对象里的哪个值比较
			// 默认比较id
			swapIdgetValue(listName, echoName, componentKey) {
				let result = this[listName].find(e => e['id'] == this[componentKey])
				if (result) {
					return result[echoName]
				} else {
					return '请选择'
				}
			},

			// 确定值
			confirmValue(e) {
				if (this.checkEchoKey == 'companyId'){
					this.syuser_id = e.syuser_id
				}
				this[this.checkEchoKey] = e.id
				if (this.checkEchoKey == 'payId') {
					this.payDateList = new Array(e.nums).fill('')
				}
				console.log(e, 'eeeeeeee')
				console.log(this[this.checkEchoKey], 'checkEchoKey')
				this.showcheckBox = false
			},

			// 选择
			select(keyName, listName, titleName, echoKey) {
				if (this.detail.status != 0 && this.detail.status != 1) return
				// 选择框标题
				this.checkBoxTitle = titleName
				// 选择框中数组展示的key
				this.checkBoxKeyName = keyName

				// 回显key
				this.checkEchoKey = echoKey

				this.checkBoxList = this[listName]

				this.showcheckBox = true
			},

			// 获取详情
			getDetail() {
				consultDetail({
					id: this.id
				}).then(res => {
					if (res.res) {
						this.detail = res.obj.consult
						this.zcMobile = res.obj.zcMobile
						this.purchaseBossId = this.detail.purchaseBossId
						this.company_account = this.detail.company_account_id
						this.test_address = this.detail.test_address_id
						this.reverso_context = this.detail.reverso_context == 1 ? true : false
						this.invoiceType = this.detail.invoiceType == 1 ? true : false
						this.is_video = this.detail.is_video == 1 ? true : false
						this.companyId = this.detail.supplier_name
						this.purchaseBossId = this.detail.sale_manager
						this.order_type = this.detail.order_type
						this.collection_time = this.detail.collection_time_str
						this.delivery_time = this.detail.delivery_time_str
						this.className = res.obj.className
						this.classId = res.obj.classId
						this.childsyp = res.obj.childsyp
						this.files = res.obj.files
						this.syuser_id = res.obj.consult.sale_manager
						res.obj.childs.forEach(item => {
							// const sampleData = this.sampleList.find(e=>e.id == item.sample_id)
							// if(sampleData) item.sample_name = sampleData.sample_name
							item.goodsBrandName = item.goods_brand_name
							item.names = item.experiment_project_name + ` (${item.experiment_class_name})`
							item.goods_price = (item.goods_price).toFixed(2)

							querySampleList({
								consultId: item.consult_id
							}).then(ok => {
								ok.obj.forEach(e => {
									if (e.id == item.sample_id) {
										item.sample_name = e.sample_name
									}
								})
							})
						})

						this.childOrderList = res.obj.childs

						if (this.childOrderList.length == 0) {
							this.childOrderList = [{
								newAdd: true,
								goods_id: '',
								goods_spec: '',
								goods_nums: 1,
								experiment_project_id: '',
								experiment_project_name: '',
								experiment_class_id: '',
								experiment_class_name: '',
								goods_price: '0.00',
								reference_price: '',
								sample_id: '',
							}]
						}
						console.log(this.detail, 'this.detail')
						return
						// this.detail['mainData'] = this.detail['of']
						// delete this.detail['of']

						let {
							mainData: {
								sale_user,
								sale_manager,
								supplier_name,
								totalPrice,
								company,
								pay_way,
								currency_type,
								taxes,
								outBillType,
								invoiceType,
								reverso_context,
								send_address,
								addressee_name,
								addressee_mobile,
								// 收款时间
								collection_time,
								// 发货时间
								delivery_time,
								msg,
								order_status,
								parentOf
							},
							collectionTimes,
							files,
							childs,
							scaleList,
							salecbscaleList,
							isDisabled
						} = this.detail
						if (this.detail.order_status == 5 || this.detail.order_status == 10 || this.detail
							.order_status == 20) {
							this.isNum = true
						} else {
							this.isNum = false
						}
						this.collection_time = this.$alterTime(collection_time, false)
						this.delivery_time = this.$alterTime(delivery_time, false)
						this.payDateList = collectionTimes
						this.files = files
						this.send_address = send_address
						this.addressee_name = addressee_name
						this.addressee_mobile = addressee_mobile
						this.msg = msg

						this.ml = scaleList || []
						this.cb = salecbscaleList

						this.childOrderList = childs

						// 采购人员id
						if (sale_user) {
							this.purchasePersonnelId = sale_user
						}

						// 销售主管
						if (sale_manager) {
							this.purchaseBossId = sale_manager
						}

						// 客户
						if (company) {
							this.clientId = company.id
						}

						// 所属公司
						if (supplier_name) {
							this.companyId = supplier_name - 0
						}

						// 总价
						this.totalPrice = totalPrice

						// 付款方式
						if (pay_way) {
							this.payId = pay_way
						}

						// 币种
						if (currency_type) {
							this.currencyId = currency_type
						}

						// 发票
						if (outBillType) {
							this.invoiceId = outBillType.id
						}

						// 防止税率为0
						let id = this.taxRateList.find(e => e.taxValue == taxes).id
						this.taxeId = id

						// 是否开票
						this.invoiceType = invoiceType == 1 ? true : false

						// 样品回收
						this.reverso_context = reverso_context == 1 ? true : false
						// 审核之后的编辑不允许修改采购类别和订单币种
						// if (order_status != 5 && order_status != 10 && order_status != 20) {
						// 	this.isDisabled = true
						// }
						this.isDisabled = isDisabled

					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			// 获取客户列表
			getPurchaseCompanyList() {
				fetchClientListApi().then(res => {
					if (res.res) {
						this.clientList = res.obj
					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			//  获取发票
			getInvoiceList() {
				fetchInvoiceTypeListApi({
					type: 1
				}).then(res => {
					if (res.res) {
						this.invoiceList = res.obj
					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			// 获取所属公司列表
			getCompanyList() {
				fetchCompanyListApi({
					userType: 6
				}).then(res => {
					if (res.res) {
						this.companyList = res.obj
					} else {
						this.$tip(res.resMsg)
					}
				})
			},


			// 获取付款列表
			getPayList() {
				fetchPurchasePayWayApi().then(res => {
					if (res.res) {
						this.payList = res.obj
					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			// 获取税率
			getTaxRateList() {
				fetchTaxRateListApi().then(res => {
					if (res.res) {
						this.taxRateList = res.obj
					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			// 获取采购人员列表/销售主管列表
			getpurchasePersonnelList(type) {
				fetchBunListApi({
					type
				}).then(res => {
					if (res.res) {
						// 采购人员,分成人员
						if (type == -1) {
							this.purchasePersonnelList = this.mlList = this.cbList = res.obj
						} else {
							this.saleBossList = res.obj
						}
					} else {
						this.$tip(res.resMsg)
					}
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
	.btnBox {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		border-top: 1px #ccc solid;
		padding: 20rpx 0;
	}

	.btnBox1 {
		display: flex;
		border-top: 1px #ccc solid;
	}

	.child-order-input {
		text-align: right;
	}

	.files-list {
		.file-item {
			display: flex;
			justify-content: space-between;
			align-items: center;

			view {
				color: $primary;
				width: 500rpx;
			}

			image {
				width: 35rpx;
				height: 35rpx;
			}
		}
	}

	.confirm1 {
		// width: 130rpx;
		height: 60rpx;
		border-radius: 30rpx;
		text-align: center;
		line-height: 60rpx;
		color: #FFF;
		background-color: #1e9fff;
		margin: 5rpx 10rpx;
		padding: 0px 50rpx;
	}

	.confirm {
		// width: 130rpx;
		height: 65rpx;
		border-radius: 30rpx;
		text-align: center;
		line-height: 65rpx;
		color: #FFF;
		background-color: $primary;
		margin: 10rpx auto;
		padding: 0px 50rpx;
	}


	.add-order {
		position: fixed;
		right: 50rpx;
		bottom: 50rpx;
		z-index: 2;
		width: 80rpx;
		height: 80rpx;
		background-color: #fff;
		border-radius: 50%;

		image {
			width: 100%;
			height: 100%;
		}
	}


	.child-order {
		margin: 50rpx 20rpx 20rpx;
		border-top: 1rpx #ccc solid;

		.group-hint {
			display: flex;
			justify-content: space-between;
		}
	}

	textarea {
		border: 1rpx solid #999;
		border-radius: 7rpx;
		width: 450rpx;
		height: 200rpx;
		box-sizing: border-box;
		padding: 10rpx;
	}

	@import '@/layout/group.scss';

	.list {
		overflow: hidden;
		border-top: 1rpx #ccc solid;

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
	.u-btn--warning {
		border-color: #3C8BDB !important;
		background-color: #3C8BDB !important;
	}
</style>
