import r from '@/request/index.js'
import Vue from 'vue'

// 个人认证
export function personAuthApi(data) {
	return r({
		url: `/wx/addOrUpdateUserData.ajax`,
		method: 'post',
		data
	})
}

// 获取我的认证信息
export function getPersonAuthInfoApi() {
	return r({
		url: `/wx/getIdentifyData.ajax`,
	})
}

// 清空认证信息
export function clearAuthInfoApi() {
	return r({
		url: '/wx/clearBindData.ajax',
	})
}

// 上传文件
export function uploadFileApi(params) {
	console.log(params, 'params')
	return new Promise((resolve, reject) => {
		const {
			filePath = '', reqUrl = '', name = '', formData = {}
		} = params
		console.log(formData, 'formData')
		console.log(name, 'name')
		uni.uploadFile({
			url: Vue.prototype.$baseUrl + reqUrl,
			filePath,
			header: {
				'token': uni.getStorageSync('token'),
				'X-Channel': 'wx',
			},
			name,
			formData,
			success(res) {
				if (res.statusCode === 200) {
					resolve(JSON.parse(res.data))
				} else {
					uni.showToast({
						title: '上传失败'
					})
					reject()
				}
			},
			fail() {
				uni.showToast({
					title: '上传失败'
				})
				reject()
			}
		})
	})
}


// 企业认证
export function companyAuthApi(data) {
	return r({
		url: `/wx/addOrUpdateUserCompanyData.ajax`,
		method: 'post',
		data
	})
}

// 预约实验
export function subTestApi(data) {
	return r({
		url: '/wx/serviceConsultAdd.ajax',
		method: 'post',
		data
	})
}

// 获取实验
export function getTestListApi(data) {
	return r({
		url: '/wx/expMakeList.ajax',
		data
	})
}

// 获取实验订单列表
export function fetchTestOrderListApi(data) {
	return r({
		url: '/experimentOrder/list.ajax',
		method: 'post',
		data
	})
}

// 获取实验订单子订单列表
export function fetchTestChildOrderListApi(data) {
	return r({
		url: '/experimentOrder/getChildFormByIdExp.ajax',
		method: 'post',
		data,
	})
}

// 实验订单详情
export function fetchCheckPendingTestOrderDetailApi(data) {
	return r({
		url: '/experimentOrder/orderdetail.ajax',
		method: 'post',
		data,
	})
}

// 实验订单取消
export function cancelTestOrderApi(data) {
	return r({
		url: '/experimentOrder/customeOperateCancel.ajax',
		method: 'post',
		data
	})
}

// 实验订单所有成本已结清
export function settlementTestOrderCostApi(data) {
	return r({
		url: '/experimentOrder/costSettleSure.ajax',
		method: 'post',
		data
	})
}

// 实验订单提交审核
export function submitAuditTestOrderApi(data) {
	return r({
		url: '/experimentOrder/submitAuditExp.ajax',
		method: 'post',
		data
	})
}

// 实验订单取消提交审核
export function cancelAuditTestOrderApi(data) {
	return r({
		url: '/experimentOrder/updateStatus.ajax',
		method: 'post',
		data
	})
}

// 开票
export function saleOrderOpenBillApi(data) {
	return r({
		url: '/bill/addBillData.ajax',
		method: 'post',
		data
	})
}

// 评价客户
export function evaluateClientApi(data) {
	return r({
		url: '/eveluateCompany/saveEveluate.ajax',
		data
	})
}

// 待审核实验订单通过
// 1通过 2拒绝
export function handleCheckPendingTestOrderApi(data) {
	return r({
		url: '/experimentOrder/auditOrder.ajax',
		method: 'post',
		data,
	})
}

// 和客户沟通确认
export function communicateConfirmForClientApi(data) {
	return r({
		url: '/saleOrder/makeFrontOrder.ajax',
		method: 'post',
		data
	})
}

// 获取销售订单产品列表
export function fetchDevideUserListApi(data = {
	exceptUserId: ''
}) {
	return r({
		// &exceptUserId=${data.exceptUserId?data.exceptUserId : ''}
		url: `/sys/user/queryUsersExcept.ajax?type=-1`,
		data,
	})
}

