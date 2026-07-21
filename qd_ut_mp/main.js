import App from './App'

import Vue from 'vue'
import './uni.promisify.adaptor'
Vue.config.productionTip = false

// 分享混入
import mixin from './mixin'
Vue.mixin(mixin)

// 挂在一个全局提示
Vue.prototype.$toast = function(title) {
	uni.showToast({
		title,
		mask: true,
		icon: 'none',
		duration: 1200
	})
}


import commons from './utils/commonFuncs.js';
Object.keys(commons).forEach(e => {
	Vue.prototype['$' + e] = commons[e]
})

// 动态切换请求地址
Vue.prototype.$noneRequest = []
Vue.prototype.$dynamicDomain()


// 挂载自定义$emit,暂时这样，如果该方法用法的不多，就换回原来的
uni.$eventNameList = []
uni.$_on = function () {
	const page = getCurrentPages(),
	pageId = page[page.length - 1]['__wxExparserNodeId__'],
	realEventName = `_${pageId}${arguments[0]}`;
	uni.$eventNameList.push(realEventName)
	arguments[0] = realEventName
	uni.$on(...arguments)
}
uni.$_emit = function () {
	for (var i = 0; i < uni.$eventNameList.length; i++) {
		if (uni.$eventNameList[i].endsWith(arguments[0])) {
			arguments[0] = uni.$eventNameList[i]
			uni.$emit(...arguments)
		}
	}
}

import uView from "uview-ui";
Vue.use(uView);

App.mpType = 'app'
const app = new Vue({
	...App
})
app.$mount()