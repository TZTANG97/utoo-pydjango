<script>
export default {
  name: "CompanyInt",
  mounted() {
    var map = new AMap.Map('map', {
      resizeEnable: true,
      center: [121.185252, 31.346588],
      zoom: 13
    });

    var marker = new AMap.Marker({
      position: map.getCenter(),
      icon: '//a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-red.png',
      anchor:'bottom-center',
      offset: new AMap.Pixel(0, 0)
    });

    marker.setMap(map);

    // 设置鼠标划过点标记显示的文字提示
    marker.setTitle('上海市嘉定区恒永路328号联东U谷嘉定国际企业港90幢102室');

    // 设置label标签
    // label默认蓝框白底左上角显示，样式className为：amap-marker-label
    marker.setLabel({
      direction:'top',
      content: "<div class='info'>上海市嘉定区恒永路328号联东U谷嘉定国际企业港90幢102室</div>", //设置文本标注内容
    });
  },
}
</script>

<template>
  <div class="container">
    <main>
      <img src="@/static/hp1.webp" alt="">
      <img src="@/static/hp2.webp" alt="">
      <img src="@/static/hp3.webp" alt="">
      <img src="@/static/hp4.webp" alt="">
      <img src="@/static/hp5.webp" alt="">
      <img src="@/static/hp6.webp" alt="">
    </main>
<!--    <header>-->
<!--      <img src="@/static/top-bg.jpg"-->
<!--           alt="">-->
<!--      <div class="overlay"></div>-->
<!--      <div class="content">-->
<!--        <div class="des">-->
<!--          愉兔的愿景与使命是建立公正、科学、准确、高效、一流的公共服务平台,为保障人类健康、安全、节能、环保而服务。-->
<!--        </div>-->
<!--      </div>-->
<!--    </header>-->
<!--    <main>-->
<!--      <div class="who">-->
<!--        <div class="title">愉兔是谁</div>-->
<!--        <div class="des">-->
<!--          <span>愉兔是集专业、科技、创新于一体的科研场所，专注于提供准确可靠的检测服务。配备行业先进的检测设备及经验丰富、专业素质高超的科研人员，测试核心工艺采用先进的自动化与智能化手段，实现了对各类样品的高精度、高速度、全方位检测分析，大幅度提升效率与数据准确性。为客户找到最佳的解决方案。</span>-->
<!--          <img src="@/static/video-cover.jpg" alt="">-->
<!--&lt;!&ndash;          <video poster="@/static/video-cover.jpg" src="https://www-file.huawei.com/-/media/corp2020/videos/corporate-information/20230505-who-is-huawei-cn-720.mp4" controls></video>&ndash;&gt;-->
<!--        </div>-->
<!--      </div>-->
<!--    </main>-->

<!--    <footer>-->
<!--      <div id="map"></div>-->
<!--      <div class="company-info">-->
<!--        <div class="title">愉兔检测科技(上海)有限公司</div>-->
<!--        <div class="info-item">地址：上海市嘉定区恒永路328号联东U谷嘉定国际企业港90幢102室</div>-->
<!--        <div class="info-item">热线：18916012783</div>-->
<!--        <div class="info-item">邮箱：jfyp@utootest.cn</div>-->
<!--        <img src="@/static/qrcode_for_gh_e8c4db1fff54_258.jpg" alt="官方公众号">-->
<!--        <div class="label">公众号</div>-->
<!--      </div>-->
<!--    </footer>-->
  </div>
</template>

<style>
.amap-icon img {
  width: 25px;
  height: 34px;
}

.amap-marker-label{
  border: 0;
  padding: 7px;
  border-radius: 4px;
  white-space: normal;
}
.info {
  width: 300px;
  font-size: 14px;
  line-height: 1.2;
}
</style>

<style scoped lang="scss">
.container {
  //padding-bottom: 100px;
  img {
    width: 100%;
    vertical-align: middle;
  }
}

footer {
  display: flex;
  margin-top: 100px;
  padding: 0 250px;
  .company-info {
    margin-left: 100px;
    .title {
      font-size: 30px;
    }
    .info-item {
      color: #999;
      margin-top: 15px;
    }

    img {
      width: 122px;
      height: 125px;
      vertical-align: top;
      margin-top: 70px;
    }

    .label {
      color: #999;
    }
  }

  #map {
    width: 760px;
    height: 430px;
  }
}

main {
  //padding: 0 250px;
  //margin-top: 80px;
  .who {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;

    video, img {
      width: 800px;
      height: 450px;
      margin-top: 30px;
    }

    .title {
      position: relative;
      font-size: 36px;
      font-weight: 600;
      padding: 10px 0;
      &::after {
        display: block;
        position: absolute;
        content: '';
        left: 0;
        bottom: 0;
        width: 60px;
        height: 2px;
        background-color: var(--mainColor);
      }
    }
    .des {
      width: 800px;
      line-height: 2;
    }
  }
}

header {
  position: relative;

  img {
    width: 100%;
    vertical-align: top;
  }

  .overlay {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, .25);
  }

  .content {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    color: #fff;
    text-align: center;
  }

  .des {
    width: 630px;
    font-size: 19px;
    margin-top: 25px;
    line-height: 2;
  }
}
</style>
