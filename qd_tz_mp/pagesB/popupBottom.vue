<template>
	<!-- 底部弹框选择组件 -->
	<view class="popup-bottom">
		<u-popup height="740" :mask-close-able="false" border-radius="14" mode="bottom" v-model="show"
			@close="closePopup" @open="openPopup">
			<view class="dialog-wrapper">
				<image class="close-icon" @click="closePopup" src="../static/close.png" mode=""></image>
				<view class="dialog-hint">{{ title }}</view>
				<view class="dialog-header">
					<view class="search-box">
						<u-icon color="#95989E" class="search-icon" name="search" size="28"></u-icon>
						<input @input="search" maxlength="30" confirm-type="search" class="my-search-input" type="text"
							v-model="key_word" :placeholder="placeholder" />
					</view>
				</view>
				<!-- 单选 -->
				<scroll-view scroll-y="true" class="dialog-content" @scrolltolower="getBottom">
					<template v-if="multipleChoice">
						<view class="dialog-item" @click="selectedIndex = index"
							v-for="(item, index) in (loadable? list : showList)" :key="index">
							<image v-if="selectedIndex === index" src="../static/img/active_yes.png" mode="" />
							<image v-else src="../static/img/active_no.png" mode="" />
							<view class="dialog-item-content oh">{{ getShowTxt(item) }}</view>
						</view>
					</template>
					<template v-else>
						<!-- u-checkbox-group外层的溢出不生效 -->
						<!-- 如果为多选的动态列表 -->
						<view class="dialog-item oh" v-for="(item, index) in showList" :key="index">
							<u-checkbox-group active-color="#3C8BDB">
								<u-checkbox size="30" v-model="item.checked" shape="square">{{ getShowTxt(item) }}
								</u-checkbox>
							</u-checkbox-group>
						</view>
					</template>

					<view class="empty" v-if="!showList.length && !loadable">
						暂无数据
					</view>

					<!-- 《加载》组件 -->
					<list-loading v-if="loadable" :loading="loading" :isRefresh="isRefresh" :total="showList.length">
					</list-loading>
				</scroll-view>
				<view class="dialog-footer" @click="confirm">确&nbsp;定</view>
			</view>
		</u-popup>
		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import listLoading from "@/components/loading.vue"
	import {
		debounce
	} from '@/utils/commonFuncs.js';
	export default {
		name: "popupBottom",
		props: {
			show: {
				default: false,
				type: Boolean
			},
			title: {
				default: "",
				type: String
			},
			// 源数据
			list: {
				default: () => [],
				type: Array
			},
			showKey: {
				type: Array | String,
				default: ""
			},
			// 是否可加载的
			loadable: {
				default: false,
				type: Boolean
			},
			isRefresh: {
				default: true,
				type: Boolean
			},
			loading: {
				default: false,
				type: Boolean
			},

			// 单选
			multipleChoice: {
				default: true,
				type: Boolean
			},
			placeholder: {
				default: '请输入关键词进行检索',
				type: String
			}
		},
		components: {
			listLoading
		},

		data() {
			return {
				key_word: '',
				selectedIndex: -1,
				selectedList: [],
				listBackups: [],
				showList: []
			};
		},

		methods: {
			// 监听弹出层打开
			openPopup() {
				if (!this.loadable) {
					this.listBackups = []
					this.listBackups = [...this.list]
					this.listBackups.forEach(item => {
						if (!this.multipleChoice) {
							this.$set(item, 'checked', false)
						}
					})
					this.showList = [...this.listBackups]
				} else {
					// 判断如果数组为空，则emit一下,获取初始化数据
					if (!this.list.length) {
						this.$emit('getMoreOrSearch')
					}
				}

				// 需要优化的地方
				// 1：打开弹框之后，emit一下，获取初始化数据
				// 2：多选可在线检索
			},

			// 获取展示的内容
			getShowTxt(item) {
				if (!this.showKey) {
					return item
				} else if (Object.prototype.toString.apply(this.showKey) === '[object Array]') {
					let showStrList = []
					this.showKey.map(key => {
						if (item[key]) {
							showStrList.push(item[key])
						}
					})
					return showStrList.join('-')
				} else {
					return item[this.showKey]
				}
			},

			// 滚动触底
			getBottom(e) {
				if (this.loadable && this.isRefresh && !this.loading) {
					this.$emit('getMoreOrSearch', this.key_word)
				} else {
					console.log('资源已经加载完毕');
				}
			},

			// 关闭弹框
			closePopup() {
				// 如果不是列表是固定的，则清空关键词
				if (!this.loadable) {
					this.listBackups = []
					this.showList = []
					this.key_word = ''
				}
				this.selectedIndex = -1
				this.$emit('update:show', false)
			},

			confirm() {
				// 多列
				if (!this.multipleChoice) {
					// 暂时只返回idList
					const idList = []
					this.showList.forEach(item => {
						if (item['checked']) {
							idList.push(item.id)
						}
					})
					this.$emit('getValue', idList.join('_'))
				} else {
					if (this.selectedIndex == -1) return this.$tip('请先选中')
					this.$emit('getValue', this[this.loadable ? 'list' : 'showList'][this.selectedIndex])
				}
			},

			// 检索
			search: debounce(function() {
				console.log(this.loadable,'loadable')
				if (this.loadable) {
					this.selectedIndex = -1
					// key_word为检索关键字
					// 在组件内重置params，不需要在每个引用的地方再写一遍
					this.$emit('update:page', 1)
					this.$emit('update:list', [])
					this.$emit('update:is-refresh', true)
					this.$emit('getMoreOrSearch', this.key_word)
				} else {
					// 原始数组为空，直接pass
					if (!this.listBackups.length) return
					// 判断输入框改动之后是否存在值
					if (this.key_word) {
						console.log('1')
						let new_list = this.listBackups.filter(item => {
							// 进入循环检索
							// showKey为true，则代表item为对象，否则就是基本数据
							if (this.showKey) {
								console.log('2')
								// 如果发现showKey为数组，便利一下，只要是存在的key中有一个包含关键字，就取出来
								if (Object.prototype.toString.call(this.showKey) === '[object Array]') {
									console.log('3')
									for (let key of this.showKey) {
										if (item[key] && item[key].includes(this.key_word)) {
											console.log('4')
											return true
										}
									}
								} else {
									console.log('5')
									if (item[this.showKey]) return item[this.showKey].includes(this
										.key_word);
								}
							} else {
								console.log(item,'6')
								if (item) return item.includes(this.key_word);
							}
						});
						console.log(new_list,'7')
						this.showList = []
						new_list.forEach(item => {
							// item['checked'] = false
							this.showList.push(item)
						})
					} else {
						this.showList = []
						console.log(this.listBackups,'8')
						this.listBackups.forEach(item => {
							// item['checked'] = false
							this.showList.push(item)
						})
					}
					this.selectedIndex = -1;
				}
			}),
		}
	}
</script>

<style lang="scss" scoped>
	@import "@/layout/popup2.scss";

	.empty {
		text-align: center;
		padding: 100rpx 0;
		color: #999;
	}

	.search-box {
		position: relative;

		.search-icon {
			position: absolute;
			left: 20rpx;
			top: 18rpx;
		}

		.my-search-input {
			height: 60rpx;
			background-color: #f2f2f2;
			line-height: 60rpx;
			border-radius: 40rpx;
			box-sizing: border-box;
			padding: 0 20rpx 0 60rpx;
			font-size: 26rpx;
		}
	}

	.dialog-item-content {
		margin-left: 15rpx;
		width: 500rpx;
	}

	.close-icon {
		position: absolute;
		right: 30rpx;
		top: 30rpx;
		width: 37rpx;
		height: 37rpx;
		vertical-align: middle;
	}
</style>
