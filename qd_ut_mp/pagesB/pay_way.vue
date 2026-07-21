<template>
	<view class="pay-way">
		<uni-popup type="bottom" ref="pay_way" v-model="popupShow" :mask-click="false">
			<view class="popup-container">
				<view class="title">
					支付方式
				</view>
				<view class="item-list">
					<view class="pay-item" @click="type = 0">
						<view class="">
							<image src="@/static/balance_pay.png" mode=""></image>
							<text>余额支付</text>
						</view>
						<u-icon name="checkmark-circle" v-if="type == 0" color="#8bc34a" size="32"></u-icon>
					</view>
					<view class="pay-item" @click="type = 1">
						<view class="">
							<image src="@/static/wechat_pay.png" mode=""></image>
							<text>微信支付</text>
						</view>
						<u-icon name="checkmark-circle" v-if="type == 1" color="#8bc34a" size="32"></u-icon>
					</view>
				</view>
				<text>此单支付金额：{{ money }}</text>
				<div class="integralBox">
					<div class="imgBox">
						<div style="display: flex; align-items: center">
							<image src="../static/tb.png" mode="" />
							<span>积分抵扣</span>
						</div>
						<u-switch active-color="#e99c00" size="35" inactive-color="gray" v-model="checked"></u-switch>
					</div>
					<span style="font-size: 28rpx; font-weight: 700">仅微信/余额支付有效，当前可用积分：{{ totalIntegral }}</span>
					<br />
					<div class="sy">
						<span class="sy_left">
							<span>使用</span>
							<input :disabled="!checked" @input="inputChange"
								style="width: 180rpx;border: 1rpx #000 solid;height: 50rpx;border-radius: 6rpx;margin: 0 10rpx;padding-left: 10rpx;"
								v-model="integral_num" type="number" />
							<span>积分</span>
						</span>
						<span>-￥{{ deleteMoney }}</span>
					</div>
				</div>
				<span
					style="display: inline-block;font-size: 30rpx;width: 100%;text-align: right;font-weight: 700;">此单剩余支付金额￥
					<span v-if="!checked">{{money}}</span> <span
						v-else>{{ moneyFn(money, deleteMoney) }}</span>
				</span>
				<view class="btnBox">
					<text></text>
					<view class="btn">
						<button style="margin-right: 20rpx;" @click="closePayWay">取消</button>
						<button style="background-color: #f39800;color: #fff;" @click="choosePayWay(type)">确定</button>
					</view>
				</view>
			</view>
		</uni-popup>
		<u-modal v-model="show" :show-cancel-button='true' @confirm="confirm" ref="uModal" :async-close="true"
			content="确定要取消当前支付吗？"></u-modal>
		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import Decimal from './decimal.js'
	import {
		getIntegralConvertRatio,
		fetchMyPointsApi
	} from '@/api/index.js'
	export default {
		name: "payWay",
		props: {
			money: {
				type: Number
			}
		},
		data() {
			return {
				checked: false,
				deleteMoney: 0,
				integral_num: 0,
				surplusMoney: 0,
				type: 0,
				show: false,
				totalIntegral: 1,
				integralConvertRatio: 0,
				dom: null,
				popupShow: false
			};
		},
		watch: {
			popupShow: {
				immediate: true,
				deep: true,
				handler() {
					if (this.popupShow) {
						this.$refs['pay_way'].open()
						getIntegralConvertRatio().then(res => {
							if (res.res) {
								uni.setStorageSync('integralConvertRatio', res.obj.integral_convert_ratio)
								this.integralConvertRatio = res.obj.integral_convert_ratio
								this.integral_num = 0
								this.deleteMoney = 0
							}

						})
						fetchMyPointsApi().then(res => {
							if (res.res) {
								uni.setStorageSync('totalIntegral', res.obj.totalIntegral);
								this.totalIntegral = res.obj.totalIntegral
							}
						})
					} else {
						console.log(this.popupShow, 'false')
					}
				}
			}
		},
		methods: {
			choosePayWay(flag) {
				// 校验输入的积分和实际积分
				if (this.checked && this.integral_num % 1 !== 0)
					return this.$refs.uToast.show({
						title: '请输入正确的兑换积分',
						type: 'error ',
					})
				if (this.checked && this.integral_num < 1)
					return this.$refs.uToast.show({
						title: '请输入正确的兑换积分',
						type: 'error ',
					})
				if (this.checked && this.integral_num > this.totalIntegral)
					return this.$refs.uToast.show({
						title: '请输入正确的兑换积分',
						type: 'error ',
					})
				if (this.checked && this.integral_num / 100 > this.money)
					return this.$refs.uToast.show({
						title: '请输入正确的兑换积分',
						type: 'error ',
					})
				if (this.checked && this.deleteMoney > this.money)
					return this.$refs.uToast.show({
						title: '请输入正确的兑换积分',
						type: 'error ',
					})
				if (this.checked == false) this.integral_num = 0
				if (flag == 1 && (this.moneyFn(this.money, this.deleteMoney) == 0.00)) {
					console.log('666')
					this.$emit('choosePayWayEvent', flag, this.integral_num, this.money)
				} else {
					this.$emit('choosePayWayEvent', flag, this.integral_num)
				}
			},
			closePayWay() {
				this.show = true
			},
			confirm() {
				this.$emit('choosePayWayEvent', 'abc')
				this.popupShow = false
				this.show = false
			},
			inputChange(val) {
				this.integral_num = val.detail.value.replace(/[.]+/g, "");
				let data = new Decimal(this.integral_num == '' ? 0 : this.integral_num).div(new Decimal(100).div(this.integralConvertRatio));
				this.deleteMoney = data.toFixed(2)
			},
			moneyFn(num1, num2) {
				const data = new Decimal(num1).sub(num2);
				return data.toFixed(2)
			},

		}
	}
</script>

<style scoped lang="scss">
	.popup-container {
		background-color: #fff;
		border-radius: 10rpx;
		padding: 0 30rpx;

		.item-list {
			padding-bottom: 20rpx;

			image {
				width: 70rpx;
				height: 70rpx;
			}

			text {
				margin-left: 20rpx;
				font-weight: bold;
				vertical-align: text-top;
			}

			.pay-item {
				display: flex;
				justify-content: space-between;
				border: 1px transparent solid;
				padding-right: 30rpx;
			}

			.pay-item:nth-child(n+2) {
				margin-top: 20rpx;
			}
		}

		.title {
			padding: 20rpx 0;
			font-weight: bold;
			text-align: center;
		}
	}

	.integralBox {
		border-top: 16rpx #e99c00 solid;
		margin-top: 30rpx;
		padding-left: 40rpx;

		.imgBox {
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-top: 40rpx;
			margin-bottom: 40rpx;
			font-size: 20rpx;

			image {
				width: 70rpx;
				height: 70rpx;
				margin-right: 20rpx;
			}

			span {
				font-size: 40rpx;
				font-weight: 700;
			}
		}

		.sy {
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-top: 40rpx;
			font-size: 35rpx;
			font-weight: 700;
			margin-bottom: 40rpx;

			.sy_left {
				display: flex;
				font-size: 35rpx;
			}
		}
	}

	.btnBox {
		display: flex;
		justify-content: space-between;
		width: 100%;
		margin-top: 40rpx;

		.btn {
			width: 320rpx;
			display: flex;

			button {
				padding: 0 35rpx;
				font-size: 30rpx;
				height: 70rpx;
				line-height: 70rpx;
			}
		}

		padding-bottom: 10rpx;
	}
</style>