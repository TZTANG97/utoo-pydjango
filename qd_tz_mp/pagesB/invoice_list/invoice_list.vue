<template>
	<view class="container">
		<view class="btns">
			<view class="btn" @click="addFP">
				新增发票
			</view>
		</view>

		<view class="list">
			<view class="item" v-for="(item, idx) in list" :key="idx">
				<view class="item-row syxItem">
					<text>发票{{ idx+1 }}</text>
					<text v-if="item.is_default">默认</text>
				</view>
				<view class="item-row">
					<text>发票抬头：{{ item['invoice_title'] }}</text>
				</view>
				<view class="item-row">
					<text>企业税号：{{ item['taxNum'] }}</text>
				</view>
				<view class="item-row">
					<text>开户行名称：{{ item['bank'] }}</text>
				</view>
				<view class="item-row">
					<text>开户行账号：{{ item['bankCardNum'] }}</text>
				</view>
				<view class="item-row">
					<text>邮箱：{{ item['email'] }}</text>
				</view>
				<view class="item-row">
					<text>注册地址：{{ item['address'] }}</text>
				</view>
				<view class="item-row">
					<text>地址电话号码：{{ item['mobile'] }}</text>
				</view>
				<view class="btns">
					<view class="btn" v-if="!item.is_default" @click="defaultFn(item)">
						设为默认
					</view>
					<view class="btn" @click="deleteFn(item)">
						删除
					</view>

					<view class="btn" @click="editFn(item)">
						编辑
					</view>
				</view>


			</view>
		</view>
		<u-modal v-model="show" :show-cancel-button='true' @confirm="confirm" ref="uModal" :async-close="true"
			content="确定要删除该发票信息吗？"></u-modal>
	</view>
</template>

<script>
	import {
		fetchDefaultinvoiceInfoApi,
		addInvoiceInfoApi,
		getInvoiceInfoData,
		delinvoiceInfo
	} from '@/api/index.js'
	export default {
		data() {
			return {
				list: [],
				show: false,
				id:null
			};
		},
		onShow() {
			this.getInvoiceInfoDataFn()
		},
		methods: {
			getInvoiceInfoDataFn() {
				getInvoiceInfoData().then(res => {
					this.list = res.obj.invoiceInfs
				})
			},
			addFP() {
				uni.navigateTo({
					url: '/pagesB/invoice_info/invoice_info'
				})
			},
			editFn(data) {
				uni.navigateTo({
					url: '/pagesB/invoice_info/invoice_info?data=' + JSON.stringify(data)
				})
			},
			defaultFn(item) {
				delinvoiceInfo({
					id: item.id,
					type: 2
				}).then(res => {
					this.getInvoiceInfoDataFn()
					this.$toast(res.res ? '设置默认成功' : res.resMsg)
				})
			},

			deleteFn(item) {
				this.id = item.id
				this.show = true
			},
			confirm() {
				this.show = false
				delinvoiceInfo({
					id: this.id,
					type: 1
				}).then(res => {
					this.getInvoiceInfoDataFn()
					this.$toast(res.res ? '删除成功' : res.resMsg)
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/add-order-btn.scss';

	.container {
		padding: 0 30rpx;
	}

	.btns {
		display: flex;
		flex-direction: row-reverse;
		flex-wrap: wrap;
		margin-bottom: 20rpx;

		.btn {
			position: relative;
			height: 70rpx;
			border-radius: 40rpx;
			text-align: center;
			line-height: 70rpx;
			border: 3rpx solid $primary;
			color: $primary;
			margin: 20rpx 20rpx 0 0;
			padding: 0 40rpx;
			background-color: transparent;
			z-index: 2;
		}
	}

	.list {
		overflow: hidden;

		.item-row {
			height: 60rpx;
			line-height: 60rpx;
			box-sizing: border-box;
			padding: 0 20rpx;
			width: 100%;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;

			&:first-child {
				height: 80rpx;
				line-height: 80rpx;
				background-color: $primary;
				color: #FFF;
			}
		}

		.syxItem {
			display: flex;
			justify-content: space-between;
		}


		.item {
			margin-top: 20rpx;
			background-color: #FFF;
			border-radius: 5rpx;
			overflow: hidden;
		}
	}
</style>