// 更新分成信息
export function updateDevideInfoApi(data) {
	return r({
		url: '/experimentOrder/updateShareRatio.ajax',
		method: 'post',
		data
	})
}


// 获取实验分包订单列表
export function fetchSubOrderListApi(data) {
	return r({
		url: '/experimentSubOrder/list.ajax',
		method: 'post',
		data,
	})
}

// 获取实验分包订单产品列表
export function fetchSubChildOrderListApi(data) {
	return r({
		url: '/experimentSubOrder/getChildFormByIdExp.ajax',
		method: 'post',
		data
	})
}

// 实验分包订单详情
export function fetchCheckPendingTestSubOrderDetailApi(data) {
	return r({
		url: '/experimentSubOrder/orderdetail.ajax',
		method: 'post',
		data
	})
}

// 实验分包订单已结清
export function settlementTestSubOrderApi(data) {
	return r({
		url: '/experimentSubOrder/costSettleSure.ajax',
		method: 'post',
		data
	})
}

// 调整分成
export function adjustDevideApi(data) {
	return r({
		// url: '/saleOrder/updateShareRatio.ajax',
		url:'/experimentSubOrder/updateShareRatio.ajax',
		data,
		method: 'post'
	})
}


// 取消实验分包订单
export function cancelTestSubOrderApi(data) {
	return r({
		url: '/experimentSubOrder/customeOperateCancel.ajax',
		method: 'post',
		data
	})
}

// 调租订单：评价客户
export function tzEvaluateClientApi(data) {
	return r({
		url: '/eveluateCompany/saveEveluateNew.ajax',
		data
	})
}

// 取消实验分包订单审核申请
export function cancelTestSubOrderAuditApplicationApi(data) {
	return r({
		url: '/experimentSubOrder/updateStatus.ajax',
		method: 'post',
		data
	})
}

// 待审核实验分包子订单通过/拒绝
// 1通过 2拒绝
export function handleCheckPendingTestSubOrderApi(data) {
	return r({
		url: '/experimentSubOrder/auditOrder.ajax',
		method: 'post',
		data
	})
}

// 实验分包提交审核
export function submitAuditForTestSubOrderApi(data) {
	return r({
		url: '/experimentSubOrder/submitAuditExp.ajax',
		method: 'post',
		data
	})
}


// 获取实验分包子订单
export function fetchTestSubChildOrder(data) {
	return r({
		url: '/expSubPurchaseOrder/getOrdersBySaleOrderId.ajax',
		method: 'post',
		data,
	})
}

// 实验分包子订单详情
export function fetchCheckPendingTestSubChildOrderDetailApi(data) {
	return r({
		url: '/expSubPurchaseOrder/orderdetail.ajax',
		method: 'post',
		data,
	})
}

// 检查实验分包子订单的状态
export function checkTestSubChildOrderStatusApi(data) {
	return r({
		url: '/experimentSubOrder/getOrderStatus.ajax',
		method: 'post',
		data,
	})
}

// 实验分包子订单取消订单
export function cancelTestSubChildOrderApi(data) {
	return r({
		// url: '/purchaseOrderController/cancelOperate.ajax',
		url: '/expSubPurchaseOrder/cancelOperate.ajax',
		method: 'post',
		data
	})
}
// 实验子订单取消订单
export function cancelOperatExperimentChild(data) {
	return r({
		url: '/experimentChildOrder/cancelOperate.ajax?type=0&id=' + data,
		method: 'get',
	})
}

// 实验分包子订单申请付款
export function putInPayTestSubChildOrderApi(data) {
	return r({
		url: '/expSubPurchaseOrder/pay.ajax',
		method: 'post',
		data
	})
}

// 实验分包子订单确认已下单
export function confirmOrderTestSubChildOrderApi(data) {
	return r({
		url: '/expSubPurchaseOrder/addOrderData.ajax',
		method: 'post',
		data
	})
}

