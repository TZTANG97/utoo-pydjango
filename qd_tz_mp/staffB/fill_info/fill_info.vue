<template>
	<view class="container">
		<view class="title">
			身份信息
		</view>
		<view class="input-list">
			<view class="item">
				<view class="label">姓名</view>
				<input type="text" v-model="name" placeholder="请输入姓名" maxlength="11" />
			</view>
			<view class="item">
				<view class="label">身份</view>
				<input type="text" :disabled="true" v-model="work" placeholder="请选择身份，如：学生" />
				<picker @change="bindPickerChange" :value="selectedWordIdx" :range="workList">
					<image src="@/static/down.png" mode=""></image>
				</picker>
			</view>
		</view>

		<view class="submit-btn" @click="submit">
			提&nbsp;交
		</view>

		<view class="tip">
			为了向您提供更高效以及精准的服务，注册时会要求您提供相应的身份信息，若您拒绝提供，您可以随时退出注册流程。
		</view>

	</view>
</template>

<script>
	import {
		regingSaveUserInfoApi
	} from '@/api/index'
	export default {
		data() {
			return {
				name: '',
				work: '',
				openid: '',
				workList: ['高校', '科研院所', '企业', '医院', '其他'],
				selectedWordIdx: 0,
				mobile: '',
				ticket: '',
				openid: '',
				mobile: '',
				ticket: ''
			}
		},
		onLoad({ ticket, openid, mobile }) {
			if (ticket) {
				this.ticket = ticket
			}
			if (openid) {
				this.openid = openid
			}
			if (mobile) {
				this.mobile = mobile
			}
		},

		methods: {

			// 确认工作
			bindPickerChange({
				detail: {
					value
				}
			}) {
				this.work = this.workList[value - 0]
			},

			// 提交信息
			submit() {
				if (!this.name) return this.$toast('请输入姓名')
				if (!this.work) return this.$toast('请选择身份')
				const {
					name,
					work,
					openid,
					mobile,
					ticket
				} = this
				regingSaveUserInfoApi({
					name,
					openid,
					work,
					mobile,
					ticket
				}).then(res => {
					if (res.res) {
						uni.redirectTo({
							url: '/staffB/result/result?title=提交成功'
						})
					} else {
						this.$toast(res.resMsg ? res.resMsg : '提交失败，请重试！')
					}
				})
			},
		}
	}
</script>



<style scoped lang="scss">
	.tip {
		margin-top: 40rpx;
		padding: 0 20rpx;
		color: #6A6A6A;
	}

	.submit-btn {
		height: 80rpx;
		border-radius: 5rpx;
		background-color: $primary;
		color: #fff;
		text-align: center;
		line-height: 80rpx;
		margin: 60rpx 20rpx 0;
	}

	.title {
		padding: 25rpx 20rpx;
	}

	.input-list {
		background-color: #fff;

		.label {
			position: relative;

			&::before {
				content: '*';
				left: -18rpx;
				top: 0;
				color: #f00;
				position: absolute;
			}
		}

		.item {
			position: relative;
			padding: 0 25rpx;
			display: flex;
			align-items: center;
			height: 100rpx;

			image {
				position: absolute;
				right: 20rpx;
				top: 50%;
				width: 50rpx;
				margin-top: -25rpx;
				height: 50rpx;
				z-index: 2;
			}
		}

		input {
			flex-grow: 1;
			height: 100rpx;
			margin-left: 100rpx;
		}
	}
</style>
<style>
	page {
		background-color: #F6F6F6;
	}
</style>