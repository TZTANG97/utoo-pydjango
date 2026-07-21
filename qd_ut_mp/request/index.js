import {
	loginForCodeApi
} from '../api/loign';
import Vue from 'vue'
let requestTask = null;
export const requestClose = () => {
	if(requestTask) {
		requestTask.abort()
	}
}
// 正在进行中的请求数量,防止加载图标闪动
let requesting = 0
const request = (params) => {
	return new Promise((resolve, reject) => {
		if (!Vue.prototype.$baseUrl) {
			return Vue.prototype.$noneRequest.push({
				resolve,
				reject,
				params,
				excFunction
			})
		} else {
			excFunction(resolve, reject, params)
		}
	}).catch(err => {

	})
}


// 执行函数
const excFunction = function(resolve, reject, params) {
	const {
		url = '',
			method = 'get',
			cType = 'application/x-www-form-urlencoded',
			data = '',
			showLoading
	} = params

	console.log(showLoading)

	if(showLoading !== false) {
		uni.showLoading({
			title: "加载中...",
			mask: true
		})
	}




	requestTask = uni.request({
		url: Vue.prototype.$baseUrl + url,
		data,
		method,
		header: {
			'Content-Type': cType,
			token: uni.getStorageSync('token'),
			'uniapp': 'true',
			'X-Channel': 'wx',
		},
		success(res) {
			uni.hideLoading()
			if (res.statusCode === 200) {
				if(res.data.error && res.data.error == '403') {
					uni.removeStorageSync('userInfo')
					uni.removeStorageSync('userList')
					uni.removeStorageSync('token')
					uni.removeStorageSync('uType')
					// uType: 0普通用户  1内部用户
					uni.removeStorageSync('is_identify')
					uni.removeStorageSync('defaultAccount')
					setTimeout(() => {
						uni.reLaunch({
							url: '/pages/my/my'
						})
					}, 1000)
					reject()
				} else if(res.data.resMsg == '用户未登录') {
					uni.removeStorageSync('userInfo')
					uni.removeStorageSync('userList')
					uni.removeStorageSync('token')
					uni.removeStorageSync('uType')
					// uType: 0普通用户  1内部用户
					uni.removeStorageSync('is_identify')
					uni.removeStorageSync('defaultAccount')
					setTimeout(() => {
						uni.reLaunch({
							url: '/pages/my/my'
						})
					}, 1000)
					reject()
				} else {
					resolve(res.data)
				}
			} else {
				switch (res.statusCode) {
					case 401:
						uni.showToast({
							title: '请先登录',
							icon: 'none'
						})
						uni.removeStorageSync('userInfo')
						uni.removeStorageSync('token')
						uni.removeStorageSync('userList')
						uni.removeStorageSync('uType')
						// uType: 0普通用户  1内部用户
						uni.removeStorageSync('is_identify')
						uni.removeStorageSync('defaultAccount')
						setTimeout(() => {
							uni.reLaunch({
								url: '/pages/my/my'
							})
						}, 1000)
					case 404:
						uni.showToast({
							title: '找不到资源',
							icon: 'none'
						})
						uni.removeStorageSync('userInfo')
						uni.removeStorageSync('token')
						uni.removeStorageSync('userList')
						uni.removeStorageSync('uType')
						// uType: 0普通用户  1内部用户
						uni.removeStorageSync('is_identify')
						uni.removeStorageSync('defaultAccount')
						setTimeout(() => {
							uni.reLaunch({
								url: '/pages/my/my'
							})
						}, 1000)
					case 500:
						uni.showToast({
							title: '请求失败，请重试！',
							icon: 'none'
						})
				}
				reject()
			}
		},

		fail() {
			uni.hideLoading()
			// uni.showToast({
			// 	title: '请检查您的网络连接',
			// 	icon: 'none'
			// })
			reject()
		},
	})
}

export default request
