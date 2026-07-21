<template>
	<view class="container">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					来源订单：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{sonDetial.saleOrder}}
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
					<view class="text-content" @click="select('name', 'clientList', '实验分包公司', 'clientId')">
						{{ swapIdgetValue('clientList', 'name', 'clientId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					预计完成时间：
				</view>
				<view class="group-content">
					<view class="text-content" @click="chooseDate('delivery_time')">
						{{ delivery_time? delivery_time : '请选择完成时间' }}
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
					是否开票：
				</view>
				<view class="group-content">
					<view class="text-content">
						<u-switch @change="invoiceSwitch" v-model="invoiceType" active-color="#E96302" size="28">
						</u-switch>
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
					<view class="text-content">
						{{ item.goodsName? item.goodsName : '请选择产品名称' }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品型号：
				</view>
				<!-- @click="chooseProductModel(item, index)" -->
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
						<!-- @input="getTotal" -->
						<input :disabled="!item.newAdd" class="child-order-input" type="digit"
							v-model.number.lazy="item.goodsNums" placeholder="请输入数量">
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
					实验测试项目：
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ item.experiment_project_name? item.experiment_project_name : '请选择实验测试项目'}}
					</view>
					<u-icon v-if="item.newAdd" size="28" name="arrow-right"></u-icon>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					分包单价：
				</view>
				<view class="group-content">
					<view class="text-content">
						<input class="child-order-input" type="digit" v-model.number.lazy="item.cost_price">
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
	import devideInto from '../devideInto.vue'
	import uploadProgress from '../uploadProgress'
	import {
		// 详情
		esCreateOrderPage,
		// 采购人员列表/销售主管列表
		fetchBunListApi,
		// 税率
		fetchTaxRateListApi,
		// 付款方式
		fetchPurchasePayWayApi,
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
		expSubmitOrder
	} from '@/api/index.js'
	import {
		createOrderPagexcx
	} from '@/api/staffB.js'
  import {queryTestUsers1Api, queryUsersApi} from "../../api";
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
				// 采购主管id
				purchaseBossId: -1,
				// 客户id
				clientId: -1,

				// 总价,可以修改的
				totalPrice: 0,
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
				// 完成时间
				delivery_time: '',

				// 备注
				msg: '',

				sonDetial: {},

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


				checkBoxTitle: '',
				showcheckBox: false,
				checkBoxList: [],
				checkBoxKeyName: '',
				checkEchoKey: '',
				class_id: 0,
				saleOrderId: 0,
				disabledCheck: false,
        // 测试主管列表
        queryUsersList: [],
        testManagerId:-1,
        textShow: false,
        textind: null,
        testers: [],
			}
		},
		onLoad(options) {
			let {
				class_id,
				id
			} = options
			this.class_id = class_id
			this.saleOrderId = id
			esCreateOrderPage({
				saleOrderId: id
			}).then(res => {
				this.sonDetial = res.obj
			})
			// 获取可选产品列表
			createOrderPagexcx(id).then(res => {
				console.log(res, 'res666')
				res.obj.childs.forEach(item => {
					item['checked'] = false
				})
				this.childOrderList = res.obj.childs
			})
			let title = '创建实验分包子订单'

			uni.setNavigationBarTitle({
				title
			})

			// 获取一些必要的基本数据
			const rquestArr = [this.getPurchaseCompanyList(), this.getInvoiceList(),
				this.getPayList(), this.getTaxRateList(), this.getpurchasePersonnelList(1), this
				.getpurchasePersonnelList(-1),this.getQueryUsersApi(3)
			]
			Promise.all(rquestArr).catch(err => {
				this.$tip2('数据拉取失败')
			})
		},
		methods: {
      getQueryUsersApi(type) {
        queryUsersApi({type}).then(res => {
          if (res.res) {
            console.log(res,'res')
            this.queryUsersList = res.obj
          } else {
            this.$tip(res.resMsg)
          }
        })
      },
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
			// 提交数据
			submitData() {

				if (!this.order_time) {
					return this.$tip('请选择下单时间')
				}

				if (this.clientId == -1) {
					return this.$tip('请选择客户')
				}

				if (this.purchaseBossId == -1) {
					return this.$tip('请选择销售主管')
				}

        if (this.testManagerId == -1) {
          return this.$tip('请选择实验室测试主管')
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
				let arr = []
				let idList = []
				let fileId = []
				let costPrices = []
        let testuserids=[]
        let num = 0
				this.files.forEach(item => {
					fileId.push(item.id)
				})
				newChildOrderList.forEach(item => {
					if (item.cost_price) {
            costPrices.push(item.cost_price)
            num+=Number(item.cost_price)
          }
					idList.push(item.id)
          if (item.testUserIdP) {
            testuserids.push(item.testUserIdP)
          }

					arr.push({
						orderId: item.orderId,
						goodsName: item.goodsName,
						goodsSpec: item.goodsSpec,
						goodsBrandName: item.goodsBrandName,
						goodsNums: item.goodsNums,
						experiment_project_name: item.experiment_project_name,
						costPrice: item.cost_price,
					})
				})
				console.log(costPrices,'costPrices')
				if (costPrices.length != idList.length) return this.$tip('请输入分包单价')
        console.log(testuserids,idList,'ssssssss')
				if (testuserids.length != idList.length) return this.$tip('请选择测试人员')
				let obj = {
					saleOrderId: this.saleOrderId,
					collection_time: this.payDateList.length == 0 ? '' : this.payDateList, // 预计付款时间
					sale_manager: this.purchaseBossId, // 销售主管
					order_time: this.order_time, // 下单时间
					stock_company_name: this.clientId, // 实验分包公司
					delivery_time: this.delivery_time, // 预计完成时间
					pay_way: this.payId, // 付款方式
					invoiceType: this.invoiceType, // 是否开票
					currency_type: this.currencyId, // 订单币种
					inBillTypeId: this.invoiceId, // 进项开票类型
					taxes: this.taxeId, // 税率
					orderdata: fileId.join(','), // 订单资料
					msg: this.msg, // 订单备注
					childs: JSON.stringify(arr),
					checkChilds: idList.join(','),
					costPrices: costPrices.join(','),
          test_manager:this.testManagerId+'',
          test_user_ids :testuserids.join(','),
          totalPrice:num,
				}
				expSubmitOrder(obj, this.class_id).then(res => {
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
				console.log(this.setDateForKey, 'setDateForKey')
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
					console.log('确定值', this.payDateList)
				}
				this.showcheckBox = false
			},

			// 选择
			select(keyName, listName, titleName, echoKey) {

				if (this.id) {
					// 采购类别
					if (titleName == '订单币种') {
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
						// 采购人员,分成人员
						if (type == -1) {} else {
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
