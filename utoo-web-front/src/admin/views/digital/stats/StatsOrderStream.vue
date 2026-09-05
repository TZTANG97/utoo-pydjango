<template>
  <article class="stream" :class="streamClass">
    <header>
      <h3>{{ title }}</h3>
      <span class="badge" :class="badgeClass">{{ items.length }}</span>
    </header>
    <div
      class="stream__viewport"
      @mouseenter="paused = true"
      @mouseleave="paused = false"
    >
      <div
        v-if="items.length"
        class="stream__track"
        :class="{ 'is-scrolling': shouldScroll, 'is-paused': paused }"
        :style="trackStyle"
      >
        <div
          v-for="(row, i) in loopItems"
          :key="`${keyPrefix}-${i}`"
          class="order-row"
          :class="{ 'order-row--alert': variant === 'overdue' }"
        >
          <div class="order-row__id">{{ row.orderNum || '—' }}</div>
          <div class="order-row__cols">
            <template v-if="variant === 'doing'">
              <span>{{ row.user_name || '—' }}</span>
              <span>预计 {{ row.expect_finishtime || '—' }}</span>
              <span>开始 {{ row.start_time || '—' }}</span>
              <span>{{ row.experiment_project_name || '—' }}</span>
              <span>{{ row.line_num || '—' }}</span>
            </template>
            <template v-else-if="variant === 'overdue'">
              <span>{{ row.user_name || '—' }}</span>
              <span class="text-danger">超时 {{ row.expect_finishtime || '—' }}</span>
              <span class="text-danger">超期 {{ row.timeout_days ?? '—' }} 天</span>
              <span>{{ row.experiment_project_name || '—' }}</span>
              <span>{{ row.line_num || '—' }}</span>
            </template>
            <template v-else>
              <span>{{ row.user_name || '—' }}</span>
              <span>完成 {{ row.end_time || row.finish_time || '—' }}</span>
              <span>{{ row.experiment_project_name || '—' }}</span>
              <span>{{ row.line_num || '—' }}</span>
            </template>
          </div>
        </div>
      </div>
      <div v-else class="empty-soft">{{ emptyText }}</div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

type Row = Record<string, unknown>
type StreamVariant = 'doing' | 'overdue' | 'done'

const props = withDefaults(
  defineProps<{
    title: string
    items: Row[]
    variant: StreamVariant
    emptyText: string
    keyPrefix: string
    /** 超过该条数启用循环滚动 */
    scrollMin?: number
  }>(),
  {
    scrollMin: 4,
  },
)

const paused = ref(false)

const streamClass = computed(() => {
  if (props.variant === 'overdue') return 'stream--overdue'
  if (props.variant === 'done') return 'stream--done'
  return 'stream--doing'
})

const badgeClass = computed(() => {
  if (props.variant === 'overdue') return 'badge--danger'
  if (props.variant === 'done') return 'badge--ok'
  return ''
})

/** 数据翻倍以实现无缝循环 */
const loopItems = computed(() => {
  if (props.items.length >= props.scrollMin) {
    return [...props.items, ...props.items]
  }
  return props.items
})

const shouldScroll = computed(() => props.items.length >= props.scrollMin)

/** 约 4.5s/条，上限 120s */
const trackStyle = computed(() => {
  if (!shouldScroll.value) return undefined
  const sec = Math.min(120, Math.max(18, props.items.length * 4.5))
  return { '--scroll-duration': `${sec}s` }
})
</script>

<style scoped lang="scss">
.stream {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.78);
  min-height: 280px;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.16);
    h3 {
      margin: 0;
      font-size: 14px;
    }
  }
}

.stream--overdue {
  border-color: rgba(239, 68, 68, 0.35);
  box-shadow: inset 0 0 0 1px rgba(239, 68, 68, 0.08), 0 0 24px rgba(239, 68, 68, 0.08);
  header {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.16), transparent);
  }
}

.stream--done header {
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.12), transparent);
}
.stream--doing header {
  background: linear-gradient(90deg, rgba(14, 165, 233, 0.12), transparent);
}

.badge {
  min-width: 24px;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 12px;
  background: rgba(14, 165, 233, 0.2);
  color: #7dd3fc;
}
.badge--danger {
  background: rgba(239, 68, 68, 0.22);
  color: #fca5a5;
}
.badge--ok {
  background: rgba(16, 185, 129, 0.2);
  color: #6ee7b7;
}

.stream__viewport {
  flex: 1;
  max-height: 420px;
  overflow: hidden;
  padding: 8px;
  mask-image: linear-gradient(to bottom, transparent 0, #000 12px, #000 calc(100% - 12px), transparent 100%);
}

.stream__track.is-scrolling {
  animation: streamScroll var(--scroll-duration, 36s) linear infinite;
}

.stream__track.is-scrolling.is-paused {
  animation-play-state: paused;
}

@keyframes streamScroll {
  from {
    transform: translateY(0);
  }
  to {
    transform: translateY(-50%);
  }
}

.order-row {
  padding: 10px;
  border-radius: 10px;
  margin-bottom: 6px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid transparent;
}

.order-row--alert {
  background: rgba(239, 68, 68, 0.06);
}

.order-row__id {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 12px;
  color: #cbd5e1;
  margin-bottom: 6px;
  word-break: break-all;
}

.order-row__cols {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  font-size: 11px;
  color: #94a3b8;
}

.text-danger {
  color: #f87171 !important;
  font-weight: 600;
}

.empty-soft {
  padding: 36px 12px;
  text-align: center;
  color: #64748b;
  font-size: 13px;
  background: repeating-linear-gradient(
    -45deg,
    transparent,
    transparent 6px,
    rgba(148, 163, 184, 0.04) 6px,
    rgba(148, 163, 184, 0.04) 12px
  );
  border-radius: 10px;
}
</style>
