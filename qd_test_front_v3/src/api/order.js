import request from '@/utils/request'

// 获取订单列表
export function getOrderListApi(params) {
  return request({
    url: '/pc/myExperimentOrderList.ajax',
    params,
    timeout: 60000,
    headers: {
      "content-type": "application/x-www-form-urlencoded",
    }
  })
}


// 查看订单详情
export function getOrderDetailApi(params) {
  return request({
    url: '/experimentOrder/orderdetail.ajax',
    params
  })
}

// 查看订单详情2
export function getRechargeDetailApi(params) {
  return request({
    url: '/offlineRecharge/rechargeDetail.ajax',
    params
  })
}

// 评价订单（与 submitEvaluateApi 相同）
export function evaluateOrderApi(data) {
  return request({
    method: 'post',
    url: `/pc/writeevaluate.ajax`,
    data,
  })
}


// 产品订单
export function getProductOrderListApi(params) {
  return request({
    url: '/experimentOrder/getChildFormByIdExp.ajax',
    params,
    headers: {
      "content-type": "application/x-www-form-urlencoded",
    }
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2023/11/23 16:27:09
 * 功能：获取实验子订单
 */
export function fetchTestChildOrderApi(params) {
  return request({
    url: '/experimentChildOrder/getOrdersBySaleOrderId.ajax',
    params,
    headers: {
      "content-type": "application/x-www-form-urlencoded",
    }
  })
}

// 实验子订单详情
export function getTestChildOrderDetailApi(params) {
  return request({
    // url: '/experimentOrder/checkChildOrder.ajax',
    url: '/experimentChildOrder/orderdetail.ajax',
    params
  })
}


// 我的资产订单列表
export function getOrderListForTypeApi(params) {
  return request({
    url: '/pc/experimentOrderList.ajax',
    params,
    headers: {
      "content-type": "application/x-www-form-urlencoded",
    }
  })
}

// 待处理订单，待还款订单
export function getMyOrderListForTypeApi(params) {
  return request({
    url: '/pc/myExperimentOrderList.ajax',
    params,
    timeout: 60000,
    headers: {
      "content-type": "application/x-www-form-urlencoded",
    }
  })
}

// 获取发票列表
export function getInvoiceListApi(params) {
  return request({
    url: `/pc/center/getInvoiceList.ajax`,
    params,
    headers: {
      "content-type": "application/x-www-form-urlencoded",
    }
  })
}

// 取消发票管理
export function cancelInvoiceApi(params) {
  return request({
    url: `/pc/cancelInvoiceInfo.ajax`,
    params,
  })
}


// 获取可开票的订单
export function getAllowBillListApi(params) {
  return request({
    url: `/pc/center/getInvoiceOrderList.ajax`,
    params,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    }
  })
}

// orderIds 订单id
// invoiceTitle 抬头
// type  发票类型1专  2普
// isPay   是否回款 0：未回款 ,1：已回款
// notes  备注

// 开发票
export function billingApi(data) {
  return request({
    method: 'post',
    url: `/pc/center/applyInvoice.ajax`,
    data: {...data, isPay: 0, notes: ''}
  })
}

// 评价
export function submitEvaluateApi(data) {
  return request({
    method: 'post',
    url: `/pc/writeevaluate.ajax`,
    data
  })
}

// 复测
export function againTestApi(data) {
  return request({
    method: 'post',
    url: `/retestapplication/addretestapplication.ajax`,
    data
  })
}

// 确认完成
export function confirmCompleteApi(params) {
  return request({
    url: '/experimentChildOrder/sureOk.ajax',
    params
  })
}

// 兑换详情
export function redeemGoodsDetail(params) {
  return request({
    url: '/redeem/redeemGoodsLogDetail.ajax',
    params
  })
}
