<template>
  <admin-page-card title="用户管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">添加用户</el-button>
    </template>

    <el-form :inline="true" @submit.prevent="reload">
      <el-form-item label="部门">
        <el-select v-model="deptId" placeholder="全部" clearable filterable style="width: 180px">
          <el-option label="全部" value="" />
          <el-option
            v-for="item in deptOptions"
            :key="String(item.id)"
            :label="String(item.deptName || item.id)"
            :value="String(item.id)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="用户名">
        <el-input v-model="userName" placeholder="用户名" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="userName" label="用户名" min-width="120" />
      <el-table-column prop="trueName" label="姓名" min-width="100" />
      <el-table-column prop="deptName" label="部门" min-width="140" />
      <el-table-column prop="mobilePhoneNumber" label="手机" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.userStatus === 1 ? 'success' : 'info'">
            {{ row.userStatus === 1 ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDisable(row)">禁用</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px">
      <el-form label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.userName" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item v-if="!editingId" label="密码">
          <el-input v-model="form.userPassword" type="password" placeholder="默认 123456" show-password />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.trueName" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="form.deptId" filterable style="width: 100%">
            <el-option
              v-for="item in deptOptions"
              :key="String(item.id)"
              :label="String(item.deptName || item.id)"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.roleIds" multiple filterable style="width: 100%">
            <el-option
              v-for="item in roleOptions"
              :key="String(item.id)"
              :label="String(item.roleName || item.name || item.id)"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.mobilePhoneNumber" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.userDesc" type="textarea" :rows="2" />
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
  addUser,
  deleteUser,
  fetchDeptOptions,
  fetchUserList,
  fetchUserRoleOptions,
  getUserById,
  updateUser,
} from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { isAjaxOk } from '@/utils/request'

const deptId = ref('')
const userName = ref('')
const deptOptions = ref<Record<string, unknown>[]>([])
const roleOptions = ref<Record<string, unknown>[]>([])
const { loading, rows, total, pagination, load } = useDataTable(fetchUserList)
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const form = reactive({
  userName: '',
  userPassword: '',
  trueName: '',
  deptId: '0',
  roleIds: [] as string[],
  mobilePhoneNumber: '',
  email: '',
  userDesc: '',
})

const dialogTitle = computed(() => (editingId.value ? '编辑用户' : '添加用户'))

onMounted(async () => {
  deptOptions.value = await fetchDeptOptions()
  roleOptions.value = await fetchUserRoleOptions()
  await reload()
})

function reload() {
  return load({
    deptId: deptId.value,
    userName: userName.value.trim(),
  })
}

function resetForm() {
  editingId.value = null
  form.userName = ''
  form.userPassword = ''
  form.trueName = ''
  form.deptId = '0'
  form.roleIds = []
  form.mobilePhoneNumber = ''
  form.email = ''
  form.userDesc = ''
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  const res = await getUserById(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error('加载用户失败')
    return
  }
  const data = res.obj as Record<string, unknown>
  editingId.value = String(data.id)
  form.userName = String(data.userName || '')
  form.trueName = String(data.trueName || '')
  form.deptId = String(data.deptId || '0')
  form.roleIds = Array.isArray(data.roleIds) ? data.roleIds.map(String) : []
  form.mobilePhoneNumber = String(data.mobilePhoneNumber || '')
  form.email = String(data.email || '')
  form.userDesc = String(data.userDesc || '')
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.userName.trim()) {
    ElMessage.warning('请填写用户名')
    return
  }
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      userName: form.userName.trim(),
      trueName: form.trueName.trim(),
      deptId: form.deptId,
      roleIds: form.roleIds,
      mobilePhoneNumber: form.mobilePhoneNumber,
      email: form.email,
      userDesc: form.userDesc,
    }
    if (!editingId.value) {
      payload.userPassword = form.userPassword || '123456'
    }
    const res = editingId.value
      ? await updateUser({ ...payload, id: editingId.value })
      : await addUser(payload)
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await reload()
      return
    }
    ElMessage.error('保存失败，用户名可能已存在')
  } finally {
    saving.value = false
  }
}

async function handleDisable(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定禁用该用户吗？', '提示', { type: 'warning' })
  const res = await deleteUser(String(row.id))
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
