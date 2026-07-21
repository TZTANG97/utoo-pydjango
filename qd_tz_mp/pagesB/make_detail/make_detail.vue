<template>
	<view class="container">
		<view class="group" v-if="detail">
			<view class="group-item" v-if="detail.order_id">
				<view class="group-label">
					订单编号
				</view>
				<!--  @click="viewDetail" -->
				<view class="group-content">
					<view class="text-content">
						{{ detail['order_num'] }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					实验分类
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail['className'] }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					姓名
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail['userName'] }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					手机号
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail['mobile'] }}
					</view>
				</view>
			</view>
			<!-- 			<view class="group-item">
				<view class="group-label">
					公司名称
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail['company_name'] }}
					</view>
				</view>
			</view> -->
			<view class="group-item">
				<view class="group-label">
					客服人员
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail['syUserName'] }}
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					样品是否回收
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail.reverso_context }}
					</view>
				</view>
			</view>
			<template v-if="detail.reverso_context">
				<view class="group-item">
					<view class="group-label">
						收件人姓名
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ detail.addressee_name }}
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						收件人电话
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ detail.addressee_mobile }}
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						云视频
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ detail.is_video? '是' : '否' }}
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						是否线下到场
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ detail.is_arrive == 1 ? '是' : '否' }}
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						是否我要上机
					</view>
					<view class="group-content">
						<view class="text-content">
							{{ detail.is_on == '1' ? '是' : '否' }}
						</view>
					</view>
				</view>
			</template>
			<view class="group-item">
				<view class="group-label">
					样品收件地址
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail['send_address']? detail['send_address'] : '' }}
					</view>
				</view>
			</view>
			<view class="group-item test-need" v-if="detail['content']">
				<view class="group-label">
					实验需求
				</view>
				<view class="group-content">
					<view class="text-content">
						{{ detail['content'] }}
					</view>
				</view>
			</view>
		</view>
		<view class="tableBox" v-if="ypList.length > 0">
			<view class="tableTr">
				<view>样品数量</view>
				<view>样品名称/类型</view>
				<view>主要成分</view>
				<view v-for="(item,index) in nameList" :key="index">
					{{item}}
				</view>
				<view>是否含磁</view>
				<view>是否喷金</view>
			</view>
			<view class="tableTd" v-for="item,index in ypList" :key="item.id">
				<view class='tableTdView'>{{item.sample_num}}</view>
				<view class='tableTdView'>{{item.sample_name}}</view>
				<view class='tableTdView'>{{item.main_component}}</view>
				<view class='tableTdView' v-for="(sub,subInd) in subList" v-if="sub.index == index" :key="subInd">
					{{ sub.sttribute_name }}
				</view>
				<view class='tableTdView'>{{item.is_magnetic == 0 ? '是' : '否'}}</view>
				<view class='tableTdView'><text>{{item.is_gold_spraying == 0 ? '是' : '否'}}<text v-if="item.gold_desc && item.is_gold_spraying == 1">({{item.gold_desc}})</text></text></view>

			</view>

		</view>

		<view class="btns">
			<view class="btn" v-if="detail.is_cancel" @click="cancelSub">
				取消预约
			</view>
		</view>

		<view class="group" style="margin: 30rpx 20rpx 0;" v-for="(item, index) in childs" :key="index">
			<view class="group-hint">
				产品信息
			</view>
			<view class="group-item">
				<view class="group-label">
					产品名称
				</view>
				<view class="group-content">
					{{ item.goods_name }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品型号
				</view>
				<view class="group-content">
					{{ item.goods_spec }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					产品品牌
				</view>
				<view class="group-content">
					{{ item.goods_brand_name }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					数量
				</view>
				<view class="group-content">
					{{ item.goods_nums }}台
				</view>
			</view>
			<view class="group-item" v-if="item.experiment_project_name">
				<view class="group-label">
					实验项目
				</view>
				<view class="group-content">
					{{ item.experiment_project_name }}
				</view>
			</view>
			<view class="group-item" v-if="item.experiment_class_name">
				<view class="group-label">
					实验分类
				</view>
				<view class="group-content">
					{{ item.experiment_class_name }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					实际金额
				</view>
				<view class="group-content">
					{{ item.goods_price? item.goods_price.toFixed(2) : 0.00 }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					标准金额
				</view>
				<view class="group-content">
					{{ item.reference_price? item.reference_price.toFixed(2) : 0.00 }}
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					总价
				</view>
				<view class="group-content">
					{{ item.goods_price? (item.goods_price * item.goods_nums).toFixed(2) : '0.00' }}
				</view>
			</view>
		</view>

	</view>
</template>

<script>
	import {
		fetchSubOrderDetailApi,
		cancelConsultApi
	} from '@/api/index'
	export default {
		data() {
			return {
				id: '',
				detail: null,
				childs: [],
				ypList: [],
				nameList: [],
				subList: []
			};
		},
		onLoad({
			id
		}) {
			if (id) {
				this.id = id
				fetchSubOrderDetailApi({
					id: this.id
				}).then(res => {
					if (res.res) {
						let arr = []
						let list = []
						this.childs = res.obj.childs
						delete res.obj.childs
						this.detail = res.obj
						this.ypList = res.obj.ypList
						// 处理样品详情数据
						res.obj.ypList.forEach((item, index) => {
							list.push({
								index: index,
								data: item.sampleAttributeManageList,
							});
							item.sampleAttributeManageList.forEach(a => {
								arr.push(a.sttribute_name)
							})

						});
						this.nameList = Array.from(new Set(arr))
						for (let i = 0; i < list.length; i++) {
							for (let j = 0; j < list[i].data.length; j++) {
								this.subList.push({
									index: list[i].index,
									name: list[i].data[j].sttribute_name,
									data: list[i].data[j].attributeListsanji,
								})
							}
						}
						for (let i = 0; i < this.subList.length; i++) {
							this.subList[i].sttribute_name = ''
							for (let j = 0; j < this.subList[i].data.length; j++) {
								this.subList[i].sttribute_name += this.subList[i].data[j].sttribute_name + '，'
							}
							if (this.subList[i].sttribute_name.endsWith('，')) {
								this.subList[i].sttribute_name = this.subList[i].sttribute_name.slice(0, -1);
							}
						}
					} else {
						this.$toast(res.resMsg)
					}
				})
			}
		},
		methods: {
			cancelSub() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定取消预约吗？',
					success({
						confirm
					}) {
						if (confirm) {
							cancelConsultApi(that.id).then(res => {
								that.$toast(res.resMsg)
								if (res.res) {
									that.detail.is_cancel = 0
									that.detail.status = 3
								}
							})
						}
					}
				})
			},


			viewDetail() {
				const {
					order_id,
					order_type,
					order_status
				} = this.detail
				if (order_status >= 30) {
					if (order_type == 6) {
						uni.navigateTo({
							url: '/test/test_order_detail/test_order_detail?id=' + order_id
						})
					} else if (order_type == 8) {
						uni.navigateTo({
							url: '/test/subpackage_detail/subpackage_detail?id=' + order_id
						})
					}
				} else {
					this.$toast(!order_status ? '订单已取消' : '订单未审核')
				}
			}
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/group.scss';


	.btns {
		display: flex;
		flex-direction: row-reverse;
		flex-wrap: wrap;
		padding-bottom: 20rpx;

		.btn {
			height: 70rpx;
			border-radius: 40rpx;
			text-align: center;
			line-height: 70rpx;
			padding: 0 40rpx;
			background-color: $primary;
			color: #fff;
			margin: 20rpx;
		}
	}

	.test-need {
		display: block !important;

		.group-content {
			align-items: normal;
			padding: 10rpx;
			box-sizing: border-box;
			height: 300rpx;
			overflow-y: scroll;
			border: 1rpx solid #CECECE;
			border-radius: 7rpx;
			margin-top: 15rpx;
		}
	}

	.tableBox {
		overflow-x: auto;
		margin-top: 10rpx;

		.tableTr {
			width: 1400rpx;
			display: flex;
			background-color: #CECECE;
			padding: 10rpx 10rpx 12rpx;

			view {
				width: 200rpx;
				text-align: center;
				padding: 12rpx 0;
			}
		}

		.tableTd {
			width: 1400rpx;
			display: flex;

			.tableTdView {
				display: flex;
				align-items: center;
				justify-content: center;
				width: 200rpx;
				word-break: break-all;
				padding: 12rpx 0;
				border-left: 1px #ccc solid;
				border-bottom: 1px #ccc solid;
			}

			.tableTdOther {
				width: 200rpx;
				text-align: center;
				padding: 12rpx 0;
				border-left: 1px #ccc solid;
				border-bottom: 1px #ccc solid;
			}
		}
	}
</style>
