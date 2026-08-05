<template>
  <admin-page-card :title="title">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增仓库</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent="reload">
      <el-form-item label="仓库名称">
        <el-input
          v-model="filters.storeName"
          clearable
          style="width: 160px"
          @keydown.enter.prevent="reload"
        />
      </el-form-item>
      <el-form-item label="负责人">
        <el-input
          v-model="filters.trueName"
          clearable
          style="width: 140px"
          @keydown.enter.prevent="reload"
        />
      </el-form-item>
      <el-form-item label="手机">
        <el-input
          v-model="filters.mobile"
          clearable
          style="width: 140px"
          @keydown.enter.prevent="reload"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="storeNum" label="仓库编号" min-width="120" />
      <el-table-column prop="storeName" label="仓库名称" min-width="140" />
      <el-table-column prop="trueName" label="负责人" min-width="100">
        <template #default="{ row }">{{ row.trueName || row.userName || '-' }}</template>
      </el-table-column>
      <el-table-column prop="moblie" label="手机" min-width="120" />
      <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="Number(row.status) === 1 ? 'success' : 'info'" size="small">
            {{ Number(row.status) === 1 ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="addTime" label="创建时间" min-width="160" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="warning" @click="toggleStatus(row)">
            {{ Number(row.status) === 1 ? '停用' : '启用' }}
          </el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          <el-button link type="primary" @click="openConfig(row)">配置</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑仓库' : '新增仓库'" width="520px">
      <el-form label-width="90px">
        <el-form-item label="仓库编号"><el-input v-model="form.storeNum" /></el-form-item>
        <el-form-item label="仓库名称" required><el-input v-model="form.storeName" /></el-form-item>
        <el-form-item label="负责人">
          <el-select
            v-model="form.storeUserid"
            filterable
            clearable
            :loading="userLoading"
            placeholder="请选择负责人"
            style="width: 100%"
          >
            <el-option
              v-for="o in userOptions"
              :key="String(o.value)"
              :label="String(o.label)"
              :value="String(o.value)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="手机"><el-input v-model="form.moblie" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.mark" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 120px">
            <el-option :value="1" label="启用" />
            <el-option :value="0" label="停用" />
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  deleteSampleStorehouse,
  deleteStorehouse,
  fetchSampleStorehouseList,
  fetchStorehouseList,
  saveSampleStorehouse,
  saveStorehouse,
  updateSampleStorehouseStatus,
  updateStorehouseStatus,
} from '@/api/inventory'
import { fetchUserList } from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const props = withDefaults(
  defineProps<{ mode?: 'goods' | 'sample' | 'retain'; title?: string }>(),
  { mode: 'goods', title: '仓库管理' }
)

const router = useRouter()

const filters = reactive({ storeName: '', trueName: '', mobile: '' })
const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const userLoading = ref(false)
const userOptions = ref<{ value: string; label: string }[]>([])
const form = reactive({
  storeNum: '',
  storeName: '',
  storeUserid: '',
  moblie: '',
  address: '',
  mark: '',
  status: 1,
})

const loader = (params: Record<string, unknown>) => {
  const p = { ...params, ...filters }
  if (props.mode === 'goods') return fetchStorehouseList(p)
  return fetchSampleStorehouseList(props.mode === 'retain', p)
}

const { loading, rows, total, pagination, load } = useDataTable(loader)

function reload() {
  pagination.page = 1
  load()
}

async function loadUserOptions() {
  userLoading.value = true
  try {
    const res = await fetchUserList(
      { start: 0, length: 1000, type: -1, draw: 1 },
      { silentError: true }
    )
    const list = Array.isArray(res.data) ? res.data : []
    userOptions.value = list
      .map((u) => {
        const id = String(u.id ?? u.userId ?? '')
        const name = String(u.userName || u.user_name || '')
        const trueName = String(u.trueName || u.true_name || '')
        return { value: id, label: trueName ? `${name}（${trueName}）` : name || id }
      })
      .filter((o) => o.value)
  } catch {
    userOptions.value = []
  } finally {
    userLoading.value = false
  }
}

onMounted(() => {
  void loadUserOptions()
  load()
})

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    storeNum: '',
    storeName: '',
    storeUserid: '',
    moblie: '',
    address: '',
    mark: '',
    status: 1,
  })
  void loadUserOptions()
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  editingId.value = String(row.id)
  Object.assign(form, {
    storeNum: String(row.storeNum || ''),
    storeName: String(row.storeName || ''),
    storeUserid: String(row.storeUserid || row.store_userid || ''),
    moblie: String(row.moblie || ''),
    address: String(row.address || ''),
    mark: String(row.mark || ''),
    status: Number(row.status ?? 1),
  })
  void loadUserOptions()
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.storeName.trim()) {
    ElMessage.warning('请填写仓库名称')
    return
  }
  saving.value = true
  try {
    const payload = { ...form, id: editingId.value || undefined }
    const res =
      props.mode === 'goods'
        ? await saveStorehouse(payload)
        : await saveSampleStorehouse(props.mode === 'retain', payload)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: Record<string, unknown>) {
  const next = Number(row.status) === 1 ? 0 : 1
  const res =
    props.mode === 'goods'
      ? await updateStorehouseStatus(String(row.id), next)
      : await updateSampleStorehouseStatus(props.mode === 'retain', String(row.id), next)
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
    return
  }
  ElMessage.success(next === 1 ? '已启用' : '已停用')
  load()
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确认删除该仓库？', '提示', { type: 'warning' })
  const res =
    props.mode === 'goods'
      ? await deleteStorehouse(String(row.id))
      : await deleteSampleStorehouse(props.mode === 'retain', String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
    return
  }
  ElMessage.success('已删除')
  load()
}

function openConfig(row: Record<string, unknown>) {
  router.push({
    name: 'InventoryWarehouseConfig',
    query: { mode: props.mode, id: String(row.id) },
  })
}
</script>

<style scoped>
.filter-form {
  margin-bottom: 12px;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
