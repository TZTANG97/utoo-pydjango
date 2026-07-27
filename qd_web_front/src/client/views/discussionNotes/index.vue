<template>
  <div class="container">
<!--    <el-tabs v-model="activeName" @tab-click="handleClick" class="tab_content">-->
<!--      <el-tab-pane label="喜欢" name="1"></el-tab-pane>-->
<!--      <el-tab-pane label="收藏" name="2"></el-tab-pane>-->
<!--      <el-tab-pane label="发布" name="3"></el-tab-pane>-->
<!--    </el-tabs>-->
    <div class="tabs_box">
      <div class="tabs">
          <div class="tabs_item" :class="activeName == '1' ? 'active':''" @click="handleClick('1')">喜欢</div>
          <div class="tabs_item" :class="activeName == '2' ? 'active':''" @click="handleClick('2')">收藏</div>
          <div class="tabs_item" :class="activeName == '3' ? 'active':''" @click="handleClick('3')">发布</div>
      </div>
      <div style="height: 40px; position:relative;">
        <el-button v-if="show && activeName == '3'" class="issueBtn" size="medium" type="primary" @click="toIssue">发布</el-button>
      </div>
    </div>

    <div v-if="activeName == '1'" class="content">
      <discussionList v-if="show && activeName == '1'" :listType="1" :areaScroll="true" style="width: 100%; height: calc(100vh - 220px)"></discussionList>
    </div>
    <div v-if="activeName == '2'" class="content">
      <discussionList v-if="show && activeName == '2'" :listType="2" :areaScroll="true" style="width: 100%; height: calc(100vh - 220px)"></discussionList>
    </div>
    <div v-if="activeName == '3'" class="content">
      <discussionList v-if="show && activeName == '3'" :listType="3" :areaScroll="true" style="width: 100%; height: calc(100vh - 220px)"></discussionList>
    </div>
  </div>
</template>
<script>
import discussionList from "@client/views/discussion/components/list.vue";

export default {
  components: {discussionList},
  data() {
    return {
      activeName: '1',
      show: true
    }
  },
  methods: {
    handleClick(type) {
      this.activeName = type;
      this.show = false;
      setTimeout(() => {
        this.show = true;
      },500)
    },
    toIssue() {
      this.$router.push('/discussionNotes/issue')
    },
  }
}
</script>

<style scoped lang="scss">
.container {
  position: relative;
  background: #f5f6f8;
  min-height: 100vh;
  padding-top: 72px;
  .tab_content {
    position: absolute;
    background: #ffffff;
    left: 16px;
    right: 16px;
    top: 0;
  }
}
.content {
  padding: 0 20px 24px;
  max-width: 880px;
  margin: 0 auto;
}
.issueBtn {
  position: absolute;
  right: 0;
  top: 50px;
  z-index: 3;
}
.tabs_box {
  position: static;
  top: 0;
  background: #ffffff;
  width: 100%;
  display: flex;
  justify-content: space-between;
  .tabs {
    display: flex;
    padding: 0 20px;
    .tabs_item {
      width: 60px;
      height: 40px;
      font-size: 14px;
      display: flex;
      align-items: center;
      cursor: pointer;
      justify-content: center;
      border-bottom: 3px solid transparent;
    }
    .active {
      color:  var(--mainColor);
      border-bottom: 3px solid  var(--mainColor);
    }
  }
}

</style>