// 实验分包子订单厂家已发货
export function shipmentsTestSubChildOrderApi(data) {
	return r({
		url: '/expSubPurchaseOrder/updateOrderStatus.ajax',
		method: 'post',
		data
	})
}

// 实验分包子订单编辑功能
export function editTestSubChildOrderApi(data) {
	return r({
		url: `/expSubPurchaseOrder/editPage.ajax`,
		data
	})
}

// 获取业务/公司人员名单
export function fetchBunListApi(data) {
	return r({
		url: '/sys/user/queryUsers.ajax',
		data
	})
}

// 获取税率
export function fetchTaxRateListApi(data) {
	return r({
		url: '/taxesConfig/getAllConfigs.ajax',
		data
	})
}

// 获取采购偶订单付款方式
export function fetchPurchasePayWayApi(data) {
	return r({
		url: '/consumePaytype/getallptype.ajax',
		method: 'post',
	})
}

// 获取发票类型
export function fetchInvoiceTypeListApi(data) {
	return r({
		url: '/billtype/allBill.ajax',
		data
	})
}

// 采购订单获取公司
export function fetchPurchaseCompanyApi() {
	return r({
		url: '/member/loadCGStockCompanyNames.ajax',
		method: 'post',
	})
}

// 待付款采购订单编辑功能,包含来源订单的
export function purchaseOriginOrderEditApi(data) {
	return r({
		url: '/purchaseOrderController/updateOrder.ajax',
		method: 'post',
		data
	})
}
export function purchaseOriginOrderEditApi2(data) {
	return r({
		url: '/expSubPurchaseOrder/updateOrder.ajax',
		method: 'post',
		data
	})
}
// 测试主管
export function queryUsersApi(data) {
	return r({
		url: '/sys/user/queryUsers.ajax',
		data
	})
}
// 测试人员
export function queryTestUsers1Api(data) {
	return r({
		url: '/sys/user/queryTestUsers1.ajax',
		data
	})
}

// 新增实验分包子订单
export function addTestSubChildOrderApi(data) {
	return r({
		url: '/expSubPurchaseOrder/submitOrder.ajax',
		method: 'post',
		data
	})
}

// 获取实验分包子订单
export function fetchChildOrderListForIdApi(data) {
	return r({
		url: '/expSubPurchaseOrder/createOrderPage.ajax',
		method: 'post',
		data
	})
}
// 编辑实验订单
export function fetchEditTestOrderDetailApi(data) {
	return r({
		url: '/experimentOrder/editPage.ajax',
		method: 'post',
		data,
	})
}

// 获取公司列表
export function fetchCompanyListApi(data) {
	return r({
		url: '/supplier/queryAll.ajax',
		data
	})
}

// 客户名称列表
export function fetchClientListApi(data) {
	return r({
		url: '/member/loadCustomerNames.ajax',
		data
	})
}

// 实验分包子订单列表
export function fetchTestSubGoodsListApi(data) {
	return r({
		url: '/experimentGoods/list.ajax',
		method: 'post',
		data,
	})
}

// 根据所选规格获取参考报价
export function fetchPriceApi(data) {
	return r({
		url: '/goods/selectPriceByskuId.ajax',
		data,
	})
}

// 保存实验订单
export function saveTestOrderApi(data) {
	return r({
		url: '/experimentOrder/editSaveFormExp.ajax',
		method: 'post',
		data,
		cType: 'application/json',
	})
}


// 获取测试实验项目
export function fetchTestProductGoodsListApi(data) {
	return r({
		url: '/experimentProject/list.ajax',
		method: 'post',
		data,
	})
}

// 新增实验订单
export function addTestOrderApi(data) {
	return r({
		url: '/experimentOrder/submitExpOrder.ajax',
		method: 'post',
		cType: 'application/json',
		data
	})
}

// 实验订单分包订单编辑
export function editTestSubOrderApi(data) {
	return r({
		url: '/experimentSubOrder/editPage.ajax',
		method: 'post',
		data,
	})
}

