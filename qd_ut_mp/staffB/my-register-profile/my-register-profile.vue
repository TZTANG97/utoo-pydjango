<template>
	<view class="container">

	</view>
</template>

<script>
	export default {
		data() {
			return {

			};
		},
		onLoad() {
			const userType = uni.getStorageSync('userInfo')['userType'];
			if (!userType) {
				uni.navigateTo({
					url: '/staffB/choose_identity/choose_identity'
				})
			} else {
				// 1个人 2企业
				// get_data：获取认证数据展示
				let url = '/staffB/personal_cert/personal_cert?get_data=1'
				if (userType === 2) {
					url = '/staffB/enterprise_cert/enterprise_cert'
				}
				uni.navigateTo({
					url
				})
			}
		},
	}
</script>

<style lang="scss">

</style>