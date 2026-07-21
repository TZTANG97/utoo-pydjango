<template>
	<view class="container">
		<view class="group">
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
						{{ orderData.parentOf.order_id }}
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
					下单时间
				</view>
				<view class="group-content" @click="chooseDate('order_time')">
					<view class="text-content" v-if="orderData">
						{{ order_time ? order_time : '请选择下单时间' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					客户名称
				</view>
				<view class="group-content" @click="select('name', 'clientList', '客户名称', 'clientId')">
					{{ swapIdgetValue('clientList', 'name', 'clientId') }}
					<u-icon size="28" name="arrow-right"></u-icon>
					<!-- 					<view class="text-content">
						{{ orderData.company.name }}
					</view> -->
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
					预计收货时间
				</view>
				<view class="group-content">
					<view class="text-content" @click="chooseDate('delivery_time')">
						{{ delivery_time ? delivery_time : '请选择预计收货时间' }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>

			<view class="group-item">
				<view class="group-label">
					订单资料
				</view>
				<view class="group-content">
					<view class="text-content" @click="uploadFile(3)">
						<image style="width: 35rpx;height: 35rpx;margin-right: 10rpx;vertical-align: middle;"
							src="@/static/img/upload.png" mode=""></image>
						<text>上传</text>
					</view>
				</view>
			</view>
			<view class="files-list" v-if="files.length">
				<view class="file-item" v-for="(item, index) in files" :key="index">
					<view class="oh" @click="preImage(index, 'files')">{{ item.name }}</view>
					<image src="@/static/delete.png" mode="" @click="deleteFile(index, 'files')"></image>
				</view>
			</view>
			<upload-progress ref="prg"></upload-progress>


			<view class="group-item">
				<view class="group-label">
					测试资料
				</view>
				<view class="group-content">
					<view class="text-content" @click="uploadFile(4)">
						<image style="width: 35rpx;height: 35rpx;margin-right: 10rpx;vertical-align: middle;"
							src="@/static/img/upload.png" mode=""></image>
						<text>上传</text>
					</view>
				</view>
			</view>
			<view class="files-list" v-if="testFiles.length">
				<view class="file-item" v-for="(item, index) in testFiles" :key="index">
					<view class="oh" @click="preImage(index, 'testFiles')">{{ item.name }}</view>
					<image src="@/static/delete.png" mode="" @click="deleteFile(index, 'testFiles')"></image>
				</view>
			</view>
			<upload-progress ref="prg2"></upload-progress>


			<view class="group-item" style="align-items: start !important;">
				<view class="group-label">
					订单备注：
				</view>
				<view class="group-content">
					<view class="text-content">
						<textarea v-model="msg" placeholder="请输入备注内容" maxlength="120" />
					</view>
				</view>
			</view>
		</view>


		<view class="group child-order" style="margin: 20rpx;" v-for="item,index in childOrderData" :key="index">
			<view class="group-hint">
				<text>子订单-{{ index + 1 }}</text>
				<checkbox-group @change="childOrderData[index]['checked'] = !item['checked']">
					<checkbox :disabled="disabledCheck" :checked="item['checked']" />
				</checkbox-group>
			</view>
			<view class="group-item">
				<view class="group-label">
					订单编号：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ item.order_id? item.order_id : '暂无' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品名称
				</view>
				<view class="group-content">
					{{ item.goods_name }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品型号
				</view>
				<view class="group-content">
					{{ item.goods_spec }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品品牌
				</view>
				<view class="group-content">
					{{ item.goods_brand_name }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					数量
				</view>
				<view class="group-content">
					{{ item.goods_nums }}台
<!-- 					<input :disabled="isNum" class="child-order-input" style="text-align: right;" type="digit"
						v-model.number.lazy="item.goods_nums" placeholder="请输入数量"> -->
				</view>
			</view>
			<view class="group-item" v-if="item.experiment_project_name">
				<view class="group-label">
					实验测试项目
				</view>
				<view class="group-content">
					{{ item.experiment_project_name }}
				</view>
			</view>
			<view class="group-item" v-if="item.experiment_class_name">
				<view class="group-label">
					实验测试分类
				</view>
				<view class="group-content">
					{{ item.experiment_class_name }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					测试人员：
				</view>
				<view class="group-content">
					<view class="text-content" @click="textShowFn(item,index)">
						<text>{{ item.test_user_id == 22 ? '抢单' : item.testUser ? item.testUser : '请选择测试人员' }}</text>
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>

				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					实验平台
				</view>
				<view class="group-content" @click="selectTestPlatform(index)">
					<text v-if="item.line_num">{{ item.line_num }}</text>
					<text v-else>请选择实验平台</text>
					<u-icon size="28" name="arrow-right"></u-icon>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					状态
				</view>
				<view class="group-content">
					{{ status_list[item['order_status']] }}
				</view>
			</view>
		</view>

		<view class="confirm" @click="submitData">
			确&nbsp;定
		</view>
		<!-- 		<u-select v-model="textShow" mode="single-column" label-name="userName" value-name="id"
			:list="testers" @confirm="testConfirm"></u-select> -->
		<!-- 选择测试人员 -->
		<popup-bottom v-if="textShow" :show.sync="textShow" :list.sync="testers" title="选择测试人员" showKey="userName"
			@getValue="testConfirm"></popup-bottom>

		<!-- 选择实验平台 -->
		<popup-bottom v-if="showPlatformOptionDialog" :show.sync="showPlatformOptionDialog" :list.sync="platformList"
			title="选择实验平台" showKey="line_num" @getValue="confirmpPlatform"></popup-bottom>

		<!-- 公用弹框-完整数据 -->
		<popup-bottom v-if="showcheckBox" :show.sync="showcheckBox" :list.sync="checkBoxList" :title="checkBoxTitle"
			:showKey="checkBoxKeyName" @getValue="confirmValue"></popup-bottom>

		<!-- 仅适用于选择产品型号 -->
		<!-- 		<popup-bottom :show.sync="showChooseProductModel" :list.sync="productModelList" title="选择型号"
			@getValue="confirmProductModel"></popup-bottom> -->

		<!-- 选择日期 -->
		<u-calendar btn-type="warning" v-if="showCalendar" @change="confirmDate" max-date="2222-01-01"
			active-bg-color="#3C8BDB !important" v-model="showCalendar" mode="date"></u-calendar>

		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import {
		editChildApi,
		fetchTestPlatformListApi,
		submitTestOrderChildOrderApi,
		submitTestOrderChildOrderApi2,
		fetchClientListApi,
		fetchCompanyListApi,
		fetchBunListApi,
		queryAllCompanykh,
		queryTestUsers
	} from '@/api/index.js'
	import popupBottom from '../popupBottom'
	import uploadProgress from '../uploadProgress'
	import {
		editPagexcx
	} from '@/api/staffB.js'
	export default {
		components: {
			popupBottom,
			uploadProgress
		},
		data() {
			return {
				id: '',
				files: [],
				status_list: {
					0: "已取消",
					1: "待处理",
					2: "已处理",
					3: "已驳回",
					10: "生产中",
					20: "运输中",
					30: "已签收",
					40: "已验收",
					16: "测试中",
					17: "测试完成",
					35: "已下单",
					36: "样品入库",
					37: "样品领用",
					38: "测试中",
					39: "测试完成",
					41:"样品归还",
					42:"样品寄回",
					43:"样品留存",
					45:"已发货",
					46:"已入库",
					50:"已完成"
				},
				// 是否认证
				uType: 0,
				orderData: null,
				childOrderData: null,
				testFiles: [],
				// 备注内容
				msg: '',
				showPlatformOptionDialog: false,
				platformList: [],
				line: null,
				checkBoxTitle: '',
				checkBoxKeyName: '',
				checkEchoKey: '',
				checkBoxList: [],
				showcheckBox: false,
				showCalendar: false,
				setDateForKey: null,
				payDateList: [],
				disabledCheck: false,
				clientList: [],
				companyList: [],
				purchasePersonnelList: [],
				saleBossList: [],
				queryAllCompanyList: [],
				purchasePersonnelId: '',
				purchaseBossId: '',
				delivery_time: '',
				customerAccount: '',
				companyId: '',
				clientId: '',
				order_time: '',
				testers: [],
				test_user_id: '',
				test_user: '',
				textShow: false,
				textIndex: null,
				platformIndex: null,
			};
		},
		created() {
			this.getPlatformList()
			this.getPurchaseCompanyList()
			this.getCompanyList()
			this.getpurchasePersonnelList(1)
			this.getpurchasePersonnelList(-1)
			this.queryAllCompanykhFn()
		},
		onLoad({
			id
		}) {
			if (!id) return this.$tip2('缺少订单ID')
			const uType = uni.getStorageSync('uType')
			if (uType) {
				this.uType = uType
			}
			this.id = id
			this.getDetail()
			// let arr = []

		},

		methods: {

			// 删除
			deleteFile(idx, k) {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定删除该资料吗？',
					success(e) {
						if (e.confirm) {
							that[k].splice(idx, 1)
						}
					}
				})
			},

			// 获取实验平台列表
			getPlatformList() {
				fetchTestPlatformListApi({
					draw: 1,
					start: 0,
					length: 999,
					line_num: ''
				}).then(res => {
					if (!res.error) {
						this.platformList = res.data
					} else {
						this.$toast(res.error)
					}
				})
			},

			// 确认选择实验平台
			confirmpPlatform(e) {
				this.childOrderData.forEach((item, index) => {
					if (index == this.platformIndex) {
						item.line_id = e.id
						item.line_num = e.line_num
					}
				})
				this.showPlatformOptionDialog = false
			},
			textShowFn(item, index) {
				this.queryTestUsersFn(item.experiment_class_id)
				this.textIndex = index
			},
			// 选择实验平台
			selectTestPlatform(index) {
				this.platformIndex = index
				this.showPlatformOptionDialog = true
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
			// 确定值
			confirmValue(e) {
				this[this.checkEchoKey] = e.id
				this.showcheckBox = false
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
			// 设置key，并打开日历选择器
			chooseDate(keyName) {
				this.setDateForKey = keyName
				this.showCalendar = true
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
			// 获取客户账户
			queryAllCompanykhFn() {
				queryAllCompanykh({
					parentId: '',
				}).then(res => {
					if (!res.error) {
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
							id: 22
						}]
						res.obj.forEach(item => {
							this.testers.push(item)
						})
						this.textShow = true
					} else {
						this.$toast(res.error)
					}
				})
			},
			testConfirm(e) {
				console.log(e, 'eeeee')
				// this.childOrderData.forEach((item, index) => {
				// 	if (index == this.textIndex) {
				// 		item.test_user_id = val[0].value
				// 		item.test_user = val[0].label
				// 	}
				// 	console.log(item,'item')
				// })
				this.childOrderData.forEach((item, index) => {
					if (index == this.textIndex) {
						item.test_user_id = e.id
						item.testUser = e.userName
					}
				})
				console.log(this.childOrderData, 'childOrderData')
				this.textShow = false
			},

			// 提交资料
			uploadFile(type) {
				// 3 订单资料
				// 4 测试资料
				this.$uploadFile2(this.$refs[type === 3 ? 'prg' : 'prg2'], {
					type
				}).then(res => {
					this[type === 3 ? 'files' : 'testFiles'].push(res)
				})
			},

			// 确定提交
			submitData() {
				let test_user_id = []
				let line_id = []
				let checkChilds = []
				// let nums = []
				this.childOrderData.forEach(item => {
					if (item.checked) {
						checkChilds.push(item.id)
						if (item.test_user_id) test_user_id.push(item.test_user_id)
						if (item.line_id) line_id.push(item.line_id)
						// if (item.goods_nums) nums.push(item.goods_nums)
					}
				})
				if (test_user_id.length != checkChilds.length) return this.$tip('请选择测试人员')
				if (line_id.length != checkChilds.length) return this.$tip('请选择实验平台')
				// if (nums.length != checkChilds.length) return this.$tip('请输入数量')
				// for (let i = 0; i < nums.length; i++) {
				// 	if (nums[i].toString().split(".")[1]) {
				// 		let num = nums[i].toString().split(".")[1]
				// 		if (num.length != 1) return this.$tip('数量最多只保留一位小数')
				// 	}
				// }
				let obj = {
					id: this.id,
					sale_manager: this.purchaseBossId || '',
					order_time: this.order_time,
					customer_name: this.clientId || '',
					supplier_name: this.companyId || '',
					custom_user_id: this.customerAccount || '',
					sale_user: this.purchasePersonnelId || '',
					delivery_time: this.delivery_time,
					expect_finishtimes: '',
					accessoryId: this.files.map(item => item['id'] + ''),
					accessoryIdTest: this.testFiles.map(item => item['id'] + ''),
					msg: this.msg,
					test_user_ids: test_user_id.join(','),
					line_ids: line_id.join(','),
					checkChilds: checkChilds.join(','),

				}
				console.log(obj, 'obj')
				submitTestOrderChildOrderApi2(obj).then(res => {
					if (res.res) {
						uni.$emit('isEdit')
						uni.redirectTo({
							url: '/staffB/result/result?title=编辑成功'
						})
					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			preImage(idx, k) {
				let list = this[k].map(e => e.path + '/' + e.name)
				this.$preFile(idx, list)
			},

			// 获取详情
			getDetail() {

				editChildApi({
					id: this.id
				}).then(res => {
					if (res.res) {
						let {
							of: mainData,
							files,
							testFiles,
							line,
							childs
						} = res.obj
						this.orderData = mainData
						this.purchaseBossId = mainData.sale_manager
						this.clientId = mainData.customer_name
						this.companyId = mainData.supplier_name
						this.customerAccount = mainData.custom_user_id
						this.purchasePersonnelId = mainData.sale_user



						this.delivery_time = this.$alterTime(mainData.delivery_time, false)
						this.order_time = this.$alterTime(mainData.order_time, false)
						let order_status = this.orderData.order_status
						editPagexcx(this.id).then(res => {
							res.obj.saleChilds.forEach((item, index) => {
								let id = res.obj.childs.find(e => e.id == item.id)
								if (id && id.id == item.id) {
									item['checked'] = true
									const lineId = this.platformList.find(e => e
										.id == item.line_id)
									item.test_user_id = item.test_user_id ? item
										.test_user_id : ''
									item.line_id = item.line_id ? item.line_id : ''
									item.line_num = lineId.line_num
								}
							})
							this.childOrderData = res.obj.saleChilds
						})

						this.files = files
						this.testFiles = testFiles
						this.line = line
						this.msg = mainData['msg']
						if (order_status == 20 || order_status == 30 || order_status == 35 || order_status == 45 ||
							order_status == 50) {
							this.disabledCheck = true
						}
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
</style>
<style>
	.u-btn--warning {
		border-color: #3C8BDB !important;
		background-color: #3C8BDB !important;
	}

	page {
		background-color: #f2f2f2;
	}
</style>
