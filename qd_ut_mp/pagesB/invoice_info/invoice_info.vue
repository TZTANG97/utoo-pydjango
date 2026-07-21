<template>
	<view class="container">
		<view class="form">
			<view class="form-item">
				<view class="label">
					发票抬头：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" type="text" :disabled="disabled" maxlength="30"
						v-model="name" placeholder="请输入发票抬头">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					税号：
				</view>
				<view class="control">
					<input type="text" v-model="credit_code" placeholder="请输入税号">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					电子邮箱：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="text" maxlength="30"
						v-model="email" placeholder="请输入电子邮箱">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					开户行名称：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="number" maxlength="11"
						v-model="bank_name" placeholder="请输入开户行名称">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					开户行账号：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="number" maxlength="19"
						v-model="bank_account" placeholder="请输入开户行账号">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					注册地址：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="number" maxlength="11"
						v-model="reg_address" placeholder="请输入注册地址">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					注册电话：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="number" maxlength="11"
						v-model="reg_mobile" placeholder="请输入注册电话">
				</view>
			</view>
			<view class="form-item">
				<view class="label">
					收件地址：
				</view>
				<view class="control">
					<input :class="disabled? 'disable': ''" :disabled="disabled" type="number" maxlength="11"
						v-model="sj_address" placeholder="请输入收件地址">
				</view>
			</view>
		</view>

		<view class="main-btn" @click="confirmInvoiceInfo">
			确&nbsp;定
		</view>
	</view>
</template>

<script>
	import {
		email,
		bank,
		credit_code,
		idCard
	} from '@/constant/regular.js'
	import {
		fetchDefaultinvoiceInfoApi,
		addInvoiceInfoApi,
		updateinvoiceInfo
	} from '@/api/index.js'
	export default {
		data() {
			return {
				name: '',
				credit_code: '',
				email: '',
				bank_name: '',
				bank_account: '',
				reg_address: '',
				reg_mobile: '',
				sj_address: '',
				isEdit: false,
				id: 0
			};
		},
		onLoad(data) {
			if (!data.data) return this.isEdit = false
			this.isEdit = true
			let obj = JSON.parse(data.data)
			this.name = obj.invoice_title
			this.credit_code = obj.taxNum
			this.email = obj.email
			this.bank_name = obj.bank
			this.bank_account = obj.bankCardNum
			this.reg_address = obj.address
			this.reg_mobile = obj.mobile
			this.sj_address = obj.address_info
			this.id = obj.id
		},
		methods: {
			// 确定
			confirmInvoiceInfo() {
				if (this.name == '') return this.$toast('请输入发票抬头')
				if (this.email == '') return this.$toast('请输入邮箱')
				if (this.credit_code == '') return this.$toast('请输入税号')
				const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
				if (this.email && !emailRegex.test(this.email)) {
					return this.$toast('电子邮箱格式错误')
				}
				// const taxNumberRegex = /^[0-9A-Z]{15,18}$/;
				// if (this.credit_code && !taxNumberRegex.test(this.credit_code)) {
				// 	return this.$toast('税号格式错误')
				// }
				// const bankAccountRegex = /^\d{12,19}$/
				// if (this.bank_account && !bankAccountRegex.test(this.bank_account)) {
				// 	return this.$toast('开户行账号格式错误')
				// }

				const {
					name,
					credit_code,
					email,
					bank_name,
					bank_account,
					reg_address,
					reg_mobile,
					sj_address
				} = this
				if (this.isEdit) {
					updateinvoiceInfo({
						invoice_title: name,
						taxNum: credit_code,
						email,
						bank: bank_name,
						bankCardNum: bank_account,
						address: reg_address,
						mobile: reg_mobile,
						address_info: sj_address,
						id: this.id
					}).then(res => {
						this.$toast(res.res ? '编辑成功' : res.resMsg)
						setTimeout(() => {
							uni.navigateBack();
						}, 1200)
					})
				} else {
					addInvoiceInfoApi({
						invoice_title: name,
						taxNum: credit_code,
						email,
						bank: bank_name,
						bankCardNum: bank_account,
						address: reg_address,
						mobile: reg_mobile,
						address_info: sj_address,
					}).then(res => {
						this.$toast(res.res ? '新增成功' : res.resMsg)
						setTimeout(() => {
							uni.navigateBack();
						}, 1200)
					})
				}

			},
		}
	}
</script>

<style lang="scss" scoped>
	@import "@/layout/form-item.scss";

	.main-btn {
		margin-bottom: 50rpx;
	}

	.container {
		padding: 0 30rpx;
	}
</style>