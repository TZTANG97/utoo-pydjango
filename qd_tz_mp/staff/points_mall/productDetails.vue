<template>
	<view class="box">
		<view class="info">
			<view class="img">
				<u-swiper height="460" :list="imgList" indicatorActiveColor="#ff9b01" indicatorInactiveColor="#d3d7db"
					indicator indicatorMode="line" circular></u-swiper>
			</view>
			<!-- <img :src="'https://qgongye.oss-cn-shanghai.aliyuncs.com/'+data.app_manage_main_photo.path+'/'+data.app_manage_main_photo.name"
				alt="" /> -->
			<view class="msg">
				<text>{{data.goodName}}</text>
				<p>注意事项：</p>
				<textarea v-model="data.goodDescription" maxlength="-1"></textarea>
				<!-- <view style="overflow-wrap: anywhere;">{{data.goodDescription}}</view> -->
			</view>
		</view>
		<view class="btnBox" v-if="uType != '1'">
			<view class="btn" @click="okFn">
				确认兑换
			</view>
		</view>

		<view v-if="show" class="popupBox">
			<u-icon name="close-circle" class="closeIcon" @click="show = false" size="50"></u-icon>
			<view class="delivery" v-if="dz.length > 0">
				<p>收货地址选择</p>
				<!-- <u-input height="80" @click="pickerShow = true" type="textarea" v-model="dzData2" /> -->
				<view class="shdz" @click="pickerShow = true">{{dzData2}}</view>
				<!-- <view class="deliveryItem" v-for="item,index in dz">
					<view class="msg">
						<text>{{item.delivery_name}} {{item.delivery_phone}}</text> <br>
						<text>{{item.delivery_address}}{{item.detail_address}}</text>
					</view>
					<view class="select">
						<p :style="{border:item.is_default == 1 ? '16rpx #ff9b01 solid' : '1rpx #dde0e6 solid;'}"
							@click="selectBtn(item,index)"></p>
					</view>
					<view class="edit" @click="editFn(item)">
						<u-icon size="40" name="edit-pen-fill" color="#2979ff"></u-icon>
					</view>
				</view> -->
			</view>
			<view class="delivery" v-if="dz.length != 0">
				<p>确认收货地址</p>
				<view class="xxDelivery" style="margin: 10rpx 0;"><text>收件人</text><input :disabled="!edit" v-model="name"
						type="text"></input></view>
				<view class="xxDelivery"><text>手机号</text><input :disabled="!edit" v-model="mobile" type="text"></input>
				</view>
				<view v-if="edit">
					<Region :width='500' ref="region" @region="resgclick" />
				</view>
				<view v-else class="xxDelivery" style="margin: 20rpx 0 19rpx 0;"><text>收货地址</text><input disabled v-model="editDz" type="text"></input></view>
				<view class="xxDelivery"><text>详细地址</text><input :disabled="!edit" v-model="address" type="text"></input>
				</view>
			</view>
			<view class="btnBox" v-if="dz.length != 0">
				<view class="btn" @click="editFn" v-if="!edit">
					编辑地址
				</view>
				<view class="btn" @click="dzEditFn" v-if="edit">
					确认地址
				</view>
			</view>



			<view class="delivery" v-if="dz.length == 0">
				<p>添加收货地址</p>
				<view class="xxDelivery" style="margin: 24rpx 0;"><text>收件人</text><input v-model="name"
						type="text"></input></view>
				<view class="xxDelivery"><text>手机号</text><input v-model="mobile" type="text"></input></view>
				<view>
					<Region :width='500' @region="resgclick" />
				</view>
				<view class="xxDelivery"><text>详细地址</text><input v-model="address" type="text"></input></view>
			</view>
			<view class="btnBox">
				<view class="btn" @click="dzOkFn" v-if="dz.length == 0">
					确认地址
				</view>
			</view>

			<!-- <view class="delivery">
				<p>修改收货地址</p>
				<view class="xxDelivery" style="margin: 10rpx 0;"><text>收件人</text><input v-model="name"
						type="text"></input></view>
				<view class="xxDelivery"><text>手机号</text><input v-model="mobile" type="text"></input></view>
				<view>
					<Region :width='500' ref="region" @region="resgclick" />
				</view>
				<view class="xxDelivery"><text>详细地址</text><input v-model="address" type="text"></input></view>
			</view>
			<view class="btn" @click="dzEditFn">
				确认地址
			</view> -->
			<view class="nums">
				<p>输入兑换数量</p>
				<input class="numsInput" type="number" v-model.number.lazy="nums">
			</view>
			<view class="jf">
				<p>优先选择积分</p>
				<view class="jfBox">
					帐号积分：<view @click="jfSelect(1)"
						:style="{border:prioritize == 1 ? '16rpx #ff9b01 solid' : '1rpx #dde0e6 solid;','margin-right':'120rpx'}">
					</view>
					公司积分：<view @click="jfSelect(2)"
						:style="{border:prioritize == 2 ? '16rpx #ff9b01 solid' : '1rpx #dde0e6 solid;'}"></view>
				</view>
			</view>

			<view class="btnBox2" v-if="!edit">
				<view class="btn" style="color: #000;border: 1rpx #444546 solid;background: #fff;" @click="show = false">
					取消兑换
				</view>
				<view class="btn" @click="okFn1">
					确认兑换
				</view>
			</view>
		</view>
		<u-picker v-if="pickerShow" @confirm="dateConfirm" v-model="pickerShow" :default-selector="is_default"
			:range="dzList" range-key="label" mode="selector"></u-picker>
		<u-toast ref="uToast" />
	</view>
