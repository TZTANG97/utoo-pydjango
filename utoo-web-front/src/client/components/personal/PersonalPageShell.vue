<template>
  <div class="pc-page">
    <header class="pc-page__hero">
      <div class="pc-page__hero-main">
        <div class="pc-page__icon" v-if="icon">
          <svg-icon :icon-class="icon" />
        </div>
        <div class="pc-page__titles">
          <h1 class="pc-page__title">{{ title }}</h1>
          <p v-if="subtitle" class="pc-page__subtitle">{{ subtitle }}</p>
        </div>
      </div>
      <div v-if="$slots.extra" class="pc-page__extra">
        <slot name="extra" />
      </div>
    </header>

    <div v-if="$slots.toolbar" class="pc-page__toolbar">
      <slot name="toolbar" />
    </div>

    <section :class="bare ? 'pc-page__body' : 'pc-page__card'" v-loading="loading">
      <slot />
    </section>
  </div>
</template>

<script>
export default {
  name: 'PersonalPageShell',
  props: {
    title: { type: String, default: '' },
    subtitle: { type: String, default: '' },
    icon: { type: String, default: '' },
    loading: { type: Boolean, default: false },
    bare: { type: Boolean, default: false },
  },
}
</script>

<style scoped lang="scss">
.pc-page {
  width: 100%;
  margin: 0 auto;
  animation: pc-fade-in 0.35s ease;
}

.pc-page__hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #ffffff 0%, #fffaf6 100%);
  border: 1px solid #e8edf5;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.pc-page__hero-main {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.pc-page__icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(233, 99, 2, 0.12);
  color: var(--mainColor, #e96302);
  font-size: 22px;
}

.pc-page__title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.3;
}

.pc-page__subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.pc-page__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 14px 20px;
  background: #fff;
  border: 1px solid #e8edf5;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}

.pc-page__card {
  padding: 8px 20px 24px;
  background: #fff;
  border: 1px solid #e8edf5;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  min-height: 320px;
}

.pc-page__body {
  min-height: 320px;
}

@keyframes pc-fade-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

