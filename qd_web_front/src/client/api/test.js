import request from '@client/utils/request'


// 获取首页实验列表
export function getOrderListApi() {
  return request({
    url: '/pc/expMakeList.ajax',
    silentError: true,
  })
}


// 预约实验
export function subTestApi(params) {
  return request({
    url: '/pc/serviceConsultAdd.ajax',
    params
  })
}

// 获取实验详情
export function getTestDetailApi(id) {
  return request({
    url: '/pc/testClassDetail.ajax?id=' + id,
  })
}


// 获取首页推荐实验
export function getRecommendTestListApi(id) {
  return request({
    url: '/pc/indexExpList.ajax',
    method: 'post',
    silentError: true,
  })
}


// 获取实验分类列表
export function getTestCateListApi() {
  return request({
    url: '/pc/indexClassList.ajax',
    silentError: true,
  })
}

// 获取实验列表
export function getTestListAPi(params) {
  return request({
    url: '/pc/selExpList.ajax',
    params
  })
}

// 获取属性状态数据
export function getAttributeStateList(params) {
  return request({
    url: '/ordersampleinfomation/getAttributeStateList.ajax',
    params
  })
}

// 获取稳定性数据
export function getStabilityList(params) {
  return request({
    url: '/ordersampleinfomation/getStabilityList.ajax',
    params
  })
}

// 获取预约信息
export function sampleattributemanageList(params) {
  return request({
    url: '/sampleAttributeManage/sampleattributemanageList.ajax',
    params
  })
}

// 系统消息
export function myExpMakeStatusList(params) {
  return request({
    url: '/pc/myExpMakeStatusList.ajax',
    params
  })
}

// 意见反馈
export function addFeedBack(id) {
  return request({
    url: '/wx/addFeedBack.ajax',
    method: 'post'
  })
}

