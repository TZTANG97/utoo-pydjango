<template>
	<view class="container">
		<view class="group">
			<!-- 			<view class="group-item">
				<view class="group-label">
					<span style="color: #f00;">*</span>
					<span>样品ID</span>
				</view>
				<view class="group-content">
					<span v-if="sample_id">{{ sample_id.split('_')[1] }}</span>
					<image v-if="!id" @click="scan(1)" src="@/static/f-scan.png" mode=""></image>
				</view>
			</view> -->
			<view class="group-item" v-if="type == 1" @click="show = true">
				<view class="group-label">
					<span style="color: #f00;">*</span>
					<span>产品名称</span>
				</view>
				<view class="group-content">
					<view class="text-content" >
						<span>{{ cpName }}</span>
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>


			<view class="group-item" v-if="type == 1 || type == 5"
				@click="chooseLocation? chooseLocation = false : chooseLocation = true">
				<view class="group-label">
					选择存放位置 type={{type}}
				</view>
				<view class="group-content">
					{{ chooseLocation? '是' : '否' }}
				</view>
			</view>
			<template v-if="(type == 1 || type == 5)? chooseLocation : type != 3 && type != 4">
				<view class="group-item">
					<view class="group-label">
						仓库名称
					</view>
					<view class="group-content">
						<view class="text-content" @click="select('sample_store_name', 'ckList', '仓库名称', 'ckName')">
							{{ swapIdgetValue('ckList', 'sample_store_name', 'ckName') }}
							<u-icon size="28" name="arrow-right"></u-icon>
						</view>
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						库存位置
					</view>
					<view class="group-content">
						<view class="text-content" @click="select('blockName', 'ckRessList', '库存位置', 'store_id')">
							{{ swapIdgetValue('ckRessList', 'blockName', 'store_id') }}
							<u-icon size="28" name="arrow-right"></u-icon>
						</view>
						<!-- 						<input type="text" v-model="store">
									<image @click="scan(2)" src="@/static/f-scan.png" mode=""></image> -->
					</view>
				</view>
			</template>

			<view class="group-item" v-if="type == 3">
				<view class="group-label">
					<span>实验平台</span>
				</view>
				<view class="group-content">
					<span v-if="line_id">{{ line_name }}</span>
					<image v-if="!id" @click="scan(3)" src="@/static/f-scan.png" mode=""></image>
				</view>
			</view>



			<!-- 			<template v-if="(type == 1 || type == 5)? chooseLocation : type != 3 && type != 4">
				<view class="group-item">
					<view class="group-label">
						仓库名称
					</view>
					<view class="group-content">
						<input type="text" v-model="store_name">
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						库存位置
					</view>
					<view class="group-content">
						<input type="text" v-model="store">
						<image @click="scan(2)" src="@/static/f-scan.png" mode=""></image>
					</view>
				</view>
			</template> -->

			<template v-if="type == 2">
				<view class="group-item">
					<view class="group-label">
						<span style="color: #f00;">*</span>
						<span>预计完成时间</span>
					</view>
					<view class="group-content">
						<input type="number" placeholder="请输入预计完成时间" v-model="finish_time">
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						<span style="color: #f00;">*</span>
						<span>时间类型</span>
					</view>
					<view class="group-content" @click="time_type == 1? time_type = 2 : time_type = 1">
						<view class="text-content">
							{{ time_type === 1? '小时' : '天' }}
						</view>
					</view>
				</view>
			</template>
			<template v-if="type == 6">
				<view class="group-item">
					<view class="group-label">
						<span style="color: #f00;">*</span>
						<span>快递单号</span>
					</view>
					<view class="group-content">
						<input type="text" placeholder="请输入快递单号" v-model="express_no">
					</view>
				</view>
				<view class="group-item">
					<view class="group-label">
						<span style="color: #f00;">*</span>
						<span>快递公司</span>
					</view>
					<view class="group-content">
						<input type="text" placeholder="请输入快递公司" v-model="express_name" />
					</view>
				</view>
			</template>
			<template v-if="type == 7">
				<template v-if="handle === 1">
					<view class="group-item" @click="lcNewLocation? lcNewLocation = false : lcNewLocation = true">
						<view class="group-label">
							是否选择位置信息
						</view>
						<view class="group-content">
							{{ lcNewLocation? '是' : '否' }}
						</view>
					</view>
					<template v-if="lcNewLocation">
						<view class="group-item">
							<view class="group-label">
								<span style="color: #f00;">*</span>
								<span>新仓库名称</span>
							</view>
							<view class="group-content">
								<input type="text" v-model="new_store_name">
							</view>
						</view>
						<view class="group-item">
							<view class="group-label">
								<span style="color: #f00;">*</span>
								<span>新库存位置</span>
							</view>
							<view class="group-content">
								<input type="text" v-model="new_store">
								<image @click="scan(4)" src="@/static/f-scan.png" mode=""></image>
							</view>
						</view>
					</template>
				</template>
				<view class="group-item">
					<view class="group-label">
						操作
					</view>
					<view class="group-content" @click="handle === 1? handle = 2 : handle = 1 ">
						<div class="text-content">
							{{ handle === 1? '样品留存' : '样品报废' }}
						</div>
						<image src="@/static/switch.png" mode=""></image>
					</view>
				</view>
			</template>
			<view class="group-item" v-if="type == 2">
				<view class="group-label">
					<span>预约云视频时间</span>
				</view>
				<view class="group-content">
					<uni-datetime-picker v-model="setting_time" type="datetime" />
				</view>
			</view>
			<view class="group-item" v-if="type == 2">
				<view class="group-label">
					<span>腾讯视频会议号</span>
				</view>
				<view class="group-content">
					<input type="text" placeholder="请输入会议号" v-model="meeting_num">
				</view>
			</view>
		</view>
		<u-popup v-model="show" mode="center" width="100%" height="80%" border-radius="10rpx">
			<view style="padding: 20rpx;">
				<view style="padding: 20rpx;border-bottom: 1px #ccc solid;">选择子订单</view>
				<scroll-view scroll-y="true" style="height: 100%;">
					<view class="list">
						<view class="item" v-for="(item, index) in cpList" :key="index">
							<view class="item-row"
								style="display: flex;justify-content: space-between;padding: 0 20rpx;align-items: center;">
								<text></text>
								<u-checkbox-group>
									<u-checkbox v-model="item.checked"></u-checkbox>
								</u-checkbox-group>
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
								<text>实验测试项目：{{ item['experiment_project_name'] }}</text>
							</view>
							<view class="item-row" v-if="item['experiment_class_name']">
								<text>实验测试分类：{{ item['experiment_class_name'] }}</text>
							</view>
						</view>
					</view>
				</scroll-view>
				<view class="confrim-btn">
					<u-button @click="cpBtn">确定</u-button>
				</view>
			</view>
		</u-popup>
		<view class="main-btn" @click="submit">
			提&nbsp;交
		</view>
		<!-- 公用弹框-完整数据 -->
		<popup-bottom v-if="showcheckBox" :show.sync="showcheckBox" :list.sync="checkBoxList" :title="checkBoxTitle"
			:showKey="checkBoxKeyName" @getValue="confirmValue"></popup-bottom>
	</view>