</template>

<script>
	import Region from '../city/city.vue'
	import {
		redeemGoodsDetail,
		getdeliveryaddress,
		duihuan,
		insertdeliveryaddress,
		updatedeliveryaddress
	} from '@/api/points.js'
	export default {
		components: {
			Region
		},
		data() {
			return {
				data: {},
				dz: [],
				dzData: null,
				nums: 1,
				totalIntegral: null,
				prioritize: 1,
				address: '',
				province: '',
				name: '',
				mobile: '',
				edit: false,
				id: null,
				imgList: [],
				show: false,
				pickerShow: false,
				dzData2: '',
				dzList: [],
				is_default: [],
				editDz:"",
				data2:null,
				val:0,
				uType: ''
			}
		},
		onLoad(e) {
			this.totalIntegral = uni.getStorageSync('totalIntegral');
			this.uType = uni.getStorageSync('uType');
			this.imgList = []
			redeemGoodsDetail(e.id).then(res => {
				this.data = res.obj.obj
				this.imgList.push('https://qgongye.oss-cn-shanghai.aliyuncs.com/' + this.data.app_manage_main_photo
					.path + '/' + this.data.app_manage_main_photo.name)
				this.data.app_manage_photos.forEach(item => {
					this.imgList.push('https://qgongye.oss-cn-shanghai.aliyuncs.com/' + item.path + '/' +
						item.name)
				})
			})
			this.dzFn()
		},
		methods: {
			// 地址接口
			async dzFn(num) {
				await getdeliveryaddress().then(res => {
					let dzList = []
					if (res.obj.expUserDeliveryAddresses.length > 0) {
						this.dz = res.obj.expUserDeliveryAddresses
						if(num != 1) this.dzData = res.obj.expUserDeliveryAddresses[0]
						res.obj.expUserDeliveryAddresses.forEach((item, index) => {
							dzList.push({
								label: item.delivery_name + ' ' + item.delivery_phone + ' ' + item
									.delivery_address + ' ' + item.detail_address,
								value: index,
								id: item.delivery_address_id,
								dzId:item.id
							})
							this.dzList = dzList
							if (item.is_default == 1 && !num){
								this.is_default = [index]
								this.dateConfirm(index)
							}
						})
						if(num == 1){
							this.dateConfirm(this.valData)
						}
						if(num == 2) this.dateConfirm(0)
					}
				})
			},
			okFn() {
				this.show = true
			},
			okFn1() {
				if (typeof this.nums != 'number' || this.nums < 1) return this.$toast('请输入大于0的数字!')
				let jf = this.data.nums * this.nums
				if (jf > this.totalIntegral) return this.$toast('积分不足！')
				if (!this.dzData) return this.$toast('请选择地址！')
				if (this.data.inventoryNum < this.nums) return this.$toast('库存不足！')
				let data = {
					id: this.data.id,
					userName: this.dzData.delivery_name,
					mobile: this.dzData.delivery_phone,
					address: this.dzData.delivery_address + this.dzData.detail_address,
					nums: this.nums,
					prioritize: this.prioritize,
				}
				duihuan(data).then(res => {
					this.$toast(res.resMsg)
					if (res.res) {
						setTimeout(() => {
							uni.navigateBack()
						}, 1500)
					}
				})
			},
			// selectBtn(item, index) {
			// 	let list = JSON.parse(JSON.stringify(this.dz))
			// 	list.forEach((e, i) => {
			// 		if (index == i) {
			// 			e.is_default = 1
			// 		} else {
			// 			e.is_default = 0
			// 		}
			// 	})
			// 	this.dz = list
			// 	this.dzData = item
			// },
			jfSelect(data) {
				this.prioritize = data
			},
			// 城市地址
			resgclick(ele) {
				let data = ele.join()
				this.province = data
			},
			// 新增地址
			dzOkFn() {
				if (!this.name) return this.$toast('请输入收件人')
				if (!this.mobile) return this.$toast('请输入手机号')
				if (!this.province) return this.$toast('请选择地址')
				if (!this.address) return this.$toast('请输入地址')
				let data = {
					name: this.name,
					mobile: this.mobile,
					province: this.province,
					address: this.address
				}
				insertdeliveryaddress(data).then(res => {
					if (res.res) {
						// this.dz = [{
						// 	delivery_name:this.name,
						// 	delivery_phone:this.mobile,
						// 	delivery_address:this.province,
						// 	detail_address:this.address,
						// 	checked: true
						// }]
						this.dzFn(2)
						this.$toast('添加成功！')
						this.province = null
					}
				})

			},
			// // 修改方法
			editFn() {
				this.edit = true
				setTimeout(() => {
					let str = this.data2.id.split(',')
					this.$refs.region.regionStr = this.editDz
					this.$refs.region.regionIndex = [0, 0, 0]
					this.previnceId = str[0]
					this.cityId = str[1]
					this.countyId = str[2]
				}, 500)
			// 	this.isRevise = true
			// 	this.name = item.delivery_name
			// 	this.mobile = item.delivery_phone
			// 	this.address = item.detail_address
			// 	this.id = item.id
			// 	setTimeout(() => {
			// 		let str = item.delivery_address_id.split(',')
			// 		this.$refs.region.regionStr = item.delivery_address
			// 		this.$refs.region.regionIndex = [0, 0, 0]
			// 		this.previnceId = str[0]
			// 		this.cityId = str[1]
			// 		this.countyId = str[2]
			// 	}, 500)
			},
			// 回调
			dateConfirm(val) {
				let data = this.dzList[val]
				this.data2 = this.dzList[val]
				this.dzData2 = data.label
				this.id = data.dzId
				let arr = data.label.split(' ')
				this.name = arr[0]
				this.mobile = arr[1]
				this.address = arr[3]
				this.editDz = arr[2]
				this.valData = val
				this.dzData = {
					delivery_name: arr[0],
					delivery_phone: arr[1],
					delivery_address: arr[2],
					detail_address: arr[3],
					id:data.dzId,
					delivery_address_id: data.id
				}
			},
			// 修改地址
			dzEditFn() {
				if (!this.name) return this.$toast('请输入收件人')
				if (!this.mobile) return this.$toast('请输入手机号')
				if (!this.previnceId) return this.$toast('请选择地址')
				if (!this.address) return this.$toast('请输入地址')
				if (!this.province) {
					this.province = `${this.previnceId},${this.cityId},${this.countyId}`
				}
				let data = {
					id: this.id,
					name: this.name,
					mobile: this.mobile,
					province: this.province,
					address: this.address
				}
				updatedeliveryaddress(data).then(res => {
					if (res.res) {
						this.$toast('修改成功！')
						this.dzFn(1)
						this.edit = false
						this.province = ''
					}
				})
			}
		}
	}
