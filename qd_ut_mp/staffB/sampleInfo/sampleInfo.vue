<template>
	<view class="container">
		<view class="syx_content" :style="{height:(visibleHeight - 120) * 2 +'rpx'}">
			<view class="box" v-for="item,index in sampleInformationList" :key="index">
				<view class="title">
					<span class="index">样品信息-{{index+1}}</span>
					<span class="delete" @click="removeSample(index)"
						v-show="sampleInformationList.length > 1">删除</span>
				</view>
				<view class="form">
					<view class="form-item">
						<view class="label must">
							样品数量：
						</view>
						<view class="control">
							<input v-model="item.sample_num" placeholder="请输入样品数量">
						</view>
					</view>
					<view class="form-item">
						<view class="label must">
							名称/类型：
						</view>
						<view class="control">
							<input v-model="item.sample_name" placeholder="请输入名称/类型">
						</view>
					</view>
					<view v-for="(a, b) in item.data" :key="b">
						<view class="form-item" v-if="a.selection == 1 && a.attributeManageList.length > 0">
							<view class="label must">
								{{a.name}}
							</view>
							<view class="syxBtnBox">
								<view v-for="subItem in a.attributeManageList" :key="subItem.id" :style="{
					                      color: subItem.checked ? '#fff' : 'gray',
					                      border: subItem.checked
					                        ? '1px solid #f39800'
					                        : '1px solid gray',
					                      background: subItem.checked ? '#f39800' : '#fff',
					                    }" @click="btnFn(true, subItem, a.attributeManageList)">
									{{ subItem.name }}
								</view>
							</view>
						</view>
						<view class="form-item" v-if="a.selection == 2 && a.attributeManageList.length > 0">
							<view class="label must">
								{{a.name}}
							</view>
							<view class="syxBtnBox">
								<view v-for="subItem in a.attributeManageList" :key="subItem.id" :style="{
					                      color: subItem.checked ? '#fff' : 'gray',
					                      border: subItem.checked
					                        ? '1px solid #f39800'
					                        : '1px solid gray',
					                      background: subItem.checked ? '#f39800' : '#fff',
					                    }" @click="btnFn(false, subItem, a.attributeManageList)">
									{{ subItem.name }}
								</view>
							</view>
						</view>
					</view>

					<view class="form-item">
						<view class="label">
							主要成分：(填写后默认进行EDS测试，无需则不填)
						</view>
						<view class="control">
							<input v-model="item.main_component" placeholder="请输入主要成分">
						</view>
					</view>
					<view class="form-item">
						<view class="label must">
							是否含磁：
						</view>
						<view class="control">
							<u-radio-group v-model="item.is_magnetic">
								<u-radio v-for="(subItem, ind) in is_magnetic" :key="subItem.id" :name="subItem.id">
									{{subItem.name}}
								</u-radio>
							</u-radio-group>
						</view>
					</view>
<!--					<view class="form-item">-->
<!--						<view class="label must">-->
<!--							是否喷金：-->
<!--						</view>-->
<!--						<view class="control">-->
<!--							<u-radio-group v-model="item.is_gold_spraying">-->
<!--								<u-radio v-for="(subItem, ind) in is_magnetic" :key="subItem.id" :name="subItem.id">-->
<!--									{{subItem.name}}-->
<!--								</u-radio>-->
<!--							</u-radio-group>-->
<!--						</view>-->
<!--					</view>-->
					<view class="form-item">
						<view class="label">
							默认喷金：(费用10元/样，如不喷金请在下方说明原因)
						</view>
						<view class="control">
							<input v-model="item.gold_desc" placeholder="请输入原因">
						</view>
					</view>
				</view>
			</view>
		</view>
		<view class="btn">
			<button style="background-color: #f39800;border-color:#f39800;color:#fff" size="mini"
				@click="addSample()">添加样品</button>
			<view>
				<button size="mini" @click="closeDialog(true)" style="margin-right: 5px;">取消</button>
				<button style="background-color:#f39800;border-color:#f39800;color:#fff" size="mini"
					@click="okFn()">确定</button>
			</view>
		</view>
		<u-modal v-model="show" :show-cancel-button='true' @confirm="confirm" ref="uModal" :async-close="true"
			content="是否确定删除该样品信息？"></u-modal>
		<u-modal v-model="show2" :show-cancel-button='true' @confirm="confirm2" ref="uModal2" :async-close="true"
			content="确定要取消预约？"></u-modal>
	</view>
</template>

