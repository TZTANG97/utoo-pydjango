<template>
	<view class="content">
		<scroll-view scroll-y class="scrollY" @scrolltolower="onreachBottom">
			<view class="search-box">
				<u-icon color="#95989E" class="search-icon" name="search" size="28"></u-icon>
				<input maxlength="20" confirm-type="search" class="my-search-input" type="text" v-model="goodsName"
							 placeholder="请输入产品名称" />
			</view>
			<view class="wrap">
				<view class="wrap-item" v-if="item.totalnum" v-for="(item, index) in dataList" :key="index"
							@click="itemdetailFn(item)">
					<u-image :src="item.imgurl" :lazy-load="true" width="178" height="170" mode="aspectFit">
						<u-loading slot="loading"></u-loading>
						<view slot="error" style="font-size: 24rpx;">加载失败</view>
					</u-image>
					<view>
						<view class="item-title">{{ item.goods_name  }}</view>
						<view class="item-model alineellipsis">型号: {{ item.goods_spec }}</view>
						<view class="item-model">品牌: {{ item.goods_brand_name }}</view>
						<view v-if="userInfo.userId">
							<!--          h类    public账号,外部账号, 外部合作公司登录能显示库存数量-->
							<view
									v-if="!roleType || roleType == userList['H_USER']['roleName'] || roleType == userList['PUBLIC']['roleName'] || roleType == userList['OUT_COOPERATE_COMPANY']['roleName'] || roleType == userList['OUT_COMPANY']['roleName']">
								<view class="item-stock" v-if="userInfo.userId">
									库存:
									<block v-if="!isNaN(item.nums)">{{ item.nums }} / {{ item.totalnum }}</block>
									<block v-else>--</block>
								</view>
							</view>
							<view v-else>
								<view class="item-model">租赁参考价: {{ item.zlckj? item.zlckj : '待添加'}}</view>
								<view class="item-model">销售参考价: {{ item.xsckj? item.xsckj : '待添加' }}</view>
								<view class="item-stock">
									库存:
									<block v-if="!isNaN(item.nums)">{{ item.nums }} / {{ item.totalnum }}</block>
									<block v-else>--</block>
									<text style="margin-left: 20rpx;"
												v-if="item.quantityInTransit && item.quantityInTransit">在途:{{ item.quantityInTransit }}</text>
								</view>
							</view>
						</view>
						<view v-else>
							<view class="item-stock">
								库存:
								<block v-if="!isNaN(item.nums)">{{ item.nums }} / {{ item.totalnum }}</block>
								<block v-else>--</block>
							</view>
						</view>
					</view>

				</view>
			</view>
			<my-loading :loading="loading" :isRefresh="isRefresh" :total="dataList.length"></my-loading>
		</scroll-view>
	</view>
</template>

<script>
import {
	debounce
} from '@/utils/commonFuncs.js';
import {
	fetchDeviceListApi
} from "@/api/index.js";
import MyLoading from '@/components/loading.vue'
export default {
	components: {
		MyLoading
	},
	data() {
		return {
			userInfo: {},
			gc_id: '',
			page: 1,
			dataList: [],
			goodsName: '',
			store_id: 0,
			list: [],
			isRefresh: true,
			loading: false,
			lang:'',
			url: 'https://qgongye.oss-cn-shanghai.aliyuncs.com/',
			roleType: '',
			userList: {},
			level: 1
		};
	},
	onLoad(options) {
		const {
			store_id = 0,
			gc_id = '',
			level
		} = options
		this.gc_id = gc_id;
		this.store_id = store_id;
		this.level = level || 1;
		this.userInfo = uni.getStorageSync('userInfo');
		this.roleType = this.userInfo.roleName;
		this.userList = uni.getStorageSync('userList') || {}
		this.dataList = []
		this.getappindex();
	},
	watch: {
		goodsName: debounce(function() {
			this.dataList = [];
			this.page = 1;
			this.isRefresh = true
			this.getappindex();
		}, 600)
	},
	methods: {

		// 页面列表
		getappindex() {
			this.loading = true
			fetchDeviceListApi({
				gc_id: this.gc_id,
				currentPage: this.page,
				goodsName: this.goodsName,
				level: this.level,
				store_id: this.store_id,
				en:this.lang==='en'?1:0,
				type: 1
			}).then(res => {
				if (res.data.length != 10) {
					this.isRefresh = false
				}

				res.data.forEach(item => {
					if (item.path) {
						if (item.path.search(this.url) != -1) {
							item.imgurl = this.url + '/upload/order/' + item.name;
						} else {
							item.imgurl = this.url + '/' + item.path + '/' + item.name;
						}
					}
					this.dataList.push(item);
				});
			}).finally(_ => {
				this.loading = false
			})
		},
		// 监听页面滚动到底部
		onreachBottom() {
			console.log(111)
			if (this.isRefresh && !this.loading) {
				this.page++;
				this.getappindex();
			}
		},
		// 查看详情
		itemdetailFn(item) {
			let {
				goods_id,
				nums,
				totalnum,
				goodType,
				goods_spec,
				zlckj,
				xsckj
			} = item
			uni.navigateTo({
				url: `/staffB/onlineClass/detail?id=${goods_id}&gc_id=${this.gc_id}&nums=${nums}&totalnum=${totalnum}&goodType=${goodType}&spec=${goods_spec}&zlckj=${zlckj ? zlckj : ''}&xsckj=${xsckj? xsckj : ''}&storeId=${this.store_id}`
			})
		}
	}
};
</script>

<style lang="scss" scoped>
.content {
	height: 100%;
	overflow: auto;
	padding: 0;
}

.search-box {
	margin: 30rpx 30rpx 0;
	.my-search-input {
		background-color: #fff;
	}
}

.scrollY {
	width: 100%;
	height: 100vh;
}

.wrap {
	padding-top: 24rpx;

	.wrap-item {
		display: flex;
		justify-content: flex-start;
		flex-wrap: wrap;
		padding: 30rpx 22rpx;
		background: #ffffff;
		margin-bottom: 24rpx;
		border-radius: 20rpx;

		>view {
			padding-left: 28rpx;

			.item-title {
				width: 440rpx;
				font-size: 28rpx;
				color: #333333;
				font-weight: bold;
				margin-bottom: 20rpx;
				display: -webkit-box;
				-webkit-box-orient: vertical;
				-webkit-line-clamp: 2;
				overflow: hidden;
			}

			.item-model {
				width: 440rpx;
				font-size: 24rpx;
				color: #333333;
				opacity: 0.7;
				margin-bottom: 14rpx;
			}

			.item-stock {
				font-size: 22rpx;
				opacity: 0.3;
				margin-bottom: 14rpx;

				text {
					color: #333;
				}
			}
		}
	}
}
</style>
