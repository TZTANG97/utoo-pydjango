<template>
	<!-- 该组件主要用来  用于订单的收款和开票 -->
	<view class="collection">
		<u-popup @close="closedPopup" width="80%" border-radius="10" v-model="show" mode="center"
			:mask-close-able="false">
			<view class="wrapper">
				<view class="title">
					{{ keyWord }}
				</view>
				<u-icon class="close-icon" name="close" @click="closePopup"></u-icon>
				<view class="submit-info">
					<view class="option" v-if="keyWord !== '下单'">
						<view class="label">金额：</view>
						<input type="digit" :placeholder="`请输入${keyWord}金额`" v-model.number.lazy="money">
					</view>
					<view class="option" v-if="keyWord !== '下单'">
						<view class="label">{{ `${keyWord}` }}时间：</view>
						<input type="text" @click="showCalendar = true" :placeholder="`请选择${keyWord}时间`" disabled
							v-model="date">
					</view>
					<view class="option">
						<view class="label label-1">
							<span>附件：</span>
							<span v-if="!single || (single && !fileList[0])" class="upload"
								@click="uploadFile">上传</span>
							<span v-else></span>
						</view>
						<view class="file-list">
							<view class="file-item" v-for="(item, idx) in fileList" :key="item.id">
								<text class="file-name oh" @click="preFile(idx)">{{ item.name }}</text>
								<text class="del" @click="delFile(idx)">删除</text>
							</view>
						</view>
						<upload-progress ref="prg"></upload-progress>
					</view>
				</view>
				<view class="submit-btn" @click="submitInfo">提交</view>
			</view>
		</u-popup>
		<u-toast ref="uToast" />
		<u-calendar btn-type="warning" max-date="2222-01-01" active-bg-color="#3C8BDB !important" v-model="showCalendar"
			mode="date" @change="confirmDate"></u-calendar>
	</view>
</template>

<script>
	import uploadProgress from './uploadProgress.vue'
	export default {
		name: "collection",
		components: {
			uploadProgress
		},
		props: {
			show: {
				type: Boolean,
				default: false
			},
			keyWord: {
				type: String,
				default: '收款'
			},

			single: {
				type: Boolean,
				default: true
			}
		},
		data() {
			return {
				showCalendar: false,
				money: '',
				date: '',
				fileList: []
			};
		},
		methods: {

			// 关闭弹框之后
			closedPopup() {
				this.money = ''
				this.date = ''
				this.fileList = []
			},

			// 预览文件
			preFile(idx) {
				const newArr = this.fileList.map(item => item.path + '/' + item.name)
				this.$preFile(idx, newArr)
			},

			// 删除文件
			delFile(idx) {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定删除该文件？',
					success(res) {
						if (res.confirm) {
							that.fileList.splice(idx, 1)
						}
					}
				})
			},

			// 上传文件
			uploadFile() {
				this.$uploadFile2(this.$refs['prg']).then(res => {
					this.fileList.push(res);
				})
			},

			// 提交信息
			submitInfo() {
				let {
					money,
					date,
					fileList,
					keyWord
				} = this
				if (keyWord != '下单') {
					if (!money) return this.$tip('请输入金额')
					if (!date) return this.$tip('请选择时间')
				}
				fileList = fileList.map(item => item.id).join(',')
				this.$emit('getValue', {
					money,
					date,
					fileList,
				})
			},

			// 确认日期
			confirmDate(e) {
				const date = new Date()
				let hour = date.getHours();
				hour = hour < 10 ? '0' + hour : hour
				let min = date.getMinutes();
				min = min < 10 ? '0' + min : min
				let second = date.getSeconds();
				second = second < 10 ? '0' + second : second
				this.date = `${e.result} ${hour}:${min}:${second}`
			},

			// 关闭弹窗
			closePopup() {
				this.$emit('update:show', false)
			}
		}
	}
</script>
<style lang="scss" scoped>
	.wrapper {
		position: relative;
		padding: 20rpx 30rpx;
		overflow: scroll;

		.file-item {
			display: flex;
			justify-content: space-between;

			.del {
				color: #f00;
			}
		}

		.file-name {
			width: 200rpx;
		}

		.upload {
			color: $primary;
		}

		.label-1 {
			display: flex;
			justify-content: space-between;
		}

		.label {
			margin-bottom: 10rpx;
		}

		.submit-btn {
			width: 100%;
			height: 60rpx;
			text-align: center;
			color: #fff;
			background-color: $primary;
			line-height: 60rpx;
			border-radius: 10rpx;
			margin-top: 50rpx;
		}

		.option {
			margin-top: 15rpx;
		}


		.close-icon {
			position: absolute;
			right: 25rpx;
			top: 25rpx;
		}

		.title {
			text-align: center;
			font-size: 32rpx;
			font-weight: bold;
			// margin-top: 10rpx;
		}
	}
</style>
<style>
	.u-btn--warning {
		border-color: #3C8BDB !important;
		background-color: #3C8BDB !important;
	}
</style>
