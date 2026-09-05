<template>
  <admin-page-card title="白名单配置管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增白名单账号</el-button>
    </template>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column prop="addTime" label="添加时间" min-width="160" />
      <el-table-column prop="userName" label="账号名称" min-width="160" />
      <el-table-column label="白名单类型" width="140" align="center">
        <template #default="{ row }">
          {{ Number(row.type) === 2 ? '商品兑换' : '发票' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center" fixed="right">
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
        @current-change="() => load()"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑白名单账号' : '添加白名单账号'"
      width="520px"
    >
      <el-form label-width="100px">
        <el-form-item label="账号名称" required>
          <el-select
            v-model="form.syuser_id"
            filterable
            remote
            clearable
            :remote-method="searchUsers"
            :loading="userLoading"
            style="width: 100%"
            placeholder="输入用户名搜索"
            @visible-change="onUserSelectVisible"
          >
            <el-option
              v-for="item in userOptions"
              :key="String(item.id)"
              :label="userLabel(item)"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="白名单类型" required>
          <el-select v-model="form.type" style="width: 100%">
            <el-option label="发票" :value="1" />
            <el-option label="商品兑换" :value="2" />
          </el-select>
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  addWhitelist,
  deleteWhitelist,
  fetchSyUserOptions,
  fetchWhitelist,
  updateWhitelist,
} from '@admin/api/ops'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const { loading, rows, total, pagination, load } = useDataTable(fetchWhitelist)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const userLoading = ref(false)
const userOptions = ref<Record<string, unknown>[]>([])
const form = reactive({
  id: '',
  syuser_id: '',
  type: 1,
})

onMounted(() => load())

function userLabel(item: Record<string, unknown>) {
  const name = String(item.userName || item.trueName || item.id || '')
  const trueName = String(item.trueName || '')
  if (trueName && trueName !== name) return `${name}（${trueName}）`
  return name
}

function onUserSelectVisible(open: boolean) {
  // 新增无列表、编辑仅有当前项时，展开下拉再拉一批可选用户
  if (open && userOptions.value.length <= 1) searchUsers('')
}

async function searchUsers(keyword: string) {
  userLoading.value = true
  try {
    const res = await fetchSyUserOptions(keyword || '')
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      const list = res.obj as Record<string, unknown>[]
      // 编辑态：保证当前已选账号仍在选项中
      if (form.syuser_id && !list.some((u) => String(u.id) === form.syuser_id)) {
        const current = userOptions.value.find((u) => String(u.id) === form.syuser_id)
        if (current) list.unshift(current)
      }
      userOptions.value = list
    } else {
      if (!isAjaxOk(res)) ElMessage.error(ajaxErrorMessage(res, '用户列表加载失败'))
    }
  } finally {
    userLoading.value = false
  }
}

function openCreate() {
  form.id = ''
  form.syuser_id = ''
  form.type = 1
  userOptions.value = []
  isEdit.value = false
  dialogVisible.value = true
  searchUsers('')
}

function openEdit(row: Record<string, unknown>) {
  form.id = String(row.id)
  form.syuser_id = String(row.syuserId || '')
  form.type = Number(row.type || 1)
  userOptions.value = [
    {
      id: form.syuser_id,
      userName: row.userName,
    },
  ]
  isEdit.value = true
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.syuser_id) {
    ElMessage.warning('请选择账号')
    return
  }
  saving.value = true
  try {
    const res = isEdit.value
      ? await updateWhitelist({ ...form })
      : await addWhitelist({ syuser_id: form.syuser_id, type: form.type })
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await load()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该白名单吗？', '提示', { type: 'warning' })
  const res = await deleteWhitelist(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await load()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
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
