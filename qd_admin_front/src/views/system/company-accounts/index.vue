<template>
  <admin-page-card title="公司账户管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">添加账户</el-button>
    </template>

    <el-alert
      v-if="defaultAccount"
      type="success"
      :closable="false"
      show-icon
      class="default-banner"
    >
      <template #title>
        默认账户：{{ defaultAccount.companyName }} /
        {{ defaultAccount.bank }} /
        {{ defaultAccount.bankCardNum }}
      </template>
    </el-alert>
    <el-alert v-else type="info" :closable="false" show-icon class="default-banner">
      尚未设置默认账户
    </el-alert>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="companyName" label="公司名称" min-width="160" />
      <el-table-column prop="bank" label="开户行" min-width="140" />
      <el-table-column prop="bankCardNum" label="银行账号" min-width="180" />
      <el-table-column label="默认" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.defaultAccount === 1" type="success">默认</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="addTime" label="添加时间" min-width="160" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-if="row.defaultAccount !== 1"
            link
            type="success"
            @click="handleSetDefault(row)"
          >
            设为默认
          </el-button>
          <el-button
            link
            type="danger"
            :disabled="row.defaultAccount === 1"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="reload"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form label-width="90px">
        <el-form-item label="公司名称">
          <el-input v-model="form.companyName" />
        </el-form-item>
        <el-form-item label="开户行">
          <el-input v-model="form.bank" />
        </el-form-item>
        <el-form-item label="银行账号">
          <el-input v-model="form.bankCardNum" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  createCompanyAccount,
  deleteCompanyAccount,
  fetchCompanyAccountList,
  fetchDefaultCompanyAccount,
  setDefaultCompanyAccount,
  updateCompanyAccount,
} from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { isAjaxOk } from '@/utils/request'

const defaultAccount = ref<Record<string, unknown> | null>(null)
const { loading, rows, total, pagination, load } = useDataTable(fetchCompanyAccountList)
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const form = reactive({ companyName: '', bank: '', bankCardNum: '' })

const dialogTitle = computed(() => (editingId.value ? '编辑账户' : '添加账户'))

onMounted(() => reload())

async function loadDefault() {
  defaultAccount.value = await fetchDefaultCompanyAccount()
}

async function reload() {
  await Promise.all([load(), loadDefault()])
}

function resetForm() {
  editingId.value = null
  form.companyName = ''
  form.bank = ''
  form.bankCardNum = ''
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  form.companyName = String(row.companyName || '')
  form.bank = String(row.bank || '')
  form.bankCardNum = String(row.bankCardNum || '')
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.companyName.trim() || !form.bankCardNum.trim()) {
    ElMessage.warning('请填写公司名称和银行账号')
    return
  }
  saving.value = true
  try {
    const payload = {
      companyName: form.companyName.trim(),
      bank: form.bank.trim(),
      bankCardNum: form.bankCardNum.trim(),
    }
    const res = editingId.value
      ? await updateCompanyAccount({ ...payload, id: editingId.value })
      : await createCompanyAccount(payload)
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await reload()
      return
    }
    ElMessage.error('保存失败，银行账号可能已存在')
  } finally {
    saving.value = false
  }
}

async function handleSetDefault(row: Record<string, unknown>) {
  const res = await setDefaultCompanyAccount(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('已设为默认账户')
    await reload()
  } else {
    ElMessage.error('设置失败')
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该账户吗？', '提示', { type: 'warning' })
  const res = await deleteCompanyAccount(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
  } else {
    ElMessage.error('删除失败，默认账户不可删除')
  }
}
</script>

<style scoped lang="scss">
.default-banner {
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
