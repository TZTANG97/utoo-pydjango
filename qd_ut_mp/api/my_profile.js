import r from '@/request/index.js'


// 设置昵称
export function setNickNameApi(nickName) {
	return r({
		url: `/wx/updateNickName.ajax?nickName=${nickName}`,
	})
}