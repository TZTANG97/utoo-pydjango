<template>
	<view class="container">
		<view class="group">
			<view class="group-item" v-if="id">
				<view class="group-label">
					订单编号：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail.mainData.order_id? detail.mainData.order_id : '暂无'}}
					</view>
				</view>
			</view>
			<view class="group-item" v-if="id">
				<view class="group-label">
					制单人员：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail.mainData.addUser.trueName? detail.mainData.addUser.trueName : '暂无'}}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单类型：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'queryAllList', '订单类型', 'class_id')">
						{{ swapIdgetValue('queryAllList', 'name', 'class_id') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					下单时间：
				</view>
				<view class="group-content">
					<view class="text-content" @click="chooseDate('order_time')">
						{{ order_time? order_time : '请选择下单时间' }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					客户名称：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'clientList', '客户名称', 'clientId')">
						{{ swapIdgetValue('clientList', 'name', 'clientId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
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
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					销售人员：
				</view>
				<view class="group-content">
					<view class="text-content"
								@click="select('userName', 'purchasePersonnelList', '销售人员', 'purchasePersonnelId')">
						{{ swapIdgetValue('purchasePersonnelList', 'userName', 'purchasePersonnelId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					供应商：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('company_name', 'companyList', '供应商', 'companyId')">
						{{ swapIdgetValue('companyList', 'company_name', 'companyId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单币种：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('label', 'currencyList', '订单币种', 'currencyId')">
						{{ swapIdgetValue('currencyList', 'label', 'currencyId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					分成信息：
				</view>
				<view class="group-content" @click="showDevideInfo = true">
					<view class="text-content">
						<text>查看</text>
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>


			<view class="group-item">
				<view class="group-label">
					预计收货时间：
				</view>
				<view class="group-content">
					<view class="text-content" @click="chooseDate('delivery_time')">
						{{ delivery_time? delivery_time : '请选择收货时间' }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					付款方式：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'payList', '付款方式', 'payId')">
						{{ swapIdgetValue('payList', 'name', 'payId') }}
					</view>
					<u-icon v-if="(id && detail.mainData.order_status != 50) || !id" size="28"
									name="arrow-right"></u-icon>
				</view>
			</view>

			<view class="group-item" v-for="(item, index) in payDateList" :key="index">
				<view class="group-label">
					预计收款时间：
				</view>
				<view class="group-content" @click="chooseDate(index)">
					<view class="text-content">
						{{ item? item : '请选择'}}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单总价：
				</view>
				<view class="group-content">
					<view class="text-content">
						<input style="text-align: right;" type="digit" v-model.number.lazy="totalPrice"
									 placeholder="请输入订单总价">
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					是否开票：
				</view>
				<view class="group-content">
					<view class="text-content">
						<u-switch @change="invoiceSwitch" v-model="invoiceType" active-color="#E96302" size="28">
						</u-switch>
					</view>
				</view>
			</view>
			<view class="group-item" v-if="invoiceType">
				<view class="group-label">
					出项开票类型：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'invoiceList', '出项开票类型', 'invoiceId')">
						{{ swapIdgetValue('invoiceList', 'name', 'invoiceId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item" v-if="invoiceType">
				<view class="group-label">
					税率：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'taxRateList', '税率', 'taxeId')">
						{{ swapIdgetValue('taxRateList', 'name', 'taxeId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item" style="align-items: start !important;">
				<view class="group-label">
					样品是否回收：
				</view>
				<view class="group-content">
					<view class="text-content">
						<u-switch @change="reversoSwitch" v-model="reverso_context" active-color="#E96302" size="28">
						</u-switch>
					</view>
				</view>
			</view>
			<view class="group-item" v-if="reverso_context">
				<view class="group-label">
					收件人姓名
				</view>
				<view class="group-content">
					<view class="text-content">
						<input v-model="addressee_name" style="text-align: right;" placeholder="请输入收件人姓名" />
					</view>
				</view>
			</view>
			<view class="group-item" v-if="reverso_context">
				<view class="group-label">
					收件人电话
				</view>
				<view class="group-content">
					<view class="text-content">
						<input v-model="addressee_mobile" style="text-align: right;" placeholder="请输入收件人电话" />
					</view>
				</view>
			</view>
			<view class="group-item" v-if="reverso_context">
				<view class="group-label">
					样品回收地址
				</view>
				<view class="group-content">
					<view class="text-content">
						<textarea v-model="send_address" placeholder="请输入回收地址" maxlength="120" />
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单资料：
				</view>
				<view class="group-content">
					<view class="text-content" @click="uploadFile">
						<image style="width: 35rpx;height: 35rpx;margin-right: 10rpx;vertical-align: middle;"
									 src="@/static/img/upload.png" mode=""></image>
						<text>上传</text>
					</view>
				</view>
			</view>
			<view class="files-list" v-if="files.length">
				<view class="file-item" v-for="(item, index) in files" :key="index">
					<view class="oh" @click="preImage(index)">{{ item.name }}</view>
					<image src="@/static/delete.png" mode="" @click="deleteFile(index)"></image>
				</view>
			</view>
			<upload-progress ref="prg"></upload-progress>

			<view class="group-item" style="align-items: start !important;">
				<view class="group-label">
					订单备注
				</view>
				<view class="group-content">
					<view class="text-content">
						<textarea v-model="msg" placeholder="请输入备注内容" maxlength="120" />
					</view>
				</view>
			</view>
		</view>

		<!-- 子订单 -->
		<view class="group child-order" v-for="(item, index) in childOrderList" :key="index">
			<view class="group-hint">
				<text>子订单-{{ index + 1 }}</text>
				<text @click="deleteChildOrder(index)">删除</text>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品名称：
				</view>
				<view class="group-content">
					<view class="text-content" @click="chooseProduct(item.newAdd, index)">
						{{ item.goodsName? item.goodsName : '请选择产品名称' }}
						<u-icon v-if="item.newAdd" size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品型号：
				</view>
				<view class="group-content">
					<view class="text-content" @click="chooseProductModel(item, index)">
						{{ item.goodsSpec? item.goodsSpec : '请选择产品型号' }}
						<u-icon v-if="detail && detail.mainData.order_status != 50" size="28"
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
						<input :disabled="isNum" @input="getTotal(true)" class="child-order-input"
									 type="digit" v-model.number.lazy="item.goodsNums" set placeholder="请输入数量">
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					实验测试项目：
				</view>
				<view class="group-content" @click="chooseTestProduct(item.newAdd, index)">
					<view class="text-content">
						{{ item.experiment_project_name? item.experiment_project_name : '请选择实验测试项目'}}
					</view>
					<u-icon v-if="item.newAdd" size="28" name="arrow-right"></u-icon>
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
						<input class="child-order-input" @input="getTotal" type="text"
									 v-model.number.lazy="item.goodsPrice">
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					标准测试金额：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ item.reference_price? item.reference_price : '0.00' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					总价：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ (item.goodsNums * item.goodsPrice).toFixed(2) }}
					</view>
				</view>
			</view>
		</view>


		<view class="confirm" @click="submitData">
			确&nbsp;定
		</view>


		<!-- 公用弹框-完整数据 -->
		<popup-bottom :show.sync="showcheckBox" :list.sync="checkBoxList" :title="checkBoxTitle"
									:showKey="checkBoxKeyName" @getValue="confirmValue"></popup-bottom>


		<!-- 公用弹框-分页加载 -->
		<popup-bottom :loadable="true" :loading="productLoading" :is-refresh.sync="productIsRefresh"
									:show.sync="showDynamicPopup" :list.sync="productList" title="选择产品" showKey="goods_name"
									@getMoreOrSearch="getGoodsList" @getValue="confirmProduct" :page.sync="productPage"></popup-bottom>

		<!-- 分页加载-获取实验项目 -->
		<popup-bottom :loadable="true" :loading="testLoading" :is-refresh="testIsRefresh"
									:show.sync="showTestProjectPopup" :list.sync="testList" title="选择产品" show-key="project_name"
									@getMoreOrSearch="getTestProjectList" @getValue="confirmTestProject" :page.sync="testPage"></popup-bottom>


		<!-- 仅适用于选择产品型号 -->
		<popup-bottom :show.sync="showChooseProductModel" :list.sync="productModelList" title="选择型号"
									@getValue="confirmProductModel"></popup-bottom>

		<!-- 选择日期 -->
		<u-calendar btn-type="warning" @change="confirmDate" max-date="2222-01-01" active-bg-color="#E96302 !important"
								v-model="showCalendar" mode="date"></u-calendar>


		<!-- 添加子订单图标 -->
		<view class="add-order"
					@click="showDynamicPopup = true, currentSelectedChildOrderIndex = childOrderList.length">
			<image src="@/static/add.png" mode=""></image>
		</view>

		<!-- 分成信息 -->
		<devide-into :cbUnit="false" :showMl="true" :showCb="true" :cb="cb" :ml="ml" :backUpList="cbList"
								 :show.sync="showDevideInfo" @confirmDevideList="confirmDevideInfo"></devide-into>

		<u-toast ref="uToast" />
	</view>
</template>

<script>
// 弹框组件
import popupBottom from '../popupBottom.vue'
import devideInto from '../devideInto.vue'
import uploadProgress from '../uploadProgress'
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
		devideInto,
		uploadProgress
	},
	data() {
		return {
			isShowView: false,
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
			order_time: '',
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
			testLoading: false,
			testIsRefresh: true,
			testList: [],
			testPage: 1,
			mlList: [],
			ml: [],
			cbList: [],
			cb: [],
			showDevideInfo: false,
			queryAllList: [],
			class_id: '',
			isNum: false,
			send_address: '',
			addressee_name: '',
			addressee_mobile: '',
		}
	},
	onLoad(options) {
		let {
			id
		} = options

		let title = '添加订单'

		if (id) {
			title = '编辑订单'
		}

		uni.setNavigationBarTitle({
			title
		})

		// 获取一些必要的基本数据
		const rquestArr = [this.getPurchaseCompanyList(), this.getInvoiceList(), this.getCompanyList(),
			this.getPayList(), this.getTaxRateList(), this.getpurchasePersonnelList(1), this
					.getpurchasePersonnelList(-1), this.queryAllFn()
		]
		this.isNum = false
		if (id) {
			this.id = id
			this.getDetail()
		}
		Promise.all(rquestArr).catch(err => {
			this.$tip2('数据拉取失败')
		})
	},
	methods: {
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
					let data = e.goodsNums.toString().split(".")[1]
					let data2 = e.goodsNums.toString().split(".")[0]
					let str = Number(data2)
					if (data) {
						if (data.length == 1) {
							str = Number(data2) + Number('0.' + data)
						} else {
							str = Number(data2) + Number('0.' + data[0])
						}
					}
					e.goodsNums = str
					total += str * e.goodsPrice;
				} else {
					total += e.goodsNums * e.goodsPrice;
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
			this.childOrderList[this.currentSelectedChildOrderIndex]['goodsPrice'] = test_price
			this.childOrderList[this.currentSelectedChildOrderIndex]['reference_price'] = test_price
			this.childOrderList[this.currentSelectedChildOrderIndex]['experiment_class_id'] = class_id
			this.childOrderList[this.currentSelectedChildOrderIndex]['experiment_project_id'] = id
			this.getTotal()
			this.getTotal(true)
			this.showTestProjectPopup = false
		},



		// 选择实验测试项目
		chooseTestProduct(isNew, index) {
			if (!isNew) return
			this.currentSelectedChildOrderIndex = index
			this.showTestProjectPopup = true
		},



		// 获取实验项目
		getTestProjectList(project_name = '') {
			this.testLoading = true

			fetchTestProductGoodsListApi({
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
					this.testList = [...this.testList, ...res.data]
				} else {
					this.$tip(res.error)
				}
			}).finally(_ => {
				this.testLoading = false
			})
		},

		// 提交数据
		submitData() {

			if (!this.id) {
				if (!this.order_time) {
					return this.$tip('请选择下单时间')
				}

				if (this.clientId == -1) {
					return this.$tip('请选择客户')
				}

				if (this.purchaseBossId == -1) {
					return this.$tip('请选择销售主管')
				}

				if (this.purchasePersonnelId == -1) {
					return this.$tip('请选择销售人员')
				}

				if (this.companyId == -1) {
					return this.$tip('请选择供应商')
				}

				if (this.currencyId == -1) {
					return this.$tip('请选择币种')
				}

				if (!this.delivery_time) {
					return this.$tip('请选择收货时间')
				}

				if (this.payId == -1) {
					return this.$tip('请选择付款方式')
				}


				if (!this.childOrderList.length) {
					return this.$tip('请至少添加一个子订单')
				}
			}

			// 数据校验
			if (this.invoiceType) {
				if (this.invoiceId == -1) {
					return this.$tip('请选择出项开票类型')
				}
				if (this.taxeId == -1) {
					return this.$tip('请选择税率')
				}
			}
			console.log(this.reverso_context, '.reverso_context')
			if (this.reverso_context) {
				if (!this.send_address) {
					return this.$tip('请输入回收地址')
				}
				if (!this.addressee_name) {
					return this.$tip('请输入收件人姓名')
				}
				if (!this.addressee_mobile) {
					return this.$tip('请输入收件人电话')
				}
			}



			this.payDateList.forEach(e => {
				if (!e) {
					this.$tip('请选择付款时间')
					throw new Error('请选择付款时间')
				}
			})


			// 获取订单总价和订单数量
			// 顺便校验格式
			let goodsAmount = 0
			this.childOrderList.forEach((e, i) => {
				if (!e.goodsName) {
					this.$tip(`${i+1}号子订单未选择产品`)
					throw new Error(`${i+1}号子订单未选择产品`)
				}
				// if (!e.goodsSpec) {
				// 	this.$tip(`${i+1}号子订单未选择型号`)
				// 	throw new Error(`${i+1}号子订单未选择型号`)
				// }
				if (!e.goodsNums) {
					this.$tip(`${i+1}号子订单数量不能为0`)
					throw new Error(`${i+1}号子订单数量不能为0`)
				}

				if (!e.experiment_project_name) {
					this.$tip(`${i+1}号子订单未选择测试项目`)
					throw new Error(`${i+1}号子订单未选择测试项目`)
				}

				goodsAmount += e.goodsNums
			})

			let mlStr = '',
					cbStr = ''

			mlStr = this.ml.map(item => `${item.userId}_${item.scale}`)
			mlStr = mlStr.join(',')

			cbStr = this.cb.map(item => `${item.userId}_${item.scale}`)
			cbStr = cbStr.join(',')

			// 最后一个订单的数据
			let {
				experiment_class_id,
				experiment_class_name,
				experiment_project_id,
				experiment_project_name,
				goodsBrandId,
				goodsBrandName,
				goodsName,
				goodsNums,
				goodsPrice,
				reference_price,
				id,
				goodsSpec
			} = this.childOrderList[this.childOrderList.length - 1]


			if (this.id) {
				var {
					mainData: {
						order_id,
						order_status,
						exp_type_id
					},
					syuser_id
				} = this.detail
			}

			let arrData = [],
					firstObj = {
						accessoryId: this.files.map(item => item.id + ''),
						bzcsj: reference_price + '',
						collection_time: this.payDateList.length == 0 ? '' : this.payDateList,
						currency_type: this.currencyId + '',
						customer_name: this.clientId + '',
						// 发货时间
						delivery_time: this.delivery_time,
						exp_type_id: this.id ? exp_type_id + '' : '',
						experiment_class_id: experiment_class_id + '',
						experiment_class_name: experiment_class_name,
						experiment_project_id: experiment_project_id + '',
						experiment_project_name: experiment_project_name,
						goods_amount: goodsAmount + '',
						goods_brand_id: goodsBrandId + '',
						goods_brand_name: goodsBrandName,
						goods_name: goodsName,
						goods_nums: goodsNums + '',
						goods_spec: goodsSpec,
						rent_day_pric: goodsPrice + '',
						goods_zj: (goodsNums * goodsPrice).toFixed(2),
						class_id: this.class_id,
						id: id ? id + '' : '',
						msg: this.msg,
						ofId: this.id,
						orderId: this.id ? order_id : '',
						orderStatus: this.id ? order_status + '' : '',
						order_time: this.order_time,
						order_type: '1',
						// 好像是订单资料
						orderdata: "",
						outBillTypeId: this.invoiceId + '',
						pay_way: this.payId + '',
						sale_manager: this.purchaseBossId,
						sale_user: this.purchasePersonnelId,
						supplier_name: this.companyId == -1 ? '' : this.companyId + '',
						syuser_id: this.id ? syuser_id + '' : '',
						taxes: this.taxeId != -1 ? this.taxRateList.find(e => e.id == this.taxeId).taxValue + '' : '',
						totalPrice: this.totalPrice.toFixed(2),
						user_scale_info: mlStr,
						salecb_user_scale_info: cbStr,
					}
			if (this.reverso_context) {
				firstObj.reverso_context = 1
				firstObj.send_address = this.send_address
				firstObj.addressee_name = this.addressee_name
				firstObj.addressee_mobile = this.addressee_mobile
			} else {
				firstObj.reverso_context = 2
			}

			if (this.invoiceType) {
				firstObj['invoiceType'] = 'on'
			}

			arrData.push(firstObj)

			this.childOrderList.forEach(e => {
				arrData.push({
					experiment_class_id: e.experiment_class_id + '',
					experiment_class_name: e.experiment_class_name,
					experiment_project_id: e.experiment_project_id + '',
					experiment_project_name: e.experiment_project_name,
					goods_id: e.goodsId + '',
					goods_nums: e.goodsNums + '',
					goods_price: e.goodsPrice + '',
					goods_spec: e.goodsSpec,
					id: e.id ? e.id + '' : '',
					reference_price: e.reference_price + '',
				})
			})

			if (!this.id) {
				if (this.disabledTotalPrice != this.totalPrice) {
					const that = this
					uni.showModal({
						title: '提示',
						content: '订单总价与产品价格总和不一致。确认是否要提交？',
						success({
											confirm
										}) {
							if (confirm) {
								addTestOrderApi(arrData).then(res => {
									if (res.res) {
										uni.redirectTo({
											url: '/staffB/result/result?title=添加成功'
										})
									} else {
										that.$tip(res.resMsg)
									}
								})
							}
						}
					})
				} else {
					addTestOrderApi(arrData).then(res => {
						if (res.res) {
							uni.redirectTo({
								url: '/staffB/result/result?title=添加成功'
							})
						} else {
							this.$tip(res.resMsg)
						}
					})
				}
			} else {
				saveTestOrderApi(arrData).then(res => {
					if (res.res) {
						uni.$emit('isEdit');
						uni.redirectTo({
							url: '/staffB/result/result?title=编辑成功'
						})
					} else {
						this.$tip(res.resMsg)
					}
				})
			}
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
			this.childOrderList[this.currentSelectedChildOrderIndex].goodsSpec = e
			this.showChooseProductModel = false
		},

		// 选择产品型号
		chooseProductModel(item, currentSelectedChildOrderIndex) {
			this.currentSelectedChildOrderIndex = currentSelectedChildOrderIndex
			console.log(item, 'item')
			if (item.id) {
				// 已完成的订单不能修改
				if (this.detail.mainData.order_status == 50) return
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
				goodsId: id,
				newAdd: true,
				goodsName: goods_name,
				// 型号
				goodsSpec: '',
				goodsSpecList: goods_model.split(','),
				// 品牌名称
				goodsBrandName: goods_brand_name,
				goodsBrandId: goods_brand_id,
				goodsNums: 1,
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
				goodsName: keyWord,
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
			this[this.checkEchoKey] = e.id
			if (this.checkEchoKey == 'payId') {
				this.payDateList = new Array(e.nums).fill('')
			}
			this.showcheckBox = false
		},

		// 选择
		select(keyName, listName, titleName, echoKey) {

			if (this.id) {
				// 采购类别
				if (titleName == '订单币种' && this.isDisabled) {
					return this.$tip(`付款之后不能更改${titleName}`)
				}

				const {
					order_status = ''
				} = this.detail.mainData

				if (titleName == '付款方式' && (order_status == 50 || order_status == 30)) return this.$tip('不允许修改付款方式')
			}

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
			uni.showLoading()
			fetchEditTestOrderDetailApi({
				id: this.id
			}).then(res => {
				uni.hideLoading()
				if (res.res) {
					this.detail = res.obj
					this.detail['mainData'] = this.detail['of']
					delete this.detail['of']

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
							// 下单时间
							order_time,
							// 发货时间
							delivery_time,
							msg,
							order_status,
							parentOf,
							class_id
						},
						collectionTimes,
						files,
						childs,
						scaleList,
						salecbscaleList,
						isDisabled,
					} = this.detail
					if (this.detail.order_status == 5 || this.detail.order_status == 10 || this.detail
							.order_status == 20) {
						this.isNum = true
					} else {
						this.isNum = false
					}
					this.order_time = this.$alterTime(order_time, false)
					this.delivery_time = this.$alterTime(delivery_time, false)
					this.payDateList = collectionTimes
					this.files = files
					this.send_address = send_address
					this.addressee_name = addressee_name
					this.addressee_mobile = addressee_mobile
					this.msg = msg
					this.class_id = class_id;
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
				this.isShowView = true;
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


.confirm {
	width: 600rpx;
	height: 65rpx;
	border-radius: 30rpx;
	text-align: center;
	line-height: 65rpx;
	color: #FFF;
	background-color: $primary;
	margin: 40rpx auto;
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
</style>
<style>
.u-btn--warning {
	border-color: #e96302 !important;
	background-color: #e96302 !important;
}
</style>
