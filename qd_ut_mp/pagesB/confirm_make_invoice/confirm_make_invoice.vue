<template>
	<view class="container">
		<view class="form">
			<view class="form-item">
				<view class="label">
					可开票金额：
				</view>
				<view class="control money">
					<text>{{ format_with_Intl(money) }}</text>元
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					公司名称：
				</view>
				<view class="control">
					<input type="text" maxlength="30" v-model="invoiceInfo.invoice_title" placeholder="请输入姓名">
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					信用代码：
				</view>
				<view class="control">
					<input type="text" maxlength="30" v-model="invoiceInfo.taxNum" placeholder="请输入姓名">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					开户行名称：
				</view>
				<view class="control">
					<input type="text" maxlength="30" v-model="invoiceInfo.bank" placeholder="请输入开户行名称">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					开户行账号：
				</view>
				<view class="control">
					<input type="text" maxlength="30" v-model="invoiceInfo.bankCardNum" placeholder="请输入开户行账号">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					注册地址：
				</view>
				<view class="control">
					<input type="text" maxlength="30" v-model="invoiceInfo.address" placeholder="请输入注册地址">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					注册电话：
				</view>
				<view class="control">
					<input type="text" maxlength="30" v-model="invoiceInfo.mobile" placeholder="请输入注册电话">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					发票类型：
				</view>
				<view class="control" style="margin-top: 20rpx;">
					<uni-data-select :clear="false" v-model="value" :localdata="range"></uni-data-select>
				</view>
			</view>
			<view class="form-item">
				<view class="label must">
					电子邮箱：
				</view>
				<view class="control">
					<input type="text" maxlength="30" v-model="invoiceInfo.email" placeholder="请输入电子邮箱">
				</view>
			</view>
<!-- 			<view class="form-item" v-else>
				<view class="label must">
					收件地址：
				</view>
				<view class="control">
					<input type="text" maxlength="50" v-model="invoiceInfo.address_info" placeholder="请输入收件地址">
				</view>
			</view> -->
		</view>

		<view class="main-btn" @click="confirmSubmit">
			确&nbsp;定
		</view>
	</view>
</template>

<script>
	import {
		confirmMakeInvoiceApi,
		fetchDefaultinvoiceInfoApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
				id: '',
				money: 0,
				type: 1,
				invoiceInfo: null,
				value: 1,
				range: [{
						value: 1,
						text: "电子普通发票"
					},
					{
						value: 3,
						text: "电子增值税专票"
					},
				],
			};
		},
		onLoad({
			money = 0,
			id = '',
			type = 1
		}) {
			this.id = id
			this.money = money - 0
			this.type = type - 0
			fetchDefaultinvoiceInfoApi().then(res => {
				if (res.res) {
					this.invoiceInfo = res.obj
				}
			})
		},
		methods: {

			format_with_Intl(num = 0) {
				let str = parseFloat(num).toFixed(2);
				let parts = str.split(".");
				let integerPart = parts[0];
				integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				return `${integerPart}.${parts[1]}`;
			},

			// 确定提交
			confirmSubmit() {
				if (!this.invoiceInfo.invoice_title) return this.$toast('公司名称不能为空')
				if (!this.invoiceInfo.taxNum) return this.$toast('信用代码不能为空')
				if (!this.invoiceInfo.email) return this.$toast('电子邮箱不能为空')
				// if (this.value === 2 && !this.invoiceInfo.address_info) return this.$toast('收件地址不能为空')
				const {
					email,
					bankCardNum,
					bank,
					mobile,
					address
				} = this.invoiceInfo
				confirmMakeInvoiceApi({
					bank_account: bankCardNum,
					bank_name: bank,
					credit_code: this.creditCode,
					email,
					ids: this.id,
					invoiceTitle: this.companyName,
					// 1电子 2纸质
					invoice_type: this.value,
					// 如果是1，则ids是发票订单的订单编号，2：测试实验订单的订单号
					order_type: this.type,
					reg_address: address,
					reg_mobile: mobile,
					// 1专2普
					type: 2,
				}).then(res => {
					if (res.res) {
						uni.redirectTo({
							url: '/staffB/result/result?title=开票成功'
						})
					} else {
						this.$toast(res.resMsg)
					}
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
	@import "@/layout/form-item.scss";


	.money {
		margin-top: 20rpx;

		text {
			font-size: 65rpx;
			font-weight: bold;
			color: $primary;
			vertical-align: bottom;
			margin-right: 5rpx;
		}
	}

	.main-btn {
		margin-bottom: 30rpx;
	}

	textarea {
		width: 100%;
		height: 300rpx;
		border: 1rpx solid #F0F0F0;
		border-radius: 10rpx;
		margin-top: 10rpx;
		box-sizing: border-box;
		padding: 10rpx;
	}


	.container {
		padding: 0 30rpx;
	}
</style>