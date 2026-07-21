import Vue from 'vue'
export default {
	data() {
		return {
			syUser: null,
		}
	},
	onLoad() {
		const token = uni.getStorageSync('token');
		if (token && !this.syUser) {
			this.syUser = uni.getStorageSync('userInfo')
		}
	},
	onUnload() {
		// 离开页面自动取消当前页面监听的事件
		const page = getCurrentPages(),
			pageId = page[page.length - 1]['__wxExparserNodeId__'],
			eventList = uni.$eventNameList;


		// 退出页面自动取消当前页面的所有监听事件
		for (var i = 0; i < eventList.length; i++) {
			if (eventList[i].startsWith(`_${pageId}`)) {
				uni.$off(eventList[i])
				eventList.splice(i, 1)
			}
		}
	},
	onShareAppMessage() {
		return {
			path: '/pages/index/index'
		}
	},

	onShareTimeline() {},
}