<template>
	<view class="container">
		<uni-section title="综合评价" type="line">
			<uni-rate v-model="rateValue" activeColor="#E96302" />
		</uni-section>
		<uni-section title="评价内容" type="line" padding>
			<textarea v-model="evaluate_content" placeholder="请输入评价内容" maxlength="120" />
		</uni-section>

		<view class="main-btn" @click="submitEvaluate">
			提&nbsp;交
		</view>
	</view>
</template>

<script>
	import {
		submitEvaluateApi
	} from '@/api/index.js'
	export default {
		data() {
			return {
				rateValue: 5,
				evaluate_content: '',
				id: ''
			}
		},
		onLoad({
			id
		}) {
			if (id) this.id = id
		},
		methods: {
			submitEvaluate() {
				if (!this.evaluate_content) return this.$toast('请填写评价内容')
				submitEvaluateApi({
					id: this.id,
					star: this.rateValue,
					content: this.evaluate_content
				}).then(res => {
					if (res.res) {
						uni.redirectTo({
							url: '/staffB/result/result?title=评价成功'
						})
						uni.$_emit('finishEval', this.id)
					} else {
						this.$toast(res.resMsg)
					}
				})
			}
		}
	}
</script>


<style lang="scss">
	.uni-rate {
		padding-left: 15rpx !important;
	}

	.uni-section-header__decoration {
		background-color: $primary !important;
	}
</style>

<style scoped>
	textarea {
		border: 3rpx solid rgba(233, 99, 2, .6);
		border-radius: 10rpx;
		padding: 10rpx;
		box-sizing: border-box;
		width: 100%;
	}

	.container {
		padding: 0 30rpx;
	}
</style>