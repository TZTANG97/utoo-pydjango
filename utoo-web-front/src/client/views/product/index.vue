<script>
export default {
  data() {
    return {
      productList: []
    }
  },
  methods: {},
  mounted() {
    for (let i = 0; i < 20; i++) {
      this.productList.push({
        deviceIcon: 'https://qgongye.oss-cn-shanghai.aliyuncs.com/goods/33ebe2cf-1ba0-4833-b6b0-27ac95e57213.png',
        deviceName: '日本PHOTRON 高速摄像机-UX系列日本PHOTRON 高速摄像机-UX系列日本PHOTRON 高速摄像机-UX系列日本PHOTRON 高速摄像机-UX系列日本PHOTRON 高速摄像机-UX系列',
        referencePrice: 3000
      })
    }
  }
}
</script>

<template>
  <div class="product-list">
    <div v-for="(item, idx) in productList" :key="idx" class="product-item">
      <div class="control-box">
        <img :src="item['deviceIcon']" :alt="item['deviceName']" class="device-icon">
      </div>
      <div class="device-info">
        <div class="device-name">
          {{ item['deviceName'] }}
        </div>
        <div class="device-desc">
          大功率，更高效
        </div>
      </div>
      <!--        <div class="reference-price">统一参考价：{{ item['price'] }}</div>-->
    </div>
  </div>
</template>

<style scoped lang="scss">
.product-list {
  display: flex;
  flex-wrap: wrap;
  width: 1037px;
  margin: 60px auto 0;
  overflow: hidden;

  .product-item {
    cursor: pointer;
    margin: 50px 0 0 15px;
    transition: all .3s linear;
    padding: 10px;
    background-color: #fff;
    width: 248px;
    overflow: hidden;

    .control-box {
      width: 228px;
      height: 214px;
      overflow: hidden;

      .device-icon {
        width: 100%;
        height: 100%;
        vertical-align: middle;
        transition: all .3s linear;
      }
    }

    &:hover {
      box-shadow: 0 15px 30px rgba(0, 0, 0, .3);
      //transform: translate3d(0, -2px, 0);

      .device-icon {
        transform: scale(1.1);
      }
    }

    .device-info {
      box-sizing: border-box;
      padding: 15px 10px;

      .device-name, .device-desc {
        text-align: center;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
      }

      .device-desc {
        font-size: 14px;
        color: #b0b0b0;
        margin-top: 10px;
      }
    }


    &:nth-child(4n+1) {
      margin-left: 0;
    }
  }
}

</style>
<style>
.body {
  background-color: #F5F5F5;
}
</style>
