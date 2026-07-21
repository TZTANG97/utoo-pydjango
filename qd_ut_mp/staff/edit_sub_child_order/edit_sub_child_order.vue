<template>
	<view class="container">
		<view class="group">
			<view class="group-item" v-if="id">
				<view class="group-label">
					订单编号：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail.order_id? detail.order_id : '暂无'}}
					</view>
				</view>
			</view>

			<view class="group-item">
				<view class="group-label">
					来源订单：
				</view>
				<view class="group-content">
					<view class="text-content" style="color: #E96302;">
						{{ parentReference? parentReference: '暂无' }}
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
          实验室测试主管：
        </view>
        <view class="group-content">
          <view class="text-content" @click="select('userName', 'queryUsersList', '实验室测试主管', 'testManagerId')">
            {{ swapIdgetValue('queryUsersList', 'userName', 'testManagerId') }}
            <u-icon size="28" name="arrow-right"></u-icon>
          </view>
        </view>
      </view>
			<view class="group-item">
				<view class="group-label">
					实验分包公司：
				</view>
				<view class="group-content">
					<view class="text-content"
						@click="select('name', 'purchaseCompanyList', '进货公司', 'purchaseCompanyId')">
						{{ swapIdgetValue('purchaseCompanyList', 'name', 'purchaseCompanyId') }}
					</view>
					<u-icon size="28" name="arrow-right"></u-icon>
				</view>
			</view>

			<view class="group-item">
				<view class="group-label">
					付款方式：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'payList', '付款方式', 'payId')">
						{{ swapIdgetValue('payList', 'name', 'payId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>


			<view class="group-item" v-for="(item, index) in payDateList" :key="index">
				<view class="group-label">
					预计付款时间：
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
					<text v-if="id">预计发货时间：</text>
					<text v-else>预计完成时间：</text>
				</view>
				<view class="group-content">
					<view class="text-content" @click="chooseDate('delivery_time')">
						{{ delivery_time? delivery_time : `请选择${id? '发货' : '完成'}时间` }}
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
					进项开票类型：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'invoiceList', '进项开票类型', 'invoiceId')">
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
					订单备注：
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
					产品名称：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ item.goods_name? item.goods_name : '请选择产品名称' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品品牌：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ item.goods_brand_name? item.goods_brand_name : '请选择产品品牌' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品型号：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ item.goods_spec? item.goods_spec : '请选择产品型号' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					数量：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ item.goods_nums? item.goods_nums : '请选择产品数量' }}
					</view>
				</view>
			</view>
      <view class="group-item">
        <view class="group-label">
          测试人员：
        </view>
        <view class="group-content">
          <view class="text-content" @click="textFn(item,index)">
            {{ item.testUser ? item.testUser : '请选择测试人员' }}
          </view>
          <u-icon size="28" name="arrow-right"></u-icon>
        </view>
      </view>
			<view class="group-item">
				<view class="group-label">
					{{ id? '成本' : '分包' }}单价：
				</view>
				<view class="group-content">
					<view class="text-content">
						<input style="text-align: right;" type="digit" v-model.number.lazy="item.pcost_price"
							placeholder="请输入单价">
					</view>
				</view>
			</view>
		</view>


		<view class="confirm" @click="submitData">
			确&nbsp;定
		</view>

    <popup-bottom v-if="textShow" :show.sync="textShow" :list.sync="testers"
                  title="选择测试人员" showKey="userName" @getValue="testConfirm"></popup-bottom>
		<!-- 公用弹框-完整数据 -->
		<popup-bottom :show.sync="showcheckBox" :list.sync="checkBoxList" :title="checkBoxTitle"
			:showKey="checkBoxKeyName" @getValue="confirmValue"></popup-bottom>

		<!-- 选择日期 -->
		<u-calendar btn-type="warning" @change="confirmDate" max-date="2222-01-01" active-bg-color="#E96302 !important"
			v-model="showCalendar" mode="date"></u-calendar>
		<u-toast ref="uToast" />
	</view>
</template>

