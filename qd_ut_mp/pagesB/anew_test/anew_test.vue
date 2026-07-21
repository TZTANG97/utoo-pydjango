<template>
	<view class="container">
<!-- 		<uni-section title="选择子订单" type="line">
			<uni-data-picker :map="{text:'orderId',value:'id'}" placeholder="请选择子订单" popup-title="子订单"
				:localdata="childList" v-model="id">
			</uni-data-picker>
		</uni-section> -->
		<view class="list" v-if="childList.length != 0 && type">
			<view class="item" v-for="(item, index) in childList" :key="index">
				<view class="item-row"
					style="display: flex;justify-content: space-between;padding: 0 20rpx;align-items: center;">
					<text></text>
					<u-checkbox-group>
						<u-checkbox v-model="item.checked"></u-checkbox>
					</u-checkbox-group>
				</view>
				<view class="item-row">
					<text>单号：{{ item['orderId'] }}</text>
				</view>
				<view class="item-row" v-if="item['goodsSpec']">
					<text>产品型号：{{ item['goodsSpec'] }}</text>
				</view>
				<view class="item-row">
					<text>产品品牌：{{ item['goodsBrandName'] }}</text>
				</view>
				<view class="item-row">
					<text>产品名称：{{ item['goodsName'] }}</text>
				</view>
			</view>
		</view>
		<!-- 2是完成测试 -->
		<uni-section v-if="type !== 2" title="测试内容" type="line" padding>
			<textarea v-model="test_content" placeholder="请输入测试内容" maxlength="200" />
		</uni-section>

		<view class="main-btn" @click="submitTest">
			提&nbsp;交
		</view>
	</view>
</template>

<script>
	import {
		anewTestApi,
		confirmCompleteApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
				id: '',
				test_content: '',
				childList: [],
				type: 0
			}
		},
		onLoad({
			id = '',
			type = ''
		}) {
			let title = '再次测试'
			if (id) this.id = id

			if (type) {
				this.type = type - 0
				let arr = JSON.parse(uni.getStorageSync('childList'))
				arr.forEach(item=>{
					item.checked = false
				})
				this.childList = arr
				if(this.type === 2) {
					title = '确认完成'
				}
			}
			uni.setNavigationBarTitle({
				title
			})
		},
		onHide() {
			console.log('123');
			uni.removeStorageSync('childList')
		},
		methods: {
			submitTest() {
				let ids = []
				this.childList.forEach(item=>{
					if(item.checked){
						ids.push(item.id)
					}
				})
				if(ids.length == 0)  return this.$toast('请选择一条数据')
				if(ids.length != 1)  return this.$toast('只能选择一条数据')
				// if (this.type && !this.id) return this.$toast('请选择子订单')
				if (this.type !== 2 && !this.test_content) return this.$toast('请输入测试内容')

				if (this.type === 2) {
					confirmCompleteApi({
						id: ids[0]
					}).then(res => {
						if (res.res) {
							uni.redirectTo({
								url: '/staffB/result/result?title=订单已完成'
							})
							this.$toast(res.resMsg)
						} else {
							this.$toast(res.resMsg)
						}
					})
				} else {
					let data = {
						orderId: ids[0],
						mark: this.test_content
					}
					anewTestApi(data).then(res => {
						if (res.res) {
							uni.redirectTo({
								url: '/staffB/result/result?title=提交成功'
							})
							this.$toast(res.resMsg)
						} else {
							this.$toast(res.resMsg)
						}
					})
				}
			}
		}
	}
</script>

<style lang="scss">
	.uni-rate {
		padding-left: 15rpx !important;
	}

	.uni-section-header__decoration {
		background-color: $primary !important;
	}
	
</style>

<style scoped lang="scss">
	textarea {
		border: 3rpx solid rgba(233, 99, 2, .6);
		border-radius: 10rpx;
		padding: 10rpx;
		box-sizing: border-box;
		width: 100%;
	}

	.container {
		padding: 0 20rpx;
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
	}
	
	.item {
		margin-top: 20rpx;
		background-color: #FFF;
		border-radius: 5rpx;
		overflow: hidden;
	}
</style>