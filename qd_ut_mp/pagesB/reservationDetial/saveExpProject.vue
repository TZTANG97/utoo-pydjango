<template>
	<view class="container">
		<view class="group">
			<view class="group-item">
				<view class="group-label">
					一级分类：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'oneList', '一级分类', 'first_id')">
						{{ swapIdgetValue('oneList', 'name', 'first_id') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					二级分类：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'twoList', '二级分类', 'sec_id')">
						{{ swapIdgetValue('twoList', 'name', 'sec_id') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					三级分类：
				</view>
				<view class="group-content">
					<view class="text-content" @click="select('name', 'threeList', '三级分类', 'class_id')">
						{{ swapIdgetValue('threeList', 'name', 'class_id') }}
						<u-icon size="28" name="arrow-right"></u-icon>
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					项目名称：
				</view>
				<view class="group-content">
					<view class="text-content">
						<input class="child-order-input" type="text" v-model="project_name" placeholder="请输入项目名称">
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					测试单价：
				</view>
				<view class="group-content">
					<view class="text-content">
						<input class="child-order-input" type="digit" v-model="test_price" placeholder="请输入测试单价">
					</view>
				</view>
			</view>
			<view class="group-item">
				<view class="group-label">
					隶属国家：
				</view>
				<view class="group-content">
					<view class="text-content">
						<input class="child-order-input" type="text" v-model="country" placeholder="请输入隶属国家">
					</view>
				</view>
			</view>
		</view>
		<view class="confirm" @click="submitData">
			保&nbsp;存
		</view>
		<u-toast ref="uToast" />
		<!-- 公用弹框-完整数据 -->
		<popup-bottom :show.sync="showcheckBox" :list.sync="checkBoxList" :title="checkBoxTitle"
			:showKey="checkBoxKeyName" @getValue="confirmValue"></popup-bottom>
	</view>
</template>

<script>
	import popupBottom from '../popupBottom.vue'
	import {queryAll,queryByParentId,submitExperimentProject} from '@/api/reservationList.js'
	export default {
		components: {
			popupBottom,
		},
		data() {
			return {
				oneList:[],
				first_id:null,
				twoList:[],
				sec_id:null,
				class_id: null,
				threeList: [],
				country:'',
				test_price:'',
				project_name:'',
				checkBoxTitle: null,
				checkBoxKeyName: null,
				checkEchoKey: null,
				checkBoxList: [],
				showcheckBox: false,
			}
		},
		onLoad(e) {
			queryAll().then(res=>{
				this.oneList = res.obj
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
				if (this.checkEchoKey == 'first_id') {
					queryByParentId(this.first_id).then(res=>{
						this.twoList = res.obj
					})
				}
				if (this.checkEchoKey == 'sec_id') {
					queryByParentId(this.sec_id).then(res=>{
						this.threeList = res.obj
					})
				}
				this.showcheckBox = false
			},
			submitData(){
				let data = {
					first_id:this.first_id,
					sec_id:this.sec_id,
					class_id:this.class_id,
					country:this.country,
					test_price:this.test_price,
					project_name:this.project_name,
				}
				submitExperimentProject(data).then(res=>{
					if(res.res){
						this.$tip('保存成功')
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