<template>
	<view class="container">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					所属品牌：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'brandList', '所属品牌', 'brandId')">
						{{ swapIdgetValue('brandList', 'name', 'brandId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item" v-if="!shows">
				<view class="group-label">
					产品名称：
				</view>
				<view class="group-content ">
					<view class="text-content inputBox"
						@click="select('goods_name', 'productList', '产品名称', 'productId')">
						{{ swapIdgetValue('productList', 'goods_name', 'productId') }}
						<u-icon size="28" name="arrow-right"></u-icon>
						<text @click.stop="delete1Fn(index)" style="color: red;padding: 0 24rpx 0 50rpx;">删除</text>
					</view>
				</view>
			</view>
			<view class="group-item" v-if="shows">
				<view class="group-label">
					添加产品名称：
				</view>
				<view class="group-content">
					<view class="text-content">
						<input class="child-order-input" type="text" v-model="name" placeholder="请输入产品名称">
					</view>
				</view>
			</view>
			<view class="confirm1" @click="addFn2" v-if="shows">
				确认添加
			</view>
			<view class="confirm1" @click="addFn1" v-if="!shows">
				添加产品名称
			</view>
			<view class="group-item" v-for="item,index in list" :key="index">
				<view class="group-label">
					<text v-if="index == 0">产品型号：</text>
				</view>
				<view class="group-content">
					<view class="text-content inputBox">
						<input class="child-order-input" type="text" v-model="item.model" placeholder="请输入产品型号"> <text
							@click="deleteFn(index)" style="color: red;padding: 0 24rpx 0 50rpx;">删除</text>
					</view>
				</view>
			</view>
			<text></text>
			<view class="confirm1" @click="addFn">
				添加产品型号
			</view>
			<view class="confirm" @click="submitData">
				保&nbsp;存
			</view>
		</view>
		<u-toast ref="uToast" />
		<!-- 公用弹框-完整数据 -->
		<popup-bottom :show.sync="showcheckBox" :list.sync="checkBoxList" :title="checkBoxTitle"
			:showKey="checkBoxKeyName" @getValue="confirmValue"></popup-bottom>
	</view>
</template>

<script>
	import popupBottom from '../popupBottom.vue'
	import {
		queryBrand,
		loadGoodsNames,
		selGoodsModels,
		submitExperimentGoods,
		addGoodsName,
		delGoodsName
	} from '@/api/reservationList.js'
	export default {
		components: {
			popupBottom,
		},
		data() {
			return {
				brandId: null,
				brandList: [],
				productId: null,
				productList: [],
				checkBoxTitle: null,
				checkBoxKeyName: null,
				checkEchoKey: null,
				checkBoxList: [],
				showcheckBox: false,
				list: [{
					model: ''
				}],
				name: '',
				shows: false
			}
		},
		onLoad(e) {
			queryBrand().then(res => {
				this.brandList = res.obj
			})
		},
		onShow() {

		},
		methods: {
			// 选择
			select(keyName, listName, titleName, echoKey) {
				// 选择框标题
				this.checkBoxTitle = titleName
				// 选择框中数组展示的key
				this.checkBoxKeyName = keyName

				// 回显key
				this.checkEchoKey = echoKey

				this.checkBoxList = this[listName]

				this.showcheckBox = true
			},
			swapIdgetValue(listName, echoName, componentKey) {
				let result = this[listName].find(e => e['id'] == this[componentKey])
				if (result) {
					return result[echoName]
				} else {
					return '请选择'
				}
			},
			// 确定值
			confirmValue(e) {
				this[this.checkEchoKey] = e.id
				if (this.checkEchoKey == 'brandId') {
					loadGoodsNames({
						goods_brand_id: this.brandId
					}).then(res => {
						this.productList = res.obj
					})
				}
				if (this.checkEchoKey == 'productId') {
					selGoodsModels(this.productId).then(res => {
						this.list = res.obj
					})
				}
				this.showcheckBox = false
			},
			deleteFn(index) {
				this.list.splice(index, 1)
			},
			delete1Fn() {
				const that = this
				if(!that.productId) that.$tip('请选择产品名称')
				uni.showModal({
					title: '提示',
					content: '确定删除？',
					success(res) {
						if (res.confirm) {
							delGoodsName(that.productId).then(res => {
								if (res.res) {
									that.shows = !that.shows
									that.productId = null
									that.$tip('删除成功')
									loadGoodsNames({
										goods_brand_id: that.brandId
									}).then(res => {
										that.productList = res.obj
									})
								}
							})
						}
					}
				})
			},
			addFn2() {
				if (!this.brandId) return this.$tip('请选择品牌')
				if (!this.name) return this.$tip('请输入名称')
				let data = {
					goods_name: this.name,
					goods_brand_id: this.brandId,
				}
				addGoodsName(data).then(res => {
					if (res.res) {
						this.shows = !this.shows
						this.productId = null
						this.$tip('添加成功')
						loadGoodsNames({
							goods_brand_id: this.brandId
						}).then(res => {
							this.productList = res.obj
						})
					}
				})
			},
			addFn1() {
				this.shows = !this.shows
			},
			addFn() {
				this.list.push({
					model: ''
				})
			},
			submitData() {
				let str = ''
				this.list.forEach(item=>{
					str += item.model + ','
				})
				if(!this.productId) return this.$tip('请选择品牌')
				if(!this.brandId) return this.$tip('请输入名称')
				let data = {
					id: this.productId,
					goods_brand_id: this.brandId,
					goods_model: str.slice(0, -1)
				}
				submitExperimentGoods(data).then(res => {
					if(res.res){
						this.$tip('新增成功')
						setTimeout(() => {
							uni.navigateBack();
						}, 1500)
					} else {
						this.$tip(res.error)
					}
				})
			}
		}
	}
</script>

<style lang="scss" scoped>
	@import '@/layout/group.scss';

	.child-order-input {
		text-align: right;
	}

	.inputBox {
		display: flex;
	}

	.confirm1 {
		width: 260rpx;
		height: 65rpx;
		border-radius: 30rpx;
		text-align: center;
		line-height: 65rpx;
		color: #FFF;
		background-color: #42a5f5;
		margin: 10rpx;
	}

	.confirm {
		width: 260rpx;
		height: 65rpx;
		border-radius: 30rpx;
		text-align: center;
		line-height: 65rpx;
		color: #FFF;
		background-color: $primary;
		margin: 40rpx auto;
	}
</style>