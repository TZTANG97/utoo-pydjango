<template>
  <admin-page-card title="所属公司管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">添加所属公司</el-button>
    </template>

    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="用户名">
        <el-input v-model="filters.userName" placeholder="用户名" clearable />
      </el-form-item>
      <el-form-item label="企业名称">
        <el-input v-model="filters.companyName" placeholder="企业名称" clearable />
      </el-form-item>
      <el-form-item label="联系人">
        <el-input v-model="filters.trueName" placeholder="联系人" clearable />
      </el-form-item>
      <el-form-item label="联系电话">
        <el-input v-model="filters.mobile" placeholder="联系电话" clearable />
      </el-form-item>
      <el-form-item label="区域">
        <el-select v-model="filters.areaId" clearable filterable style="width: 140px">
          <el-option
            v-for="item in areaOptions"
            :key="String(item.id)"
            :label="String(item.areaName || item.id)"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="userName" label="用户名" min-width="120" />
      <el-table-column prop="companyName" label="企业名称" min-width="160" />
      <el-table-column prop="areaName" label="区域" width="120" />
      <el-table-column prop="addressLabel" label="注册地址" min-width="140" show-overflow-tooltip />
      <el-table-column prop="trueName" label="联系人" width="100" />
      <el-table-column prop="mobile" label="联系电话" min-width="120" />
      <el-table-column prop="companyCode" label="公司代码" min-width="120" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px">
      <el-form label-width="110px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.userName" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="企业名称" required>
          <el-input v-model="form.companyName" />
        </el-form-item>
        <el-form-item label="区域" required>
          <el-select v-model="form.areaInfo" filterable style="width: 100%">
            <el-option
              v-for="item in areaOptions"
              :key="String(item.id)"
              :label="String(item.areaName || item.id)"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="注册地址">
          <el-input v-model="form.addressInfo" placeholder="详细地址" />
        </el-form-item>
        <el-form-item label="联系人" required>
          <el-input v-model="form.trueName" />
        </el-form-item>
        <el-form-item label="联系电话" required>
          <el-input v-model="form.mobile" />
        </el-form-item>
        <el-form-item label="公司代码">
          <el-input v-model="form.companyCode" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item v-if="!editingId" label="初始密码">
          <el-input v-model="form.password" placeholder="默认 123456" />
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
  deleteSupplier,
  fetchAreaOptions,
  fetchSupplierList,
  getSupplierById,
  saveSupplier,
} from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { isAjaxOk } from '@/utils/request'

const filters = reactive({
  userName: '',
  companyName: '',
  trueName: '',
  mobile: '',
  areaId: '',
})
const areaOptions = ref<Record<string, unknown>[]>([])
const { loading, rows, total, pagination, load } = useDataTable(fetchSupplierList)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const form = reactive({
  userName: '',
  companyName: '',
  areaInfo: '',
  addressInfo: '',
  trueName: '',
  mobile: '',
  companyCode: '',
  email: '',
  password: '',
})

const dialogTitle = computed(() => (editingId.value ? '编辑所属公司' : '添加所属公司'))

onMounted(async () => {
  areaOptions.value = await fetchAreaOptions()
  await reload()
})

function reload() {
  return load({
    userName: filters.userName.trim(),
    company_name: filters.companyName.trim(),
    trueName: filters.trueName.trim(),
    mobile: filters.mobile.trim(),
    areaId: filters.areaId,
  })
}

function resetForm() {
  editingId.value = null
  form.userName = ''
  form.companyName = ''
  form.areaInfo = ''
  form.addressInfo = ''
  form.trueName = ''
  form.mobile = ''
  form.companyCode = ''
  form.email = ''
  form.password = ''
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getSupplierById(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error('加载公司信息失败')
    return
  }
  const data = res.obj as Record<string, unknown>
  editingId.value = Number(data.id)
  form.userName = String(data.userName || '')
  form.companyName = String(data.companyName || data.company_name || '')
  form.areaInfo = data.areaInfo ? String(data.areaInfo) : ''
  form.addressInfo = String(data.addressInfo || data.address_info || '')
  form.trueName = String(data.trueName || '')
  form.mobile = String(data.mobile || '')
  form.companyCode = String(data.companyCode || data.company_code || '')
  form.email = String(data.email || '')
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.userName.trim() || !form.companyName.trim() || !form.trueName.trim() || !form.mobile.trim()) {
    ElMessage.warning('请填写必填项')
    return
  }
  if (!form.areaInfo) {
    ElMessage.warning('请选择区域')
    return
  }
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      userName: form.userName.trim(),
      company_name: form.companyName.trim(),
      areaInfo: form.areaInfo,
      addressInfo: form.addressInfo.trim(),
      trueName: form.trueName.trim(),
      mobile: form.mobile.trim(),
      company_code: form.companyCode.trim(),
      email: form.email.trim(),
    }
    if (editingId.value) {
      payload.id = editingId.value
    } else if (form.password.trim()) {
      payload.password = form.password.trim()
    }
    const res = await saveSupplier(payload)
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await reload()
      return
    }
    ElMessage.error('保存失败，用户名或企业名称可能已存在')
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除（禁用）该所属公司吗？', '提示', { type: 'warning' })
  const res = await deleteSupplier(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('操作成功')
    await reload()
  } else {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
