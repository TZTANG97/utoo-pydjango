<script>
import { resolveCatalogImage, onCatalogImgError } from "@client/utils/oss-image";

export default {
  name: "cateDetail",
  data() {
    return {
      dialog_content: null,
      missingParam: false,
    };
  },
  mounted() {
    this.loadDetail();
  },
  methods: {
    resolveCatalogImage,
    onCatalogImgError,
    loadDetail() {
      const raw = window.localStorage.getItem("cateDetail");
      if (!raw) {
        this.missingParam = true;
        this.dialog_content = null;
        return;
      }
      try {
        const parsed = JSON.parse(raw);
        if (!parsed || typeof parsed !== "object" || !parsed.name) {
          this.missingParam = true;
          this.dialog_content = null;
          return;
        }
        this.dialog_content = parsed;
        this.missingParam = false;
      } catch (_) {
        this.missingParam = true;
        this.dialog_content = null;
      }
    },
    goCate() {
      this.$router.replace({ path: "/cate" }).catch(() => {});
    },
  },
};
</script>

<template>
  <div class="container">
    <div class="cate-content" v-if="dialog_content">
      <div class="title">{{ dialog_content["name"] }}</div>
      <div class="cate-main-img">
        <img
          :src="resolveCatalogImage(dialog_content['main_photo'])"
          @error="onCatalogImgError"
          alt=""
        />
      </div>
      <div class="jj">简介：{{ dialog_content["intro"] }}</div>
      <div class="project-desc">
        <span>项目介绍：</span>
        <div v-html="dialog_content['project_details']" />
      </div>
    </div>
    <div class="missing-param" v-else-if="missingParam">
      <p>缺少分类详情参数，无法展示内容。</p>
      <el-button type="primary" @click="goCate">返回测试预约</el-button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.missing-param {
  padding-top: 120px;
  text-align: center;
  color: #666;

  p {
    margin-bottom: 20px;
    font-size: 18px;
  }
}

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
