<template>
	<view class="container">
		<view class="header">
			<image src="@/static/head.png" mode=""></image>
			<view class="nick-name">
				Jin
			</view>
			<view class="user-mobile">
				17555523231
			</view>
		</view>
		<view class="badge">
			<image src="@/static/badge.png" mode=""></image>
			<image src="@/static/badge.png" mode=""></image>
			<image src="@/static/badge.png" mode=""></image>
			<image src="@/static/badge.png" mode=""></image>
			<image src="@/static/badge.png" mode=""></image>
		</view>
		<view class="main-menu">
			<view class="main-menu-item">
				<view class="num">10</view>
				<view class="label">我的订单</view>
			</view>
			<view class="main-menu-item">
				<view class="num">8</view>
				<view class="label">我的发票</view>
			</view>
			<view class="main-menu-item">
				<view class="num">10</view>
				<view class="label">预约记录</view>
			</view>
		</view>
		<view class="sub-menu">
			<view class="sub-menu-item">
				<view class="label">
					我的积分
				</view>
				<view class="money">
					<text>10500</text>
					<view class="btn">
						兑换
					</view>
				</view>
			</view>
			<view class="sub-menu-item">
				<view class="label">
					我的余额
				</view>
				<view class="money">
					<text>0</text>
					<view class="btn">
						兑换
					</view>
				</view>
			</view>
		</view>
		<view class="make-task">
			<view class="label">
				<text>DISCOVERY</text>
				<text>探索任务</text>
			</view>
			<image src="@/static/right.png" mode=""></image>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {

			};
		}
	}
</script>

<style lang="scss" scoped>
	
	.regular-user {
		
	}
	
	.make-task {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 40rpx 0;
		
		.label {
			text:nth-child(1) {
				font-size: 40rpx;
				font-weight: bold;
			}
			
			text:nth-child(2) {
				color: #B4B5B5;
				margin-left: 20rpx;
				font-size: 24rpx;
			}
		}
		
		image {
			width: 30rpx;
			height: 30rpx;
		}
	}
	
	.sub-menu {
		display: flex;
		justify-content: space-between;
		margin-top: 20rpx;
		.sub-menu-item {
			display: flex;
			flex-direction: column;
			justify-content: space-between;
			width: 48%;
			border-radius: 15rpx;
			height: 160rpx;
			background-color: #F8FAF9;
			padding: 20rpx;
			
			.money {
				display: flex;
				justify-content: space-between;
			}
			
			.btn {
				padding: 5rpx 23rpx;
				background-color: $primary;
				border-radius: 30rpx;
				color: #fff;
			}
			
			.label {
				color: #B4B5B5;
				font-size: 24rpx;
			}
			
			text {
				font-weight: bold;
				font-size: 40rpx;
			}
		}
	}
	
	.main-menu {
		display: flex;
		justify-content: space-around;
		align-items: center;
		margin-top: 30rpx;
		background-color: #F8FAF9;
		border-radius: 10rpx;
		height: 200rpx;
		.main-menu-item {
			text-align: center;
		}
		.num {
			font-size: 40rpx;
			font-weight: bold;
		}
		
		.label {
			color: #B4B5B5;
			font-size: 24rpx;
			margin-top: 10rpx;
		}
	}
	
	.badge {
		display: flex;
		justify-content: space-around;
		margin-top: 40rpx;

		image {
			width: 90rpx;
			height: 90rpx;
			border-radius: 50%;
		}
	}

	.header {
		width: 400rpx;
		height: 400rpx;
		border-radius: 50%;
		border: 2rpx solid #efefef;
		margin: 20rpx auto 0;
		text-align: center;

		image {
			width: 120rpx;
			height: 120rpx;
			border-radius: 50%;
			border: 2rpx solid #efefef;
			margin-top: 60rpx;
		}

		.nick-name,
		.user-mobile {
			margin-top: 10rpx;
			font-size: bold;
		}
	}

	.container {
		padding: 0 20rpx;
	}
</style>