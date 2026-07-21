<template>
	<view class="container">
		<view class="ide-list flex-around">
			<view class="ide" v-for="(item, idx) in ideList" :key="idx"
				:class="selectedIdeIndex == idx? 'ide-active' : ''" @click="chooseIde(idx)">
				<image src="https://ask.dcloud.net.cn/uploads/avatar/000/08/81/38_avatar_max.jpg" mode=""></image>
				<view class="ide-name">{{ item }}</view>
			</view>
		</view>

		<view class="main-btn" @click="goToVerify">
			去完善
		</view>
		<!-- 		<navigator open-type="navigateBack" hover-class="none" :delta="1" class="next-time">
			下次再说
		</navigator> -->
	</view>
</template>

<script>
	export default {
		data() {
			return {
				ideList: [
					'个人', '企业'
				],
				selectedIdeIndex: 0
			};
		},
		methods: {
			chooseIde(idx) {
				if (this.selectedIdeIndex == idx) return
				this.selectedIdeIndex = idx
			},
			// 去认证
			goToVerify() {
				let url = '../personal_cert/personal_cert'
				if (this.selectedIdeIndex) {
					// 企业
					url = '../enterprise_cert/enterprise_cert'
				}

				uni.redirectTo({
					url
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
	.next-time {
		margin-top: 30rpx;
		color: $primary;
		text-align: center;
	}

	.main-btn {
		margin-top: 70rpx;
		width: 85%;
	}

	.ide {
		border: 1rpx solid #F0F0F0;
		padding: 40rpx 35rpx;
		border-radius: 10rpx;

		.ide-name {
			margin-top: 20rpx;
			font-weight: bold;
		}

		image {
			width: 100rpx;
			height: 100rpx;
			border-radius: 50%;
		}
	}

	.ide-active {
		border: 1rpx solid $primary;
	}

	.ide-list {
		margin-top: 200rpx;
	}

	.container {
		text-align: center;
	}
</style>