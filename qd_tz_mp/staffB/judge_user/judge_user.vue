<template>
	<view class="container">
		
	</view>
</template>

<script>
	export default {
		onLoad(options) {
			const is_login = uni.getStorageSync('userInfo');
			if(!is_login) uni.redirectTo({
				url: '/pages/login/login'
			})
			const { package_name, path_name, id } = options
			uni.redirectTo({
				url: `/${package_name}/${path_name}/${path_name}?id=${id}`
			})
		},
		methods: {
			
		}
	}
</script>

<style>

</style>
