import r from '@/request/index.js'

// 设置密码
export function setPwdApi(data) {
	return r({
		url: `/wx/setPassword.ajax?telephone=${data['phone']}&password=${data['pwd']}&password1=${data['confirmPwd']}`,
	})
}