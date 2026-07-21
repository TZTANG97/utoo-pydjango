import r from '@/request/index.js'


// 获取验证码
export function getCodeApi(mobile) {
	return r({
		url: `/wx/getVerifyCodeLogin.ajax?telephone=${mobile}`,
	})
}

// 使用 手机号/账号 密码登录
export function loginForPwdApi({
	loginName,
	password
}) {
	return r({
		url: `/wx/userLoginToken.ajax?loginName=${loginName}&password=${password}`,
	})
}

// 验证码登录
export function loginForCodeApi(mobile, code) {
	return r({
		url: `/wx/phoneCodeLogin.ajax?telephone=${mobile}&code=${code}`
	})
}

export function fetchUserListApi() {
	return r({
		url: `/index/userRoles.ajax`,
	})
}


// 一键登录
export function fastLoginApi(code) {
	return r({
		url: `/wx/phoneOneLoginTZ.ajax?code=${code}`
	})
}


// 用户扫码登录时得一键登录
export function getUserInfoApi(data) {
	return r({
		url: '/wx/getUserInfo.ajax',
		data
	})
}