</template>

<script>
	import {
		scanOperateApi,
	} from '@/api/index.js'
	import {
		experimentChildOrderList,
		queryStore,
		queryListByStoreId,
	} from '@/api/staffB.js'
	import popupBottom from '../popupBottom.vue'
	export default {
		components: {
			popupBottom,
		},
		data() {
			return {
				id: '',
				type: '',
				sample_id: '',
				store: '',
				finish_time: '',
				line_id: '',
				line_name: '',
				new_store: '',
				new_store_name: '',
				new_store_id: '',
				express_no: '',
				express_name: '',
				time_type: 1,
				store_name: '',
				store_id: '',
				handle: 1,
				chooseLocation: false,
				lcNewLocation: false,
				showCalendar: false,
				setting_time: null,
				meeting_num: null,
				show: false,
				cpName: '请选择',
				cpList: [],
				cpData: [],
				ckList: [],
				ckRessList:[],
				checkBoxTitle: '',
				checkBoxKeyName: '',
				checkEchoKey: '',
				checkBoxList: [],
				showcheckBox: false,
				ckName: '',
			}
		},
		onLoad({
			type,
			id = '',
			line_id = '',
			line_name = ''
		}) {
			this.type = type - 0

			// 如果有id，说明是从订单跳转过来的
			if (id) {
				// 没什么意意义，就是单传的判断一下
				this.id = id
				this.sample_id = 'childId_' + id

				if (this.type === 3) {
					this.line_id = line_id
					this.line_name = line_name
				}
			}
			if (type == 1) {
				experimentChildOrderList(id).then(res => {
					res.data.forEach(item => {
						item.checked = false
					})
					this.cpList = res.data
				})
				queryStore().then(res => {
					this.ckList = res.obj
					console.log(res, 'ressssssssssss')
				})
			}
		},
		methods: {
			cpBtn() {
				let arr = []
				this.cpData = []
				this.cpList.forEach(item => {
					if (item.checked) arr.push(true)
				})
				if (arr.length == 0) return this.$toast('请选择一条数据！')
				if (arr.length != 1) return this.$toast('只能选择一条数据！')
				this.cpList.forEach(item => {
					if (item.checked) this.cpData.push(item)
				})
				this.cpName = this.cpData[0].goods_name
				this.show = false
			},
			scan(val) {
				const that = this
				uni.scanCode({
					success(res) {
						console.log(res);
						if (res.errMsg) {
							switch (val) {
								case 1:
									that.sample_id = res.result;
									break;
								case 2:
									let [store_id, store_name, store] = res.result.split(';')
									that.store_id = store_id
									that.store_name = store_name
									that.store = store
									break;
								case 3:
									let [line_id, line_name] = res.result.split(';')
									that.line_id = line_id
									that.line_name = line_name
									break;
								default:
									let [new_store_id, new_store_name, new_store] = res.result.split(';')
									that.new_store_id = new_store_id
									that.new_store_name = new_store_name
									that.new_store = new_store
							}
						} else {
							that.$toast('二维码无效，请重试！')
						}
					},
					fail(err) {
						if (err.errMsg !== 'scanCode:fail cancel') {
							that.$toast('二维码无效，请重试！')
						}
					},
				})
			},
			// 选择
			select(keyName, listName, titleName, echoKey) {
				// 选择框标题
				this.checkBoxTitle = titleName
				// 选择框中数组展示的key
				// if(keyName == 'blockName|number'){
				// 	this.checkBoxKeyName = keyName
				// }else{

				// }
				this.checkBoxKeyName = keyName


				// 回显key
				this.checkEchoKey = echoKey



				console.log(echoKey,'6666')
				if(echoKey === 'store_id'){
					console.log("???")
					queryListByStoreId(this.ckName).then(res=>{
						this.ckRessList  = res.obj
						this.checkBoxList = this[listName]
						this.showcheckBox = true
						// setTimeout(()=>{

						// },1000)
					})
				}else{
					this.checkBoxList = this[listName]
					this.showcheckBox = true
				}
			},
			// 根据id获取值并回显
			// 数组名称，展示的名称，组件内的哪个值跟对象里的哪个值比较
			// 默认比较id
			swapIdgetValue(listName, echoName, componentKey) {
				let result = this[listName].find(e => e['id'] == this[componentKey])
				if (result) {
					if(echoName == 'blockName'){
						return result.blockName + '-' + result.number
					}else{
						return result[echoName]
					}
				} else {
					return '请选择'
				}
			},
			// 确定值
			confirmValue(e) {
				this[this.checkEchoKey] = e.id
				this.showcheckBox = false
				if(this.checkEchoKey == 'ckNmae'){
					console.log(this.ckName,'6666')
				}
			},
			removeBOM(str) {
				// UTF-8 BOM is represented by the Unicode character \uFEFF
				if (str.charCodeAt(0) === 0xFEFF) {
					return str.slice(1);
				}
				return str;
			},

			submit() {
				console.log(this.setting_time, '.setting_time')
				console.log(this.meeting_num, '.meeting_num')
				let params = {
					type: this.type,
					childId: this.id,
				}
				if (this.setting_time) params.setting_time = this.setting_time
				if (this.meeting_num) params.meeting_num = this.meeting_num

				console.log(params, 'params')
				if (this.chooseLocation && (this.type == 1 || this.type == 5)) {
					if (!this.store_id) return this.$toast('请选择库存位置')
					// params['storePosId'] = this.removeBOM(this.store_id)
					params['storePosId'] = this.store_id
					params['isPosition'] = 1
				} else {
					// params['storePosId'] = this.store_id ? this.removeBOM(this.store_id) : ''
					params['storePosId'] = this.store_id ? this.removeBOM(this.store_id) : ''
					params['isPosition'] = 0
				}


				if (this.type == 2) {
					if (!this.finish_time) return this.$toast('请输入预计完成时间')
					params['finish_time'] = this.finish_time
					params['time_type'] = this.time_type
				}

				if (this.type == 3) {
					// if (!this.line_id) return this.$toast('请扫描实验平台二维码')
					params['lineId'] = this.removeBOM(this.line_id)
				}

				if (this.type == 6) {
					if (!this.express_no) return this.$toast('请输入快递单号')
					if (!this.express_name) return this.$toast('请输入快递公司名称')
					params['expressNo'] = this.express_no
					params['expressName'] = this.express_name
				}

				if (this.type == 7) {
					if (this.handle === 1 && this.lcNewLocation) {
						params['isPosition'] = 1
						if (!this.new_store_id) return this.$toast('请选择新的库存位置')
						params['newStorePosId'] = this.removeBOM(this.new_store_id)
					}
					params['key'] = this.handle
				}

				scanOperateApi(params).then(res => {
					if (res.res) {

						// 如果存在id，则证明是从订单页面过来的。
						if (this.id) {
							uni.$_emit('refersh')
						}

						uni.redirectTo({
							url: `/staffB/result/result?title=操作成功`
						})
					} else {
						this.$toast(res.resMsg)
					}
				})
			},
			// 打开日历选择器
			chooseDate() {
				this.showCalendar = true
			},
		}
	}
</script>

<style scoped lang="scss">
	@import '@/layout/group.scss';

	.main-btn {
		margin-top: 20rpx;
	}

	.group-content {
		image {
			width: 55rpx;
			height: 55rpx;
			vertical-align: middle;
			margin-left: 15rpx;
		}
	}

	input {
		text-align: right;
	}

	.container {
		padding: 0 20rpx;
	}

	/deep/ .uni-datetime-picker--btn {
		background-color: #3C8BDB;
	}

	/deep/ .uni-calendar-item__weeks-box .uni-calendar-item--checked {
		background-color: #3C8BDB;
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
</style>
