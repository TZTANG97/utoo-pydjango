<template>
  <div class="text-truncation">
    <!-- 文本内容容器 -->
    <div class="text-content ql-editor" :class="{ 'expanded': isExpanded }" ref="textContainer">
      <div v-if="accessory && accessory.length > 0 && !isExpanded" class="leftImageBox">
          <img
            class="leftImage"
            :src="buildOssImageUrl(accessory[0].path, accessory[0].name, accessory[0].imageUrl)"
            alt=""
            @error="onThumbError"
          />
          <div v-if="thumbBroken" class="leftImage-fallback">暂无图片</div>
      </div>
      <div style="flex: 1" :class="{
        'showImageBox': !isExpanded && accessory && accessory.length > 0
      }">
        <div v-if="accessory && accessory.length > 0 && isExpanded" style="margin-bottom: 10px">
          <carousel :slides="slides"></carousel>
        </div>
        <div v-html="initContent(content)"></div>
      </div>
    </div>
    <button
      v-if="showToggleBtn && !isExpanded"
      type="button"
      class="open-more-btn"
      @click="toggleExpand"
    >
      查看全文
      <i class="el-icon-arrow-down" />
    </button>

<!--    &lt;!&ndash; 收起按钮 &ndash;&gt;-->
<!--    <button v-if="isExpanded" class="toggle-btn fold" @click="toggleExpand">-->
<!--      收起-->
<!--    </button>-->
  </div>
</template>

<script>
import 'quill/dist/quill.core.css';
import 'quill/dist/quill.snow.css';
import 'quill/dist/quill.bubble.css';
import Carousel from "@client/views/discussion/comments/Carousel.vue";
import { buildOssImageUrl, OSS_BASE } from "@client/utils/oss-image";
export default {
  components: {Carousel},
  props: {
    // 文本内容
    content: {
      type: String,
      required: true
    },
    // 最多显示行数
    index: {
      type: Number,
      default: 2
    },
    // 最多显示行数
    accessory: {
      type: Array,
      default: () => {
        return []
      }
    }
  },
  data() {
    return {
      isExpanded: false, // 是否展开
      showToggleBtn: false, // 是否显示切换按钮
      slides: [],
      thumbBroken: false,
    };
  },
  watch: {
    // 监听内容变化，重新判断是否需要显示按钮
    content() {
      this.thumbBroken = false;
      this.$nextTick(() => {
        this.checkTextOverflow();
      });
    },
    accessory() {
      this.thumbBroken = false;
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.checkTextOverflow();
    })
    // 初始判断

  },
  methods: {
    buildOssImageUrl,
    onThumbError(e) {
      this.thumbBroken = true;
      if (e && e.target) {
        e.target.style.display = "none";
      }
    },
    initContent(text) {
      if(text) {
        let str = decodeURIComponent(text);
        let str1 = str.replaceAll(/%25/g, '%');
        text = str1.replaceAll('<img', '<img style="width: 300px; display: block;margin: 0 auto;"');
        // 正文里历史 UAT 静态域名的图片改为 OSS（与 Java 讨论区一致）
        text = text.replaceAll('https://uat.utoo.laide.tech/', `${OSS_BASE}/`);
        text = text.replaceAll('http://uat.utoo.laide.tech/', `${OSS_BASE}/`);
        return text
      } else {
        return ''
      }
    },
    getContent(content) {
      if(content.length < 120) {
        return content
      } else {
        let text = content.slice(0, 120)
        text += '...';
        return text
      }
    },
    // 检查文本是否超出限制行数
    checkTextOverflow() {
      const container = this.$refs.textContainer;
      if (!container) return;
      // 比较实际高度和可见高度判断是否溢出
      if(container.scrollHeight > 150) {
        this.showToggleBtn = true;
      } else {
        this.showToggleBtn = false;
      }
    },

    // 切换展开/收起状态
    toggleExpand() {
      this.$emit('openText', this.index)
      this.isExpanded = !this.isExpanded;
      if(this.accessory && this.accessory.length > 0) {
        let data = []
        this.accessory.forEach(ite => {
          data.push({
            imageUrl: buildOssImageUrl(ite.path, ite.name, ite.imageUrl),
            altText: ''
          })
        })
        this.slides = data;
      }
      this.$forceUpdate();
    }
  }
};
</script>

