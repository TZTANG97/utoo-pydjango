<template>
	<view class="devide-into">
		<u-popup @open="openedPopup" v-model="show" mode="center" width="80%" :mask-close-able="false"
			border-radius="14">
			<view class="popup-wrapper">
				<u-icon @click="closePopup" name="close" sieze="28" class="close-icon"></u-icon>
				<view class="popup-hint">生成预约单</view>
				<scroll-view scroll-y="true" class="popup-main">
					<view style="margin-bottom: 10rpx;font-size: 30rpx;">选择寄送地址</view>
					<u-radio-group v-model="value" :wrap="true" :label-disabled="false">
						<u-radio  @change="radioChange" v-for="(item, index) in appointmentList" :key="index" :name="item.id"
							>
							{{item.true_name}}&nbsp;{{item.mobile}}&nbsp;{{item.address}}
						</u-radio>
					</u-radio-group>
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
		name: "appointment",
		components: {
			popupBottom
		},
		props: {
			show: {
				type: Boolean,
				default: false,
				required: true
			},
			appointmentList: {
				required: true
			}
		},
		data() {
			return {
				value:'',
				id:null
			};
		},
		methods: {

			// 打开弹窗
			openedPopup() {
				this.id = null
				this.value = ''
			},

			// 关闭弹框
			closePopup() {
				this.$emit('update:show', false)
			},

			// 确定分成
			confirmDevide() {
				this.$emit('appointmentClose', this.id)
			},
			radioChange(e){
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