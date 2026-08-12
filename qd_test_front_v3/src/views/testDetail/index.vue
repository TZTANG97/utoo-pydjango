<script>
import { getTestDetailApi } from "@/api/test";
import subTest from "@/components/subTest.vue";
import sampleInfo from "@/components/sampleInfo.vue";
import SubTestAll from "@/components/subTestAll.vue";
import {mapGetters} from "vuex";

export default {
  name: "testDetail",
  components: {SubTestAll, subTest, sampleInfo },
  data() {
    return {
      openDialog: {
        show: false,
        type: 0,
      },
      testDetail: null,
      test_id: "",
      special_type: null,
      yyObj: {},
    };
  },
  computed: {
    ...mapGetters(["name", "mobile", "authInfo"]),
  },
  mounted() {
    this.test_id = this.$route["params"]["id"];
    getTestDetailApi(this.test_id).then((res) => {
      if (res.res) {
        this.special_type = res.obj.special_type;
        this.testDetail = res.obj;
        this.testDetail["app_project_details"]
          ? (this.testDetail["app_project_details"] = this.testDetail[
              "app_project_details"
            ].replace(/<img/g, '<img style="width: 100%"'))
          : "";
        console.log(this.testDetail["app_project_details"]);
      } else {
        this.$notify.error(res.resMsg);
      }
    });
  },
  methods: {
    // 开始预约
    subTest() {
      if (!this.name) {
        this.$confirm("是否前往登录?", "提示", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        }).then(() => {
          this.$router.push("/login");
        });
        return;
      }
      this.openDialog.show = true;
      this.openDialog.type = this.special_type == 1 ? 0 : 1;
    },
    // 下一步操作
    nextStep(obj) {
      this.subTest(false);
      this.yyObj = obj;
    },
    // 关闭弹窗方发
    openDialogClose() {
      this.openDialog.show = false;
      this.openDialog.type = 2;
    },
  },
};
</script>

<template>
  <div class="test-detail" v-if="testDetail">
    <el-carousel trigger="click" height="500px" :interval="7000">
      <el-carousel-item
        v-for="(item, idx) in testDetail['manage_photos']"
        :key="idx"
      >
        <img :src="item" alt="" />
      </el-carousel-item>
    </el-carousel>

    <div class="book-action">
      <el-button
        size="medium"
        type="primary"
        @click="subTest()"
      >立即预约</el-button>
    </div>
    <div class="test-desc" v-html="testDetail['app_project_details']" style="margin-top: 70px" />
    <sub-test-all
      v-if="special_type == 1"
      @nextStep="nextStep"
      :open-dialog.sync="openDialog"
      :test-id="test_id" :special_type="special_type"
      :test-name="testDetail['name']"
      @openDialogClose="openDialogClose">
    </sub-test-all>

<!--    <sample-info-->
<!--      :special_type="special_type"-->
<!--      :open-dialog="openDialog"-->
<!--      @openDialogClose="openDialogClose"-->
<!--      :yyObj="yyObj"-->
<!--    ></sample-info>-->
    <sub-test
      v-if="special_type != 1"
      @nextStep="nextStep"
      :open-dialog.sync="openDialog"
      :test-id="test_id"
      :test-name="testDetail['name']"
      @openDialogClose="openDialogClose"
    ></sub-test>
  </div>
</template>

<style scoped lang="scss">
.book-action {
  margin: 40px 0 50px;
  text-align: center;
}

.el-button {
  width: 160px;
  height: 54px;
  font-size: 18px;
}

.test-desc {
  color: #999;
  line-height: 1.8;
  text-align: left;
}

img {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  max-height: 500px;
}

.test-detail {
  width: 1037px;
  margin: 70px auto 0;
  text-align: center;
}
</style>