// 保存实验分包订单编辑
export function saveTestSubOrderApi(data) {
	return r({
		url: '/experimentSubOrder/editSaveFormExpSub.ajax',
		method: 'post',
		data,
		cType: 'application/json',
	})
}

// 新增实验分包订单
export function addTestSubOrderApi(data) {
	return r({
		url: '/experimentSubOrder/submitExpSubOrder.ajax',
		method: 'post',
		cType: 'application/json',
		data
	})
}


// 获取实验子订单详情
export function fetchTestOrderChildOrderDetailApi(id) {
	return r({
		url: '/experimentOrder/checkChildOrder.ajax?id=' + id,
	})
}

// 实验子订单 样品到货，取消订单
export function sampleAOGandCancelApi(data) {
	return r({
		url: '/experimentOrder/updateChildStatus.ajax',
		method: 'post',
		data
	})
}


// 实验子订单-开始/完成 测试
// 1开始 2完成
export function testOrderChildOrderTestApi(data) {
	return r({
		url: '/experimentOrder/operateTest.ajax',
		method: 'post',
		data
	})
}

// 获取实验平台列表
export function fetchTestPlatformListApi(data) {
	return r({
		url: '/lab/selLineList.ajax',
		method: 'post',
		data
	})
}

// 修改实验子订单
export function submitTestOrderChildOrderApi(data) {
	return r({
		url: '/experimentOrder/editSaveChildForm.ajax',
		method: 'post',
		cType: 'application/json',
		data
	})
}
export function submitTestOrderChildOrderApi2(data) {
	return r({
		url: '/experimentChildOrder/updateOrder.ajax',
		method: 'post',
		data
	})
}



// 获取全部分类
export function fetchCateListApi(id) {
	return r({
		url: '/wx/selFirAndSecClassList.ajax',
		// url: '/pc/indexClassList.ajax',
	})
}

// 搜索
export function seatchTestApi(data) {
	return r({
		url: '/pc/selThirdClassByKeyWordList.ajax',
		data
	})
}


// 根据二级获取三级
export function fetchCate3ListApi(data) {
	return r({
		url: '/pc/selThirdClassList.ajax',
		data
	})
}

// 修改订单的支付状态
export function changeOrderPayStatusApi(data) {
	return r({
		url: '/wx/pay.ajax',
		data
	})
}


// 获取生成的预约单pdf链接
export function fetchPDFUrlApi(data) {
	return r({
		url: '/pc/printYyd.ajax',
		data
	})
}


// 获取所有二级分类
export function fetchCate2ListApi(data) {
	return r({
		url: '/wx/selSecondClassList.ajax',
		data
	})
}


// 获取项目介绍
export function fetchProjectIntroduceApi(id) {
	return r({
		url: `/pc/xcxtestClassDetail.ajax?id=${id}`,
	})
}

// 获取首页一,二级菜单
export function fetchGradeMenus(param) {
	return r({
		url: '/index/app_index_class.ajax',
		data: param
	})
}

// 获取首页下拉菜单
export function fetchPullDownMenus(param) {
	return r({
		url: '/index/store_house_list.ajax',
		md: 'post',
		data: param
	})
}
export function fetchDeviceListApi(param) {
	return r({
		url: '/index/app_index.ajax',
		data: param
	})
}
export function fetchDeviceDetailApi(param) {
	return r({
		url: '/index/app_goods.ajax',
		data: {
			goodsSpec: param.goodsSpec,
			...param
		}
	})
}

// 扫码注册时保存用户信息
export function regingSaveUserInfoApi(data) {
	return r({
		url: '/wx/userInfoAdd.ajax',
		data
	})
}


// 获取我的预约单
export function fetchMyMakeOrderListApi(data) {
	return r({
		url: '/pc/myExpMakeList.ajax',
		data
	})
}


// 获取我的资产金额
export function fetchMyAssetsApi() {
	return r({
		url: '/wx/center/getAccount.ajax',
	})
}


// 获取我的资产页面的订单列表
export function fetchAssetsListApi(data) {
	return r({
		url: '/pc/experimentOrderList.ajax',
		data
	})
}


