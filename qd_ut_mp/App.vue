<script>
	export default {
		onLaunch() {
		}
	};
</script>

<style lang="scss">
	@import "uview-ui/index.scss";
	@import "@/layout/common.scss";
  page {
    background: #f9f9f9;
  }
  .search-box {
    position: relative;

    .search-icon {
      position: absolute;
      left: 20rpx;
      top: 18rpx;
    }

    .my-search-input {
      height: 60rpx;
      background-color: #f2f2f2;
      line-height: 60rpx;
      border-radius: 40rpx;
      box-sizing: border-box;
      padding: 0 20rpx 0 60rpx;
      font-size: 26rpx;
    }
  }

</style>
