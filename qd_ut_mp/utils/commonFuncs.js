// 全局挂载
import Vue from 'vue'
import {
	IMAGE_FILE_LIST,
	OTHER_FILE_LIST
} from '@/constant/status.js'
// 防抖函数
function debounce(fn, detay = 800) {
	let timer;
	return function() {
		const ctx = this,
			args = arguments
		if (timer) clearTimeout(timer)
		timer = setTimeout(function() {
			fn.apply(ctx, args)
		}, detay)
	}
}

// 可选取的文件格式
// let allForamt = [...IMAGE_FILE_LIST, ...OTHER_FILE_LIST]
// allForamt = allForamt.map(item => '.' + item)

// 上传文件
function uploadFile2(componentInstance, param = {}) {
	// 是否正在上传中
	if (componentInstance.uploading) return naviteToast('文件正在上传...')

	if (!(componentInstance instanceof Vue)) {
		throw new Error('请传入组件实例')
	}

	if (typeof param !== 'object') {
		throw new Error('$uploadFile方法的参数只能是对象')
	}

	const {
		url = '/experimentOrder/uploadChildData.ajax',
			name = 'orderdata',
			type = 3,
			...extraParam
	} = param
	return new Promise((resolve, reject) => {
		const token = uni.getStorageSync('token')
		// 目前只能选择图像
		// 手写or等待官方完善
		uni.chooseImage({
			count: 1,
			success(res) {
				componentInstance.uploading = true
				Vue.prototype.$uploadTask = uni.uploadFile({
					url: `${Vue.prototype.$baseUrl}${url}`,
					filePath: res.tempFilePaths[0],
					name,
					timeout: 10000,
					header: {
						token,
						uniapp: 'true',
						'X-Channel': 'wx',
					},
					formData: {
						type,
						...extraParam
					},
					success(response) {
						const res = JSON.parse(response.data)
						if (res.res) {
							const {
								id,
								path,
								name
							} = res.obj
							resolve({
								id: id + '',
								path,
								name
							})
						} else {
							naviteToast(res.resMsg)
							reject()
						}
					},
					fail(err) {
						let title = '上传失败，请重试！';
						switch (err.errMsg) {
							case 'uploadFile:fail timeout':
								title = '上传超时，请检查网络并重试！'
								break;
							case 'uploadFile:fail abort':
								title = '上传已取消'
								break;
						}

						nativeToast(`${title}`)
						reject()
						console.log(err);
					},
					complete() {
						Vue.prototype.$uploadTask = null
						componentInstance.progressBar = 0
						componentInstance.uploading = false
					}
				});

				// 监听进度
				Vue.prototype.$uploadTask.onProgressUpdate(({
					progress
				}) => {
					componentInstance.progressBar = progress
				})
			}
		})
	})
}

// 提示
function tip(title) {
	if (!title) return
	this.$refs.uToast.show({
		title,
		position: 'bottom',
		duration: 1500
	})
}

// 提示并返回上级
function tip2(title) {
	nativeToast(title, 1400)
	setTimeout(() => {
		uni.navigateBack({
			delta: 1
		})
	}, 1600)
}

// 时间戳转化
function alterTime(timestamp, intact = true) {
	let time = new Date(timestamp);
	let year = time.getFullYear();
	let month = time.getMonth() + 1;
	month = month < 10 ? '0' + month : month
	let day = time.getDate();
	day = day < 10 ? '0' + day : day
	let hour = time.getHours();
	hour = hour < 10 ? '0' + hour : hour
	let min = time.getMinutes();
	min = min < 10 ? '0' + min : min
	let second = time.getSeconds();
	second = second < 10 ? '0' + second : second
	if (intact) {
		return `${year}-${month}-${day} ${hour}:${min}:${second}`
	} else {
		return `${year}-${month}-${day}`
	}
}

// 预览文件
function preFile(currentFileIndex, fileList) {
	// 当前用户选中的索引
	const selectedPath = fileList[currentFileIndex]
	const tailName = checkFormat(selectedPath)
	if (OTHER_FILE_LIST.includes(tailName)) {
		uni.showLoading({
			title: '正在打开文件...',
			mask: true
		})
		uni.downloadFile({
			url: selectedPath,
			success: function(res) {
				const filePath = res.tempFilePath;
				uni.openDocument({
					filePath,
					// showMenu: true,
					fail(err) {
						nativeToast('文件预览失败')
					},
					complete() {
						uni.hideLoading()
					},
					// success: function(res) {
					// 	console.log('打开文档成功', res)
					// }

				});
			}
		});
	} else if (IMAGE_FILE_LIST.includes(tailName)) {
		// 把图片类型的都单独抽出来
		const imageFormatList = fileList.filter(e => IMAGE_FILE_LIST.includes(checkFormat(e)))
		const newIndex = imageFormatList.findIndex(e => e == selectedPath)

		uni.previewImage({
			urls: imageFormatList,
			current: newIndex
		})
	} else {
		nativeToast('该文件类型不支持预览')
	}
}

// 检查路径的文件格式
function checkFormat(path) {
	const arr = path.split('.')
	return arr[arr.length - 1]
}


// 消息订阅
function penSubscribe() {
	return new Promise(resolve => {
		wx.requestSubscribeMessage({
			tmplIds: ['P1ObhAeTfgawOPzQsq6UG7bGOcz-rbdfoeEQNWJ5X4s'],
			success(res) {
				resolve()
			},
			fail(err) {
				resolve()
			}
		})
	})
}

// 校验为空
function isTrue(val = '') {
	const list = [undefined, null, 0, '', false, '0']
	return !(list.includes(val))
}

// 解决扫码得出的内容不相等的问题
function equality(arr) {
	return arr.map(e => e.replace('\uFEFF', ''))
}

// 原生提示
function nativeToast(title, duration = 1800) {
	uni.showToast({
		title,
		icon: 'none',
		mask: true,
		duration
	})
}

const dynamicDomain = async function() {
	// uni.showLoading('身份检测中...')
	const env = wx.getAccountInfoSync().miniProgram.envVersion
	// release / trial 必须走已在公众平台配置的合法域名；
	// develop 才连 UAT（开发者工具可勾选「不校验合法域名」，真机体验版不会）。
	if (env === 'release' || env === 'trial') {
		Vue.prototype.$baseUrl = 'https://utootesting.com/console'
	} else {
		// Vue.prototype.$baseUrl = 'http://127.0.0.1:18083/api'
		Vue.prototype.$baseUrl = 'https://uat.utoodev.laide.tech/api'
	}
}

module.exports = {
	debounce,
	tip,
	tip2,
	alterTime,
	preFile,
	penSubscribe,
	isTrue,
	equality,
	uploadFile2,
	dynamicDomain
}
