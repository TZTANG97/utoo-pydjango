<template>
	<view class="balance-recharge">
		<view class="header">
			<image src="../static/logo.png" mode=""></image>
			<text>上海愉兔检测科技有限公司</text>
		</view>
		<view class="input">
			<text class="currency">￥</text>
			<u-field :disabled="true" :clearable="false" :border-bottom="false" v-model="money"
				placeholder="输入充值金额"></u-field>
		</view>
		<!-- 判断充值金额是否有效 -->
		<u-keyboard :class="money - 0 >= 0.01? 'u-tooltips-submit-normal' : 'u-tooltips-submit-disable'" v-model="show"
			:cancel-btn="false" :mask="false" :safe-area-inset-bottom="true" :show-tips="false" ref="uKeyboard"
			mode="number" :mask-close-able="false" @change="enter" @backspace="backspace"
			@confirm="finish"></u-keyboard>
		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import {
		rechargeToBalanceApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
				money: '',
				show: true
			}
		},
		methods: {

			// 退格
			backspace() {
				let new_money = this.money.split('')
				new_money.splice(new_money.length - 1, 1)
				this.money = new_money.join('')
			},

			async finish(e) {
				this.show = true
				if (this.money - 0 < 0.01) return
				const money = parseFloat(this.money)
				this.money = money.toFixed(2)
				if (money > 99999.99) return this.$tip('充值金额超过最大限制')

				const result = await wx.login(),
					that = this;
				rechargeToBalanceApi({
					code: result.code,
					money: this.money
				}).then(res => {
					if (res.res) {
						const {
							timeStamp,
							prepayId,
							paySign,
							nonceStr,
						} = res.obj
						wx.requestPayment({
							timeStamp: timeStamp + '',
							nonceStr,
							package: `prepay_id=${prepayId}`,
							signType: 'RSA',
							paySign,
							success(res) {
								uni.redirectTo({
									url: '/staffB/result/result?title=充值成功'
								})
							}
						})
					} else {
						this.$tip('充值失败，请重试！')
					}
				})
			},

			// 输入充值金额
			enter(e) {
				e = e + ''

				// 首字符不能为.
				if (!this.money && e === '.') e = '0.'
				// 整数开头不能连着输入两个0
				if (this.money === '0' && e === '0') return
				// 只能出现一个.
				if (this.money.indexOf('.') !== -1 && e === '.') return
				// 小数位长度不能超过2
				if (this.money[this.money.length - 3] === '.') return
				// 限制整数位长度
				if (this.money.split('.')[0].length === 5 && this.money.length === 5 && e !== '.') return

				this.money += e
			},
		}
	}
</script>

<style lang="scss">
	.u-tooltip-item {
		font-size: 36rpx !important;
	}

	.u-label {
		display: none !important;
	}

	.u-field {
		padding: 0 !important;
	}

	.u-field__input-wrap {
		font-size: 80rpx !important;
		height: 120rpx !important;
	}

	.input {
		display: flex;
		position: relative;
		z-index: 10075;
		width: 100%;
		background-color: #fff;
		padding: 30rpx 20rpx;
		margin-top: 40rpx;
		border-radius: 20rpx;

		.currency {
			font-weight: bold;
			font-size: 60rpx;
			vertical-align: top;
		}
	}

	.header {
		margin-top: 30rpx;

		image {
			width: 90rpx;
			height: 90rpx;
			border-radius: 10rpx;
		}

		text {
			margin-left: 25rpx;
			color: #000;
			font-size: 35rpx;
		}
	}


	.u-tooltips-submit-disable {
		.u-tooltips-submit {
			color: #D7D9DE !important;
		}
	}

	.u-tooltips-submit-normal {
		.u-tooltips-submit {
			color: $primary !important;
		}
	}

	.u-keyboard-grids-btn {
		font-size: 42rpx;
	}

	.balance-recharge {
		padding: 0 30rpx;
		overflow: hidden;
	}

	page {
		background-color: #F6F6F6;
	}
</style>