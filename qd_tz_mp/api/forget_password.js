import r from '@/request/index.js'

// 获取验证码
export function fetchCodeApi(phone) {
	return r({
		url: `/wx/getVerifyCodeFindPw.ajax?telephone=${phone}`,
	})
}

// 验证验证码
export function verifyCodeApi(data) {
	return r({
		url: `/wx/telCodeVerify.ajax?telephone=${data['phone']}&tel_code=${data['code']}`,
	})
}