<template>
  <admin-page-card title="咨询方式设置">
    <el-form v-loading="loading" label-width="100px" class="consult-form" style="max-width: 560px">
      <el-form-item label="公司名称">
        <el-input v-model="form.qdName" placeholder="可留空（与旧站一致）" clearable />
      </el-form-item>
      <el-form-item label="服务热线">
        <el-input v-model="form.serviceMobile" clearable />
      </el-form-item>
      <el-form-item label="传真">
        <el-input v-model="form.qdFax" clearable />
      </el-form-item>
      <el-form-item label="地址">
        <el-input v-model="form.qdAddress" placeholder="可留空（与旧站一致）" clearable />
      </el-form-item>
      <el-form-item label="电子邮箱">
        <el-input v-model="form.qdEmail" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="warning" :loading="saving" @click="handleSubmit">保存</el-button>
        <el-button :disabled="saving || loading" @click="handleReset">取消/恢复</el-button>
        <el-button link type="danger" :disabled="saving || loading" @click="handleClear">清空全部</el-button>
      </el-form-item>
      <p class="hint">公司名称、地址允许为空以便恢复业务原值；「取消/恢复」回退到最近一次已加载/已保存的值。</p>
    </el-form>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { getConsultConfig, saveConsultConfig } from '@admin/api/ops'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const loading = ref(false)
const saving = ref(false)

type ConsultForm = {
  id: number | undefined
  qdName: string
  serviceMobile: string
  qdFax: string
  qdAddress: string
  qdEmail: string
}

const form = reactive<ConsultForm>({
  id: undefined,
  qdName: '',
  serviceMobile: '',
  qdFax: '',
  qdAddress: '',
  qdEmail: '',
})

/** 最近一次成功加载/保存的快照，用于取消恢复 */
const savedSnapshot = ref<ConsultForm>({ ...form })

function applyForm(src: Partial<ConsultForm>) {
  form.id = src.id
  form.qdName = String(src.qdName || '')
  form.serviceMobile = String(src.serviceMobile || '')
  form.qdFax = String(src.qdFax || '')
  form.qdAddress = String(src.qdAddress || '')
  form.qdEmail = String(src.qdEmail || '')
}

function takeSnapshot() {
  savedSnapshot.value = {
    id: form.id,
    qdName: form.qdName,
    serviceMobile: form.serviceMobile,
    qdFax: form.qdFax,
    qdAddress: form.qdAddress,
    qdEmail: form.qdEmail,
  }
}

async function load() {
  loading.value = true
  try {
    const res = await getConsultConfig()
    if (isAjaxOk(res) && res.obj) {
      const obj = res.obj as Record<string, unknown>
      applyForm({
        id: obj.id ? Number(obj.id) : undefined,
        qdName: String(obj.qdName || ''),
        serviceMobile: String(obj.serviceMobile || ''),
        qdFax: String(obj.qdFax || ''),
        qdAddress: String(obj.qdAddress || ''),
        qdEmail: String(obj.qdEmail || ''),
      })
      takeSnapshot()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    }
  } catch (err: unknown) {
    const msg =
      err && typeof err === 'object' && 'message' in err
        ? String((err as { message?: string }).message || '')
        : ''
    ElMessage.error(msg || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  saving.value = true
  try {
    const res = await saveConsultConfig({ ...form })
    if (isAjaxOk(res)) {
      ElMessage.success('咨询方式设置成功')
      takeSnapshot()
      await load()
    } else {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
    }
  } catch (err: unknown) {
    const msg =
      err && typeof err === 'object' && 'message' in err
        ? String((err as { message?: string }).message || '')
        : ''
    ElMessage.error(msg || '保存失败')
  } finally {
    saving.value = false
  }
}

function handleReset() {
  applyForm(savedSnapshot.value)
  ElMessage.info('已恢复为最近一次已保存的值')
}

function handleClear() {
  form.qdName = ''
  form.serviceMobile = ''
  form.qdFax = ''
  form.qdAddress = ''
  form.qdEmail = ''
}

onMounted(() => load())
</script>

<style scoped lang="scss">
.consult-form {
  margin-top: 24px;
}
.hint {
  margin: 0;
  color: #909399;
  font-size: 13px;
  line-height: 1.5;
  max-width: 480px;
}
</style>
