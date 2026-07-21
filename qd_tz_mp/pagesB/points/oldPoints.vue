<template>
	<view class="container">
		<view class="money">
			<view class="detail-money">
				<view class="total-point">
					<view class="label">我的积分 <u-icon @click="myTotalIntegral(1)" name="question-circle" color="#2979ff"
							size="28"></u-icon> ：</view>
					<view class="points">{{ totalIntegral }}</view>
				</view>
				<view class="expiring">
					<view class="label">临期积分 <u-icon @click="myTotalIntegral(2)" name="question-circle" color="#2979ff"
							size="28"></u-icon>：</view>
					<view class="points">{{ expireIntegral }}</view>
				</view>
			</view>
		</view>
		<view class="main">
			<view class="title-list">
				<view class="title-item" @click="cutList(0)">
					积分收支明细
				</view>
				<view class="title-item" @click="cutList(1)">
					积分兑换明细
				</view>
				<view class="slider" :style="{ left: selectedIdx? selectedIdx * 30 + selectedIdx * 168 + 'rpx' : '0' }">
				</view>
			</view>

			<uni-section v-show="!selectedIdx">
				<uni-data-select :clear="false" v-model="value" :localdata="range" @change="change"></uni-data-select>
			</uni-section>
		</view>

		<view class="list">
			<view class="order-list">
				<view class="item" v-for="(item, idx) in list" :key="idx">
					<view class="title"  v-if="selectedIdx == 0">
					</view>
					<view class="title"  v-if="selectedIdx == 1" style="color: #fff;padding-left: 22rpx;">
						<text>{{item.order_id}}</text>
					</view>
					<view class="content" v-if="selectedIdx == 0">
						<view class="content-item">
							关联订单：{{ item.type == 4 ? '签到获得积分' : item.orderNum }}
						</view>
						<view class="content-item">
							时间：{{ $alterTime(item.addTime) }}
						</view>
						<view class="content-item">
							积分：{{ item.type == 1? '+' : ''  }}{{ item.integral }}
						</view>
					</view>
					<view class="content" v-if="selectedIdx == 1">
						<view class="content">
							<view class="content-item">
								用户名：{{ item.user_name }}
							</view>
							<view class="content-item">
								手机号：{{ item.mobile }}
							</view>
							<view class="content-item">
								地址：{{ item.address }}
							</view>
							<view class="content-item">
								兑换时间：{{ $alterTime(item.redeem_time) }}
							</view>
							<view class="content-item">
								商品名称：{{ item.goodName }}
							</view>
							<view class="content-item">
								商品数量：{{ item.redeem_num }}
							</view>
							<view class="content-item">
								积分：{{ item.type == 1? '+' : ''  }}{{ item.integralsum }}
							</view>
							<view class="content-item">
								发货状态：{{ item.fhstatus == 1 ? '待发货' : item.fhstatus == 2 ? '已发货'  : ''}}
							</view>
							<view class="content-item" v-if="item.fhstatus == 2">
								快递公司：{{ item.express_company}}
							</view>
							<view class="content-item" v-if="item.fhstatus == 2">
								快递单号：{{ item.express_num}}
							</view>
							<view class="content-item" v-if="item.fhstatus == 2">
								发货时间：{{ $alterTime(item.fh_time)}}
							</view>
						</view>
					</view>
				</view>
			</view>
			<my-loading :loading="loading" :total="list.length" :is-refresh="isRefresh"></my-loading>
			<u-modal v-model="show" :title-style="{color: 'red'}">
				<view class="slot-content">
					<rich-text :nodes="content"></rich-text>
				</view>
			</u-modal>
		</view>
	</view>
</template>

