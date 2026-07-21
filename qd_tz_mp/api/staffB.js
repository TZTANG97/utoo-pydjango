import r from '@/request/index.js'

// 充值申请
export function accountLogAdd1(data) {
	return r({
		url: `/funds/accountLog_add.ajax?accType=1&accountAdd=2`,
		method: 'post',
		data
	})
}
// 提现申请
export function accountLogAdd2(data) {
	return r({
		url: `/funds/accountLog_add.ajax?accType=2&accountAdd=2`,
		method: 'post',
		data
	})
}
// 转账申请
export function accountTransferAdd(data) {
	return r({
		url: `/funds/account_transfer_add.ajax?accType=11`,
		method: 'post',
		data
	})
}
// 借贷款申请
export function accountLoanAdd(data) {
	return r({
		url: `/funds/account_loan_add.ajax?accType=12`,
		method: 'post',
		data
	})
}
// 查询用户列表
export function accountUser(data) {
	return r({
		url: `/account_User.ajax?accountType=${data}&start=1&length=999&draw=1`,
	})
}
// 数字化运营中心
export function digitalManageCenterxcx(data) {
	return r({
		url: `/digitalManage/digitalManageCenterxcx.ajax`,
	})
}
// 获取实验下拉框
export function queryAll(data) {
	return r({
		url: `/experimentManage/queryAll.ajax?type=` + data,
	})
}
// 实验订单数据
export function selExpSaleByYear(params) {
	return r({
		url: `/digitalManage/selExpSaleByYear.ajax?year=${params.year}&test_type=${params.test_type}&order_type=${params.order_type}`,
	})
}
// 公司列表筛选
export function selCompanySaleByYear(params) {
	return r({
		url: `/digitalManage/selCompanySaleByYear.ajax?year=${params.year}&type=${params.type}`,
	})
}
// 获取可用余额
export function accountUserId(data) {
	return r({
		url: `/funds/account_userId.htm?userId=${data.userId}&type=${data.type}`,
	})
}
// 实验已收/应收
export function expListxcx(data) {
	return r({
		url: `/digitalManage/expListxcx.ajax?draw=1&type=${data.type}&length=10&start=${data.start}&company_id=${data.company_id}&customer_name=${data.customer_name}&order_id=${data.order_id}&order_startime=${data.order_startime}&order_endtime=${data.order_endtime}&supplier_name=${data.supplier_name}`,
	})
}
// 柱状图
export function expListxcx2(data) {
	return r({
		url: `/digitalManage/expListxcx.ajax?draw=1&type=0&length=10&start=${data.start}&order_type=6&currency_type=1&year=${data.year}&customer_name=${data.customer_name}&company_id=${data.company_id}&order_id=${data.order_id}&order_startime=${data.order_startime}&order_endtime=${data.order_endtime}&supplier_name=${data.supplier_name}&test_type=${data.test_type}`,
	})
}
// 柱状图
export function expListxcx3(data) {
	return r({
		url: `/digitalManage/expListxcx.ajax?draw=1&type=0&length=10&start=${data.start}&order_type=8&currency_type=1&year=${data.year}&customer_name=${data.customer_name}&company_id=${data.company_id}&order_id=${data.order_id}&order_startime=${data.order_startime}&order_endtime=${data.order_endtime}&supplier_name=${data.supplier_name}&test_type=${data.test_type}`,
	})
}
// 柱状图
export function expListxcx4(data) {
	return r({
		url: `/digitalManage/expListxcx.ajax?draw=1&type=4&length=10&start=${data.start}&currency_type=1&year=${data.year}&customer_name=${data.customer_name}&sale_user=${data.sale_user}&company_id=${data.company_id}&order_id=${data.order_id}&order_startime=${data.order_startime}&order_endtime=${data.order_endtime}&supplier_name=${data.supplier_name}`,
	})
}
// 实验分包已收/应收
export function expSubListxcx(data) {
	return r({
		url: `/digitalManage/expSubListxcx.ajax?draw=1&type=${data.type}&length=10&start=${data.start}&company_id=${data.company_id}&customer_name=${data.customer_name}&order_id=${data.order_id}&order_startime=${data.order_startime}&order_endtime=${data.order_endtime}&supplier_name=${data.supplier_name}&currency_type=1`,
	})
}
// 柱状图
export function expListxcx5(data) {
	return r({
		url: `/digitalManage/expSubListxcx.ajax?draw=1&type=4&length=10&start=${data.start}&currency_type=1&year=${data.year}&customer_name=${data.customer_name}&company_id=${data.company_id}&order_id=${data.order_id}&order_startime=${data.order_startime}&order_endtime=${data.order_endtime}&supplier_name=${data.supplier_name}`,
	})
}
// 获取公司列表
export function supplierQueryAll() {
	return r({
		url: `/supplier/queryAll.ajax?userType=6`,
	})
}
// 待审核付款实验分包子订单数字


// 待审核付款实验分包子订单数据列表
export function getAuditOrderList1(orderId,orderType,draw,length,start) {
	return r({
		url: `/wx/getAuditOrderList1.ajax?start=${start}&length=10&draw=1&orderType=9&orderId=${orderId}&pay_status=32`,
	})
}

