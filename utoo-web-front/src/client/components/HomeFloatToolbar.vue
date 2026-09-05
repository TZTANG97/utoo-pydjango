<script setup>
import {
  ChatDotRound,
  Headset,
  EditPen,
  Top,
} from "@element-plus/icons-vue";

defineProps({
  backTopDisabled: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["system", "service", "feedback", "back-top"]);
</script>

<template>
  <aside class="home-float-toolbar" aria-label="快捷操作">
    <el-tooltip content="系统消息" placement="left" :show-after="200">
      <button type="button" class="toolbar-btn" @click="$emit('system')">
        <el-icon :size="20"><ChatDotRound /></el-icon>
        <span class="toolbar-label">消息</span>
      </button>
    </el-tooltip>

    <el-tooltip content="在线客服" placement="left" :show-after="200">
      <button type="button" class="toolbar-btn" @click="$emit('service')">
        <el-icon :size="20"><Headset /></el-icon>
        <span class="toolbar-label">客服</span>
      </button>
    </el-tooltip>

    <el-tooltip content="意见反馈" placement="left" :show-after="200">
      <button type="button" class="toolbar-btn" @click="$emit('feedback')">
        <el-icon :size="20"><EditPen /></el-icon>
        <span class="toolbar-label">反馈</span>
      </button>
    </el-tooltip>

    <div class="toolbar-divider" />

    <el-tooltip content="回到顶部" placement="left" :show-after="200">
      <button
        type="button"
        class="toolbar-btn toolbar-btn--top"
        :class="{ 'is-disabled': backTopDisabled }"
        :disabled="backTopDisabled"
        @click="$emit('back-top')"
      >
        <el-icon :size="20"><Top /></el-icon>
        <span class="toolbar-label">顶部</span>
      </button>
    </el-tooltip>
  </aside>
</template>

<style scoped lang="scss">
.home-float-toolbar {
  position: fixed;
  right: 24px;
  /* 贴右下，避开首页轮播垂直居中的左右箭头 */
  top: auto;
  bottom: 48px;
  transform: none;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 8px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(233, 99, 2, 0.12);
  box-shadow:
    0 8px 32px rgba(233, 99, 2, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(12px);
}

.toolbar-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  width: 52px;
  height: 52px;
  padding: 0;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--mainColor);
  cursor: pointer;
  transition:
    background 0.22s ease,
    color 0.22s ease,
    transform 0.22s ease,
    box-shadow 0.22s ease;

  &:hover:not(.is-disabled):not(:disabled) {
    background: linear-gradient(135deg, #fff4eb 0%, #ffe8d6 100%);
    color: #c95500;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(233, 99, 2, 0.18);
  }

  &:active:not(.is-disabled):not(:disabled) {
    transform: translateY(0);
  }

  &.is-disabled,
  &:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  &--top:not(.is-disabled):not(:disabled) {
    color: #606266;
  }
}

.toolbar-label {
  font-size: 11px;
  line-height: 1;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.toolbar-divider {
  height: 1px;
  margin: 2px 6px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(233, 99, 2, 0.2),
    transparent
  );
}
</style>
