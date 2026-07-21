<template>
	<view class="container">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					来源单号：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{sonDetial.saleOrder}}
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
					审核主管：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('userName', 'saleBossList', '审核主管', 'purchaseBossId')">
						{{ swapIdgetValue('saleBossList', 'userName', 'purchaseBossId') }}
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
					所属公司：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('company_name', 'companyList', '所属公司', 'companyId')">
						{{ swapIdgetValue('companyList', 'company_name', 'companyId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					客户账号：
				</view>
				<view class="group-content">
					<view class="text-content"
						@click="select('mobile', 'queryAllCompanyList', '客户账号', 'customerAccount')">
						{{ swapIdgetValue('queryAllCompanyList', 'mobile', 'customerAccount') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>

			<!-- 客户账号：所属公司 -->
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
				<checkbox-group @change="childOrderList[index]['checked'] = !item['checked']">
					<checkbox :disabled="disabledCheck" :checked="item['checked']" />
				</checkbox-group>
			</view>
			<view class="group-item">
				<view class="group-label">
					子订单编号：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ item.orderId }}
					</view>
				</view>
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
					<view class="text-content">
						{{ item.goodsSpec? item.goodsSpec : '' }}
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
						<input :disabled="!item.newAdd" @input="getTotal" class="child-order-input" type="digit"
							v-model.number.lazy="item.goodsNums" placeholder="请输入数量">
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
					测试人员：
				</view>
				<view class="group-content">
					<view class="text-content" @click="textFn(item,index)">
						{{ item.test_user ? item.test_user : '请选择测试人员' }}
					</view>

					<!-- <view class="text-content" @click="select('userName', 'testers', '测试人员', 'testersId')">
						{{ swapIdgetValue('testers', 'userName', 'testersId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view> -->
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					实验平台：
				</view>
				<view class="group-content">
					<view class="text-content" @click="platFn(item,index)">
						{{ item.line? item.line : '请选择实验平台' }}
					</view>

					<!-- <view class="text-content" @click="select('className', 'platformList', '实验平台', 'classId')">
						{{ swapIdgetValue('platformList', 'className', 'classId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view> -->
					<!-- <view class="text-content">
						{{ item.experiment_class_name? item.experiment_class_name : '暂无' }}
					</view> -->
				</view>
			</view>

		</view>


		<view class="confirm" @click="submitData">
			提交审核
		</view>
		<!-- 选择实验平台 -->
		<popup-bottom v-if="platShow" :show.sync="platShow" :list.sync="platformList"
			title="选择实验平台" showKey="line_num" @getValue="confirmpPlatform"></popup-bottom>

		<!-- 选择实验平台 -->
		<popup-bottom v-if="textShow" :show.sync="textShow" :list.sync="testers"
			title="选择测试人员" showKey="userName" @getValue="testConfirm"></popup-bottom>

<!-- 		<u-select  v-model="platShow" mode="single-column" label-name="line_num" value-name="id"
			:list="platformList" @confirm="platConfirm"></u-select> -->
<!-- 		<u-select v-model="textShow" mode="single-column" label-name="userName" value-name="id"
			:list="testers" @confirm="testConfirm"></u-select> -->
		<!-- 公用弹框-完整数据 -->
		<popup-bottom :show.sync="showcheckBox" :list.sync="checkBoxList" :title="checkBoxTitle"
			:showKey="checkBoxKeyName" @getValue="confirmValue"></popup-bottom>

		<!-- 仅适用于选择产品型号 -->
		<popup-bottom :show.sync="showChooseProductModel" :list.sync="productModelList" title="选择型号"
			@getValue="confirmProductModel"></popup-bottom>

		<!-- 选择日期 -->
		<u-calendar btn-type="warning" @change="confirmDate" max-date="2222-01-01" active-bg-color="#3C8BDB !important"
			v-model="showCalendar" mode="date"></u-calendar>

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
		// 付款方式
		fetchPurchasePayWayApi,
		// 所属公司列表
		fetchCompanyListApi,
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
		exCcreateOrderPage,
		fetchTestPlatformListApi,
		queryAllCompanykh,
		queryTestUsers,
		exSubmitOrder
	} from '@/api/index.js'
	import {
		createOrderPagexcx
	} from '@/api/staffB.js'
	export default {
		components: {
			popupBottom,
			devideInto,
			uploadProgress
		},
		data() {
			return {
				id: '',
				detail: null,
				// 采购人员
				purchasePersonnelId: -1,
				// 采购主管id
				purchaseBossId: -1,
				// 客户id
				clientId: -1,
				customerAccount: -1,
				testersId: -1,
				classId: -1,
				// 所属公司id
				companyId: -1,

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

				// 客户列表
				clientList: [],
				// 发票列表
				invoiceList: [],
				// 所属公司列表
				companyList: [],
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

				// 选择产品型号
				showChooseProductModel: false,
				// 产品型号列表
				productModelList: [],

				sonDetial: {},
				platformList: [],
				queryAllCompanyList: [],
				testers: [],
				class_id: 0,
				textShow: false,
				platShow: false,
				textind: null,
				platind: null,
				disabledCheck: false,
				childOrderList: []
			}
		},
		onLoad(options) {
			let {
				id,
				class_id
			} = options
			console.log(class_id, 'class_id')
			this.class_id = class_id
			this.id = id
			exCcreateOrderPage({
				saleOrderId: id
			}).then(res => {

				this.sonDetial = res.obj
			})
			// 获取可选产品列表
			createOrderPagexcx(id).then(res => {
				res.obj.childs.forEach(item => {
					item['checked'] = false
				})
				this.childOrderList = res.obj.childs
			})
			let title = '创建实验子订单'

			uni.setNavigationBarTitle({
				title
			})

			// 获取一些必要的基本数据
			const rquestArr = [this.getPurchaseCompanyList(), this.getCompanyList(),
				this.getpurchasePersonnelList(1), this
				.getpurchasePersonnelList(-1), this.fetchTestPlatformListApiFn(), this.queryAllCompanykhFn(),
			]

			Promise.all(rquestArr).catch(err => {
				this.$tip2('数据拉取失败')
			})
		},
		methods: {
			// 选择实验测试项目
			chooseTestProduct(isNew, index) {
				if (!isNew) return
			},
			// platConfirm(val) {
			// 	this.childOrderList[this.platind].line_id = val[0].value
			// 	this.childOrderList[this.platind].line = val[0].label
			// 	this.platind = null
			// },
			// 确认选择实验平台
			confirmpPlatform(e) {
				console.log(e,'eeee')
				this.childOrderList.forEach((item, index) => {
					if (index == this.platind) {
						item.line_id = e.id
						item.line = e.line_num
					}
				})
				console.log(this.childOrderList,'childOrderList')
				this.platShow = false
			},
			testConfirm(e) {
				console.log(e,'eeee')
				this.childOrderList.forEach((item, index) => {
					if (index == this.textind) {
						item.test_user_id = e.id
						item.test_user = e.userName
					}
				})
				console.log(this.childOrderList,'childOrderList')
				this.textShow = false
				// this.childOrderList[this.textind].test_user_id = val[0].value
				// this.childOrderList[this.textind].test_user = val[0].label
				// this.textind = null
			},
			textFn(item, index) {
				this.queryTestUsersFn(item.experiment_class_id)
				this.textind = index
				// if (this.childOrderList[index].id == item.id) {
				// 	this.textind = index
				// } else {
				// 	this.textind = null
				// }
			},
			// platFn(item, index) {
			// 	if (this.childOrderList[index].id == item.id) {
			// 		this.platind = index
			// 	} else {
			// 		this.platind = null
			// 	}
			// 	this.platShow = !this.platShow
			// },
			// 选择实验平台
			platFn(item,index) {
				this.platind = index
				this.platShow = true
			},

			// 提交数据
			submitData() {
				if (!this.order_time) {
					return this.$tip('请选择下单时间')
				}

				if (this.clientId == -1 && this.customerAccount == -1) {
					return this.$tip('请选择客户')
				}

				if (this.purchaseBossId == -1) {
					return this.$tip('请选择销售主管')
				}

				if (this.purchasePersonnelId == -1) {
					return this.$tip('请选择销售人员')
				}

				if (this.companyId == -1) {
					return this.$tip('请选择所属公司')
				}
				if (!this.delivery_time) {
					return this.$tip('请选择收货时间')
				}

				let newChildOrderList = this.childOrderList.filter(item => item['checked'])
				if (!newChildOrderList.length) {
					return this.$tip('请至少选择一个子订单')
				}
				let arr = []
				let idList = []
				let fileId = []
				let test_user_id = []
				let line_id = []
				this.files.forEach(item => {
					fileId.push(item.id)
				})
				newChildOrderList.forEach(item => {
					idList.push(item.id)
					if (item.test_user_id) test_user_id.push(item.test_user_id)
					if (item.line_id) line_id.push(item.line_id)
					arr.push({
						"orderId": item.orderId,
						"goodsName": item.goodsName,
						"goodsSpec": item.goodsSpec,
						"goodsBrandName": item.goodsBrandName,
						"goodsNums": item.goodsNums,
						"experiment_project_name": item.experiment_project_name,
						"experiment_class_name": item.experiment_class_name,
						"test_user_id": item.test_user_id,
						"line_id": item.line_id,
					})
				})
				if (test_user_id.length != newChildOrderList.length) return this.$tip('请选择测试人员')
				if (line_id.length != newChildOrderList.length) return this.$tip('请选择实验平台')
				let obj = {
					saleOrderId: this.id,
					order_time: this.order_time, // 下单时间
					sale_manager: this.purchaseBossId, // 审核主管
					customer_name: this.clientId, // 客户名称
					supplier_name: this.companyId, // 所属公司
					custom_user_id: this.customerAccount, // 客户账号
					sale_user: this.purchasePersonnelId, // 销售人员
					delivery_time: this.delivery_time, // 收货时间
					orderdata: fileId.join(','), // 订单资料
					msg: this.msg, // 订单备注
					childs: JSON.stringify(arr),
					checkChilds: idList.join(','),
					test_user_ids: test_user_id.join(','),
					line_ids: line_id.join(','),
				}
				console.log(obj,'obj')
				exSubmitOrder(obj, this.class_id).then(res => {
					if (res.res) {
						this.$toast('创建成功')
						setTimeout(() => {
							uni.navigateBack();
						}, 1200)
					} else {
						this.$toast(res.resMsg == null ? '创建失败' : res.resMsg)
					}
				})
			},
			// 确定产品型号
			confirmProductModel(e) {
				this.showChooseProductModel = false
			},
			// 选择产品
			chooseProduct(isNew, index) {
				if (!isNew) return
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
				this.showcheckBox = false
			},

			// 选择
			select(keyName, listName, titleName, echoKey) {
				// 选择框标题
				this.checkBoxTitle = titleName
				// 选择框中数组展示的key
				this.checkBoxKeyName = keyName

				// 回显key
				this.checkEchoKey = echoKey

				this.checkBoxList = this[listName]

				this.showcheckBox = true
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
			// 获取实验平台
			fetchTestPlatformListApiFn() {
				fetchTestPlatformListApi({
					draw: 1,
					start: 0,
					length: 999,
					line_num: ''
				}).then(res => {
					console.log(res,'789')
					if (!res.error) {
						this.platformList = res.data
					} else {
						this.$toast(res.error)
					}
				})
			},

			// 获取客户账户
			queryAllCompanykhFn() {
				queryAllCompanykh({
					parentId: '',
				}).then(res => {
					if (!res.error) {
						this.queryAllCompanyList = []
						this.queryAllCompanyList = res.obj
					} else {
						this.$toast(res.error)
					}
				})
			},
			// 获取测试人员
			async queryTestUsersFn(id) {
				await queryTestUsers(id).then(res => {
					if (!res.error) {
						this.testers = [{
							userName: '抢单',
							id: 22,
						}]
						console.log(res,'resssssss')
						res.obj.forEach(item => {
							this.testers.push(item)
						})
						this.textShow = !this.textShow
					} else {
						this.$toast(res.error)
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
							this.purchasePersonnelList = res.obj
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
		border-color: #3C8BDB !important;
		background-color: #3C8BDB !important;
	}
</style>
