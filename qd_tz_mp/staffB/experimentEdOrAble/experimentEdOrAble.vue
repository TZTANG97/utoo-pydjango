<template>
	<view class="container">
		<view class="search-header syxStyle" v-if="searchShow">
			<input type="text" @input="inputFn" v-model="customer_name" placeholder="客户企业名称" maxlength="30">
			<input type="text" @input="inputFn" v-model="order_id" placeholder="订单编号" maxlength="30">
			<input type="text" @input="inputFn" v-model="order_startime" @click="isStartFn(1)" placeholder="下单开始时间">
			<input type="text" @input="inputFn" v-model="order_endtime" @click="isStartFn(2)" placeholder="下单结束时间">
			<input type="text" @input="inputFn" @click="showFn(false)" disabled v-model="supplier_name"
				placeholder="全部所属公司">
			<view style="display: flex;justify-content: space-around;width: 50%;">
				<view class="btn" @click="searchFn(1)">
					搜索
				</view>
				<view class="btn" @click="searchFn(2)">
					重置
				</view>
			</view>
		</view>
		<view class="syxIcon" v-else @click="searchShow = true">
			<u-icon name="arrow-down"></u-icon>
		</view>
		<view class="dataList">
			<view class="item" v-for="item,index in dataList" :key="index"
				@click="viewDetail(item.id, item.isOut,item)">
				<view class="item-row">
					<text>订单编号：{{ item.order_id }}</text>
				</view>
				<view class="item-row" v-if="type == 8">
					<text>来源订单：{{ item.parentOf.order_id }}</text>
				</view>
				<view class="item-row" v-if="item.company.name">
					<text>客户企业名称：{{ item.company.name }}</text>
				</view>
				<view class="item-row" v-if="type != 8">
					<text>所属公司名称：{{ item.supplierUser.company_name }}</text>
				</view>
				<view class="item-row" v-else>
					<text>进货公司名称：{{ item.stock_company_name }}</text>
				</view>
				<view class="item-row">
					<text>销售主管：{{ item.saleManagerUser.userName }}</text>
				</view>
				<view class="item-row" v-if="type != 8">
					<text>销售人员：{{ item.saleUser.userName }}</text>
				</view>
				<view class="item-row" v-else>
					<text>采购人员：{{ item.saleUser.userName ? item.saleUser.userName : '' }}</text>
				</view>
				<view class="item-row">
					<text>订单总价：{{ item.totalPrice.toFixed(2) }}</text>
				</view>
				<view class="item-row">
					<text>是否开票：{{ item.invoiceType === 1? '是' : '否' }}</text>
				</view>
				<view class="item-row">
					<text>下单时间：{{ item.delivery_time? $alterTime(item.delivery_time, false): '' }}</text>
				</view>
				<view class="item-row" v-if="type != 8">
					<text>录入时间：{{ item.addTime? $alterTime(item.addTime, false) : '' }}</text>
				</view>
				<view class="item-row">
					<text>订单状态：{{ ORDER_STATUS[item.order_status] }}</text>
				</view>
			</view>
		</view>
		<u-select v-if="show" v-model="show" @confirm="confirm" :list="list"></u-select>
		<u-picker v-model="dateShow" mode="time" @confirm="dateConfirm" :params="params"></u-picker>
		<my-loading :loading="isLoading" :isRefresh="isRefresh" :total="dataList.length"></my-loading>
	</view>
</template>

