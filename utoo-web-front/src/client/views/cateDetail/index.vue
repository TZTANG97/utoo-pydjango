<script>
export default {
  name: "cateDetail",
  data() {
    return {
      dialog_content: ''
    }
  },
  mounted() {
    const cateDetail = window.localStorage.getItem('cateDetail');
    if (cateDetail) {
      this.dialog_content = JSON.parse(cateDetail)
    }
  },
}
</script>

<template>
  <div class="container">
    <div class="cate-content" v-if="dialog_content">
      <div class="title">{{ dialog_content['name'] }}</div>
      <div class="cate-main-img">
        <img :src="dialog_content['main_photo']" alt="">
      </div>
      <div class="jj">
        简介：{{ dialog_content['intro'] }}
      </div>
      <div class="project-desc">
        <span>项目介绍：</span>
        <div v-html="dialog_content['project_details']"/>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.cate-content {

  .title {
    font-size: 35px;
  }

  padding-top: 80px;
  width: 40%;
  margin: auto;

  .project-desc {
    margin-top: 30px;
  }


  .jj {
    margin-top: 20px;
    line-height: 1.7;
  }

  .cate-main-img {
    text-align: center;
    margin-top: 30px;

    img {
      max-width: 300px;
    }
  }
}
</style>