<style scoped>
.text-truncation {
  position: relative;
}
.showImageBox {
  width: 700px;
}
.text-content {
  color: #434343;
  font-size: 15px;
  line-height: 1.65;
  max-height: 150px;
  overflow: hidden;
  padding: 0;
  display: flex;
}
.leftImageBox {
  position: relative;
  margin-right: 14px;
  flex-shrink: 0;
  width: 148px;
  height: 110px;
  border-radius: 10px;
  overflow: hidden;
  background: #f3f4f6;
}
.leftImage {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.leftImage-fallback {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #a8abb2;
  background: #f3f4f6;
}

/* 展开状态样式 */
.text-content.expanded {
  max-height: initial;
}


.open-more-btn {
  display: block;
  margin: 12px auto 0;
  padding: 0;
  border: none;
  background: none;
  color: var(--mainColor);
  font-size: 14px;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

/* 收起按钮样式 */
.toggle-btn.fold {
  color: var(--mainColor);
}
.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=SimHei]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=SimHei]::before {
  content: "黑体";
  font-family: "SimHei";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=Microsoft-YaHei]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=Microsoft-YaHei]::before {
  content: "微软雅黑";
  font-family: "Microsoft YaHei";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=KaiTi]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=KaiTi]::before {
  content: "楷体";
  font-family: "KaiTi";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=FangSong]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=FangSong]::before {
  content: "仿宋";
  font-family: "FangSong";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=Arial]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=Arial]::before {
  content: "Arial";
  font-family: "Arial";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=Times-New-Roman]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=Times-New-Roman]::before {
  content: "Times New Roman";
  font-family: "Times New Roman";
}

.ql-snow .ql-picker.ql-font .ql-picker-label[data-value=sans-serif]::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value=sans-serif]::before {
  content: "sans-serif";
  font-family: "sans-serif";
}

.ql-font-SimSun {
  font-family: "SimSun";
}

.ql-font-SimHei {
  font-family: "SimHei";
}

.ql-font-Microsoft-YaHei {
  font-family: "Microsoft YaHei";
}

.ql-font-KaiTi {
  font-family: "KaiTi";
}

.ql-font-FangSong {
  font-family: "FangSong";
}

.ql-font-Arial {
  font-family: "Arial";
}

.ql-font-Times-New-Roman {
  font-family: "Times New Roman";
}

.ql-font-sans-serif {
  font-family: "sans-serif";
}

/* 字号设置 */
/* 默认字号 */
.ql-snow .ql-picker.ql-size .ql-picker-label::before,
.ql-snow .ql-picker.ql-size .ql-picker-item::before {
  content: "16px";
}

/*.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="12px"]::before,*/
/*.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="12px"]::before {*/
/*  content: "12px";*/
/*  font-size: 12px;*/
/*}*/
/*.ql-size-12px {*/
/*  font-size: 14px;*/
/*}*/

/*.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="14px"]::before,*/
/*.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="14px"]::before {*/
/*  content: "14px";*/
/*  font-size: 14px;*/
/*}*/

/*.ql-size-14px {*/
/*  font-size: 14px;*/
/*}*/

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="16px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="16px"]::before {
  content: "16px";
  font-size: 16px;
}

.ql-size-16px {
  font-size: 16px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="18px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="18px"]::before {
  content: "18px";
  font-size: 18px;
}

.ql-size-18px {
  font-size: 18px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="20px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="20px"]::before {
  content: "20px";
  font-size: 20px;
}

.ql-size-20px {
  font-size: 20px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="22px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="22px"]::before {
  content: "22px";
  font-size: 22px;
}

.ql-size-22px {
  font-size: 22px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="26px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="26px"]::before {
  content: "26px";
  font-size: 26px;
}

.ql-size-26px {
  font-size: 26px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="28px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="28px"]::before {
  content: "28px";
  font-size: 28px;
}

.ql-size-28px {
  font-size: 28px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="30px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="30px"]::before {
  content: "30px";
  font-size: 30px;
}

.ql-size-30px {
  font-size: 30px;
}

.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="34px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="34px"]::before {
  content: "34px";
  font-size: 34px;
}

.ql-size-34px {
  font-size: 34px;
}


.ql-snow .ql-picker.ql-size .ql-picker-label[data-value="36px"]::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value="36px"]::before {
  content: "36px";
  font-size: 36px;
}

.ql-size-36px {
  font-size: 36px;
}



</style>
