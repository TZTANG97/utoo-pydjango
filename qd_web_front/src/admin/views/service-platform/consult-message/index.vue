<template>
  <admin-page-card title="用户业务咨询消息配置">
    <el-form label-width="100px" class="setting-form" @submit.prevent>
      <div class="section-title">公众号消息</div>
      <el-form-item label="账号">
        <el-select
          v-model="form.gzh_userId"
          filterable
          clearable
          placeholder="请选择"
          style="width: 280px"
          :loading="usersLoading"
        >
          <el-option
            v-for="u in userOptions"
            :key="String(u.id)"
            :label="String(u.userName || u.trueName || u.id)"
            :value="String(u.id)"
          />
        </el-select>
        <span class="inline-label">是否发送</span>
        <el-switch v-model="form.gzh_issend" :active-value="1" :inactive-value="0" active-text="ON" inactive-text="OFF" />
      </el-form-item>

      <div class="section-title">mail消息</div>
      <el-form-item label="mail">
        <el-select
          v-model="form.service_mail"
          filterable
          clearable
          placeholder="请选择"
          style="width: 280px"
          :loading="usersLoading"
        >
          <el-option
            v-for="m in mailOptions"
            :key="m"
            :label="m"
            :value="m"
          />
        </el-select>
        <span class="inline-label">是否发送</span>
        <el-switch v-model="form.mail_issend" :active-value="1" :inactive-value="0" active-text="ON" inactive-text="OFF" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </el-form-item>
    </el-form>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { getConsultSetting, saveConsultSetting } from '@admin/api/service-platform'
import { fetchUserList } from '@admin/api/system'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type UserOpt = {
  id: string | number
  userName?: string
  trueName?: string
  email?: string
}

const saving = ref(false)
const usersLoading = ref(false)
const userOptions = ref<UserOpt[]>([])
const form = reactive({
  gzh_userId: '',
  gzh_issend: 0,
  service_mail: '',
  mail_issend: 0,
})

const mailOptions = computed(() => {
  const set = new Set<string>()
  for (const u of userOptions.value) {
    const email = String(u.email || '').trim()
    if (email) set.add(email)
  }
  if (form.service_mail && !set.has(form.service_mail)) {
    set.add(form.service_mail)
  }
  return Array.from(set).sort()
})

async function loadUsers() {
  usersLoading.value = true
  try {
    const res = await fetchUserList(
      { start: 0, length: 2000, type: -1, draw: 1 },
      { silentError: true }
    )
    const rows = Array.isArray(res.data) ? res.data : []
    userOptions.value = rows.map((r) => {
      const row = r as Record<string, unknown>
      return {
        id: (row.id ?? '') as string | number,
        userName: String(row.userName || row.user_name || ''),
        trueName: String(row.trueName || row.true_name || ''),
        email: String(row.email || ''),
      }
    }).filter((u) => u.id !== '' && u.id != null)
  } finally {
    usersLoading.value = false
  }
}

async function loadSetting() {
  const res = await getConsultSetting()
  if (!isAjaxOk(res) || !res.obj || typeof res.obj !== 'object') return
  const data = res.obj as Record<string, unknown>
  form.gzh_userId = String(
    data.gzh_userId_ut ?? data.gzh_userId ?? data.gzhUserId ?? ''
  )
  form.gzh_issend = Number(data.gzh_issend_ut ?? data.gzh_issend ?? 0) ? 1 : 0
  form.service_mail = String(
    data.service_mail_ut ?? data.service_mail ?? data.serviceMail ?? ''
  )
  form.mail_issend = Number(data.mail_issend_ut ?? data.mail_issend ?? 0) ? 1 : 0
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadSetting()])
  // 已保存账号若不在当前列表中，补一条便于回显
  if (form.gzh_userId && !userOptions.value.some((u) => String(u.id) === form.gzh_userId)) {
    userOptions.value.unshift({
      id: form.gzh_userId,
      userName: form.gzh_userId,
    })
  }
})

async function handleSave() {
  saving.value = true
  try {
    const res = await saveConsultSetting({
      gzh_userId: form.gzh_userId,
      gzh_issend: form.gzh_issend,
      service_mail: form.service_mail,
      mail_issend: form.mail_issend,
    })
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.setting-form {
  max-width: 720px;
  padding: 8px 4px;
}
.section-title {
  margin: 8px 0 16px;
  padding-left: 10px;
  border-left: 2px solid #0d9540;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  line-height: 24px;
}
.inline-label {
  margin: 0 12px 0 24px;
  color: #606266;
  white-space: nowrap;
}
</style>
