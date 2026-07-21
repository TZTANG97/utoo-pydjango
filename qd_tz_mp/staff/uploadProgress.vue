<template>
	<view class="upload-progress" v-if="progressBar">
		<progress class="progress" border-radius="7" :percent="progressBar" show-info stroke-width="10"
			activeColor="#3C8BDB" />
		<view class="cancel-btn" @click="cancelUpload">
			取消
			<!-- <u-icon name="close"></u-icon> -->
		</view>
	</view>
</template>

<script>
	export default {
		name: "uploadProgress",
		data() {
			return {
				progressBar: 0,
				uploading: false
			};
		},
		methods: {
			cancelUpload() {
				const that = this
				uni.showModal({
					title: '提示',
					content: '确定取消上传？',
					success(res) {
						if (res.confirm) {
							if(that.$uploadTask) {
								that.$uploadTask.abort()
							} else {
								that.$tip('取消失败，文件已上传')
							}
							that.uploading = false
						}
					}
				})
			},
		}
	}
</script>

<style scoped>
	.cancel-btn {
		width: 10%;
		text-align: right;
	}

	.progress {
		width: 90%;
	}

	.upload-progress {
		display: flex;
		padding: 0 10rpx;
	}
</style>