</script>
<style scoped lang="scss">
	.box {
		display: flex;
		flex-direction: column;
		align-items: center;
		width: 100%;
		height: 100vh;
		background-color: #fbfaf6;
		padding-top: 20rpx;

		.info {
			display: flex;
			flex-direction: column;
			align-items: center;
			width: 70%;
			background-color: #faf7f2;
			padding: 30rpx 30rpx 0 30rpx;

			.img {
				width: 100%;
				height: 460rpx;
				background-color: #fffffb;
			}

			.msg {
				width: 100%;
				height: 530rpx;
				margin: 40rpx 0 0 0;
				overflow-y: auto;

				text {
					display: flex;
					width: 100%;
					color: #2d2c2a;
					font-size: 24rpx;
					border-bottom: 1rpx #c9c6c2 solid;
					padding-bottom: 15rpx;
					margin-bottom: 20rpx;
				}

				p {
					color: #21201f;
					font-size: 24rpx;
					margin: 10rpx 0 30rpx 0;
					font-weight: 700;
					line-height: 36rpx;
				}
				textarea{
					width: 100%;
					height: 390rpx;
				}
			}
		}
	}

	.popupBox {
		position: absolute;
		left: 0;
		top: 0;
		z-index: 10;
		width: 100%;
		height: 100vh;
		background-color: #fbfaf6;
		padding: 30rpx 50rpx;
		.closeIcon{
			position: absolute;
			right: 50rpx;
			top: 30rpx;
		}
	}

	.nums {
		display: flex;
		width: 100%;
		height: 120rpx;
		margin: 20rpx 0;

		p {
			color: #21201f;
			font-size: 30rpx;
			margin: 10rpx 0 20rpx 0;
			font-weight: 700;
			line-height: 36rpx;
		}


	}

	.jf {
		width: 100%;
		height: 120rpx;
		margin: 20rpx 0;

		p {
			color: #21201f;
			font-size: 30rpx;
			margin: 10rpx 0;
			font-weight: 700;
			line-height: 36rpx;
		}

		.jfBox {
			display: flex;
			align-items: center;
			margin-top: 30rpx;
			margin-left: 20rpx;

			view {
				// display: inline-block;
				width: 40rpx;
				height: 40rpx;
				border-radius: 50%;
				border: 1rpx #dde0e6 solid;
				background: transparent;
			}
		}
	}

	.delivery {
		width: 100%;
		height: auto;
		padding: 10rpx 30rpx;
		margin-top: 20rpx;

		p {
			color: #21201f;
			font-size: 30rpx;
			margin: 10rpx 0;
			font-weight: 700;
			line-height: 36rpx;
		}

		.deliveryItem {
			display: flex;
			padding: 10rpx 20rpx;
			margin-bottom: 20rpx;

			.msg {
				width: 80%;

				text {
					display: inline-block;
					width: 100%;
					white-space: nowrap;
					overflow: hidden;
					text-overflow: ellipsis;
				}
			}

			.select {
				display: flex;
				justify-content: center;
				align-items: center;
				width: 10%;

				p {
					width: 50rpx;
					height: 50rpx;
					border-radius: 50%;
					border: 1rpx #dde0e6 solid;
					background: transparent;
				}
			}

			.edit {
				display: flex;
				justify-content: center;
				align-items: center;
				width: 10%;
			}
		}

		.addBtn {
			width: 160rpx;
			color: #fff;
			background: red;
			text-align: center;
			padding: 10rpx 0;
			border-radius: 22rpx;
			margin-left: 75%;
		}

		.xxDelivery {
			display: flex;
			padding: 0 8rpx;

			&>text {
				width: 168rpx;
				font-size: 32rpx;
			}

			input {
				width: 400rpx;
				border: 1rpx #ccc solid;
				padding-left: 36rpx;
				height: 50rpx;
			}
		}
	}
	.btnBox{
		width: 100%;
		display: flex;
		justify-content: center;
	}
	.btnBox2{
		width: 100%;
		display: flex;
		justify-content: space-around;
	}
	.btn {
		color: #fff;
		background-color: #ff9b01;
		padding: 10rpx 0;
		border-radius: 20rpx;
		margin-top: 30rpx;
		margin-bottom: 40rpx;
		width: 200rpx;
		text-align: center;
	}

	.numsInput {
		border: 1rpx #ccc solid;
		padding: 10rpx;
		margin-left: 20rpx;
	}
	.numsInput2 {
		margin-left: 38rpx;
	}
	// ::v-deep textarea{
	// 	border: 1rpx #ccc solid !important;
	// 	padding: 15rpx !important;
	// 	height: 37px !important;
	// }
	// ::v-deep .u-input__right-icon{
	// 	display: none;
	// }
	.shdz{
		border: 1rpx #ccc solid;
		padding: 15rpx;
		width: 100%;
	}
</style>