<script>
	import MyLoading from "@/components/loading.vue"
	import {
		fetchMyPointsApi,
		fetchMyPointsListApi
	} from '@/api/index.js'
	import {
		userredeemloglist
	} from '@/api/points.js'
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				page: 1,
				list: [],
				isRefresh: true,
				loading: false,
				selectedIdx: 0,
				totalIntegral: 0,
				expireIntegral: 0,
				value: 0,
				range: [{
						value: 0,
						text: '全部'
					},
					{
						value: 1,
						text: '已获取'
					},
					{
						value: 2,
						text: '已消耗'
					}
				],
				show: false,
				content: '',
				integralConvertRatio: 0

			}
		},
		created() {
			const data = uni.getStorageSync('integralConvertRatio');
			if (data) this.integralConvertRatio = data
		},
		onLoad(data) {
			this.getList()
			let obj = JSON.parse(data.dataObj)
			this.totalIntegral = obj.totalIntegral
			this.expireIntegral = obj.expireIntegral
			// this.getPoints()

		},
		onReachBottom() {
			if (this.isRefresh) {
				this.page++
				if(this.selectedIdx == 0) this.getList()
				if(this.selectedIdx == 1) this.getIntegralListFn()
			}
		},
		methods: {

			change() {
				this.page = 1
				this.isRefresh = true
				this.list = []
				if(this.selectedIdx == 0) this.getList()
				if(this.selectedIdx == 1) this.getIntegralListFn()
			},

			getList() {
				fetchMyPointsListApi({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
					type: this.value
				}).then(res => {
					if (res.res) {
						const {
							obj: {
								data
							}
						} = res
						this.list = [...this.list, ...data]
						if (data.length !== 10) {
							this.isRefresh = false
						}
					} else {
						this.$tip(res.resMsg)
					}
				})
			},


			// getPoints() {
			// 	this.loading = true
			// 	fetchMyPointsApi().then(res => {
			// 		if (res.res) {
			// 			const {
			// 				obj: {
			// 					totalIntegral,
			// 					expireIntegral,
			// 					expireDate
			// 				}
			// 			} = res
			// 			this.totalIntegral = totalIntegral
			// 			this.expireIntegral = expireIntegral
			// 		} else {
			// 			this.$toast(res.resMsg)
			// 		}
			// 	}).finally(_ => {
			// 		this.loading = false
			// 	})
			// },

			cutList(idx) {
				if (this.selectedIdx === idx) return
				this.selectedIdx = idx
				this.page = 1
				this.list = []
				if (this.selectedIdx == 0) {
					console.log(idx,'00')
					this.isRefresh = true
					this.getList()
				} else {
					console.log(idx,'11')
					this.isRefresh = true
					this.getIntegralListFn()
				}
			},
			getIntegralListFn(){
				userredeemloglist({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
					type: 0,
				}).then(res=>{
					if (res.res) {
						const {
							obj: {
								data
							}
						} = res
						this.list = [...this.list, ...data]
						if (data.length !== 10) {
							this.isRefresh = false
						}
					} else {
						this.$tip(res.resMsg)
					}
				})
			},
			myTotalIntegral(data) {
				if(data == 1){
					this.content = `1. 消费 1 元获得 1 积分，100 积分可抵扣 ${this.integralConvertRatio} 元，积分可累积使用<br>
					2. 网页/小程序预约下单时可自主选择是否使用积分抵扣`
				}else{
					this.content = `1. 积分有效期为获得之日起的一年内，请及时使用您的积分<br>
					2. 若您有即将到期的积分，会在到期 30 日前于此处显示`
				}
				this.show = true
			}
		}
	}
</script>

<style scoped lang="scss">
	/deep/.uni-section .uni-section-header {
		padding: 0;
		margin-top: 20rpx;
	}

	.order-list {
		overflow: hidden;

		.item {
			background-color: #fff;
			margin: 0 20rpx;
			border: 1rpx solid #F2F2F2;

			&:nth-child(n+1) {
				margin-top: 30rpx;
			}
		}

		.title {
			padding: 35rpx 0;
			background-color: $primary;
		}

		.content {
			padding: 20rpx;

			.content-item {
				&:nth-child(n+1) {
					margin-top: 10rpx;
				}
			}
		}
	}

	.money {
		background-color: #fff;
	}

	.detail-money {
		display: flex;
		flex-wrap: wrap;

		.control {
			margin: 30rpx 0 0 30rpx;
			color: $primary;
		}

		&>view {
			width: 50%;
			padding: 40rpx 0;
		}

		.label {
			margin-left: 30rpx;
		}

		.points {
			font-size: 55rpx;
			font-weight: bold;
			color: $primary;
			margin: 10rpx 0 0 30rpx;
		}
	}

	.list {
		margin-top: 20rpx;
	}

	.main {
		padding: 0 30rpx;
	}

	.title-list {
		display: flex;
		position: relative;
		padding: 15rpx 0;

		.slider {
			position: absolute;
			left: 0;
			bottom: 0;
			width: 168rpx;
			height: 6rpx;
			background-color: $primary;
			transition: all .3s;
		}

		.title-item:nth-child(n+2) {
			margin-left: 30rpx;
		}
	}

	.header {
		display: flex;
		justify-content: space-around;

		&>view {
			width: 50%;
			padding: 40rpx 0;
		}

		.label {
			margin-left: 30rpx;
		}

		.points {
			font-size: 55rpx;
			font-weight: bold;
			color: $primary;
			margin: 10rpx 0 0 70rpx;
		}
	}

	.slot-content {
		font-size: 30rpx;
		padding: 30rpx;
	}
</style>