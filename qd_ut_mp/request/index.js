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
/** 未登录跳转防抖：已在个人中心时不再 reLaunch，避免页面闪烁死循环 */
let loginRedirectTimer = null

function clearLoginStorage() {
	uni.removeStorageSync('userInfo')
	uni.removeStorageSync('userList')
	uni.removeStorageSync('token')
	uni.removeStorageSync('uType')
	uni.removeStorageSync('is_identify')
	uni.removeStorageSync('defaultAccount')
}

function isOnMyPage() {
	try {
		const pages = getCurrentPages()
		const cur = pages && pages.length ? pages[pages.length - 1] : null
		const route = (cur && (cur.route || (cur.$page && cur.$page.fullPath))) || ''
		return String(route).indexOf('pages/my/my') !== -1
	} catch (e) {
		return false
	}
}

function redirectToMyIfNeeded() {
	if (isOnMyPage()) return
	if (loginRedirectTimer) return
	loginRedirectTimer = setTimeout(() => {
		loginRedirectTimer = null
		if (isOnMyPage()) return
		uni.reLaunch({
			url: '/pages/my/my'
		})
	}, 1000)
}

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
			if (showLoading !== false) {
				uni.hideLoading()
			}
			if (res.statusCode === 200) {
				const needLogin =
					(res.data && res.data.error && res.data.error == '403') ||
					(res.data && res.data.resMsg == '用户未登录')
				if (needLogin) {
					clearLoginStorage()
					redirectToMyIfNeeded()
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
						clearLoginStorage()
						redirectToMyIfNeeded()
						break
					case 404:
						uni.showToast({
							title: '找不到资源',
							icon: 'none'
						})
						break
					case 500:
						uni.showToast({
							title: '请求失败，请重试！',
							icon: 'none'
						})
						break
				}
				reject()
			}
		},

		fail() {
			if (showLoading !== false) {
				uni.hideLoading()
			}
			// uni.showToast({
			// 	title: '请检查您的网络连接',
			// 	icon: 'none'
			// })
			reject()
		},
	})
}

export default request
