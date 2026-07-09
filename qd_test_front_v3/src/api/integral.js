import request from '@/utils/request'

// 获取积分列表
export function getIntegralListApi(params) {
  return request({
    url: '/pc/center/getIntegralList.ajax',
    params
  })
}

// 获取积分
export function getIntegralApi() {
  return request({
    url: '/pc/getIntegral.ajax',
    silentError: true,
  })
}

// 获取积分换比
export function getIntegralConvertRatio() {
  return request({
    url: '/pc/getIntegralConvertRatio.ajax',
    silentError: true,
  })
}
// 兑换记录
export function userredeemloglist(params) {
  return request({
    url: '/redeem/userredeemloglist.ajax',
    params
  })
}



