import request from '@client/utils/request'
import {getToken} from "@client/utils/auth";

// 获取轮播图
export function getSwiperListApi() {
  return request({
    url: '/pc/bannerList.ajax',
    silentError: true,
  })
}


// 获取pdf所需呀的订单信息
export function getPDFInfoApi(id) {
  return request({
    url: '/experimentOrder/printpdf.ajax',
    params: { id }
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2023/12/13 09:21:05
 * 功能：获取二维码
 */
export function getQrcodeApi() {
  return request({
    url: '/wx/WeChatQRCodeGenerator.ajax',
  })
}


// des

/**
 * 作者：yanmh0722@163.com
 * 时间：2023/12/13 09:20:37
 * 功能：轮询检查接口状态
 */
export function getQrcodeStatusApi(ticket) {
  return request({
    url: '/wx/qrScanStatusCheck.ajax',
    params: { ticket },
  })
}



/**
 * 作者：yanmh0722@163.com
 * 时间：2023/10/19 14:30:32
 * 功能：获取用户的默认收货地址
 */
export function getUserDefaultAddressApi() {
  return request({
    url: '/pc/useraddress.ajax',
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2023/11/14 09:11:50
 * 功能：获取已认证企业的信息列表
 */
export function fetchCompanyInfoApi(kw, page) {
  return request({
    url: `/pc/selCompanyName.ajax?draw=1&length=10&keyword=${kw}&start=${(page - 1) * 10}`
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/01/16 14:45:21
 * 功能：获取预约单详情
 */
export function fetchSubOrderDetailApi(id) {
  return request({
    url: `/wx/reservationDetail.ajax?id=${id}`
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/01/16 14:45:17
 * 功能：上传付款回执单
 */
export function UploadPermitApi(file) {
  const form_data = new FormData()
  form_data.append('orderdata', file)
  form_data.append('type', 7)
  return request({
    method: 'post',
    url: '/experimentOrder/uploadChildData.ajax',
    data: form_data
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/01/16 16:27:26
 * 功能：判断当前订单是否能上传回执单
 */
export function judgmentPermitUploadApi() {
  return request({
    url: '/experimentOrder/loadaccessory.ajax'
  })
}



/**
 * 作者：yanmh0722@163.com
 * 时间：2024/01/16 16:51:32
 * 功能：回执单支付
 */
export function savePermitApi(params) {
  // type 1充值,2还款,3支付,4提现
  // pay_way 1支付宝2微信3线下支付
  return request({
    url: '/pc/saveaccessory.ajax',
    params
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/01/18 16:21:20
 * 功能：充值
 */
export function payApi(params) {
  return request({
    url: '/pc/addRecharge.ajax',
    params
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/01/18 16:35:13
 * 功能：检查充值状态
 */
export function checkPayStatusApi() {
  return request({
    url: '/pc/selRechargeStatus.ajax',
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/01/18 19:21:34
 * 功能：获取账户流水明细
 */
export function fetchAccountDetailApi(params) {
  return request({
    url: '/pc/selRechargeList.ajax',
    params
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/01/19 10:15:29
 * 功能：获取默认收款账户
 */
export function fetchDefaultAccountApi() {
  return request({
    url: '/pc/selDefaultAccount.ajax',
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/02/04 17:15:45
 * 功能：获取默认收款账户
 */

export function fetchMakeInvoiceDetailApi(params) {
  return request({
    url: '/invoice/invoiceDetail.ajax',
    params
  })
}


// 提现
export function submitFormApi(params) {
  return request({
    url: '/pc/addCash.ajax',
    params
  })
}

// 余额支付
export function balancePayApi(params) {
  console.log(params)
  return request({
    url: '/pc/amountPay.ajax',
    params
  })
}

// 充值详情
export function fetchPayDetailApi(params) {
  return request({
    url: '/paymentapply/applyDetail.ajax',
    params
  })
}

// 微信支付
export function wxPayApi(params) {
  return request({
    url: '/pc/prePay.ajax',
    params
  })
}

// 微信还款
export function wxRepaymentApi(params) {
  return request({
    url: '/pc/preAmountPay.ajax',
    params
  })
}


// 微信充值
export function wxTopUpApi(params) {
  return request({
    url: '/pc/rechargePrePay.ajax',
    params
  })
}

/** 待支付充值单继续支付（重新拉起二维码） */
export function wxContinueTopUpApi(params) {
  return request({
    url: '/pc/rechargeContinuePay.ajax',
    params,
    timeout: 60000,
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/04/30 08:51:04
 * 功能：查询第三方支付状态，例如：微信，支付宝
 */
export function fetchTpPayStatusApi(params) {
  return request({
    url: '/pc/queryPayStatusByOrder.ajax',
    params
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/05/29 11:28:16
 * 功能：忘记密码
 */
export function updatePasswordApi(params) {
  return request({
    url: '/pc/telCodeVerify.ajax',
    params
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/03 14:43:15
 * 功能：获取预约单
 */
export function fetchyydApi(id) {
  return request({
    url: '/pc/printYyd.ajax',
    params:{
      id
  }
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/03 14:57:48
 * 功能：获取验证码，忘记密码的时候用
 */
export function fetchForgetPwdCodeApi(telephone) {
  return request({
    url: `/pc/getVerifyCodeFindPw.ajax?telephone=${telephone}`,
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/05 10:30:31
 * 功能：新增收件地址
 */
export function addNewAddressApi(params) {
  return request({
    url: '/pc/insertdeliveryaddress.ajax',
    params
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/05 13:44:23
 * 功能：获取用户基本信息
 */
export function fetchbasicInfoApi() {
  return request({
    url: '/pc/getUserBasicInfo.ajax',
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/05 14:26:45
 * 功能：修改基本信息
 */
export function updateBasicInfoApi(params) {
  return request({
    url: '/pc/updateUserBasicInfo.ajax',
    params
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/05 15:36:15
 * 功能：获取收件地址
 */
export function fetchAddressListApi() {
  return request({
    url: '/pc/getdeliveryaddress.ajax',
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/05 17:20:57
 * 功能：修改收件地址
 */
export function updateAddressApi(params) {
  return request({
    url: '/pc/updatedeliveryaddress.ajax',
    params
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/06 10:07:41
 * 功能：删除和设置默认地址
 */
export function delAddressApi(params) {
  return request({
    url: '/pc/deldeliveryaddress.ajax',
    params
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/06 13:50:59
 * 功能：获取发票列表
 */
export function fetchInvoiceListApi() {
  return request({
    url: '/pc/getinvoiceInfo.ajax',
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/06 14:54:00
 * 功能：新增发票
 */
export function addNewInvoiceApi(params) {
  return request({
    url: '/pc/insertinvoiceInfo.ajax',
    params
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/06 16:08:30
 * 功能：删除发票
 */
export function delInvoiceApi(params) {
  return request({
    url: '/pc/delinvoiceInfo.ajax',
    params
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/06 16:19:49
 * 功能：修改发票信息
 */
export function updateInvoiceApi(params) {
  return request({
    url: '/pc/updateinvoiceInfo.ajax',
    params
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/19 09:22:15
 * 功能：取消预约
 */
export function cancelConsultApi(id) {
  return request({
    url: '/pc/cancelConsult.ajax?id=' + id,
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/25 16:05:11
 * 功能：获取主订单对应的可复测和完成的子订单列表
 */
export function fetchAgainAndFinishChildOrderListApi(params) {
  return request({
    url: '/pc/selTestOrSure.ajax',
    params
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/06/27 10:43:07
 * 功能：获取发票明细
 */
export function fetchInvoiceDetailListApi(params) {
  return request({
    url: '/pc/center/getInvoiceLogList.ajax',
    params
  })
}

/**
 * 作者：yanmh0722@163.com
 * 时间：2024/07/09 10:56:32
 * 功能：获取开票记录
 */
export function fetchInvoiceRecordListApi(params) {
  return request({
    url: '/pc/center/getInvoiceLogList.ajax',
    params
  })
}


/**
 * 作者EMAIL
 * 时间：2024/07/09 11:07:21
 * 功能：获取发票记录
 */
export function rechargeDetail(params) {
  return request({
    url: '/offlineRecharge/rechargeDetail.ajax',
    params
  })
}

/**
 * 查询业务咨询
 */
export function isServiceConsult(params) {
  return request({
    url: '/consult/isServiceConsult.ajax',
    params
  })
}

/**
 * 再来一单
 */
export function saveServiceConsult(params) {
  return request({
    url: '/pc/saveServiceConsult.ajax',
    params
  })
}


/**
 * 作者：yanmh0722@163.com
 * 时间：2024/07/22 15:37:23
 * 功能：下载资料
 */
export function downloadOrderFileApi(file) {
  const { id, info, name } = file

  fetch(`${window.location.origin}/api/pc/downloadFile.ajax?id=${id}`, {
    headers: {
      'Content-Type': 'application/octet-stream',
      'token': getToken()
    }
  })
    .then(response => response.blob())
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${info.split('.')[0]}.${name.split('.')[1]}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    })
    .catch(error => console.error('Download error:', error));
}
