<template>
	<view class="container">
		<!-- <image class="cover" src="@/static/start.webp" mode=""></image> -->
		<view class="header">
			<navigator style="position: relative; flex-grow: 1;" url="/staffB/search/search" hover-class="none">
				<input :disabled="true" class="search-input" type="text" placeholder="搜索实验">
				<image class="search-icon" src="@/static/search.png" mode=""></image>
			</navigator>
		</view>
		<view class="main">
			<view class="cate-list" :style="{ 'height': usable_heihgt + 'px' }">
				<view class="cate-1-list">
					<view :class="{ 'cate-1-item-active': idx === cateIndex }" class="cate-1-item"
						v-for="(item, idx) in cateList" :key="idx" @click="changeCate(idx)">
						<view class="cate-2-name">
							{{ item['name'] }}
						</view>
					</view>
				</view>
				<view class="cate-2-list">
					<template v-if="cateList && cateList[cateIndex] && cateList[cateIndex]['childList'].length">
						<view class="cate-2-item" v-for="(item2, idx2) in cateList[cateIndex]['childList']" :key="idx2">
							<view class="cate-2-title">{{ item2['name'] }}</view>
							<view class="cate-3-list">
								<view class="cate-3-item" v-for="(item3, idx3) in item2['childList']" :key="idx3"
									@click="knowMore(item3.id)">
									<image :src="item3.main_photo" mode=""></image>
									<view class="cate-3-name">{{ item3.name }}</view>
								</view>
							</view>
						</view>
					</template>
					<view class="none-test" v-else>
						暂无实验
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import {
		fetchCateListApi,
		fetchProjectIntroduceApi
	} from '@/api/index.js'
	import MyLoading from "@/components/loading"
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				testList: [],
				usable_heihgt: 0,
				cateList: [],
				cateIndex: 0,
			}
		},
		onLoad() {
			const that = this
			uni.getSystemInfo({
				success(res) {
					// 计算实际header高度
					that.usable_heihgt = res.windowHeight - (res.screenWidth  / 750) * 100
				}
			})
			// 获取分类列表
			fetchCateListApi().then(res => {
				if (res.res) {
					this.cateList = res.obj
					// 遍历所有一级，拿到所有二级
					this.cateList.forEach(item2 => {
						this.testList = [...this.testList, ...item2.childList]
					})

				}
			})
		},
		methods: {
			// 更换分类
			changeCate(idx) {
				if (this.cateIndex === idx) return
				this.cateIndex = idx
			},
			// 了解更多
			knowMore(id) {
				uni.navigateTo({
					url: `/staffB/test_detail/test_detail?id=${id}`
				})
			},
		}
	}
</script>


<style lang="scss" scoped>
	.cover {
		position: fixed;
		z-index: 2;
		height: 100%;
		width: 100%;
	}
	
	.none-test {
		text-align: center;
		color: #B9B9B9;
		margin-top: 30rpx;
	}
	
	.cate-1-item-active {
		position: relative;
		background-color: #fff !important;

		&::before {
			display: block;
			position: absolute;
			left: 0;
			top: 50%;
			margin-top: -20rpx;
			content: "";
			width: 7rpx;
			height: 40rpx;
			background-color: $primary;
		}
	}

	.cate-list {
		display: flex;
	}

	.cate-1-list,
	.cate-2-list {
		overflow: scroll;
	}

	.cate-1-list {
		background-color: #F8F8F8;
		width: 28%;
	}

	.cate-2-list {
		width: 72%;

		.cate-2-item {
			text-align: center;

			.cate-2-title {
				display: inline-block;
				position: relative;
				margin: 20rpx 0;

				&::before,
				&::after {
					display: block;
					content: '';
					width: 40rpx;
					height: 3rpx;
					background-color: #C7C7C7;
					top: 50%;
					margin-top: -1.5rpx;
				}

				&::before {
					position: absolute;
					left: -50rpx;
				}

				&::after {
					position: absolute;
					right: -50rpx;
				}
			}
		}

		.cate-3-list {
			display: flex;
			flex-wrap: wrap;

			image {
				width: 80rpx;
				height: 80rpx;
				border-radius: 10%;
			}
		}

		.cate-3-item {
			width: 50%;
			text-align: center;

			.cate-3-name {
				width: 180rpx;
				margin: 10px auto;
				overflow: hidden;
				text-overflow: ellipsis;
				display: -webkit-box;
				-webkit-box-orient: vertical;
				-webkit-line-clamp: 2;
				
			}

			&:nth-child(n+3) {
				margin-top: 20rpx;
			}
		}
	}

	.cate-1-item {
		display: flex;
		height: 120rpx;
		background-color: #F5F5F9;
		padding: 0 10rpx;
		align-items: center;

		.cate-2-name {
			overflow: hidden;
			text-overflow: ellipsis;
			display: -webkit-box;
			-webkit-box-orient: vertical;
			-webkit-line-clamp: 2;
		}
	}


	.cate-list {
		background-color: #fff;
	}

	.header {
		display: flex;
		align-items: center;
		height: 100rpx;
		border-bottom: 1rpx solid #F3F3F3;
		padding: 0 30rpx;

		.search-icon {
			position: absolute;
			left: 20rpx;
			top: 15rpx;
			width: 30rpx;
			height: 30rpx;
		}

		.cate {
			width: 40rpx;
			height: 40rpx;
			margin-left: 10px;
		}

		.search-input {
			box-sizing: border-box;
			height: 60rpx;
			padding: 0 70rpx;
			background-color: #fff;
			border-radius: 3rpx;
		}
	}

</style>
<style>
	page {
		background-color: #EFF6FF;
	}
</style>