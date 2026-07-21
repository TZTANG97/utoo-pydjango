<template>
	<view class="Box">
		<view class="topBox">
			<view class="keyong">
				<text>可兑换积分</text>
				<p>{{userInfo ? totalIntegral : ''}}</p>
			</view>

			<view class="linqi" style="margin-left: 40rpx;">
				<text>临期积分</text>
				<p>{{userInfo ? expireIntegral : ''}}</p>
			</view>
		</view>
		<view class="btns-list">
			<view class="btn" :style="{color:btnType == 1 ? '#258dff' : '#000'}" @click="jfdh">
				积分兑现
			</view>
			<view class="btn" :style="{color:btnType == 2 ? '#258dff' : '#000'}" @click="jfmx">
				积分明细
			</view>
			<view class="btn" :style="{color:btnType == 3 ? '#258dff' : '#000'}" @click="dhjl">
				兑换记录
			</view>
		</view>
		<view class="shop-list" v-if="btnType == 1">
			<view class="shopItem" @click="shopItemFn(item)" v-for="(item,index) in list">
				<img :src="'https://qgongye.oss-cn-shanghai.aliyuncs.com/'+item.path+'/'+item.name" alt="图片待定" />
				<view class="msg">
					<p>{{item.good_name}}</p>
					<view class="jf">
						<text>{{item.nums}}积分</text>
						<text>库存：{{item.inventory_num || 0}}</text>
					</view>
				</view>
			</view>
		</view>
		<!-- <view class="jf-list" v-if="btnType == 2">
			<view class="mxItem" v-for="item,index in mxList">
				<text>关联编号：</text><text>{{item.orderId}}</text>
				<text>类型：</text><text>{{typeFn(item.type)}}</text>
				<text>时间：</text><text>{{$alterTime(item.addTime)}}</text>
				<text>积分：</text><text>{{item.integral}}</text>
			</view>
		</view>
		<view class="dh-list" v-if="btnType == 3">
			<view class="dhItem" v-for="item,index in dhList">
				<text>用户名：</text><text>{{item.user_name}}</text>
				<text>手机号：</text><text>{{item.mobile}}</text>
				<text>地址：</text><text>{{item.address}}</text>
				<text>时间：</text><text>{{$alterTime(item.redeem_time)}}</text>
				<text>描述：</text><text>{{item.info}}</text>
			</view>
		</view> -->
		<view class="list">
			<view class="order-list" v-if="btnType == 2">
				<view class="item" v-for="(item, idx) in list" :key="idx">
					<view class="title">
					</view>
					<view class="content">
						<view class="content-item" >
							关联订单：{{ item.type == 4 ? '签到获得积分' : item.orderNum }}
						</view>
						<view class="content-item">
							类型：{{ typeFn(item.type) }}
						</view>
						<view class="content-item">
							时间：{{ $alterTime(item.addTime) }}
						</view>
						<view class="content-item">
							积分：{{ item.type == 1? '+' : ''  }}{{ item.integral }}
						</view>
					</view>
				</view>
			</view>
			<view class="order-list" v-if="btnType == 3">
				<view class="item" v-for="(item, idx) in list" :key="idx">
					<view class="title" style="color: #fff;padding-left: 22rpx;">
						<text>{{item.order_id}}</text>
					</view>
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
	</view>
</template>

