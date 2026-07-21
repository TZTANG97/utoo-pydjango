<template>
	<view>
		<view class="list" :style="{width:'100%',height:height+'rpx'}">
			<view class="name">收货地址</view>
			<picker class="picker" mode="multiSelector" :range="region" range-key="name" :value="regionIndex" @change="pickerChange"
			 @columnchange="pickerColumnchange">
				<view class="pbox" :class="{'pbox_hover':regionStr != '请选择省市区'}">
					<view style="width: 100%;text-align: left;padding-left: 36rpx;">{{regionStr}}</view>
					<text class="iconfont icon-you"></text>
				</view>
			</picker>
		</view>
	</view>
</template>
 
<script>
	import region from './city.json';
	export default {
		data() {
			return {
				// 原数组
				oldRegion: region,
				// 处理后的数组
				region: [
					[],
					[],
					[]
				],
				// 选择省市区的下标Index  传则默认选中传递的
				regionIndex: [0, 0, 0],
 
				// 选择的id
				// previnceId: 11,
				// cityId: 1101,
				// countyId: 110101,
 
				// 省市区字符串
				regionStr: '请选择省/市/区',
				code:''
			};
		},
		props: {
			// 组件高度
			height: {
				type: [Number],
				default: 92
			},
			// 组件宽度
			width: {
				type: [Number],
				default: 710
			},
			// 省id
			previnceId: {
				type: [Number],
				default: 11
			},
			// 城市id
			cityId: {
				type: [Number],
				default: 1101
			},
			// 县区id
			countyId: {
				type: [Number],
				default: 110101
			},
			// 是否是为修改(true为修改)
			isRevise: {
				type: [Boolean],
				default: false
			}
		},
		methods: {
			pickerChange(e) {
				this.regionIndex = e.detail.value;
				this.regionStr = this.region[0][this.regionIndex[0]].name + ' ' + this.region[1][this.regionIndex[1]].name + ' ' +
					this.region[2][this.regionIndex[2]].name;
					
				// 组件传值
				this.$emit('region', [this.region[0][this.regionIndex[0]].code, this.region[1][this.regionIndex[1]].code,
					this.region[2][this.regionIndex[2]].code]);
			},
			pickerColumnchange(e) {
				if (e.detail.column === 0) {
					// 声明城市数组
					let cityArr = [];
					let countyArr = [];
					// 设置下标
					this.regionIndex = [e.detail.value, 0, 0];
					// 改变城市列表
					this.region[1] = this.oldRegion[e.detail.value].children.map(item => {
						cityArr.push({
							name: item.name,
							code: item.code
						});
					})
					this.$set(this.region, 1, cityArr);
					// 改变县区列表
					this.oldRegion[e.detail.value].children[0].children.map(item => {
						countyArr.push({
							name: item.name,
							code: item.code
						});
					})
					this.$set(this.region, 2, countyArr);
				}
				if (e.detail.column === 1) {
					this.regionIndex[1] = e.detail.value;
					this.regionIndex[2] = 0;
					let countyArr = [];
					this.oldRegion[this.regionIndex[0]].children[this.regionIndex[1]].children.map(item => {
						countyArr.push({
							name: item.name,
							code: item.code
						});
					})
					this.$set(this.region, 2, countyArr);
				}
				if (e.detail.column === 2) {
					this.regionIndex[2] = e.detail.value;
				}
			},
		},
		created() {
			let provinceArr = [];
			let cityArr = [];
			this.oldRegion.map((item, index) => {
				this.region[0].push({
					name: item.name,
					code: item.code
				});
				if (this.previnceId == item.code) {
					provinceArr = item.children;
					this.regionIndex[0] = index;
				}
			})
			if(provinceArr.length == 0) provinceArr = this.oldRegion[0].children
			provinceArr.map((item, index) => {
				this.region[1].push({
					name: item.name,
					code: item.code
				});
				if (this.cityId == item.code) {
					cityArr = item.children;
					this.regionIndex[1] = index;
				}
			})
			if(cityArr.length == 0) cityArr = this.oldRegion[0].children[0].children
			cityArr.map((item, index) => {
				this.region[2].push({
					name: item.name,
					code: item.code
				});
				if (this.countyId == item.code) {
					this.regionIndex[2] = index;
				}
			})
			if (this.isRevise) {
				this.regionStr = this.region[0][this.regionIndex[0]].name + ' ' + this.region[1][this.regionIndex[1]].name + ' ' +
					this.region[2][this.regionIndex[2]].name;
			} else {
				this.regionStr = '请选择省市区';
			}
		},
		
	}
</script>
 
<style lang="scss">
	.list {
		// border-bottom: 1rpx solid #eee;
		padding: 0 8rpx;
		box-sizing: border-box;
		display: flex;
		flex-direction: row;
		align-items: center;
		position: relative;
 
		.picker {
			border: 1rpx #ccc solid;
			// padding-right: 50rpx;
			width: 434rpx;
 
			.pbox {
				width: 100%;
				height: 50rpx;
				display: flex;
				flex-direction: row;
				align-items: center;
				justify-content: space-between;
				color: #808080;
				view{
					width: 100%;
					text-align: right;
				}
				.icon-you {
					font-size: 28rpx;
				}
			}
 
			.pbox_hover {
				color: #383838;
			}
 
		}
 
		.name {
			width: 168rpx;
			font-size: 32rpx;
			color: #383838;
		}
 
		.icon-you {
			font-size: 28rpx;
			color: #999999;
		}
 
		.input {
			flex: 1;
			height: 100%;
			line-height: 92rpx;
			color: #9080A1;
		}
 
		.textarea {
			flex: 1;
			height: 100%;
			color: #A9A9A9;
		}
	}
</style>