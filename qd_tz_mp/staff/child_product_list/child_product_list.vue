<template>
	<view class="container">
		<view class="list" v-if="type == 6">
			<view class="item" v-for="(item, index) in list" :key="index">
				<view class="item-row">
				</view>
				<view class="item-row">
					<text>子订单编号：{{ item['order_id'] }}</text>
				</view>
				<view class="item-row">
					<text>产品名称：{{ item['goods_name'] }}</text>
				</view>
				<view class="item-row" v-if="item['goods_spec']">
					<text>产品型号：{{ item['goods_spec'] }}</text>
				</view>
				<view class="item-row">
					<text>产品品牌：{{ item['goods_brand_name'] }}</text>
				</view>
				<view class="item-row">
					<text>数量：{{ item['goods_nums'] }}</text>
				</view>
				<view class="item-row">
					<text>设备名称：{{ item['experiment_project_name'] }}</text>
				</view>
				<view class="item-row">
					<text>实验测试分类：{{ item['experiment_class_name'] }}</text>
				</view>
				<view class="item-row">
					<text>测试人员：{{ item.test_user_id == 22 ? '抢单' : item['testUser'] ? item['testUser'] : '' }}</text>
				</view>
				<view class="item-row">
					<text>实验平台：{{ item['line_num'] }}</text>
				</view>
				<view class="item-row">
					<text>状态：{{ item['orderStautsStr'] }}</text>
				</view>
				<view class="item-row">
					<text>预计完成时间：{{ item['finish_time']? item['finish_time'] : '0' }}{{ item['time_type'] === 1? '小时' : item['time_type'] === 3 ? '分钟': '天' }}</text>
				</view>
				<view class="item-row">
					<text>实际完成时间：{{ item['sjsj']? item['sjsj'] : '0'}}{{ getShowUnit(item['time_type']) }}</text>
				</view>
				<view class="item-row" v-if="item['sample_store_name']">
					<text>仓库位置：{{ item['sample_store_name'] }}</text>
				</view>
				<view class="item-row" v-if="item['out_num']">
					<text>样品管理单：{{ item['out_num'] }}</text>
				</view>
				<view class="item-row" v-if="item['retestApplication']">
					<text>关联复测编号：{{ item['retestApplication'] ? item['retestApplication'].order_id : '' }}</text>
				</view>
			</view>
		</view>

		<view class="list" v-else>
			<view class="item" v-for="(item, index) in list" :key="index">
				<view class="item-row">
				</view>
				<view class="item-row">
					<text>子订单编号：{{ item['orderId'] }}</text>
				</view>
				<view class="item-row">
					<text>产品名称：{{ item['goodsName'] }}</text>
				</view>
				<view class="item-row" v-if="item['goodsSpec']">
					<text>产品型号：{{ item['goodsSpec'] }}</text>
				</view>
				<view class="item-row">
					<text>产品品牌：{{ item['goodsBrandName'] }}</text>
				</view>
				<view class="item-row">
					<text>数量：{{ item['goodsNums'] }}</text>
				</view>
				<view class="item-row">
					<text>设备名称：{{ item['experiment_project_name'] }}</text>
				</view>
        <view class="item-row">
          <text>测试人员：{{ item['testUser'] }}</text>
        </view>
				<view v-if="isFlag" class="item-row">
					<text>分包单价：{{ item['pcost_price']?item['pcost_price'].toFixed(2) : '0.00' }}</text>
				</view>
				<view class="item-row">
					<text>状态：{{ status_list[item['orderStatus']] }}</text>
				</view>
				<view class="item-row">
					<text>预计完成时间：{{ item['finish_time']? item['finish_time'] : '0' }}{{ item['time_type'] === 1? '小时' : item['time_type'] === 3 ? '分钟': '天' }}</text>
				</view>
				<view class="item-row">
					<text>实际完成时间：{{ item['sjsj']? item['sjsj'] : '0'}}{{ item['time_type'] === 1? '小时' : item['time_type'] === 3 ? '分钟': '天' }}</text>
				</view>
				<view class="item-row" v-if="item['sample_store_name']">
					<text>仓库位置：{{ item['sample_store_name'] }}</text>
				</view>
				<view class="item-row" v-if="item['out_num']">
					<text>样品管理单：{{ item['out_num'] }}</text>
				</view>
				<view class="item-row" v-if="item['retestApplication']">
					<text>关联复测编号：{{ item['retestApplication'] ? item['retestApplication'].order_id : '' }}</text>
				</view>
			</view>
		</view>

		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import {
		fetchTestChildOrderDetailApi,
		fetchCheckPendingTestSubChildOrderDetailApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
        isFlag:false,
				id: '',
				type: '',
				list: [],
				status_list: {
					0: "已取消",
					1: "待处理",
					2: "已处理",
					3: "已驳回",
					10: "生产中",
					20: "运输中",
					30: "已签收",
					40: "已验收",
					36: "样品入库",
					37: "样品领用",
					38: "测试中",
					39: "测试完成",
					41: "样品归还",
					42: "样品寄回",
					43: "样品留存",
					44: "样品报废",
					50: "已完成"
				},
			};
		},
		onLoad({
			id = '',
			type = '6'
		}) {
			this.id = id
			this.type = type
			this.getDetail()
		},
		methods: {
			// 下载
			downloadFile(path) {
				const that = this
				uni.setClipboardData({
					data: path,
					success() {
						that.$toast('链接已复制，请打开浏览器下载！');
					}
				});
			},

			getShowUnit(type) {
				if(type == 1) {
					return '小时'
				}
				if(type ==2) {
					return '天'
				}
				if(type == 3) {
					return '分钟'
				}
				return '分钟'
			},

			getDetail() {
				this.loading = true
				let request;
				// 实验订单详情
				if (this.type == 6) {
					request = fetchTestChildOrderDetailApi({
						id: this.id
					})
				} else {
					// 实验分包详情
					request = fetchCheckPendingTestSubChildOrderDetailApi({
						id: this.id
					})
				}
				request.then(res => {
					if (!res.error) {
						this.list = res.obj.childs
            if (this.type != 6) {
              this.isFlag = res.obj.isFlag
            }
					} else {
						this.$toast(res.error)
					}
				}).finally(() => {
					this.loading = false
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
	.file {
		color: $primary;
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

	.loading {
		text-align: center;
		color: #999;
		margin: 20rpx 0;
	}

	.container {
		padding: 0 25rpx;
	}
</style>
<style>
	page {
		background-color: #f2f2f2;
	}
</style>
