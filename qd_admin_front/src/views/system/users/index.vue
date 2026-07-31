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
      <el-form-item label="账号">
        <el-input v-model="userName" placeholder="账号" clearable />
      </el-form-item>
      <el-form-item label="姓名">
        <el-input v-model="trueName" placeholder="姓名" clearable />
      </el-form-item>
      <el-form-item label="性别">
        <el-select v-model="userSex" clearable placeholder="全部" style="width: 100px">
          <el-option label="全部" value="" />
          <el-option label="男" value="1" />
          <el-option label="女" value="0" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="55" label="#" />
      <el-table-column prop="userName" label="账号" min-width="110" />
      <el-table-column prop="trueName" label="姓名" min-width="100" />
      <el-table-column label="性别" width="70" align="center">
        <template #default="{ row }">{{ Number(row.userSex) === 0 ? '女' : '男' }}</template>
      </el-table-column>
      <el-table-column prop="utooType" label="用户类型" min-width="110" show-overflow-tooltip />
      <el-table-column prop="deptName" label="部门" min-width="120" show-overflow-tooltip />
      <el-table-column prop="mobilePhoneNumber" label="手机" min-width="120" />
      <el-table-column prop="registerTime" label="注册时间" min-width="160" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="Number(row.userStatus) === 1 ? 'success' : 'info'">
            {{ Number(row.userStatus) === 1 ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="520" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="openRoles(row)">修改权限</el-button>
          <el-button link type="primary" @click="openPowers(row)">查看权限</el-button>
          <el-button link type="warning" @click="openPassword(row)">重置密码</el-button>
          <el-button link type="primary" @click="openAccess(row)">订单访问权限</el-button>
          <el-button link type="primary" @click="openExpManage(row)">管理测试项目</el-button>
          <el-button
            link
            :type="Number(row.userStatus) === 1 ? 'danger' : 'success'"
            @click="toggleStatus(row)"
          >
            {{ Number(row.userStatus) === 1 ? '禁用' : '启用' }}
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="720px" destroy-on-close>
      <el-form label-width="130px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="账号" required>
              <el-input v-model="form.userName" :disabled="!!editingId" placeholder="3-20位字母数字下划线" />
            </el-form-item>
          </el-col>
          <el-col v-if="!editingId" :span="12">
            <el-form-item label="密码" required>
              <el-input v-model="form.userPassword" type="password" show-password placeholder="默认 123456" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" required>
              <el-input v-model="form.trueName" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-select v-model="form.userSex" style="width: 100%">
                <el-option :value="1" label="男" />
                <el-option :value="0" label="女" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="form.mobilePhoneNumber" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="QQ号">
              <el-input v-model="form.qqNumber" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="form.email" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门" required>
              <el-select v-model="form.deptId" filterable style="width: 100%">
                <el-option
                  v-for="item in deptOptions"
                  :key="String(item.id)"
                  :label="String(item.deptName || item.id)"
                  :value="String(item.id)"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="用户类型">
              <el-select v-model="form.utooType" filterable clearable style="width: 100%">
                <el-option
                  v-for="t in utooTypeOptions"
                  :key="String(t.typeName)"
                  :label="String(t.typeName)"
                  :value="String(t.typeName)"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联账号">
              <el-select v-model="form.userId" filterable clearable style="width: 100%">
                <el-option
                  v-for="m in memberOptions"
                  :key="String(m.id)"
                  :label="String(m.label || m.userName || m.id)"
                  :value="String(m.id)"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否拥有操作权限">
              <el-select v-model="form.isCzqx" style="width: 100%">
                <el-option :value="0" label="否" />
                <el-option :value="1" label="是" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="协助者">
              <el-select v-model="form.helperId" filterable clearable style="width: 100%">
                <el-option label="无协助者" value="" />
                <el-option
                  v-for="h in helperOptions"
                  :key="String(h.id)"
                  :label="String(h.label || h.trueName || h.userName)"
                  :value="String(h.id)"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否企业用户">
              <el-select v-model="form.accountType" style="width: 100%">
                <el-option :value="0" label="否" />
                <el-option :value="1" label="是" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否接收邮件推送">
              <el-select v-model="form.isEmail" style="width: 100%">
                <el-option :value="0" label="否" />
                <el-option :value="1" label="是" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否计算利息">
              <el-select v-model="form.isRate" style="width: 100%">
                <el-option :value="0" label="否" />
                <el-option :value="1" label="是" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
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
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.userDesc" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div v-if="editingId" class="log-block">
        <div class="log-title">操作记录</div>
        <el-table :data="editLogs" border size="small" max-height="220">
          <el-table-column prop="addTime" label="操作时间" min-width="160" />
          <el-table-column prop="userName" label="操作人员" min-width="100" />
          <el-table-column prop="logInfo" label="操作" min-width="220" show-overflow-tooltip />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="roleVisible" title="修改权限" width="480px">
      <el-form label-width="80px">
        <el-form-item label="用户">{{ roleTargetName }}</el-form-item>
        <el-form-item label="角色">
          <el-select v-model="roleForm.roleIds" multiple filterable style="width: 100%">
            <el-option
              v-for="item in roleOptions"
              :key="String(item.id)"
              :label="String(item.roleName || item.id)"
              :value="String(item.id)"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleVisible = false">取消</el-button>
        <el-button type="primary" :loading="roleSaving" @click="submitRoles">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pwdVisible" title="重置密码" width="420px">
      <el-form label-width="100px">
        <el-form-item label="用户">{{ pwdTargetName }}</el-form-item>
        <el-form-item label="新密码" required>
          <el-input v-model="pwdForm.userPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" required>
          <el-input v-model="pwdForm.pwd" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdSaving" @click="submitPassword">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="powerVisible" title="查看权限" width="560px">
      <p class="power-user">用户：{{ powerTargetName }}</p>
      <el-table :data="powerMenus" border size="small" max-height="360">
        <el-table-column type="index" width="50" />
        <el-table-column prop="menuName" label="菜单" min-width="160" />
        <el-table-column prop="url" label="路径" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-dialog>

    <el-dialog v-model="accessVisible" title="修改订单访问权限" width="640px" destroy-on-close>
      <p class="power-user">用户：{{ accessTargetName }}</p>
      <el-form label-width="100px">
        <el-form-item label="公司列表">
          <div class="check-toolbar">
            <el-button link type="primary" @click="accessForm.companyIds = accessCompanys.map((c) => String(c.id))">
              全选
            </el-button>
            <el-button link @click="accessForm.companyIds = []">全部取消</el-button>
          </div>
          <el-checkbox-group v-model="accessForm.companyIds" class="check-grid">
            <el-checkbox v-for="c in accessCompanys" :key="String(c.id)" :label="String(c.id)">
              {{ c.companyName }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="订单类型">
          <div class="check-toolbar">
            <el-button link type="primary" @click="accessForm.orderTypeIds = accessTypes.map((t) => String(t.id))">
              全选
            </el-button>
            <el-button link @click="accessForm.orderTypeIds = []">全部取消</el-button>
          </div>
          <el-checkbox-group v-model="accessForm.orderTypeIds" class="check-grid">
            <el-checkbox v-for="t in accessTypes" :key="String(t.id)" :label="String(t.id)">
              {{ t.typeName }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="销售人员">
          <el-select v-model="accessForm.saleUserIds" multiple filterable clearable style="width: 100%">
            <el-option
              v-for="u in accessSaleUsers"
              :key="String(u.id)"
              :label="String(u.label || u.trueName || u.userName)"
              :value="String(u.id)"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accessVisible = false">取消</el-button>
        <el-button type="primary" :loading="accessSaving" @click="submitAccess">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="expVisible" title="添加管理测试项目" width="560px" destroy-on-close>
      <p class="power-user">用户：{{ expTargetName }}</p>
      <el-form inline>
        <el-form-item label="添加项目">
          <el-select v-model="expSelectedId" filterable clearable placeholder="请选择项目" style="width: 260px">
            <el-option
              v-for="p in expAvailable"
              :key="String(p.id)"
              :label="String(p.name)"
              :value="String(p.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="expAdding" @click="addExpProject">添加</el-button>
        </el-form-item>
      </el-form>
      <el-table :data="expLinked" border size="small" max-height="320">
        <el-table-column type="index" width="50" />
        <el-table-column prop="emname" label="关联项目" min-width="220" />
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeExpProject(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  addUser,
  addUserExpManage,
  deleteUserExpManage,
  fetchDeptOptions,
  fetchUserAccessRights,
  fetchUserExpManageAvailable,
  fetchUserExpManageList,
  fetchUserFormOptions,
  fetchUserList,
  fetchUserPowers,
  fetchUserRoleOptions,
  getUserById,
  updateUser,
  updateUserAccessRights,
  updateUserPassword,
  updateUserRoles,
  updateUserStatus,
} from '@/api/system'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const deptId = ref('')
const userName = ref('')
const trueName = ref('')
const userSex = ref('')
const deptOptions = ref<Record<string, unknown>[]>([])
const roleOptions = ref<Record<string, unknown>[]>([])
const utooTypeOptions = ref<Record<string, unknown>[]>([])
const helperOptions = ref<Record<string, unknown>[]>([])
const memberOptions = ref<Record<string, unknown>[]>([])
const { loading, rows, total, pagination, load } = useDataTable(fetchUserList)

const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const saving = ref(false)
const editLogs = ref<Record<string, unknown>[]>([])
const form = reactive({
  userName: '',
  userPassword: '',
  trueName: '',
  userSex: 1,
  deptId: '0',
  roleIds: [] as string[],
  mobilePhoneNumber: '',
  qqNumber: '',
  email: '',
  userDesc: '',
  utooType: '',
  userId: '',
  isCzqx: 0,
  helperId: '',
  accountType: 0,
  isEmail: 1,
  isRate: 1,
})

const roleVisible = ref(false)
const roleSaving = ref(false)
const roleTargetId = ref('')
const roleTargetName = ref('')
const roleForm = reactive({ roleIds: [] as string[] })

const pwdVisible = ref(false)
const pwdSaving = ref(false)
const pwdTargetId = ref('')
const pwdTargetName = ref('')
const pwdForm = reactive({ userPassword: '', pwd: '' })

const powerVisible = ref(false)
const powerTargetName = ref('')
const powerMenus = ref<Record<string, unknown>[]>([])

const accessVisible = ref(false)
const accessSaving = ref(false)
const accessTargetId = ref('')
const accessTargetName = ref('')
const accessCompanys = ref<Record<string, unknown>[]>([])
const accessTypes = ref<Record<string, unknown>[]>([])
const accessSaleUsers = ref<Record<string, unknown>[]>([])
const accessForm = reactive({
  companyIds: [] as string[],
  orderTypeIds: [] as string[],
  saleUserIds: [] as string[],
})

const expVisible = ref(false)
const expAdding = ref(false)
const expTargetId = ref('')
const expTargetName = ref('')
const expSelectedId = ref('')
const expAvailable = ref<Record<string, unknown>[]>([])
const expLinked = ref<Record<string, unknown>[]>([])

const dialogTitle = computed(() => (editingId.value ? '编辑用户' : '添加用户'))

async function loadFormOptions() {
  const res = await fetchUserFormOptions()
  if (!isAjaxOk(res) || !res.obj) return
  const obj = res.obj as Record<string, unknown>
  if (Array.isArray(obj.roles)) roleOptions.value = obj.roles as Record<string, unknown>[]
  if (Array.isArray(obj.utooTypes)) utooTypeOptions.value = obj.utooTypes as Record<string, unknown>[]
  if (Array.isArray(obj.helpers)) helperOptions.value = obj.helpers as Record<string, unknown>[]
  if (Array.isArray(obj.members)) memberOptions.value = obj.members as Record<string, unknown>[]
}

onMounted(async () => {
  deptOptions.value = await fetchDeptOptions()
  roleOptions.value = await fetchUserRoleOptions()
  await loadFormOptions()
  await reload()
})

function reload() {
  return load({
    deptId: deptId.value,
    userName: userName.value.trim(),
    trueName: trueName.value.trim(),
    userSex: userSex.value,
  })
}

function resetForm() {
  editingId.value = null
  editLogs.value = []
  Object.assign(form, {
    userName: '',
    userPassword: '123456',
    trueName: '',
    userSex: 1,
    deptId: '0',
    roleIds: [],
    mobilePhoneNumber: '',
    qqNumber: '',
    email: '',
    userDesc: '',
    utooType: '',
    userId: '',
    isCzqx: 0,
    helperId: '',
    accountType: 0,
    isEmail: 1,
    isRate: 1,
  })
}

async function openCreate() {
  resetForm()
  await loadFormOptions()
  dialogVisible.value = true
}

async function openEdit(row: Record<string, unknown>) {
  await loadFormOptions()
  const res = await getUserById(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载用户失败'))
    return
  }
  const data = res.obj as Record<string, unknown>
  editingId.value = String(data.id)
  form.userName = String(data.userName || '')
  form.trueName = String(data.trueName || '')
  form.userSex = Number(data.userSex ?? 1)
  form.deptId = String(data.deptId || '0')
  form.roleIds = Array.isArray(data.roleIds) ? data.roleIds.map(String) : []
  form.mobilePhoneNumber = String(data.mobilePhoneNumber || '')
  form.qqNumber = String(data.qqNumber || '')
  form.email = String(data.email || '')
  form.userDesc = String(data.userDesc || '')
  form.utooType = String(data.utooType || '')
  form.userId = String(data.userId || '')
  form.isCzqx = Number(data.isCzqx || 0)
  form.helperId = String(data.helperId || '')
  form.accountType = Number(data.accountType || 0)
  form.isEmail = Number(data.isEmail ?? 1)
  form.isRate = Number(data.isRate ?? 1)
  editLogs.value = Array.isArray(data.logs) ? (data.logs as Record<string, unknown>[]) : []
  dialogVisible.value = true
}

function buildPayload() {
  return {
    userName: form.userName.trim(),
    trueName: form.trueName.trim(),
    userSex: form.userSex,
    deptId: form.deptId,
    roleIds: form.roleIds,
    mobilePhoneNumber: form.mobilePhoneNumber,
    qqNumber: form.qqNumber,
    email: form.email,
    userDesc: form.userDesc,
    utooType: form.utooType,
    userId: form.userId || undefined,
    isCzqx: form.isCzqx,
    helperId: form.helperId || undefined,
    accountType: form.accountType,
    isEmail: form.isEmail,
    isRate: form.isRate,
  }
}

async function handleSubmit() {
  if (!form.userName.trim()) {
    ElMessage.warning('请填写账号')
    return
  }
  if (!form.trueName.trim()) {
    ElMessage.warning('请填写姓名')
    return
  }
  if (!editingId.value && (form.userPassword || '123456').length < 6) {
    ElMessage.warning('密码长度至少6位')
    return
  }
  saving.value = true
  try {
    const payload: Record<string, unknown> = buildPayload()
    if (!editingId.value) {
      payload.userPassword = form.userPassword || '123456'
    }
    const res = editingId.value
      ? await updateUser({ ...payload, id: editingId.value })
      : await addUser(payload)
    if (isAjaxOk(res) || res === true || (res as { res?: boolean }).res === true) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res as never, '保存失败，用户名可能已存在'))
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: Record<string, unknown>) {
  const next = Number(row.userStatus) === 1 ? 0 : 1
  await ElMessageBox.confirm(next === 1 ? '确定启用该用户吗？' : '确定禁用该用户吗？', '提示', {
    type: 'warning',
  })
  const res = await updateUserStatus(String(row.id), next)
  if (isAjaxOk(res) || res === true) {
    ElMessage.success('操作成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res as never, '操作失败'))
  }
}

async function openRoles(row: Record<string, unknown>) {
  roleTargetId.value = String(row.id)
  roleTargetName.value = `${row.trueName || ''}（${row.userName || ''}）`
  const res = await getUserById(String(row.id))
  const data = isAjaxOk(res) && res.obj ? (res.obj as Record<string, unknown>) : row
  roleForm.roleIds = Array.isArray(data.roleIds) ? data.roleIds.map(String) : []
  roleVisible.value = true
}

async function submitRoles() {
  roleSaving.value = true
  try {
    const res = await updateUserRoles({ id: roleTargetId.value, roleIds: roleForm.roleIds })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success('权限已更新')
    roleVisible.value = false
  } finally {
    roleSaving.value = false
  }
}

function openPassword(row: Record<string, unknown>) {
  pwdTargetId.value = String(row.id)
  pwdTargetName.value = `${row.trueName || ''}（${row.userName || ''}）`
  pwdForm.userPassword = ''
  pwdForm.pwd = ''
  pwdVisible.value = true
}

async function submitPassword() {
  if (!pwdForm.userPassword || pwdForm.userPassword.length < 6) {
    ElMessage.warning('密码长度至少6位')
    return
  }
  if (pwdForm.userPassword !== pwdForm.pwd) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  pwdSaving.value = true
  try {
    const res = await updateUserPassword({
      id: pwdTargetId.value,
      userPassword: pwdForm.userPassword,
      pwd: pwdForm.pwd,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '重置失败'))
      return
    }
    ElMessage.success('密码已重置')
    pwdVisible.value = false
  } finally {
    pwdSaving.value = false
  }
}

async function openPowers(row: Record<string, unknown>) {
  powerTargetName.value = `${row.trueName || ''}（${row.userName || ''}）`
  const res = await fetchUserPowers(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as { menus?: Record<string, unknown>[] }
  powerMenus.value = Array.isArray(obj.menus) ? obj.menus : []
  powerVisible.value = true
}

async function openAccess(row: Record<string, unknown>) {
  accessTargetId.value = String(row.id)
  accessTargetName.value = `${row.trueName || ''}（${row.userName || ''}）`
  const res = await fetchUserAccessRights(String(row.id))
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  const obj = res.obj as Record<string, unknown>
  accessCompanys.value = Array.isArray(obj.companys) ? (obj.companys as Record<string, unknown>[]) : []
  accessTypes.value = Array.isArray(obj.types) ? (obj.types as Record<string, unknown>[]) : []
  accessSaleUsers.value = Array.isArray(obj.saleUsers) ? (obj.saleUsers as Record<string, unknown>[]) : []
  accessForm.companyIds = (Array.isArray(obj.hasCompanys) ? obj.hasCompanys : []).map(String)
  accessForm.orderTypeIds = (Array.isArray(obj.hasTypes) ? obj.hasTypes : []).map(String)
  accessForm.saleUserIds = (Array.isArray(obj.userInfo) ? obj.userInfo : []).map(String)
  accessVisible.value = true
}

async function submitAccess() {
  accessSaving.value = true
  try {
    const res = await updateUserAccessRights({
      userId: accessTargetId.value,
      companyIds: accessForm.companyIds,
      orderTypeIds: accessForm.orderTypeIds,
      saleUserIds: accessForm.saleUserIds,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success('保存成功')
    accessVisible.value = false
  } finally {
    accessSaving.value = false
  }
}

async function refreshExpManage() {
  const [avail, linked] = await Promise.all([
    fetchUserExpManageAvailable(expTargetId.value),
    fetchUserExpManageList(expTargetId.value),
  ])
  expAvailable.value =
    isAjaxOk(avail) && Array.isArray(avail.obj) ? (avail.obj as Record<string, unknown>[]) : []
  expLinked.value =
    isAjaxOk(linked) && Array.isArray(linked.obj) ? (linked.obj as Record<string, unknown>[]) : []
  expSelectedId.value = ''
}

async function openExpManage(row: Record<string, unknown>) {
  expTargetId.value = String(row.id)
  expTargetName.value = `${row.trueName || ''}（${row.userName || ''}）`
  await refreshExpManage()
  expVisible.value = true
}

async function addExpProject() {
  if (!expSelectedId.value) {
    ElMessage.warning('请选择项目')
    return
  }
  expAdding.value = true
  try {
    const res = await addUserExpManage({
      userId: expTargetId.value,
      exp_manage_id: expSelectedId.value,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '添加失败'))
      return
    }
    ElMessage.success('添加成功')
    await refreshExpManage()
  } finally {
    expAdding.value = false
  }
}

async function removeExpProject(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该关联项目吗？', '提示', { type: 'warning' })
  const res = await deleteUserExpManage(String(row.id))
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
    return
  }
  ElMessage.success('已删除')
  await refreshExpManage()
}
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.log-block {
  margin-top: 12px;
}
.log-title {
  font-weight: 600;
  margin-bottom: 8px;
}
.power-user {
  margin: 0 0 10px;
  color: #606266;
}
.check-toolbar {
  margin-bottom: 6px;
}
.check-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 12px;
  max-height: 180px;
  overflow: auto;
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
}
</style>
