<template>
	<view class="devide-into">
		<u-popup @open="openedPopup" v-model="show" mode="center" width="80%" :mask-close-able="false"
			border-radius="14">
			<view class="popup-wrapper">
				<u-icon @click="closePopup" name="close" sieze="28" class="close-icon"></u-icon>
				<view class="popup-hint">分成信息</view>
				<scroll-view scroll-y="true" class="popup-main">
					<view class="popup-item" v-if="showMl">
						<view class="popup-label">
							<text>毛利分成：</text>
							<text @click="addDevideInfo('dynamicMl')" class="add-btn">添加</text>
						</view>
						<view class="popup-content">
							<view class="devide-item" v-for="(item, index) in dynamicMl" :key="index">
								<view class="devide-name">
									<view class="oh" @click="chooseDevideUser('dynamicMl', index)">
										{{ item.userName? item.userName : '选择分成人员' }}
									</view>
									<u-icon name="arrow-down" size="26"></u-icon>
								</view>
								<view class="devide-ratio">
									<view class="input">
										<input style="width: 70px;" type="digit" v-model.lazy.number="item.scale"
											@input="amendValue($event, 'dynamicMl' ,index)" />%
									</view>
									<u-icon @click="delDevide('dynamicMl', index)" style="margin-left: 15rpx;"
										name="close" size="26"></u-icon>
								</view>
							</view>
						</view>
					</view>
					<view class="popup-item" v-if="showLr">
						<view class="popup-label">
							<text>利润分成：</text>
							<text @click="addDevideInfo('dynamicLr')" class="add-btn">添加</text>
						</view>
						<view class="popup-content">
							<view class="devide-item" v-for="(item, index) in dynamicLr" :key="index">
								<view class="devide-name">
									<view class="oh" @click="chooseDevideUser('dynamicLr', index)">
										{{ item.userName? item.userName : '选择分成人员' }}
									</view>
									<u-icon name="arrow-down" size="26"></u-icon>
								</view>
								<view class="devide-ratio">
									<view class="input">
										<input style="width: 70px;" type="digit" v-model.lazy.number="item.scale"
											@input="amendValue($event, 'dynamicLr' ,index)" />%
									</view>
									<u-icon @click="delDevide('dynamicLr', index)" style="margin-left: 15rpx;"
										name="close" size="26"></u-icon>
								</view>
							</view>
						</view>
					</view>
					<view class="popup-item" v-if="showCb">
						<view class="popup-label">
							<text>成本分成：</text>
							<text @click="addDevideInfo('dynamicCb')" class="add-btn">添加</text>
						</view>
						<view class="popup-content">
							<view class="devide-item" v-for="(item, index) in dynamicCb" :key="index">
								<view class="devide-name">
									<view class="oh" @click="chooseDevideUser('dynamicCb', index)">
										{{ item.userName? item.userName : '选择分成人员' }}
									</view>
									<u-icon name="arrow-down" size="26"></u-icon>
								</view>
								<view class="devide-ratio">
									<view class="input">
										<input style="width: 70px;" type="digit" v-model.lazy.number="item.scale"
											@input="amendValue($event, 'dynamicCb' ,index)" />{{ cbUnit? '%' : '' }}
									</view>
									<u-icon @click="delDevide('dynamicCb', index)" style="margin-left: 15rpx;"
										name="close" size="26"></u-icon>
								</view>
							</view>
						</view>
					</view>
				</scroll-view>
				<view class="popup-btn" @click="confirmDevide">
					确&nbsp;定
				</view>
			</view>
		</u-popup>
		<!-- list是固定列表不加sync -->
		<popup-bottom :list="backUpList" title="选择分成人员" :show.sync="showChooseDevideUser" :showKey="showKey"
			@getValue="confirmDevideUser"></popup-bottom>
	</view>
</template>

<script>
	import popupBottom from './popupBottom.vue'
	export default {
		name: "divideInto",
		components: {
			popupBottom
		},
		props: {
			show: {
				type: Boolean,
				default: false,
				required: true
			},
			// 可选人员列表
			backUpList: {
				type: Array,
				default: () => [],
				required: true
			},

			// 已存在的分成人员列表
			ml: {
				type: Array,
				default: () => []
			},
			lr: {
				type: Array,
				default: () => []
			},
			cb: {
				type: Array,
				default: () => []
			},
			// 成本分成是否显示单位
			cbUnit: {
				type: Boolean,
				default: true
			},
			showMl: {
				type: Boolean,
				default: false
			},
			showCb: {
				type: Boolean,
				default: false
			},
			showLr: {
				type: Boolean,
				default: false
			}
		},
		data() {
			return {
				showChooseDevideUser: false,
				showKey: 'userName',
				currentListName: '',
				currentIndex: -1,
				dynamicCb: [],
				dynamicMl: [],
				dynamicLr: [],
			};
		},
		methods: {

			// 打开弹窗
			openedPopup() {
				this.dynamicLr = []
				this.dynamicCb = []
				this.dynamicMl = []

				this.lr.forEach(e => {
					this.dynamicLr.push(e)
				})
				this.cb.forEach(e => {
					this.dynamicCb.push(e)
				})
				this.ml.forEach(e => {
					this.dynamicMl.push(e)
				})
			},

			// 关闭弹框
			closePopup() {
				this.$emit('update:show', false)
			},

			// 确定分成
			confirmDevide() {
				this.$emit('confirmDevideList', {
					lr: this.dynamicLr,
					ml: this.dynamicMl,
					cb: this.dynamicCb
				})
			},

			// 监听修改分成
			amendValue(e, listName, index) {
				this[listName][index].scale = e.detail.value
			},

			// 选择人员弹框列表点击确定
			confirmDevideUser(e) {
				let {
					id,
					userName
				} = e
				this[this.currentListName][this.currentIndex] = {
					userId: id,
					userName,
					scale: 0
				}
				this.showChooseDevideUser = false
			},

			// 删除分成人员
			delDevide(listName, index) {
				this[listName].splice(index, 1)
			},

			// 选择分成人员
			chooseDevideUser(selectedUserListName, index) {

				// 那个列表
				this.currentListName = selectedUserListName
				// 选择列表的那个分成人员
				this.currentIndex = index

				this.showChooseDevideUser = true
			},

			// 添加分成人员额
			addDevideInfo(listName) {
				let obj = {
					userId: '',
					userName: '',
					scale: 0
				}
				if (listName == 'dynamicLr') this.dynamicLr.push(obj)
				if (listName == 'dynamicCb') this.dynamicCb.push(obj)
				if (listName == 'dynamicMl') this.dynamicMl.push(obj)
				// this.$set(this[listName], this[listName].length, obj)
			},
		}
	}
</script>

<style lang="scss" scoped>
	.popup-wrapper {
		position: relative;
	}

	.close-icon {
		position: absolute;
		right: 25rpx;
		top: 25rpx;
	}


	.popup-content {
		.devide-item {
			display: flex;
			justify-content: space-between;
			align-items: center;
			padding: 10rpx 15rpx;

			.devide-name {
				display: flex;

				view {
					max-width: 250rpx;
				}
			}

			.devide-ratio,
			.input {
				display: flex;
				align-items: center;
			}

			text {
				display: inline-block;
				vertical-align: middle;
				max-width: 300rpx;
				overflow: hidden;
				text-overflow: ellipsis;
				white-space: nowrap;
			}
		}
	}

	@import '@/layout/popup.scss';
</style>