// 获取我的发票列表
export function fetchinvoiceListApi(data) {
	return r({
		url: '/pc/center/getInvoiceList.ajax',
		data
	})
}


// 取消开票
export function cancelInvoiceApi(data) {
	return r({
		url: '/pc/cancelInvoiceInfo.ajax',
		data,
	})
}


// 获取默认开票信息
export function fetchDefaultInvoiceInfoApi(data) {
	return r({
		url: '/center/getInvoiceInfo.ajax',
		data,
	})
}

// 获取可开票列表
export function fetchTrueMakeInvoiceListApi(data) {
	return r({
		url: '/pc/center/getInvoiceOrderList.ajax',
		data,
	})
}

// 获取用户认证信息
export function fetchUserBandInfoApi(data) {
	return r({
		url: '/pc/center/getInvoiceInfo.ajax',
		data,
	})
}

// 开票
export function confirmMakeInvoiceApi(data) {
	return r({
		url: '/wx/center/applyInvoice.ajax',
		method: 'post',
		data,
		cType: 'application/json'
	})
}


// 获取预约单详情
export function fetchSubOrderDetailApi(data) {
	return r({
		url: '/wx/reservationDetail.ajax',
		data,
	})
}


// 合并实验订单和实验分包订单
export function fetchOrderListApi(data) {
	return r({
		url: '/wx/myExperimentOrderList.ajax',
		data,
	})
}

// 获取默认的发票信息
export function fetchDefaultinvoiceInfoApi(data) {
	return r({
		url: '/wx/center/getInvoiceInfo.ajax',
		data,
	})
}


// 查看卡片是否过期
export function checkCardIsExpired(data) {
	return r({
		url: '/wx/ticketIsExist.ajax',
		data,
	})
}


// 内部账号绑定微信
export function bindWxAccountApi(data) {
	return r({
		url: '/wx/bindaccount.ajax',
		data,
	})
}


// 内部账号解绑微信
export function relieveBindWxAccountApi() {
	return r({
		url: '/wx/securebind.ajax',
	})
}


// 添加发票信息
export function addInvoiceInfoApi(data) {
	return r({
		// url: '/wx/addInvoiceInfo.ajax',
		url: '/wx/insertinvoiceInfo.ajax',
		data
	})
}


// 提现
export function withdrawApi(data) {
	return r({
		url: '/wx/addCash.ajax',
		data
	})
}


// 线下支付
export function offlinePayApi(data) {
	return r({
		url: '/wx/addRecharge.ajax',
		data
	})
}

// 还款列表
export function fetchRepaymentListApi(data) {
	return r({
		url: '/wx/myExperimentOrderList.ajax',
		data
	})
}

// 余额还款
export function balanceRepaymentApi(data) {
	return r({
		url: '/wx/amountPay.ajax',
		data
	})
}

// 获取普通用户订单详情
export function fetchOrderDetailApi(data) {
	return r({
		url: '/experimentOrder/orderdetail.ajax',
		data
	})
}


// 获取普通用户实验子订单订单详情
export function fetchTestChildOrderListApi2(data) {
	return r({
		url: '/experimentChildOrder/getOrdersBySaleOrderId.ajax',
		data
	})
}

// 实验子订单详情
export function fetchTestChildOrderDetailApi(data) {
	return r({
		url: '/experimentChildOrder/orderdetail.ajax',
		data
	})
}

// 获取默认收款账户和公司
export function fetchDefaultAccountApi() {
	return r({
		url: '/pc/selDefaultAccount.ajax',
	})
}


// 提交评价
export function submitEvaluateApi(data) {
	return r({
		url: '/wx/writeevaluate.ajax',
		method: 'post',
		data
	})
}


// 确认完成
export function confirmCompleteApi(data) {
	return r({
		url: '/experimentChildOrder/sureOk.ajax',
		data
	})
}

// 复测
export function anewTestApi(data) {
	return r({
		url: '/retestapplication/addretestapplication.ajax',
		method: 'post',
		cType: 'application/json',
		// header:{
		// 	'Content-Type': 'application/json',
		// },
		data
	})
}


