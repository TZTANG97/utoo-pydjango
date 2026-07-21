<template>
	<view class="rate-customers">
		<u-popup @close="closedPopup" border-radius="10" width="80%" v-model="show" mode="center"
			:mask-close-able="false">
			<view class="wrapper">
				<view class="title">
					评价客户
				</view>
				<u-icon class="close-icon" name="close" @click="closePopup"></u-icon>
				<view class="submit-info">
					<view class="option">
						<view class="label">评价等级：</view>
						<u-rate min-count="1" :count="5" :current="star" @change="getStar"></u-rate>
					</view>
					<view class="option">
						<view class="label">评价内容：</view>
						<textarea placeholder="请输入评价内容" v-model="rateContent" />
					</view>
				</view>
				<view class="submit-btn" @click="submitInfo">提交</view>
			</view>
		</u-popup>
	</view>
</template>

<script>
	export default {
		name: "rateCustomers",
		props: {
			show: {
				default: false,
				type: Boolean
			}
		},
		data() {
			return {
				rateContent: '',
				star: 5
			};
		},
		methods: {

			// 关闭弹窗之后重置一下数据
			closedPopup() {
				this.rateContent = ''
				this.star = 5
			},

			// 提交评价
			submitInfo() {
				const {
					star,
					rateContent
				} = this
				if (!rateContent) return this.$tip('请填写评价内容')
				this.$emit('getValue', {
					star,
					rateContent
				})
			},

			// 获取评星数量
			getStar(e) {
				this.star = e
			},

			// 关闭弹框
			closePopup() {
				this.$emit('update:show', false)
			},
		}
	}
</script>

<style lang="scss" scoped>
	.label {
		margin-bottom: 10rpx;
	}

	textarea {
		width: 90%;
		height: 200rpx;
		border: 1rpx solid #EFEFEF;
		border-radius: 7rpx;
		box-sizing: border-box;
		padding: 7rpx;
	}

	.wrapper {
		position: relative;
		padding: 20rpx 30rpx;
		overflow: scroll;

		.submit-btn {
			width: 100%;
			height: 60rpx;
			text-align: center;
			color: #fff;
			background-color: $primary;
			line-height: 60rpx;
			border-radius: 10rpx;
			margin-top: 50rpx;
		}

		.option {
			margin-top: 15rpx;
		}


		.close-icon {
			position: absolute;
			right: 25rpx;
			top: 25rpx;
		}

		.title {
			text-align: center;
			font-size: 32rpx;
			font-weight: bold;
		}
	}
</style>