// 账户资金
export function assetAccountxcx() {
	return r({
		url: `/funds/assetAccountxcx.ajax`,
	})
}

export function yesterdayIncome() {
	return r({
		url: `/yesterdayIncome.ajax`,
	})
}
export function assetAccxcx() {
	return r({
		url: `/funds/assetAccxcx.ajax`,
	})
}
export function yesterdayIncomexcx() {
	return r({
		url: `/yesterdayIncomexcx.ajax`,
	})
}
// export function assetAccountxcx() {
// 	return r({
// 		url: `/funds/assetAccountxcx.ajax`,
// 	})
// }
export function selUserAmountByYearsygrxcx(data) {
	return r({
		url: `/digitalManage/selUserAmountByYearsygrxcx.ajax?year=${data}`,
	})
}
export function selUserAmountByYearsyfbgrxcx(data) {
	return r({
		url: `/digitalManage/selUserAmountByYearsyfbgrxcx.ajax?year=${data}`,
	})
}
//银行列表
export function selBankList(data) {
	return r({
		url: `/wx/selBankList.ajax`,
	})
}
// 饼图跳转页面数据接口
export function saleListxcx(data) {
	return r({
		url: `/digitalManage/saleListxcx.ajax?draw=1&type=${data.type}&length=10&start=${data.start}&customer_name=${data.customer_name}&company_id=${data.company_id}&order_id=${data.order_id}&order_startime=${data.order_startime}&order_endtime=${data.order_endtime}&supplier_name=${data.supplier_name}&currency_type=1`,
	})
}
// 跳转页面数据接口
export function expList(data) {
	return r({
		url: `/digitalManage/expList.ajax?draw=1&type=${data.type}&length=10&start=${data.start}&customer_name=${data.customer_name}&company_id=${data.company_id}&order_id=${data.order_id}&order_startime=${data.order_startime}&order_endtime=${data.order_endtime}&supplier_name=${data.supplier_name}&year=${data.year}`,
	})
}
// 查询来源单号详情
export function accountDetailxcx(id) {
	return r({
		url: `/funds/accountDetailxcx.ajax?id=${id}&accountAdd=2`,
	})
}
// 取消申请
export function passApi(id) {
	return r({
		url: `/pass.ajax?id=${id}&status=-2`,
	})
}
// 确认付款成功
export function pass1Api(id) {
	return r({
		url: `/pass.ajax?id=${id}&status=1`,
	})
}
// 上传打款凭证
export function logStatusNew(id,name) {
	return r({
		url: `/logStatusNew.ajax?id=${id}&type=2&order_status==${order_status}`,
	})
}
// 个人实验分包应付款图表跳转
export function salePayListxcx(data) {
	return r({
		url: `/digitalManage/salePayListxcx.ajax?draw=1&type=4&length=10&start=${data.start}&customer_name=${data.customer_name}&company_id=${data.company_id}&order_id=${data.order_id}&order_startime=${data.order_startime}&order_endtime=${data.order_endtime}&supplier_name=${data.supplier_name}&currency_type=1`,
	})
}
// 查看订单详情
export function orderdetaildptxcx(id) {
	return r({
		url: `/experimentOrder/orderdetaildptxcx.ajax?id=${id}`,
	})
}
// 获取编辑可选产品列表
export function editPagexcx(id) {
	return r({
		url: `/experimentChildOrder/editPagexcx.ajax?id=${id}`,
	})
}
// 获取新增可选产品列表
export function createOrderPagexcx(id) {
	return r({
		url: `/experimentChildOrder/createOrderPagexcx.ajax?saleOrderId=${id}`,
	})
}
// 生成预约单列表
export function addressList(id) {
	return r({
		url: `/testaddress/addressList.ajax`,
	})
}
// 确认生成预约单
export function geranateYydForm(data) {
	return r({
		url: `/experimentOrder/geranateYydForm.ajax?id=${data.id}&test_address_id=${data.test_address_id}`,
	})
}
// 增加关联订单
export function addRelevanceOrder_dpt(data) {
	return r({
		url: `/experimentOrder/addRelevanceOrder_dpt.ajax?order_id=${data.order_id}&rSelect=${data.rSelect}&rOrderId=${data.rOrderId}`,
	})
}
// 子订单下的子订单
export function experimentChildOrderList(id) {
	return r({
		url: `/experimentChildOrder/selGoodsList.ajax?ofId=${id}&start=0&draw=1&length=999&orderStatus=36&is_meeting=0`,
	})
}
// 查询仓库列表
export function queryStore() {
	return r({
		url: `/samplestoreHouse/queryStore.ajax`,
	})
}
// 查询仓库位置
export function queryListByStoreId(id) {
	return r({
		url: `/samplestoreHouse/queryListByStoreId.ajax?store_id=${id}&type=0`,
	})
}
// 预约云视频
export function addVideoInfo(data) {
	return r({
		url: `/experimentChildOrder/addVideoInfo.ajax`,
		method: 'post',
		data
	})
}


