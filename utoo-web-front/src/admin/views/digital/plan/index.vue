<template>
  <admin-page-card :title="pageTitle">
    <el-form :inline="true" class="filter-form" @submit.prevent="handleSearch">
      <el-form-item label="部门">
        <el-tree-select
          v-model="filters.deptId"
          :data="deptTree"
          clearable
          filterable
          check-strictly
          default-expand-all
          :render-after-expand="false"
          :placeholder="defaultDeptName || '全部'"
          style="width: 260px"
          :props="deptTreeProps"
        />
      </el-form-item>
      <el-form-item label="账号">
        <el-input v-model="filters.userName" clearable @keyup.enter="handleSearch" />
      </el-form-item>
      <el-form-item label="姓名">
        <el-input v-model="filters.trueName" clearable @keyup.enter="handleSearch" />
      </el-form-item>
      <el-form-item v-if="mode === 'test' || mode === 'sale'" label="性别">
        <el-select v-model="filters.userSex" clearable placeholder="全部" style="width: 100px">
          <el-option label="全部" value="" />
          <el-option label="男" value="1" />
          <el-option label="女" value="0" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit">查询</el-button>
        <el-button @click="handleClear">清空</el-button>
      </el-form-item>
    </el-form>

    <el-alert
      v-if="!canQuery"
      type="warning"
      :closable="false"
      show-icon
      :title="
        mode === 'sale'
          ? '当前账号无销售产出计划查询权限（仅系统管理员 / 销售主管）'
          : '当前账号无实验室产出计划查询权限（仅系统管理员 / 销售主管 / 测试主管）'
      "
      style="margin-bottom: 12px"
    />

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" label="#" width="55" />
      <el-table-column prop="trueName" label="姓名" width="120" show-overflow-tooltip />
      <el-table-column prop="deptName" label="部门" min-width="160" show-overflow-tooltip />
      <el-table-column prop="userName" label="账号" min-width="120" show-overflow-tooltip />
      <el-table-column prop="utooType" label="用户类型" width="120" show-overflow-tooltip />
      <template v-if="mode === 'test' || mode === 'sale'">
        <el-table-column prop="userSexLabel" label="性别" width="70" align="center" />
        <el-table-column prop="userStatusLabel" label="状态" width="70" align="center" />
        <el-table-column prop="helperName" label="协助者" width="100" show-overflow-tooltip />
        <el-table-column prop="firstHelperName" label="间接协助者" width="110" show-overflow-tooltip />
        <el-table-column prop="registerTime" label="注册时间" width="170" />
      </template>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="!canQuery" @click="openSet(row)">
            设定
          </el-button>
          <el-button link type="primary" :disabled="!canQuery" @click="openShow(row)">
            查看
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        :total="total"
        @current-change="reload()"
        @size-change="handlePageSizeChange"
      />
    </div>

    <el-dialog v-model="setVisible" title="设定产出目标" width="420px">
      <el-form label-width="90px">
        <el-form-item :label="mode === 'test' ? '年份' : '月份'">
          <el-date-picker
            v-if="mode === 'test'"
            v-model="setForm.period"
            type="year"
            value-format="YYYY"
            style="width: 100%"
            @change="loadExistingTarget"
          />
          <el-date-picker
            v-else
            v-model="setForm.period"
            type="month"
            value-format="YYYY-MM"
            style="width: 100%"
            @change="loadExistingTarget"
          />
        </el-form-item>
        <el-form-item label="目标金额">
          <el-input-number v-model="setForm.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="setVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showVisible" title="历年/历月目标" width="560px">
      <div class="show-user">{{ showUserName }}</div>
      <el-table :data="showRows" border>
        <el-table-column v-if="mode === 'test'" prop="year" label="年份" />
        <el-table-column v-else prop="month" label="月份" />
        <el-table-column prop="amount" label="目标金额" />
      </el-table>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  fetchSalePlanDepts,
  fetchSalePlanUsers,
  fetchTestPlanDepts,
  fetchTestPlanUsers,
  getSaleTarget,
  getTestTarget,
  saveSaleTarget,
  saveTestTarget,
  showSaleTargets,
  showTestTargets,
} from '@admin/api/digital'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const route = useRoute()
const mode = computed(() => (String(route.meta.planMode || 'test') === 'sale' ? 'sale' : 'test'))
const pageTitle = computed(() =>
  mode.value === 'sale' ? '销售人员产出计划设定' : '实验室人员产出计划设定'
)

const filters = reactive({ deptId: '', userName: '', trueName: '', userSex: '' as string })
const deptTree = ref<Record<string, unknown>[]>([])
const defaultDeptName = ref('')
const canQuery = ref(true)
const deptTreeProps = {
  label: 'deptName',
  value: 'id',
  children: 'children',
}
const loader = (params: Record<string, unknown>) => {
  if (!canQuery.value) {
    return Promise.resolve({ data: [], recordsTotal: 0, recordsFiltered: 0 })
  }
  const q: Record<string, unknown> = {
    ...params,
    deptId: filters.deptId,
    userName: filters.userName,
    trueName: filters.trueName,
  }
  if (filters.userSex !== '') {
    q.userSex = filters.userSex
  }
  return mode.value === 'sale' ? fetchSalePlanUsers(q) : fetchTestPlanUsers(q)
}
const { loading, rows, total, pagination, load } = useDataTable(loader)
pagination.pageSize = 20

type DeptNode = {
  id: string
  deptName: string
  superId: string
  children?: DeptNode[]
}

function pruneDeptTree(nodes: DeptNode[]): DeptNode[] {
  return nodes.map((node) => {
    const children = node.children?.length ? pruneDeptTree(node.children) : undefined
    return { ...node, children }
  })
}

