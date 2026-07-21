<template>
	<view class="devide-into">
		<u-popup @open="openedPopup" v-model="show" mode="center" width="80%" :mask-close-able="false"
			border-radius="14">
			<view class="popup-wrapper">
				<u-icon @click="closePopup" name="close" sieze="28" class="close-icon"></u-icon>
				<view class="popup-hint">增加关联订单</view>
				<scroll-view scroll-y="true" class="popup-main">
					<view>选择订单类型：</view>
					<u-radio-group v-model="value" :wrap="true" :label-disabled="false">
						<u-radio  @change="radioChange" :name="5">
							实验订单
						</u-radio>
						<u-radio @change="radioChange" :name="6">
							实验分包订单
						</u-radio>
					</u-radio-group>
					<view style="height: 10px;"></view>
					<view>订单号：</view>
					<u-input v-model="code" type="text" :border="true" />
				</scroll-view>
				<view class="popup-btn" @click="confirmDevide">
					确&nbsp;定
				</view>
			</view>
		</u-popup>
	</view>
</template>

<script>
	import popupBottom from './popupBottom.vue'
	export default {
		name: "relatedOrders",
		components: {
			popupBottom
		},
		props: {
			show: {
				type: Boolean,
				default: false,
				required: true
			},
		},
		data() {
			return {
				value: '',
				id: null,
				code: ''
			};
		},
		methods: {

			// 打开弹窗
			openedPopup() {
				this.id = null
				this.value = ''
				this.code = ''
			},

			// 关闭弹框
			closePopup() {
				this.$emit('update:show', false)
			},

			// 确定分成
			confirmDevide() {
				this.$emit('relatedOrdersClose', this.id, this.code)
			},
			radioChange(e) {
				this.id = e
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