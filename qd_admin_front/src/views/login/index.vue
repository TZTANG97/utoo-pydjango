<template>
  <div class="login-page">
    <div class="login-panel">
      <div class="login-brand">
        <div class="logo">UTOO</div>
        <h1>愉兔检测管理平台</h1>
        <p>Java 后台迁移 · Django + Vue 管理端</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="loginName">
          <el-input
            v-model="form.loginName"
            placeholder="请输入用户名"
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="remember">记住用户名</el-checkbox>
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="login-btn"
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const REMEMBER_KEY = 'admin_login_name'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const remember = ref(true)

const form = reactive({
  loginName: '',
  password: '',
})

const rules: FormRules = {
  loginName: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
  password: [{ required: true, message: '密码不能为空', trigger: 'blur' }],
}

onMounted(() => {
  form.loginName = localStorage.getItem(REMEMBER_KEY) || ''
})

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.loginName.trim(), form.password)
    if (remember.value) {
      localStorage.setItem(REMEMBER_KEY, form.loginName.trim())
    } else {
      localStorage.removeItem(REMEMBER_KEY)
    }
    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    await router.replace(redirect || '/dashboard')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at top left, rgba(249, 115, 22, 0.25), transparent 35%),
    linear-gradient(135deg, #fff7ed 0%, #f8fafc 45%, #eef2ff 100%);
}

.login-panel {
  width: 420px;
  padding: 40px 36px 32px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.12);
  backdrop-filter: blur(8px);
}

.login-brand {
  text-align: center;
  margin-bottom: 28px;

  .logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    border-radius: 14px;
    background: linear-gradient(135deg, #f97316, #ea580c);
    color: #fff;
    font-weight: 700;
    margin-bottom: 12px;
  }

  h1 {
    margin: 0 0 8px;
    font-size: 24px;
    color: #1f2937;
  }

  p {
    margin: 0;
    font-size: 13px;
    color: #64748b;
  }
}

.login-form {
  .login-btn {
    width: 100%;
    margin-top: 4px;
  }
}
</style>