function normalizeDeptTree(nodes: Record<string, unknown>[]): DeptNode[] {
  return pruneDeptTree(
    nodes.map((node) => {
      const children = Array.isArray(node.children)
        ? normalizeDeptTree(node.children as Record<string, unknown>[])
        : undefined
      return {
        id: String(node.id ?? ''),
        deptName: String(node.deptName || ''),
        superId: String(node.superId ?? '0'),
        children,
      }
    })
  )
}

function buildDeptTreeFromFlat(list: Record<string, unknown>[]): DeptNode[] {
  const nodes: DeptNode[] = list.map((item) => ({
    id: String(item.id ?? ''),
    deptName: String(item.deptName || ''),
    superId: String(item.superId ?? item.super_id ?? '0'),
    children: [],
  }))
  const map = new Map(nodes.map((n) => [n.id, n]))
  const roots: DeptNode[] = []
  for (const node of nodes) {
    if (!node.id) continue
    const parent = map.get(node.superId)
    if (parent && parent.id !== node.id) {
      parent.children = parent.children || []
      parent.children.push(node)
    } else {
      roots.push(node)
    }
  }
  return pruneDeptTree(roots)
}

const setVisible = ref(false)
const saving = ref(false)
const setForm = reactive({
  id: '' as string | number | '',
  userId: '',
  period: '',
  amount: 0,
})

const showVisible = ref(false)
const showUserName = ref('')
const showRows = ref<Record<string, unknown>[]>([])

function reload() {
  return load()
}

function handleSearch() {
  pagination.page = 1
  return reload()
}

function handleClear() {
  filters.userName = ''
  filters.trueName = ''
  filters.userSex = ''
  // 清空后回到权限默认部门（对齐 Java deptId2）
  if (defaultDeptId.value && defaultDeptId.value !== '0') {
    filters.deptId = defaultDeptId.value
  } else {
    filters.deptId = ''
  }
  pagination.page = 1
  return reload()
}

function handlePageSizeChange() {
  pagination.page = 1
  return reload()
}

const defaultDeptId = ref('')

async function applyPlanDepts(res: { res?: boolean; obj?: unknown }) {
  if (!isAjaxOk(res) || !res.obj || typeof res.obj !== 'object') {
    canQuery.value = false
    deptTree.value = []
    defaultDeptId.value = ''
    defaultDeptName.value = ''
    filters.deptId = ''
    return
  }
  const obj = res.obj as Record<string, unknown>
  canQuery.value = Boolean(obj.canQuery)
  defaultDeptId.value = String(obj.deptId || '')
  defaultDeptName.value = String(obj.deptName || '')
  const depts = Array.isArray(obj.depts) ? (obj.depts as Record<string, unknown>[]) : []
  deptTree.value = buildDeptTreeFromFlat(depts)
  if (defaultDeptId.value && defaultDeptId.value !== '0') {
    filters.deptId = defaultDeptId.value
  } else {
    filters.deptId = ''
  }
}

async function loadDepts() {
  if (mode.value === 'sale') {
    await applyPlanDepts(await fetchSalePlanDepts())
    return
  }
  await applyPlanDepts(await fetchTestPlanDepts())
}

async function openSet(row: Record<string, unknown>) {
  setForm.id = ''
  setForm.userId = String(row.id)
  setForm.period =
    mode.value === 'sale'
      ? `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`
      : String(new Date().getFullYear())
  setForm.amount = 0
  setVisible.value = true
  await loadExistingTarget()
}

async function loadExistingTarget() {
  if (!setForm.userId || !setForm.period) return
  const res =
    mode.value === 'sale'
      ? await getSaleTarget({ sale_user_id: setForm.userId, month: setForm.period })
      : await getTestTarget({ test_user_id: setForm.userId, year: setForm.period })
  if (isAjaxOk(res) && res.obj && typeof res.obj === 'object') {
    const obj = res.obj as Record<string, unknown>
    setForm.id = (obj.id as string | number) || ''
    setForm.amount = Number(obj.amount || 0)
  } else {
    setForm.id = ''
    setForm.amount = 0
  }
}

async function handleSave() {
  if (!setForm.period) {
    ElMessage.warning(mode.value === 'sale' ? '请选择月份' : '请选择年份')
    return
  }
  saving.value = true
  try {
    const res =
      mode.value === 'sale'
        ? await saveSaleTarget({
            id: setForm.id || undefined,
            sale_user_id: setForm.userId,
            month: setForm.period,
            amount: setForm.amount,
          })
        : await saveTestTarget({
            id: setForm.id || undefined,
            test_user_id: setForm.userId,
            year: setForm.period,
            amount: setForm.amount,
          })
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      setVisible.value = false
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function openShow(row: Record<string, unknown>) {
  const res =
    mode.value === 'sale' ? await showSaleTargets(String(row.id)) : await showTestTargets(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  showUserName.value = String(obj.trueName || obj.userName || '')
  showRows.value = Array.isArray(obj.list) ? (obj.list as Record<string, unknown>[]) : []
  showVisible.value = true
}

watch(mode, async () => {
  filters.deptId = ''
  filters.userName = ''
  filters.trueName = ''
  filters.userSex = ''
  pagination.page = 1
  pagination.pageSize = mode.value === 'test' ? 20 : 10
  await loadDepts()
  reload()
})

onMounted(async () => {
  await loadDepts()
  await reload()
})
</script>

<style scoped lang="scss">
.filter-form {
  margin-bottom: 12px;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.show-user {
  margin-bottom: 10px;
  font-weight: 600;
}
</style>