<script>
	import {
		expListxcx,
		expSubListxcx,
		supplierQueryAll,
		saleListxcx,
		expList,
		expListxcx2,
		expListxcx3,
		expListxcx4,
		expListxcx5,
		salePayListxcx
	} from '@/api/staffB.js'
	import {
		ORDER_STATUS,
	} from '@/constant/status.js'
	import MyLoading from "@/components/loading.vue"
	export default {
		components: {
			MyLoading
		},
		data() {
			return {
				type: null,
				show: false,
				list: [],
				customer_name: '',
				company_id: '',
				order_id: '',
				order_startime: '',
				order_endtime: '',
				supplier_name: '',
				searchShow: false,
				dataList: [],
				ORDER_STATUS,
				supplier_id: '',
				params: {
					year: true,
					month: true,
					day: true,
					hour: false,
					minute: false,
					second: false
				},
				dateShow: false,
				isStart: true,
				isRefresh: true,
				isLoading: false,
				page: 1,
				showType: false,
				date: '',
				userInfo: {},
				oldObj: {},
				test_type: ''
			}
		},
		created() {
			supplierQueryAll().then(res => {
				let arr = []
				res.obj.forEach(item => {
					arr.push({
						value: item.id,
						label: item.company_name
					})
				})
				this.list = arr
			})

		},
		onLoad(data) {
			this.oldObj = JSON.parse(JSON.stringify(data))
			this.userInfo = uni.getStorageSync('userInfo');
			console.log(this.userInfo, 'userInfo')
			if (data.type) this.type = data.type
			if (data.name != 'null') {
				this.customer_name = data.name
			} else {
				this.oldObj.name = ''
			}
			if (data.id != 'null') {
				this.company_id = data.id
			} else {
				this.oldObj.id = ''
			}
			if (data.date) this.date = data.date
			if (data.test_type) this.test_type = data.test_type
			let title = ''
			if (this.type == 1) {
				title = '实验订单金额'
				this.expListFn(1, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
					this
					.order_endtime, this
					.supplier_id, this.customer_name, this.test_type)
			}
			if (this.type == 2) {
				title = '实验分包订单金额'
				this.expListFn(2, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
					this
					.order_endtime, this
					.supplier_id, this.customer_name, this.test_type)
			}
			if (this.type == 3) {
				title = '实验已收'
				this.expListxcxFn(1, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime, this
					.order_endtime, this.supplier_id, this.customer_name)
			}
			if (this.type == 4) {
				title = '实验应收'
				this.expListxcxFn(2, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime, this
					.order_endtime, this.supplier_id, this.customer_name)
			}
			if (this.type == 5) {
				title = '实验分包已收'
				this.expSubListxcxFn(1, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime, this
					.order_endtime, this
					.supplier_id, this.customer_name)
			}
			if (this.type == 6) {
				title = '实验分包应收'
				this.expSubListxcxFn(2, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime, this
					.order_endtime, this
					.supplier_id, this.customer_name)
			}
			let num = 1
			if (this.type == 7) {
				title = '个人实验应收款'
				num = 4
			}
			if (this.type == 8) {
				title = '个人实验分包应付款'
				num = 4
			}
			if (this.type == 9) {
				title = '个人实验分包应收款'
				num = 5
			}
			if (this.type == 7 || this.type == 9) {
				this.list = []
				this.saleListxcxFn(num, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime, this
					.order_endtime, this
					.supplier_id, this.customer_name)
				// const data = uni.getStorageSync('overdueAryrmbsy')
				// data.forEach(item => {
				// 	this.list.push({
				// 		value: item.company_id,
				// 		label: item.company_name
				// 	})
				// })
			}
			if (this.type == 8) {
				this.salePayListxcxFn(num, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime,
					this.order_endtime, this.supplier_id, this.customer_name)
			}
			if (this.type == 10) {
				title = `个人实验总额${this.date}`
				this.expListFn(3, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
					this
					.order_endtime, this
					.supplier_id, this.customer_name)
			}
			if (this.type == 11) {
				title = `个人实验分包总额${this.date}`
				this.expListFn(4, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
					this
					.order_endtime, this
					.supplier_id, this.customer_name)
			}
			uni.setNavigationBarTitle({
				title: title
			})

		},
		onReachBottom() {
			if (this.isRefresh) {
				this.page++;
				let data = 1
				if (this.type == 1) {
					console.log('1111')
					this.expListFn(1, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
						this.order_endtime, this.supplier_id, this.customer_name, this.test_type)
				}
				if (this.type == 2) {
					this.expListFn(2, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
						this.order_endtime, this.supplier_id, this.customer_name, this.test_type)
				}
				if (this.type == 5 || this.type == 3) {
					data = 1
				}
				if (this.type == 6 || this.type == 4) {
					data = 2
				}
				if (this.type == 3 || this.type == 4) {
					this.expListxcxFn(data, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime,
						this.order_endtime, this.supplier_id, this.customer_name)
				}
				if (this.type == 5 || this.type == 6) {
					this.expSubListxcxFn(data, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime,
						this.order_endtime, this.supplier_id, this.customer_name)
				}
				if (this.type == 7) {
					data = 4
				}
				if (this.type == 8) {
					data = 4
				}
				if (this.type == 9) {
					data = 5
				}
				if (this.type == 7 || this.type == 9) {
					this.saleListxcxFn(data, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime,
						this.order_endtime, this.supplier_id, this.customer_name)
				}
				if (this.type == 8) {
					this.salePayListxcxFn(data, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime,
						this.order_endtime, this.supplier_id, this.customer_name)
				}
				if (this.type == 10) {
					this.expListFn(3, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
						this.order_endtime, this.supplier_id, this.customer_name)
				}
				if (this.type == 11) {
					this.expListFn(4, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
						this.order_endtime, this.supplier_id, this.customer_name)
				}

			}
		},
		methods: {
			// 饼图
			salePayListxcxFn(type, start, company_id, order_id, order_startime, order_endtime, supplier_name,
				customer_name) {
				let obj = {
					start: start,
					company_id: company_id,
					order_id: order_id,
					order_startime: order_startime,
					order_endtime: order_endtime,
					supplier_name: supplier_name,
					customer_name: customer_name
				}
				salePayListxcx(obj).then(res => {
					if (res) {
						if (res.obj.data.length !== 10) this.isRefresh = false
						this.dataList = [...this.dataList, ...res.obj.data]
					} else {
						this.$tip(res.error)
					}
				}).finally(() => {
					this.isLoading = false
				})
			},
			// 柱状图
			expListFn(type, start, year, company_id, order_id, order_startime, order_endtime, supplier_name, customer_name,
				test_type) {
				let obj = {
					start: start,
					year: year,
					company_id: company_id,
					order_id: order_id,
					order_startime: order_startime,
					order_endtime: order_endtime,
					supplier_name: supplier_name,
					customer_name: customer_name
				}
				console.log(obj, 'obj111')
				if (type == 1) {
					obj.test_type = test_type
					expListxcx2(obj).then(res => {
						if (res.res) {
							if (res.obj.data.data.length !== 10) this.isRefresh = false
							this.dataList = [...this.dataList, ...res.obj.data.data]
						} else {
							this.$tip(res.error)
						}
					}).finally(() => {
						this.isLoading = false
					})
				} else if (type == 2) {
					obj.test_type = test_type
					expListxcx3(obj).then(res => {
						if (res.res) {
							if (res.obj.data.data.length !== 10) this.isRefresh = false
							this.dataList = [...this.dataList, ...res.obj.data.data]
						} else {
							this.$tip(res.error)
						}
					}).finally(() => {
						this.isLoading = false
					})
				} else if (type == 3) {
					obj.sale_user = this.userInfo.userId
					expListxcx4(obj).then(res => {
						if (res.res) {
							if (res.obj.data.data.length !== 10) this.isRefresh = false
							this.dataList = [...this.dataList, ...res.obj.data.data]
						} else {
							this.$tip(res.error)
						}
					}).finally(() => {
						this.isLoading = false
					})
				} else {
					expListxcx5(obj).then(res => {
						if (res.res) {
							if (res.obj.data.data.length !== 10) this.isRefresh = false
							this.dataList = [...this.dataList, ...res.obj.data.data]
						} else {
							this.$tip(res.error)
						}
					}).finally(() => {
						this.isLoading = false
					})
				}


			},
			saleListxcxFn(type, start, company_id, order_id, order_startime, order_endtime, supplier_name, customer_name) {
				let obj = {
					type: type,
					start: start,
					length: 10,
					drawh: 1,
					company_id: company_id,
					order_id: order_id,
					order_startime: order_startime,
					order_endtime: order_endtime,
					supplier_name: supplier_name,
					customer_name: customer_name
				}
				console.log(obj, 'obj222')
				saleListxcx(obj).then(res => {
					if (res.res) {
						if (res.obj.data.length !== 10) this.isRefresh = false
						this.dataList = [...this.dataList, ...res.obj.data]
					} else {
						this.$tip(res.error)
					}
				}).finally(() => {
					this.isLoading = false
				})
			},
			// 实验
			expListxcxFn(type, start, company_id, order_id, order_startime, order_endtime, supplier_name, customer_name) {
				let obj = {
					type: type,
					start: start,
					length: 10,
					drawh: 1,
					customer_name: customer_name,
					order_id: order_id,
					order_startime: order_startime,
					order_endtime: order_endtime,
					supplier_name: supplier_name,
					company_id: company_id
				}
				console.log(obj, 'obj333')
				expListxcx(obj).then(res => {
					if (res.res) {
						if (res.obj.data.data.length !== 10) this.isRefresh = false
						this.dataList = [...this.dataList, ...res.obj.data.data]
					} else {
						this.$tip(res.error)
					}
				}).finally(() => {
					this.isLoading = false
				})
			},
			// 实验分包
			expSubListxcxFn(type, start, company_id, order_id, order_startime, order_endtime, supplier_name,
				customer_name) {
				let obj = {
					type: type,
					start: start,
					length: 10,
					drawh: 1,
					customer_name: customer_name,
					order_id: order_id,
					order_startime: order_startime,
					order_endtime: order_endtime,
					supplier_name: supplier_name,
					company_id: company_id
				}
				console.log(obj, 'obj444')
				expSubListxcx(obj).then(res => {
					if (res.res) {
						if (res.obj.data.data.length !== 10) this.isRefresh = false
						this.dataList = [...this.dataList, ...res.obj.data.data]
					} else {
						this.$tip(res.error)
					}
				}).finally(() => {
					this.isLoading = false
				})
			},
			// 选择企业
			confirm(val) {
				if (this.showType) {
					this.customer_name = val[0].label
					this.company_id = val[0].value
				} else {
					this.supplier_name = val[0].label
					this.supplier_id = val[0].value
				}

			},
			//跳转页面
			viewDetail(id, isOut, item) {
				console.log(isOut, 'isOut')
				console.log(item.order_type, 'item')
				if (this.userInfo.wx_nickname == 'admin') {
					if (isOut == 2) {
						// 实验订单
						if (this.type == 1 || this.type == 10 || this.type == 3 || this.type == 4 || this.type == 7) {
							uni.navigateTo({
								url: '/staff/order_detail/order_detail?id=' + id
							})
						} else if (this.type == 2 || this.type == 11 || this.type == 5 || this.type == 6 || this.type ==
							9 ||
							this
							.type == 8) {
							// 实验分包订单
							uni.navigateTo({
								url: '/staff/sub_detail/sub_detail?id=' + id
							})
						}
					} else {
						if (this.type == 1 || this.type == 10 || this.type == 3 || this.type == 4 || this.type == 7) {
							uni.navigateTo({
								url: '/staffB/order_detail/order_detail?id=' + id
							})
						}
						if (this.type == 2 || this.type == 11 || this.type == 5 || this.type == 6 || this.type == 9 || this
							.type == 8) {
							uni.navigateTo({
								url: '/staffB/order_detail/order_detail?id=' + id + '&type=' + this.type
							})
						}

					}
				} else {
					if (item.order_type == 6) {
						uni.navigateTo({
							url: '/staff/order_detail/order_detail?id=' + id
						})
					}
					if (item.order_type == 8) {
						uni.navigateTo({
							url: '/staff/sub_detail/sub_detail?id=' + id
						})
					}
				}

				// if (isOut == 2) {
				// 	// 实验订单
				// 	if (this.type == 1 || this.type == 10 || this.type == 3 || this.type == 4 || this.type == 7) {
				// 		uni.navigateTo({
				// 			url: '/staff/order_detail/order_detail?id=' + id
				// 		})
				// 	} else if (this.type == 2 || this.type == 11 || this.type == 5 || this.type == 6 || this.type == 9 ||
				// 		this
				// 		.type == 8) {
				// 		// 实验分包订单
				// 		uni.navigateTo({
				// 			url: '/staff/sub_detail/sub_detail?id=' + id
				// 		})
				// 	}
				// } else {
				// 	if (this.type == 1 || this.type == 10 || this.type == 3 || this.type == 4 || this.type == 7){
				// 		uni.navigateTo({
				// 			url: '/staffB/order_detail/order_detail?id=' + id
				// 		})
				// 	}
				// 	if(this.type == 2 || this.type == 11 || this.type == 5 || this.type == 6 || this.type == 9 || this.type == 8){
				// 		uni.navigateTo({
				// 			url: '/staffB/order_detail/order_detail?id=' + id + '&type=' + this.type
				// 		})
				// 	}

				// }


			},
			// 选择时间（开始/结束)
			isStartFn(num) {
				if (num == 1) {
					this.isStart = true
				} else {
					this.isStart = false
				}
				this.dateShow = true
			},
			// 时间确定
			dateConfirm(val) {
				if (this.isStart) {
					this.order_startime = val.year + '-' + val.month + '-' + val.day
				} else {
					this.order_endtime = val.year + '-' + val.month + '-' + val.day
				}
			},
			// 监听变化 重置页码数
			inputFn(data) {
				this.page = 1
				this.dataList = []
			},
			//搜索
			searchFn(num) {
				this.page = 1
				this.dataList = []
				let data = 1
				if (this.type == 5) {
					data = 1
				}
				if (this.type == 6) {
					data = 2
				}
				if (this.type == 7) {
					data = 4
				}
				if (this.type == 8) {
					data = 4
				}
				if (this.type == 9) {
					data = 5
				}
				console.log(data, 'data')
				this.isRefresh = true
				if (num == 1) {} else {
					this.customer_name = this.oldObj.name
					this.company_id = this.oldObj.id
					this.order_id = ''
					this.order_startime = ''
					this.order_endtime = ''
					this.supplier_name = ''
					this.supplier_id = ''
					this.date = this.oldObj.date
				}
				if (this.type == 7 || this.type == 9) {
					this.saleListxcxFn(data, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime,
						this
						.order_endtime, this
						.supplier_id, this.customer_name)

				} else if (this.type == 8) {
					this.salePayListxcxFn(data, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime,
						this.order_endtime, this.supplier_id, this.customer_name)
				} else if (this.type == 1) {
					this.expListFn(1, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
						this
						.order_endtime, this
						.supplier_id, this.customer_name, this.test_type)
				} else if (this.type == 2) {
					this.expListFn(2, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
						this
						.order_endtime, this
						.supplier_id, this.customer_name, this.test_type)
				} else if (this.type == 10) {
					this.expListFn(3, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
						this
						.order_endtime, this
						.supplier_id, this.customer_name)
				} else if (this.type == 11) {
					this.expListFn(4, (this.page - 1) * 10, this.date, this.company_id, this.order_id, this.order_startime,
						this
						.order_endtime, this
						.supplier_id, this.customer_name)
				} else if (this.type == 3) {
					this.expListxcxFn(1, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime, this
						.order_endtime, this.supplier_id, this.customer_name)
				} else
				if (this.type == 4) {
					this.expListxcxFn(2, (this.page - 1) * 10, this.company_id, this.order_id, this.order_startime, this
						.order_endtime, this.supplier_id, this.customer_name)
				} else {
					this.expSubListxcxFn(data, (this.page - 1) * 10, this.company_id, this.order_id, this
						.order_startime, this.order_endtime, this
						.supplier_id, this.customer_name)
				}

				this.searchShow = false

			},
			showFn(data) {
				this.show = true
				this.showType = data
			}
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/search.scss';

	.syxIcon {
		height: 50rpx;
		line-height: 50rpx;
		text-align: center;
	}

	.syxStyle {
		position: absolute;
		z-index: 20;
		top: 0;
		left: 0;
		display: flex;
		flex-direction: column;
		height: 500rpx;
		width: 100%;
		background-color: #fff;
		padding-bottom: 16rpx;
		border-radius: 20rpx;
		box-shadow: 0 2rpx 10rpx #ccc;
	}

	.btn {
		padding: 0 60rpx;

		button {
			color: #fff;
			background-color: #f39800;
			font-size: 30rpx;
			border-radius: 20rpx
		}
	}

	.dataList {
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
</style>