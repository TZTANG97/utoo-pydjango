import request from '@client/utils/request'

// 登录（Python FastAPI）
export function loginApi(params) {
  return request({
    url: '/auth/login',
    method: 'post',
    data: {
      name: params.loginName,
      password: params.password,
      loginType: '1',
    },
  })
}

// 获取用户信息（认证数据）
// silentError：失效令牌时由路由守卫处理，避免与其它接口 401 叠出重复提示
export function getInfo() {
  return request({
    url: '/auth/me',
    method: 'get',
    silentError: true,
  })
}

// 注册
export function regApi(params) {
  return request({
    url: '/pc/register.ajax',
    params
  })
}

// 获取验证码
export function getNoteCodeApi(mobile) {
  return request({
    url: '/pc/getVerifyCode.ajax?telephone=' + mobile,
  })
}

// 修改密码
export function changePwdApi(params) {
  return request({
    url: '/pc/setPassword.ajax',
    params
  })
}

// 添加认证信息
export function savaAuthInfoApi(params) {
  return request({
    url: '/pc/addOrUpdateUserData.ajax',
    params
  })
}

// 添加企业认证
export function saveAuthCompanyInfoApi(params) {
  return request({
    url: `/pc/addOrUpdateUserCompanyData.ajax`,
    params
  })
}


// 获取我的资产信息
export function getMyAssetInfoApi(params) {
  return request({
    url: `/pc/center/getAccount.ajax`,
    params
  })
}


// 添加发票信息
export function addUserInvoiceInfoApi(params) {
  return request({
    url: '/pc/addInvoiceInfo.ajax',
    params
  })
}


// 获取发票信息
export function getUserInvoiceInfoApi() {
  return request({
    url: `/pc/center/getInvoiceInfo.ajax`,
  })
}

// 上传头像
export function uploadAvatarApi(file) {
  const form_data = new FormData()
  form_data.append('photo', file)
  return request({
    method: 'post',
    data: form_data,
    url: `/pc/updatePhone.ajax`,
  })
}

export function swfUploadApi(file) {
  const form_data = new FormData()
  form_data.append('photo', file)
  return request({
    method: 'post',
    data: form_data,
    url: `/seller/swf_upload.ajax`,
  })
}

// 获取我的预约列表
export function getUserSUbListApi(params) {
  return request({
    url: '/pc/myExpMakeList.ajax',
    params
  })
}
