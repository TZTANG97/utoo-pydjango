<template>
  <div class="carousel-container" @mouseenter="pauseAutoPlay" @mouseleave="startAutoPlay">
    <!-- 轮播图片容器 -->
    <div
      class="carousel-slides"
      :style="{ transform: `translateX(-${currentIndex * 100}%)`, transition: transitionDuration }"
    >
      <div
        class="carousel-slide"
        v-for="(slide, index) in slides"
        :key="index"
      >
        <img
          :src="slide.imageUrl"
          :alt="slide.altText"
          class="carousel-image"
        >
        <div class="slide-caption" v-if="slide.caption">
          {{ slide.caption }}
        </div>
      </div>
    </div>

    <!-- 前一张/后一张按钮 -->
    <button
      class="carousel-control prev"
      @click="prevSlide"
      aria-label="Previous slide"
    >
      <i class="el-icon-arrow-left"></i>
    </button>
    <button
      class="carousel-control next"
      @click="nextSlide"
      aria-label="Next slide"
    >
      <i class="el-icon-arrow-right"></i>
    </button>

    <!-- 指示器 -->
    <div class="carousel-indicators">
      <button
        v-for="(slide, index) in slides"
        :key="index"
        class="indicator"
        :class="{ active: index === currentIndex }"
        @click="goToSlide(index)"
        :aria-label="`Go to slide ${index + 1}`"
      ></button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Carousel',
  props: {
    // 轮播图数据
    slides: {
      type: Array,
      validator: (value) => {
        return []
      }
    },
    // 自动播放间隔时间(毫秒)
    interval: {
      type: Number,
      default: 5000
    },
    // 过渡动画持续时间(毫秒)
    duration: {
      type: Number,
      default: 500
    }
  },
  data() {
    return {
      currentIndex: 0,
      timer: null
    };
  },
  computed: {
    // 计算过渡动画样式
    transitionDuration() {
      return this.duration > 0 ? `${this.duration}ms` : 'none';
    }
  },
  mounted() {
    this.startAutoPlay();
  },
  beforeUnmount() {
    this.pauseAutoPlay();
  },
  methods: {
    // 下一张
    nextSlide() {
      this.currentIndex = (this.currentIndex + 1) % this.slides.length;
    },

    // 上一张
    prevSlide() {
      this.currentIndex = (this.currentIndex - 1 + this.slides.length) % this.slides.length;
    },

    // 跳转到指定幻灯片
    goToSlide(index) {
      if (index !== this.currentIndex) {
        this.currentIndex = index;
      }
    },

    // 开始自动播放
    startAutoPlay() {
      if (this.interval > 0) {
        this.timer = setInterval(() => {
          this.nextSlide();
        }, this.interval);
      }
    },

    // 暂停自动播放
    pauseAutoPlay() {
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
    }
  }
};
</script>

<style scoped>
.carousel-container {
  position: relative;
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.carousel-slides {
  display: flex;
  width: 100%;
  height: 100%;
}

.carousel-slide {
  min-width: 100%;
  position: relative;
}

.carousel-image {
  width: 100%;
  height: 400px;
  object-fit: contain;
  display: block;
}

.slide-caption {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 1rem;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  color: white;
  font-size: 1.2rem;
}

.carousel-control {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background-color: rgba(0, 0, 0, 0.3);
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.3s ease;
  z-index: 10;
}

.carousel-control:hover {
  background-color: rgba(0, 0, 0, 0.6);
}

.prev {
  left: 1rem;
}

.next {
  right: 1rem;
}

.carousel-indicators {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.5rem;
  z-index: 10;
}

.indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: none;
  background-color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.indicator.active {
  background-color: white;
  width: 30px;
  border-radius: 5px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .carousel-image {
    height: 300px;
  }

  .carousel-control {
    width: 40px;
    height: 40px;
  }
}

@media (max-width: 480px) {
  .carousel-image {
    height: 200px;
  }

  .slide-caption {
    font-size: 1rem;
    padding: 0.5rem;
  }
}
</style>
