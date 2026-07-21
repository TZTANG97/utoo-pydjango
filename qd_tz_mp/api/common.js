import r from '@/request/index.js'


// 检测是否认证
export function checkAuthApi(userName) {
	return r({
		url: `/wx/checkLoginName.ajax`,
	})
}