// 获取preid
export function fetchOrderPrePayId(data) {
	return r({
		url: '/wx/prePay.ajax',
		data
	})
}

// 获取积分
export function fetchMyPointsApi() {
	return r({
		url: '/pc/getIntegral.ajax',
	})
}

// 获取积分列表
export function fetchMyPointsListApi(data) {
	return r({
		url: '/pc/center/getIntegralList.ajax',
		data
	})
}

// 充值
export function rechargeToBalanceApi(data) {
	return r({
		url: '/wx/rechargePrePay.ajax',
		data
	})
}

// 还款
export function repaymentApi(data) {
	return r({
		url: '/wx/preAmountPay.ajax',
		data
	})
}

// 扫码操作
export function scanOperateApi(data) {
	return r({
		url: '/wx/scanCodeOperate.ajax',
		data
	})
}

export function confirmsave(data) {
	return r({
		url: '/experimentChildOrder/confirmsave.ajax',
		data,
		method: 'get',
	})
}

// 获取banner
export function getBannerApi() {
	return r({
		url: '/wx/bannerList.ajax',
	})
}

// 获取普通用户得页面得数量
export function getUserNumberApi() {
	return r({
		url: '/wx/myInfo.ajax',
		showLoading: false
	})
}


// 获取可复测和完成的子订单列表数据
export function getFinishChildOrderListApi(data) {
	return r({
		url: '/pc/selTestOrSure.ajax',
		data
	})
}


// 获取内部用户的订单产品列表
export function getOrderProductListApi(data) {
	return r({
		url: '/experimentOrder/getChildFormByIdExp_dpt.ajax',
		data
	})
}

// 内部人员获取实验订单
export function adminFetchTestOrderListApi(data) {
	return r({
		url: '/experimentOrder/list_dpt.ajax',
		data
	})
}

// 内部人员获取实验分包订单
export function adminFetchTestSubOrderListApi(data) {
	return r({
		url: '/experimentSubOrder/list_dpt.ajax',
		data
	})
}

// 内部人员获取实验分包子订单
export function adminFetchTestSubChildOrderListApi(data) {
	return r({
		url: '/expSubPurchaseOrder/list_dpt1.ajax',
		data
	})
}

// 内部人员获取实验子订单
export function adminFetchTestChildOrderListApi(data) {
	return r({
		url: '/experimentChildOrder/list_dpt.ajax',
		data
	})
}

// 获取发票明细记录
export function fetchInvoiceDetailListApi(data) {
	return r({
		url: '/pc/center/getInvoiceLogList.ajax',
		data
	})
}

// 获取记录
export function fetchHistoryApi(data) {
	return r({
		url: '/pc/selRechargeList.ajax',
		data
	})
}

// 待申请发票，待支付订单
export function fetchNoPayOrderListApi(data) {
	return r({
		url: '/pc/myExperimentOrderList.ajax',
		data
	})
}

// 取消预约
export function cancelConsultApi(id) {
	return r({
		url: '/pc/cancelConsult.ajax?id=' + id,
	})
}

// 子订单审核
export function childAuditApi(data) {
	return r({
		url: '/experimentChildOrder/auditOrder.ajax',
		data
	})
}

// 分包子订单审核
export function subChildAuditApi(data) {
	return r({
		url: '/expSubPurchaseOrder/auditOrder.ajax',
		data
	})
}

// 子订单取消审核申请
export function cancelChildApplyApi(data) {
	return r({
		url: '/experimentChildOrder/updateStatus.ajax',
		data
	})
}

// 分包子订单取消审核申请
export function cancelSubChildApplyApi(data) {
	return r({
		url: '/expSubPurchaseOrder/updateStatus.ajax',
		data
	})
}

// 子订单发起审核申请
export function childSubmitApplyApi(data) {
	return r({
		url: '/experimentChildOrder/submitAuditExp.ajax',
		data
	})
}


// 分包子订单发起审核申请
export function subChildSubmitApplyApi(data) {
	return r({
		url: '/expSubPurchaseOrder/submitAuditExp.ajax',
		data
	})
}