<script>
	import {
		getAttributeStateList,
		getStabilityList,
		subTestApi,
		sampleattributemanageList
	} from '@/api/index.js'
	export default {
		data() {
			return {
				sampleInformationList: [{
					data: [],
					sample_num: 1,
					sample_name: "",
					main_component: "",
					is_magnetic: 1,
					is_gold_spraying: 1,
					attribute_id: "",
				}],
				stability: [], // 稳定性
				attribute: [], // 属性
				// 是否含磁
				is_magnetic: [{
					id: 0,
					name: '是'
				}, {
					id: 1,
					name: '否'
				}],
				// 是否喷金
				is_gold_spraying: [{
					id: 0,
					name: '是'
				}, {
					id: 1,
					name: '否'
				}],
				visibleHeight: 0, // 自适应高
				dataObj: [], // 预约人信息
				show: false,
				index: 0,
				show2: false,
				attributeManageList:[]
			}
		},
		onLoad({
			data,
			special_type
		}) {
			// 预约人信息
			this.dataObj = data
			sampleattributemanageList(special_type).then((res) => {
				if (res.obj == null) {
					this.attributeManageList = []
				} else {
					res.obj.attributeManageList.forEach((item, index) => {
						item.attributeManageList.map((a) => {
							a.checked = false;
						});
						this.sampleInformationList[0].data.push(item);
					});
					this.attributeManageList = res.obj.attributeManageList;
				}
			});
		},
		mounted() {

			// 获取屏幕可视区域高度
			let height = uni.getSystemInfoSync().screenHeight;
			// 获取顶部状态栏的高度
			let statusBarHeight = uni.getSystemInfoSync().statusBarHeight;
			// 计算出除去顶部状态栏后的实际可视区域高度
			this.visibleHeight = height - statusBarHeight;
		},
		methods: {
			// 删除样品信息
			removeSample(index) {
				this.show = true
				this.index = index
			},
			confirm() {
				this.sampleInformationList.splice(this.index, 1);
				this.show = false
			},
			confirm2() {
				uni.switchTab({
					url: '/pages/index/index'
				})
				this.sampleInformationList = [{
					sample_num: 1,
					data: [],
					sample_name: "",
					main_component: "",
					is_magnetic: 1,
					is_gold_spraying: 1,
					attribute_id: "",
				}]
				this.show2 = false
			},
			// 添加样品
			addSample() {
				let arr = JSON.parse(JSON.stringify(this.attributeManageList));
				this.sampleInformationList.push({
					sample_num: 1,
					sample_name: "",
					main_component: "",
					is_magnetic: 1,
					is_gold_spraying: 1,
					attribute_id: "",
					data: [],
				});
				arr.forEach((item, index) => {
					this.sampleInformationList[
						this.sampleInformationList.length - 1
					].data.push(item);
				});
			},
			// 数据处理
			mergeData(str) {
				// 按逗号分割字符串
				const pairs = str.split(";");

				// 使用一个对象来存储合并的数据
				const map = {};

				// 遍历所有的键值对
				pairs.forEach((pair) => {
					const [key, value] = pair.split(":");
					if (!map[key]) {
						// 如果对象中没有这个键，则初始化一个空数组
						map[key] = [];
					}
					// 将值添加到对应键的数组中
					map[key].push(value);
				});

				// 将对象中的键值对转换为目标格式的字符串
				const result = Object.entries(map)
					.map(([key, values]) => `${key}:${values.join(":")}`)
					.join(";");

				return this.removeTrailingCharacters(result);
			},
			removeTrailingCharacters(str) {
				// 正则表达式匹配最后一个数字及其后面的所有字符
				const regex = /(\d+)([^0-9]*)$/;

				// 用空字符串替换最后一个数字后的所有字符
				const result = str.replace(regex, "$1");

				return result;
			},
			    // 选择
			    btnFn(type, data, list) {
			      if (type) {
			        list.forEach((item) => {
			          if (item.id === data.id) {
			            item.checked = true;
			          } else {
			            item.checked = false;
			          }
			        });
			      } else {
			        list.forEach((item) => {
			          if (item.id == data.id) {
			            item.checked = !item.checked;
			          }
			        });
			      }
			    },
			// 返回
			closeDialog(data) {
				if (data) {
					this.show2 = true
				} else {
					uni.switchTab({
						url: '/pages/index/index'
					})
					this.sampleInformationList = [{
						sample_num: 1,
						data: [],
						sample_name: "",
						main_component: "",
						is_magnetic: 1,
						is_gold_spraying: 1,
						attribute_id: "",
					}]
				}

			},
			// 确认
			okFn() {
				// 数据校验
				for (let i = 0; i < this.sampleInformationList.length; i++) {
					if (this.sampleInformationList[i].sample_num < 1) return this.$toast('请填写样品数量，并且大于1')
					if (this.sampleInformationList[i].sample_name == '') return this.$toast('请填写名称或类型')
					// if (this.sampleInformationList[i].main_component == '') return this.$toast('请填写主要成分')
					for (let j = 0; j < this.sampleInformationList[i].data.length; j++) {
						if(this.sampleInformationList[i].data[j].attributeManageList.length > 1){
							const status = this.sampleInformationList[i].data[j].attributeManageList.find(e => e.checked == true)
							if (status) {} else {
								return this.$toast('请选择数据，不能为空')
							}
						}

						for (
							let k = 0; k <
							this.sampleInformationList[i].data[j].attributeManageList.length; k++
						) {

							if (
								this.sampleInformationList[i].data[j].attributeManageList[k]
								.checked == true
							) {
								this.sampleInformationList[
										i
									].attribute_id +=
									`${this.sampleInformationList[i].data[j].attributeManageList[k].parent_id}:${this.sampleInformationList[i].data[j].attributeManageList[k].id};`;
							}
						}
					}
				}
				this.sampleInformationList.forEach((item) => {
					item.attribute_id = this.mergeData(item.attribute_id);
					item.is_gold_spraying = item.gold_desc ? 1 : 0;
					delete item.data
				});
				// 数据转码
				let obj = {
					sampleInformationList: this.sampleInformationList,
				};
				let str = JSON.stringify(obj);
				let codeStr = encodeURIComponent(str);

				let dataObj = JSON.parse((this.dataObj))
				const {
					userName,
					mobile,
					company_name,
					content,
					class_id,
					address,
					recycle,
					addresseeName,
					addresseeMobile,
					is_video,
					order_list,
					is_on,
					is_arrive,
				} = dataObj
				subTestApi({
					sampleInformationList: codeStr,
					userName,
					mobile,
					company_name,
					content,
					class_id,
					address,
					recycle,
					addresseeName,
					addresseeMobile,
					is_video,
					order_list,
					is_on,
					is_arrive,
				}).then(({
					res,
					resMsg
				}) => {
					if (res) {
						this.$toast('预约成功！')
						setTimeout(() => {
							this.closeDialog(false);
						}, 1000)
					}else{
						this.$toast('请求出错，请稍后重试！')
						setTimeout(() => {
							this.closeDialog(false);
						}, 1000)
					}
				}).catch(err=>{
					this.$toast('请求出错，请稍后重试！')
					setTimeout(() => {
						this.closeDialog(false);
					}, 1000)
				})
			},
		}
	}
