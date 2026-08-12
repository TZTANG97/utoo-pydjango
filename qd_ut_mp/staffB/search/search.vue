<template>
	<view class="container">
		<div class="header" :style="{ 'borderBottom': start_search? '1rpx solid #F8F8F8' : '' }">
			<input @focus="clearList" @confirm="startSearch" v-model="key_word" type="text" placeholder="请输入设备名称"
				maxlength="20">
			<image class="search-icon" src="@/static/search.png" mode=""></image>
			<image v-if="key_word" @click="key_word = '', clearList()" class="clear-icon" src="../static/clear.png"
				mode=""></image>
		</div>


		<template v-if="start_search">
			<view class="test-list">
				<navigator :url="`/staffB/test_detail/test_detail?id=${item['id']}`" hover-class="none" class="test-item"
					v-for="(item, idx) in list" :key="idx">
					<image :src="item['main_photo']" mode=""></image>
					<view class="test-name">
						{{ item['name'] }}
					</view>
					<!-- <text>{{ item['test_price'] }}</text> -->
					<!-- <view class="other">
						<view class="price">
							<text class="money-logo">￥</text>
							<text>--</text>
						</view>
						<text class="buied">{{ item['count'] }}人已下单</text>
					</view> -->
				</navigator>
			</view>
			<my-loading :loading="loading" :isRefresh="isRefresh" :total="list.length"></my-loading>
		</template>

		<template v-else>
			<view class="hot-saerch-title">
				热门搜索
			</view>
			<view class="recommend-list">
				<!--  v-for="item in 10" :key="item" -->
				<view class="recommend-item" @click="key_word = '测试', startSearch()">
					测试
				</view>
			</view>

			<view class="search-his" v-if="his_list.length">
				<text>历史搜索</text>
				<image @click="clearHis" src="../static/delete_his.png" mode=""></image>
			</view>
			<view class="his-list" v-if="his_list.length">
				<view class="his-item" v-for="(item, idx) in his_list" :key="idx"
					@click="key_word = item, startSearch()">
					{{ item }}
				</view>
			</view>
		</template>
	</view>
</template>

<script>
	import {
		seatchTestApi
	} from '@/api/index'
	import MyLoading from "@/components/loading.vue"
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				// 是否点击率了搜索
				start_search: false,
				key_word: '',
				page: 1,
				list: [],
				his_list: [],
				isRefresh: true,
				loading: false
			}
		},

		onLoad() {
			let hist = uni.getStorageSync('his');
			if (hist.length) {
				this.his_list = hist
			}
		},

		onReachBottom() {
			if (this.isRefresh) {
				this.page++;
				this.getList()
			}
		},
		onUnload() {
			if (this.his_list.length) {
				uni.setStorageSync('his', this.his_list)
			}
		},
		methods: {

			// 聚焦清空列表
			clearList() {
				this.list = []
				this.start_search = false
				this.isRefresh = true
				this.page = 1
			},

			// 按下键盘的搜索B
			startSearch() {
				if (this.key_word === 'config') return uni.redirectTo({
					url: '/pagesB/config/config'
				})

				if (!this.key_word) return

				this.his_list.forEach((item, idx) => {
					if (item === this.key_word) {
						this.his_list.splice(idx, 1)
					}
				})

				if (this.his_list.length === 10) {
					this.his_list.splice(9, 1)
				}

				this.his_list.unshift(this.key_word)

				this.start_search = true
				this.getList()
			},

			// 获取列表
			getList() {
				this.loading = true
				seatchTestApi({
					draw: 1,
					start: (this.page - 1) * 10,
					length: 10,
					keyWord: this.key_word
				}).then(res => {
					if (res.res) {
						if (res.obj.data) {
							if (res.obj.data.length !== 10) {
								this.isRefresh = false
							}
							this.list = [...this.list, ...res.obj.data]
						}
					} else {
						this.$toast(res.resMsg)
					}
				}).finally(_ => {
					this.loading = false
				})
			},

			// 删除历史记录
			clearHis() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '清空历史记录？',
					success({
						confirm
					}) {
						if (confirm) {
							that.his_list = []
						}
					}
				})
			},
		}
	}
</script>
<style lang="scss" scoped>
	.test-list {
		display: flex;
		flex-wrap: wrap;
		margin-top: 100rpx;

		.test-item {
			width: 50%;
			box-sizing: border-box;
			padding: 20rpx 20rpx;
			border-bottom: 1rpx solid #F5F5F5;

			&:nth-child(2n-1) {
				border-right: 1rpx solid #F5F5F5;
			}

			image {
				width: 100%;
				height: 300rpx;
			}

			.test-name {
				overflow: hidden;
				text-overflow: ellipsis;
				display: -webkit-box;
				-webkit-line-clamp: 2;
				-webkit-box-orient: vertical;
				line-height: 1.5;
			}

			.other {
				display: flex;
				justify-content: space-between;
				align-items: flex-end;
				margin: 15rpx 0 25rpx 0;

				.price {
					.money-logo {
						font-size: 25rpx;
						vertical-align: bottom;
					}

					text:nth-child(2) {
						font-weight: bold;
						font-size: 35rpx;
					}
				}

				.buied {
					font-size: 25rpx;
					color: #AAAAAA;
				}
			}
		}
	}

	.hot-saerch-title {
		margin-top: 125rpx;
		font-size: 30rpx;
	}

	.search-his {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 35rpx;
		font-size: 30rpx;

		image {
			width: 45rpx;
			height: 45rpx;
		}
	}

	.recommend-list,
	.his-list {
		display: flex;
		flex-wrap: wrap;
		color: #555862;

		.recommend-item,
		.his-item {
			padding: 10rpx 30rpx;
			background-color: #F5F5F9;
			margin: 25rpx 25rpx 0 0;
			border-radius: 3rpx;
		}
	}

	.header {
		position: fixed;
		left: 0;
		top: 0;
		width: 100%;
		height: 100rpx;
		padding: 0 30rpx;
		overflow: hidden;
		background-color: #fff;

		input {
			height: 60rpx;
			margin-top: 20rpx;
			background-color: #EEEEF3;
			padding: 0 70rpx;
			border-radius: 3rpx;
		}

		image {
			position: absolute;
			top: 35rpx;
			width: 30rpx;
			height: 30rpx;
		}

		.clear-icon {
			right: 50rpx;
		}

		.search-icon {
			left: 50rpx;
		}
	}

	.container {
		padding: 0 30rpx;
	}
</style>