<script>
	// 弹框组件
	import popupBottom from '../popupBottom.vue'
	import uploadProgress from '../uploadProgress'
	import {
		// 详情
		editTestSubChildOrderApi,
		// 采购人员列表/销售主管列表
		fetchBunListApi,
		// 税率
		fetchTaxRateListApi,
		// 付款方式
		fetchPurchasePayWayApi,
		// 发票
		fetchInvoiceTypeListApi,
		// 实验分包公司列表
		fetchPurchaseCompanyApi,
		purchaseOriginOrderEditApi,
		// 新增实验分包子订单
		addTestSubChildOrderApi,
		fetchChildOrderListForIdApi,
		purchaseOriginOrderEditApi2

	} from '@/api/index.js'
	import {
		editPagexcx
	} from '@/api/staffB.js'
  import {queryTestUsers, queryUsersApi,queryTestUsers1Api} from "../../api";
	export default {
		components: {
			popupBottom,
			uploadProgress
		},
		data() {
			return {
				// 子订单ID
				id: '',
				// 父级订单编号
				parentReference: '',
				// 父级订单ID
				parentId: '',
				detail: null,
				// 采购主管id
				purchaseBossId: -1,
				// 实验分包公司Id
				purchaseCompanyId: -1,

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
				// 实验分包公司列表
				purchaseCompanyList: [],
				// 发票列表
				invoiceList: [],
				// 付款列表
				payList: [],
				// 税率列表
				taxRateList: [],
				// 销售主管列表
				saleBossList: [],

				// 付款时间列表
				payDateList: [],
				// 订单资料列表
				files: [],
        // 测试主管列表
        queryUsersList: [],
        testManagerId:-1,
				checkBoxTitle: '',
				showcheckBox: false,
				checkBoxList: [],
				checkBoxKeyName: '',
				checkEchoKey: '',
				// 禁止修改订单币种
				isDisabled: false,
				// 是否禁止选中产品
				disabledCheck: false,
        textShow: false,
        textind: null,
        testers: [],
			}
		},
		created() {
			Promise.all([this.getPurchaseCompanyList(), this.getInvoiceList(),
				this.getPayList(), this.getTaxRateList(), this.getpurchasePersonnelList(1),
        this.getQueryUsersApi(3)
			]).catch(err => {
				this.$tip2('数据拉取失败')
			})
		},
		onLoad(options) {
			let {
				id,
				// 父级ID
				parentId = ''
			} = options

			let title = '编辑订单'

			if (!id) {
				title = '添加订单'
			}

			uni.setNavigationBarTitle({
				title
			})



			if (id) {
				this.id = id
				this.getDetail()
			} else {
				this.parentId = parentId
				this.getChildOrderList()
			}
			editPagexcx(id).then(res => {
				res.obj.saleChilds.forEach((item, index) => {
					let id = res.obj.childs.find(e => e.id == item.id)
					if (id && id.id == item.id) {
						item['checked'] = true
					}
				})
				this.childOrderList = res.obj.saleChilds
			})
		},
		methods: {
      textFn(item, index) {
        this.queryTestUsersFn(-1)
        this.textind = index
      },
      testConfirm(e) {
        console.log(e,'eeee')
        this.childOrderList.forEach((item, index) => {
          if (index == this.textind) {
            item.testUserIdP = e.id
            item.testUser = e.userName
          }
        })
        console.log(this.childOrderList,'childOrderList')
        this.textShow = false
      },
      async queryTestUsersFn(type) {
        await queryTestUsers1Api({type}).then(res => {
          if (!res.error) {
            this.testers = res.obj
            console.log(res,'resssssss')
            this.textShow = !this.textShow
          } else {
            this.$tip(res.resMsg)
          }
        })
      },
			// 如果是新增获取子订单列表
			getChildOrderList() {
				fetchChildOrderListForIdApi({
					saleOrderId: this.parentId
				}).then(res => {
					if (res.res) {
						const {
							saleOrder,
							childs
						} = res.obj
						this.parentReference = saleOrder
						this.childOrderList = childs.map(item => {
							item['checked'] = false
							return item
						})
					} else {
						this.$tip(res.resMsg)
					}
				})
			},


			// 获取年月日
			getDate(oldDate) {
				const date = new Date()
				let hour = date.getHours(),
					min = date.getMinutes(),
					second = date.getSeconds();
				hour = hour < 10 ? '0' + hour : hour
				min = min < 10 ? '0' + min : min
				second = second < 10 ? '0' + second : second
				return `${oldDate} ${hour}:${min}:${second}`
			},

			// 提交数据
			submitData() {

				if (!this.id) {
					if (this.purchaseBossId == -1) {
						return this.$tip('请选择销售主管')
					}

					if (!this.order_time) {
						return this.$tip('请选择下单时间')
					}
          if (this.testManagerId == -1) {
						return this.$tip('请选择实验室测试主管')
					}

					if (this.purchaseCompanyId == -1) {
						return this.$tip('请选择实验分包公司')
					}

					if (this.payId == -1) {
						return this.$tip('请选择付款方式')
					}

					if (this.payId == -1) {
						return this.$tip('请选择付款方式')
					}

					if (!this.delivery_time) {
						return this.$tip(`请选择${this.id? '发货' : '完成'}时间`)
					}

					if (!this.currencyId == -1) {
						return this.$tip('请选择订单币种')
					}
				}


				if (this.payId == -1 || this.purchaseCompanyId == -1) return this.$tip2('数据无效！')
				// 数据校验
				if (this.invoiceType) {
					if (this.invoiceId == -1) {
						return this.$tip('请选择进项开票类型')
					}
					if (this.taxeId == -1) {
						return this.$tip('请选择税率')
					}
				}



				this.payDateList.forEach(e => {
					if (!e) {
						this.$tip('请选择付款时间')
						throw new Error('请选择付款时间')
					}
				})


				let newChildOrderList = this.childOrderList.filter(item => item['checked'])

				if (!newChildOrderList.length) {
					return this.$tip('请至少选择一个子订单')
				}

        let testuserids=[]
					console.log(newChildOrderList,'newChildOrderList')
				// 获取订单总价和订单数量
				// 顺便校验格式
				let totalPrice = 0,
					costPrices = [],
					idList = []
				newChildOrderList.forEach((e, i) => {
					if (!e.pcost_price) {
						this.$tip('请输入成本单价')
						throw new Error('')
					}
					idList.push(e.id)
          testuserids.push(e.testUserIdP)
					costPrices.push(e.pcost_price.toFixed(2))
					totalPrice += (e.goods_nums * e.pcost_price)
				})

				let lastOrder = newChildOrderList[newChildOrderList.length - 1],
					filesIdList = this.files.map(item => item.id + '').join(',')

				let obj = {
					saleOrderId: '',
					sale_manager: this.purchaseBossId + '',
					order_time: this.getDate(this.order_time),
					stock_company_name: this.purchaseCompanyId + '',
					totalPrice: totalPrice.toFixed(2),
					collection_time: !this.payDateList.length ? '' : this.payDateList.join(','),
					pay_way: this.payId + '',
					delivery_time: this.delivery_time,
					invoiceType: this.invoiceType,
					currency_type: this.currencyId + '',
					inBillTypeId: this.invoiceId !== -1 ? this.invoiceId + '' : '',
					taxes: this.taxeId != -1 ? this.taxRateList.find(e => e.id == this.taxeId).taxValue + '' : '',
					msg: this.msg,
					checkChilds: idList.join(','),
					costPrices: costPrices.join(','),
          test_manager:this.testManagerId+'',
          test_user_ids :testuserids.join(','),
				}

				if (filesIdList) {
					obj['accessoryId'] = filesIdList
				}

				if (this.id) {
					let {
						order_id,
						pay_status,
						parent_id,
						order_status
					} = this.detail

					obj['id'] = this.id
					obj['order_type'] = '1'
					obj['orderId'] = order_id
					obj['pay_status'] = pay_status
					obj['saleOrderId'] = parent_id
					obj['orderStatus'] = order_status
				} else {
					obj['saleOrderId'] = this.parentId
					obj['userId'] = this.syUser.userId
				}

				if (this.invoiceType) {
					obj['invoiceType'] = 'on'
				}
				console.log(obj, 'obj')
				if (this.id) {
					purchaseOriginOrderEditApi2(obj).then(res => {
						if (res.res) {
							uni.$emit('isEdit');
							uni.redirectTo({
								url: '/staffB/result/result?title=编辑成功'
							})
						} else {
							this.$tip(res.resMsg)
						}
					})
				} else {
					addTestSubChildOrderApi(obj).then(res => {
						if (res.res) {
							uni.$emit('isEdit');
							uni.redirectTo({
								url: '/staffB/result/result?title=添加成功'
							})
						} else {
							this.$tip(res.resMsg)
						}
					})
				}
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

			// 发票开关
			invoiceSwitch(e) {
				if (!e) {
					this.invoiceId = -1
					this.taxeId = -1
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
				if (titleName == '订单币种' && this.isDisabled) {
					return this.$tip(`付款之后不能更改订单币种`)
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
				editTestSubChildOrderApi({
					id: this.id
				}, false).then(res => {
					if (res.res) {
						this.detail = res['obj']['of']

						let {
							of: {
								sale_manager,
								stock_company_name,
								totalPrice,
								pay_way,
								currency_type,
								taxes,
								inBillType,
								invoiceType,
								// 下单时间
								order_time,
								// 发货时间
								delivery_time,
								msg,
								order_status,
								parentOf,
                test_manager
							},
							collectionTimes = [],
							files,
							isDisabled,
							// 当前订单的产品列表
							childs,
							// 全部的产品列表
							saleChilds,
						} = res.obj

						uni.showLoading({
							title: '数据渲染中...',
							mask: true
						})

						this.parentReference = parentOf ? parentOf.order_id : ''
						this.order_time = this.$alterTime(order_time, false)
						this.delivery_time = this.$alterTime(delivery_time, false)
						this.payDateList = collectionTimes
						this.files = files
						this.testManagerId = test_manager

						this.msg = msg

						// childs.forEach(item => {
						// 	item['checked'] = true
						// })

						// saleChilds.forEach(item => {
						// 	// 已取消的产品
						// 	if (item['orderStatus'] == 1) {
						// 		item['checked'] = false
						// 		childs.push(item)
						// 	}
						// })



						// this.childOrderList = childs

						// 销售主管
						if (sale_manager) {
							this.purchaseBossId = sale_manager
						}

						// 进货公司
						if (stock_company_name) {
							this.purchaseCompanyId = stock_company_name
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
						if (inBillType) {
							this.invoiceId = inBillType.id
						}

						// 防止税率为0
						let id = this.taxRateList.find(e => e.id == taxes)
						if(id) this.taxeId = id.id


						// 是否开票
						this.invoiceType = invoiceType == 1 ? true : false

						// 禁止修改订单币种
						this.isDisabled = isDisabled



						// 禁止选中
						if (order_status == 20 || order_status == 30 || order_status == 35 || order_status == 45 ||
							order_status == 50) {
							this.disabledCheck = true
						}

						uni.hideLoading()

					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			// 获取进货公司列表
			getPurchaseCompanyList() {
				fetchPurchaseCompanyApi().then(res => {
					if (res.res) {
						this.purchaseCompanyList = res.obj
					} else {
						this.$tip(res.resMsg)
					}
				})
			},

			//  获取发票
			getInvoiceList() {
				fetchInvoiceTypeListApi({
					type: 2
				}).then(res => {
					if (res.res) {
						this.invoiceList = res.obj
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
						this.saleBossList = res.obj
					} else {
						this.$tip(res.resMsg)
					}
				})
			},
      getQueryUsersApi(type) {
        queryUsersApi({type}).then(res => {
					if (res.res) {
            console.log(res,'res')
						this.queryUsersList = res.obj
					} else {
						this.$tip(res.resMsg)
					}
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
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
