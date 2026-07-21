<template>
	<view class="content" v-if="obj.goods_name">
		<view class="detail-main">
			<u-image width="100%" height="750" :src="obj.imgurl" :lazy-load="true" :fade="true" duration="450">
				<u-loading slot="loading"></u-loading>
				<view slot="error" style="font-size: 24rpx;">加载失败</view>
			</u-image>
			<view class="datail-head">
				<view class="item-title"> {{ obj.goods_name }}</view>
				<!-- <view class="item-model"> 产品型号: {{obj.goods_spec.split(',')[0]}}</view> -->
				<view class="item-model"> 产品型号: {{ spec }}</view>
				<view class="item-model"> 产品品牌: {{obj.goods_brand.name || ''}}</view>
				<!--         登录后-->
				<view v-if="userInfo.userId">
					<!-- H类，外部公司，外部合作公司。public -->
					<view
						v-if="!roleType || roleType == userList['H_USER']['roleName'] || roleType == userList['PUBLIC']['roleName'] || roleType == userList['OUT_COOPERATE_COMPANY']['roleName'] || roleType == userList['OUT_COMPANY']['roleName']">
						<view class="item-stock"> 库存:
							<block v-if="nums"> {{nums}} / {{totalnum}} </block>
							<block v-else>--</block>
						</view>
					</view>
					<view v-else>
						<view class="item-model"> 租赁参考价: {{zlckj? zlckj : '待添加'}}</view>
						<view class="item-model"> 销售参考价: {{xsckj? xsckj : '待添加'}}</view>
						<view class="item-stock"> 库存:
							<block v-if="nums"> {{nums}} / {{totalnum}} </block>
							<block v-else>--</block>
						</view>
						<view class="item-stock" v-if="obj.quantityInTransit && obj.quantityInTransit"> 在途:
							<block v-if="nums"> {{obj.quantityInTransit}} </block>
						</view>
						<view class="each-storage">
							<view class="each-storage-item" v-for="(item, index) in each_obj" :key="index">
								<view class="flag"></view><text>{{ index}}：{{ item }}台</text>
							</view>
						</view>
					</view>
				</view>
				<view v-else>
					<view class="item-stock"> 库存:
						<block v-if="nums"> {{nums}} / {{totalnum}} </block>
						<block v-else>--</block>
					</view>
				</view>
			</view>
		</view>

		<view class="detail-box">
			<text>产品详情</text>
			<view style="padding: 0 30rpx;">
				<u-empty v-if="!obj.goods_details" text="暂无详情"></u-empty>
				<u-parse :html="obj.goods_details || ''"></u-parse>
			</view>
		</view>
	</view>
</template>

<script>
	import {
		fetchDeviceDetailApi
	} from '@/api/index.js'
	import {requestClose} from "@/request";
	export default {
		data() {
			return {
				userInfo: {},
				titleStyle: {
					'fontSize': '24rpx',
					'color': '#333333',
					'opacity': '0.8'
				},
				nums: '',
				totalnum: '',
				goodType: '',
				obj: {},
				zlckj: '',
				gsfs: {},
				xsckj: '',
				each_obj: null,
				spec: '',
				storeId: '',
        lang: '',
        nowId:'',
				roleType: '',
				userList: {},
				url: 'https://qgongye.oss-cn-shanghai.aliyuncs.com/',

			}
		},
		onLoad(options) {
			const {
				gc_id = '',
					nums,
					totalnum,
					goodType,
					zlckj,
					xsckj,
					spec,
					id,
				storeId
			} = options

      this.nowId = id
			this.gc_id = gc_id
			this.nums = nums
			this.totalnum = totalnum
			this.goodType = goodType
			this.zlckj = zlckj
			this.xsckj = xsckj
			this.spec = spec
			this.storeId = storeId
			this.userInfo = uni.getStorageSync('userInfo');
			this.roleType = this.userInfo.roleName;
			this.userList = uni.getStorageSync('userList') || {}
			this.getAppGoods(this.nowId, this.goodType)
		},
		methods: {
			getAppGoods(id, type) {
				fetchDeviceDetailApi({
					id,
					type,
					goodsSpec: this.spec,
					storeId: this.storeId,
					gc_id: this.gc_id,
				}).then(res => {
					this.gsfs = res.obj.gsfs
					this.obj = res.obj.obj
					this.each_obj = res.obj.storeDetail
					var url = res.obj.obj.goods_main_photo.path
					if (url) {
						if (url.indexOf(this.url) != -1) {
							this.obj.imgurl = this.url + '/upload/order/' + this.obj.goods_main_photo.name
						} else {
							this.obj.imgurl = this.url + '/goods/' + this.obj.goods_main_photo.name
						}
					}
				})
			},
		},
		onUnload() {
			requestClose()
		},
	}
</script>

<style lang="scss" scoped>
	.each-storage {
		margin-top: 10rpx;
		font-size: 22rpx;
		color: #333333;
		opacity: 0.5;

		.each-storage-item {
			display: flex;
			align-items: center;

			text {
				margin-left: 5rpx;
			}

			.flag {
				width: 8rpx;
				height: 8rpx;
				border-radius: 50%;
				background-color: #000;
				margin-left: 5rpx;
			}
		}
	}

	.content {
		padding: 0;
	}

	.detail-main {

		.datail-head {
			padding: 24rpx;
			margin-bottom: 30rpx;
			background: #FFFFFF;

			.item-title {
				font-size: 28rpx;
				color: #333333;
				font-weight: bold;
				margin-bottom: 20rpx;
			}

			.item-model {
				font-size: 24rpx;
				color: #333333;
				opacity: 0.7;
				margin-bottom: 14rpx;
			}

			.item-stock {
				font-size: 22rpx;
				color: #333333;
				opacity: 0.5;
			}
		}
	}

	.detail-box {
		background: #FFFFFF;
		border-radius: 20rpx;
		border-top: 20rpx solid #F9F9F9;

		text {
			font-size: 28rpx;
			color: #333333;
			display: block;
			padding: 30rpx;
			text-align: center;
		}
	}
</style>