</script>

<style lang="scss" scoped>
	@import "@/layout/form-item.scss";

	.container {
		padding: 0 0 50rpx;
	}

	// .box {
	// 	padding: 10px 5px 5px;
	// }

	.syx_content {
		overflow-y: auto;
	}

	.uni-list-cell {
		display: flex;
		margin: 4rpx 20rpx 0;
	}

	.title {
		display: flex;
		justify-content: space-between;
		margin: 20rpx 0 40rpx;
		padding: 0 30rpx;

		span:first-child {
			font-size: 36rpx;
			font-weight: bold;
			color: #f39800;
		}

		span:last-child {
			color: #f00;
			cursor: pointer;
		}
	}

	.btn {
		display: flex;
		justify-content: space-between;
		padding: 10rpx;

		button {
			margin: 0;
		}
	}

	.form-item {
		padding: 0 30rpx 0;
	}

	.syx_style {
		display: flex;
		flex-wrap: wrap;
		// /deep/ .u-radio {
		// 	border: 1px gray solid;
		// 	margin: 10rpx 10rpx 0 0;
		// 	border-radius: 16rpx;
		// 	padding: 0 0 0 16rpx;
		// 	.u-radio__icon-wrap--circle{
		// 		display: none;
		// 	}
		// }
	}

	.uRadioBox,
	.checkoutBox {
		display: inline-block;
		border: 1px gray solid;
		border-radius: 8rpx;
		text-align: center;
		margin: 6rpx 10rpx 0 0;
		padding: 10rpx 20rpx;
		color: gray;
	}

	.syxBtnBox {
		width: 100%;
		display: flex;
		flex-wrap: wrap;

		view {
			padding: 10rpx 22rpx;
			border-radius: 10rpx;
			border: 1px gray solid;
			margin: 5rpx 14rpx 6rpx 0;
			cursor: pointer;
		}
	}
</style>
