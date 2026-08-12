<script>
export default {
  name: "CompanyInt",
  // 地图区块已下线；不再初始化高德，避免新标签页白等外网脚本
}
</script>

<template>
  <div class="container">
    <main>
      <img src="@/static/hp1.webp" alt="愉兔检测" fetchpriority="high" />
      <img src="@/static/hp2.webp" alt="" loading="lazy" decoding="async" />
      <img src="@/static/hp3.webp" alt="" loading="lazy" decoding="async" />
      <img src="@/static/hp4.webp" alt="" loading="lazy" decoding="async" />
      <img src="@/static/hp5.webp" alt="" loading="lazy" decoding="async" />
      <img src="@/static/hp6.webp" alt="" loading="lazy" decoding="async" />
    </main>
  </div>
</template>

<style scoped lang="scss">
.container {
  img {
    width: 100%;
    vertical-align: middle;
  }
}
</style>
