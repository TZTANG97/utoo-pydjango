<template>
  <div class="dashboard">
    <el-card class="welcome-banner" shadow="never">
      <div class="welcome-head">
        <div>
          <h2>欢迎页</h2>
          <p>
            {{ greeting }}，{{ displayName }}
            <span v-if="roleLabel">（{{ roleLabel }}）</span>
          </p>
        </div>
        <el-tag type="success" effect="plain">Java 后台迁移 · Django + Vue</el-tag>
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">当前用户</div>
          <div class="stat-value">{{ displayName }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">角色标识</div>
          <div class="stat-value">{{ roleLabel || '待配置' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">所属部门</div>
          <div class="stat-value">{{ deptName || '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">菜单数量</div>
          <div class="stat-value">{{ menuCount }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <span>平台概览</span>
          </template>
          <p class="desc">
            对齐 Java 后台 <code>/index/main.htm</code> 默认打开的欢迎页与
            <code>/vue/main.ajax</code> 菜单加载逻辑。
          </p>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="登录账号">
              {{ userStore.loginName || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">
              {{ welcome?.email || profileEmail || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="手机号">
              {{ welcome?.mobilePhoneNumber || profileMobile || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="欢迎页类型">
              userType = {{ welcome?.userType ?? userStore.userType }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <span>快捷入口</span>
          </template>
          <div class="quick-links">
            <el-button type="primary" plain disabled>资金账户</el-button>
            <el-button type="primary" plain disabled>数字化中心</el-button>
          </div>
          <el-alert
            class="tips"
            title="提示"
            type="info"
            :closable="false"
            show-icon
            description="侧边栏菜单来自 /api/vue/main.ajax。尚未迁移的业务菜单会暂时不可点击，待对应 Vue 页面和 Django 接口完成后启用。"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const welcome = computed(() => userStore.welcome)
const profile = computed(() => userStore.profile || {})

const displayName = computed(
  () => welcome.value?.userName || userStore.userName || userStore.loginName || '-'
)
const roleLabel = computed(
  () => welcome.value?.roleName || userStore.roleName || ''
)
const deptName = computed(() => welcome.value?.deptName || '')
const profileEmail = computed(() => String(profile.value.email || ''))
const profileMobile = computed(() => String(profile.value.mobilePhoneNumber || ''))

const menuCount = computed(() => {
  if (typeof welcome.value?.menuCount === 'number') {
    return welcome.value.menuCount
  }
  const walk = (items: typeof userStore.menus): number =>
    items.reduce((sum, item) => sum + 1 + walk(item.children || []), 0)
  return walk(userStore.menus)
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '上午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})
</script>

<style scoped lang="scss">
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-banner {
  background: linear-gradient(135deg, #fff7ed 0%, #ffffff 60%);

  h2 {
    margin: 0 0 8px;
    font-size: 22px;
    color: #1f2937;
  }

  p {
    margin: 0;
    color: #64748b;
  }
}

.welcome-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.stat-card {
  min-height: 108px;
}

.stat-title {
  color: #909399;
  font-size: 13px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  word-break: break-all;
}

.desc {
  margin: 0 0 16px;
  color: #606266;
  line-height: 1.7;
}

.quick-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.tips {
  margin-top: 8px;
}
</style>