// 编辑子订单
export function editChildApi(data) {
	return r({
		url: '/experimentChildOrder/editPage.ajax',
		data
	})
}

// 获取稳定性数据
export function getStabilityList(params) {
	return r({
		url: '/ordersampleinfomation/getStabilityList.ajax',
		params
	})
}

// 获取属性状态数据
export function getAttributeStateList(params) {
	return r({
		url: '/ordersampleinfomation/getAttributeStateList.ajax',
		params
	})
}

// 创建实验子订单接口
export function exCcreateOrderPage(data) {
	return r({
		url: '/experimentChildOrder/createOrderPage.ajax',
		method: 'post',
		data,
	})
}

// 创建实验分包子订单接口
export function esCreateOrderPage(data) {
	return r({
		url: '/expSubPurchaseOrder/createOrderPage.ajax',
		method: 'post',
		data,
	})
}

// 获取客户账户
export function queryAllCompanykh(params) {
	return r({
		url: '/member/queryAllCompanykh.ajax',
		params,
	})
}

// 获取测试人员
export function queryTestUsers(classid) {
	return r({
		url: '/sys/user/queryTestUsers.ajax?type=-1&classid=' + classid,
	})
}

// 获取积分兑换比
export function getIntegralConvertRatio() {
	return r({
		url: '/pc/getIntegralConvertRatio.ajax',
	})
}
// 获取预约信息
export function sampleattributemanageList(special_type) {
	return r({
		url: '/sampleAttributeManage/sampleattributemanageList.ajax?special_id=' + special_type,
	})
}

// 创建实验子订单
export function exSubmitOrder(data, classId) {
	return r({
		url: '/experimentChildOrder/submitOrder.ajax?class_id=' + classId,
		method: 'post',
		data,
		// cType:'pplication/json;charset=UTF-8',
	})
}

// 创建实验分包子订单
export function expSubmitOrder(data, classId) {
	return r({
		url: '/expSubPurchaseOrder/submitOrder.ajax?class_id=' + classId,
		method: 'post',
		data,
	})
}
// 我的审核
export function getAuditOrderList(orderId, orderType, draw, length, start) {
	return r({
		url: `/wx/getAuditOrderList.ajax?orderId=${orderId}&orderType=${orderType}&draw=${draw}&length=${length}&start=${start}`,
	})
}
// 账户资金详情
export function selExpSumByYearxcx(statistics_time) {
	return r({
		url: '/selExpSumByYearxcx.ajax?statistics_time=' + statistics_time,
	})
}
// 明细列表
export function getLog(params) {
	return r({
		url: '/wx/getLog.ajax' + params,
	})
}
// 明细列表
export function getOrderCount() {
	return r({
		url: '/wx/getOrderCount.ajax',
		showLoading: false
	})
}
// 发票列表
export function getInvoiceInfoData() {
	return r({
		url: '/wx/getinvoiceInfo.ajax',
	})
}
// 修改发票
export function updateinvoiceInfo(data) {
	return r({
		url: '/wx/updateinvoiceInfo.ajax',
		data
	})
}
// 设置默认发票
export function delinvoiceInfo(data) {
	return r({
		url: '/wx/delinvoiceInfo.ajax',
		data
	})
}
// 订单类型
export function queryAll(data) {
	return r({
		url: '/experimentManage/queryAll.ajax?type=3',
		data
	})
}

// 积分签到
export function signInIntegral(data) {
	return r({
		url: '/wx/signInIntegral.ajax',
		data
	})
}

// 个人信息
export function getbindstatus(data) {
	return r({
		url: `/wx/getbindstatus.ajax`,
	})
}

// 加载封面
export function getXcxBanner(data) {
	return r({
		url: `/pc/getXcxBanner.ajax`,
	})
}

// 提交提案改善
export function addProposalImprove(data) {
	return r({
		url: '/productOrder/addProposalImprove.ajax',
		data		
	})
}
export function isFlag(data) {
	return r({
		url: '/wx/isFlag.ajax',
		data		
	})
}
