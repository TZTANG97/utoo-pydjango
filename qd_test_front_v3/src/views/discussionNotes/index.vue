<template>
  <div class="notes-page">
    <div class="notes-shell">
      <header class="notes-hero">
        <div class="notes-hero__text">
          <h1 class="notes-hero__title">喜欢收藏</h1>
          <p class="notes-hero__desc">管理你点过喜欢、收藏过的讨论，以及自己发布的帖子</p>
        </div>
        <el-button
          v-if="activeName === '3'"
          class="notes-hero__cta"
          type="primary"
          @click="toIssue"
        >
          发布帖子
        </el-button>
      </header>

      <div class="notes-panel">
        <nav class="segmented" role="tablist">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            type="button"
            role="tab"
            class="segmented__item"
            :class="{ 'is-active': activeName === tab.value }"
            :aria-selected="activeName === tab.value"
            @click="handleClick(tab.value)"
          >
            <span class="segmented__label">{{ tab.label }}</span>
            <span class="segmented__hint">{{ tab.hint }}</span>
          </button>
        </nav>

        <div class="notes-feed">
          <discussionList
            :key="'notes-' + activeName"
            :list-type="Number(activeName)"
            :area-scroll="true"
            class="notes-feed__list"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import discussionList from "@/views/discussion/components/list.vue";

export default {
  name: "DiscussionNotes",
  components: { discussionList },
  data() {
    return {
      activeName: "1",
      tabs: [
        { value: "1", label: "喜欢", hint: "我点过的" },
        { value: "2", label: "收藏", hint: "稍后看" },
        { value: "3", label: "发布", hint: "我的帖子" },
      ],
    };
  },
  methods: {
    handleClick(type) {
      if (this.activeName === type) return;
      this.activeName = type;
    },
    toIssue() {
      this.$router.push("/discussionNotes/issue");
    },
  },
};
</script>

<style scoped lang="scss">
/* 撑满 app-main，禁止外层再出滚动条；只让列表区域滚动 */
.notes-page {
  height: 100%;
  width: 100%;
  min-height: 0;
  padding: 16px 20px 16px;
  background: linear-gradient(180deg, #f7f8fa 0%, #eef1f5 100%);
  box-sizing: border-box;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.notes-shell {
  width: 100%;
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.notes-hero {
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
  padding: 18px 22px;
  border-radius: 14px;
  color: #fff;
  background:
    radial-gradient(circle at 88% 18%, rgba(255, 255, 255, 0.22), transparent 42%),
    linear-gradient(135deg, var(--mainColor) 0%, #ff8a3d 100%);
  box-shadow: 0 8px 22px rgba(233, 99, 2, 0.18);
}

.notes-hero__title {
  margin: 0;
  font-size: 22px;
  font-weight: 650;
  letter-spacing: 0.02em;
}

.notes-hero__desc {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.92;
}

.notes-hero__cta {
  flex-shrink: 0;
  border: none;
  background: #fff;
  color: var(--mainColor);
  font-weight: 600;

  &:hover,
  &:focus {
    background: #fff7f0;
    color: var(--mainColor);
  }
}

.notes-panel {
  width: 100%;
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 14px rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.segmented {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 8px;
  padding: 14px 16px 12px;
  background: #fff;
  border-bottom: 1px solid #f0f2f5;
}

.segmented__item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 2px;
  min-width: 120px;
  min-height: 52px;
  padding: 10px 18px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: #f7f8fa;
  color: #595959;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease,
    box-shadow 0.18s ease, transform 0.18s ease;

  &:hover {
    background: #f0f2f5;
    color: #303133;
  }

  &.is-active {
    color: var(--mainColor);
    background: rgba(233, 99, 2, 0.08);
    border-color: rgba(233, 99, 2, 0.18);
    box-shadow: inset 0 0 0 1px rgba(233, 99, 2, 0.06);
  }

  &:active {
    transform: scale(0.98);
  }
}

.segmented__label {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.2;
}

.segmented__hint {
  font-size: 12px;
  opacity: 0.72;
}

.notes-feed {
  flex: 1;
  min-height: 0;
  padding: 16px 20px 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.notes-feed__list {
  width: 100%;
  flex: 1;
  min-height: 0;
  height: 100%;
}

@media (max-width: 720px) {
  .notes-page {
    padding: 12px;
  }

  .notes-hero {
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
  }

  .notes-hero__cta {
    width: 100%;
  }

  .segmented {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
  }

  .segmented__item {
    min-width: 0;
    align-items: center;
    padding: 10px 8px;
  }

  .segmented__hint {
    display: none;
  }

  .notes-feed {
    padding: 12px;
  }
}
</style>
