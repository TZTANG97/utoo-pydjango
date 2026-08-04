<template>
  <div class="login-page">
    <div class="login-panel">
      <div class="login-brand">
        <div class="logo">UTOO</div>
        <h1>愉兔检测管理平台</h1>
        <p>检测业务管理后台</p>
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
          <el-checkbox v-model="remember">记住密码</el-checkbox>
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
import { useUserStore } from '@admin/stores/user'

/** Align with Java admin: remember username + password (localStorage, base64 password). */
const REMEMBER_FLAG_KEY = 'admin_remember_password'
const REMEMBER_NAME_KEY = 'admin_login_name'
const REMEMBER_PWD_KEY = 'admin_login_pwd'

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

function encodePwd(pwd: string): string {
  return btoa(String.fromCharCode(...new TextEncoder().encode(pwd)))
}

function decodePwd(raw: string): string {
  try {
    const bytes = Uint8Array.from(atob(raw), (c) => c.charCodeAt(0))
    return new TextDecoder().decode(bytes)
  } catch {
    return ''
  }
}

function clearRemembered() {
  localStorage.removeItem(REMEMBER_FLAG_KEY)
  localStorage.removeItem(REMEMBER_NAME_KEY)
  localStorage.removeItem(REMEMBER_PWD_KEY)
}

function loadRemembered() {
  const name = localStorage.getItem(REMEMBER_NAME_KEY) || ''
  const pwdRaw = localStorage.getItem(REMEMBER_PWD_KEY) || ''
  const flagged = localStorage.getItem(REMEMBER_FLAG_KEY) === '1'
  if (flagged || pwdRaw || name) {
    remember.value = Boolean(flagged || pwdRaw || name)
    form.loginName = name
    form.password = pwdRaw ? decodePwd(pwdRaw) : ''
  }
}

function saveRemembered() {
  if (!remember.value) {
    clearRemembered()
    return
  }
  localStorage.setItem(REMEMBER_FLAG_KEY, '1')
  localStorage.setItem(REMEMBER_NAME_KEY, form.loginName.trim())
  localStorage.setItem(REMEMBER_PWD_KEY, encodePwd(form.password))
}

onMounted(() => {
  loadRemembered()
})

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.loginName.trim(), form.password)
    saveRemembered()
    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/admin/dashboard'
    await router.replace(redirect || '/admin/dashboard')
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