<script>
	import MyLoading from "@/components/loading.vue"
	import {
		List_dpt,
		userredeemloglist,
		getIntegral,
		getIntegralList
	} from '@/api/points.js'
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				btnType: 1,
				page: 1,
				dataList: [],
				dhList: [],
				userInfo:null,
				mxList:[],
				expireIntegral:0,
				totalIntegral:0,
				list:[],
				loading: false,
				isRefresh: true,
			}
		},
		onShow() {
			this.userInfo = uni.getStorageSync('userInfo');
			getIntegral().then(res=>{
				this.expireIntegral = res.obj.expireIntegral
				this.totalIntegral = res.obj.totalIntegral
			})
			this.btnType = 1
			this.page = 1
			this.list = []
			this.isRefresh = true
			this.List_dptFn()
		},
		onLoad() {

		},
		onReachBottom() {
			if (this.isRefresh) {
				this.page++
				if(this.btnType == 1) this.List_dptFn()
				if(this.btnType == 2) this.getIntegralListFn()
				if(this.btnType == 3) this.userredeemloglistFn()
			}
		},
		methods: {
			// 商品列表
			List_dptFn(){
				List_dpt({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
				}).then(res => {
					if (res.data) {
						this.list = [...this.list, ...res.data]
						if (res.data.length !== 10) {
							this.isRefresh = false
						}
					} else {
						this.$tip(res.resMsg)
					}
				})
			},
			// 积分明细
			getIntegralListFn(){
				getIntegralList({
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
			// 兑换记录
			userredeemloglistFn(){
				userredeemloglist({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
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
			// 积分兑换
			jfdh() {
				if(!this.userInfo){
					uni.switchTab({
						url: '/pages/my/my'
					});
				}else{
					this.isRefresh = true
					this.list = []
					this.btnType = 1
					this.page = 1
					this.List_dptFn()
				}
			},
			// 积分明细
			jfmx() {
				if(!this.userInfo){
					uni.switchTab({
						url: '/pages/my/my'
					});
				}else{
					this.isRefresh = true
					this.list = []
					this.btnType = 2
					this.page = 1
					this.getIntegralListFn()
				}
			},
			// 兑换记录
			dhjl() {
				if(!this.userInfo){
					uni.switchTab({
						url: '/pages/my/my'
					});
				}else{
					this.isRefresh = true
					this.list = []
					this.btnType = 3
					this.page = 1
					this.userredeemloglistFn()
				}
			},
			// 商品详情页
			shopItemFn(item) {
				if(!this.userInfo){
					uni.switchTab({
						url: '/pages/my/my'
					});
				}else{
					uni.navigateTo({
						url: '/staff/points_mall/productDetails?id=' + item.id
					})
				}

			},
			// 积分类型
			typeFn(type){
				return type == 1 ? "订单完成增加" : type == 2 ? "兑换支出" : type == 3 ? '积分支出' : type == 4 ? '签到' : ''
			}
		}
	}
</script>

<style scoped lang="scss">
	.Box {
		width: 100%;
		background-color: #fcfbf7;
	}

	.topBox {
		display: flex;
		align-items: center;
		width: 100%;
		padding-bottom: 40rpx;
		border-bottom: #f9f8f4 1rpx solid;
		background-color: #fbfaf6;
		padding: 40rpx;
		.keyong,
		.linqi {
			display: flex;
			flex-direction: column;
			justify-content: space-between;
			// width: 160rpx;
			height: 110rpx;

			text {
				color: #b7b6b2;
				font-size: 25rpx;
			}

			p {
				font-weight: 700;
				font-size: 46rpx;
			}
		}
	}

	.btns-list {
		display: flex;
		justify-content: space-around;
		width: 100%;
		margin: 40rpx 0;
	}

	.shop-list {
		display: flex;
		justify-content: space-between;
		flex-wrap: wrap;
		padding: 0 24rpx;

		.shopItem {
			width: 48%;
			margin: 20rpx 0;
			background-color: #faf7f2;

			img {
				width: 100%;
				height: 300rpx;
				background-color: #fff;
			}

			.msg {
				padding: 20rpx;

				p {
					padding-bottom: 20rpx;
					color: #5b5a56;
					font-size: 24rpx;
				}

				.jf {
					display: flex;
					justify-content: space-between;
					color: #5b5a56;

					text {
						font-size: 24rpx;
					}
				}
			}
		}
	}
	.jf-list{
		width: 100%;
		.mxItem{
			display: flex;
			align-content: space-between;
			flex-wrap: wrap;
			margin: 30rpx 0;
			border: 1rpx #ccc solid;
			padding: 20rpx;

			text {
				width: 50%;
			}
		}
	}

	.dh-list {
		width: 100%;

		.dhItem {
			display: flex;
			align-content: space-between;
			flex-wrap: wrap;
			margin: 30rpx 0;
			border: 1rpx #ccc solid;
			padding: 20rpx;

			text {
				width: 50%;
			}
		}
	}
	.list {
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
</style>
