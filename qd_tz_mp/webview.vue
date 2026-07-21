<template>
	<web-view :src="src"></web-view>
</template>

<script>
	export default {
		data() {
			return {
				src: ''
			}
		},
		onLoad({ src = '' }) {
			this.src = src
		},
		methods: {
			
		}
	}
</script>

<style>

</style>
