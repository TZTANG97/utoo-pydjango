<template>
  <admin-page-card title="会员线下充值">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增充值</el-button>
    </template>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="充值单号">
        <el-input v-model="filters.recharge_num" clearable />
      </el-form-item>
      <el-form-item label="开始时间">
        <el-date-picker v-model="filters.startTime" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" />
      </el-form-item>
      <el-form-item label="结束时间">
        <el-date-picker v-model="filters.endTime" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload()">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="rechargeNum" label="充值单号" min-width="180" />
      <el-table-column prop="addTime" label="时间" min-width="160" />
      <el-table-column prop="trueName" label="会员" width="100" />
      <el-table-column prop="mobile" label="手机" min-width="120" />
      <el-table-column prop="money" label="金额" width="100" />
      <el-table-column label="类型" width="90">
        <template #default="{ row }">
          {{ Number(row.rechargeType) === 1 ? '赠送' : '充值' }}
        </template>
      </el-table-column>
      <el-table-column prop="kpje" label="已开票" width="90" />
      <el-table-column prop="czry" label="操作人" width="100" />
      <el-table-column prop="mark" label="备注" min-width="140" show-overflow-tooltip />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="reload()"
      />
    </div>

    <el-dialog v-model="createVisible" title="新增线下充值" width="680px" destroy-on-close>
      <el-form label-width="130px">
        <el-form-item label="会员电话" required>
          <div class="user-pick">
            <el-input
              :model-value="createForm.mobile"
              readonly
              placeholder="点击选择会员"
              @click="openPicker"
            />
            <el-button @click="openPicker">选择</el-button>
          </div>
        </el-form-item>
        <el-form-item label="姓名">
          <span class="readonly-text">{{ createForm.trueName || '-' }}</span>
        </el-form-item>
        <el-form-item label="公司">
          <span class="readonly-text">{{ createForm.companyName || '-' }}</span>
        </el-form-item>
        <el-form-item label="账户余额">
          <span class="readonly-text">{{ balanceText }}</span>
        </el-form-item>
        <el-form-item label="充值金额" required>
          <el-input-number v-model="createForm.money" :min="0.01" :precision="2" :step="100" />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-radio-group v-model="createForm.recharge_type">
            <el-radio :value="0">充值</el-radio>
            <el-radio :value="1">赠送</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="上传用户付款资料">
          <div class="upload-block">
            <div v-if="payFiles.length" class="file-list">
              <div v-for="(f, idx) in payFiles" :key="String(f.id)" class="file-item">
                <span class="file-name" :title="String(f.info || f.name || '')">
                  {{ f.info || f.name || `附件${idx + 1}` }}
                </span>
                <el-button link type="danger" @click="removePayFile(idx)">删除</el-button>
              </div>
            </div>
            <el-upload :show-file-list="false" :http-request="onUploadPayFile" accept="*">
              <el-button :loading="uploading">上传文件</el-button>
            </el-upload>
          </div>
        </el-form-item>
        <el-form-item label="充值备注">
          <el-input
            v-model="createForm.mark"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            placeholder="请输入内容最多500字"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">确认充值</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pickerVisible" title="选择会员" width="780px">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="手机">
          <el-input v-model="pickerMobile" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadPicker()">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="pickerLoading" :data="pickerRows" border stripe @row-click="pickUser">
        <el-table-column prop="trueName" label="姓名" width="120" />
        <el-table-column prop="mobile" label="手机" min-width="120" />
        <el-table-column prop="companyName" label="公司" min-width="160" />
        <el-table-column prop="ye" label="余额" width="100" />
        <el-table-column prop="userName" label="用户名" min-width="120" />
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="pickerPagination.page"
          v-model:page-size="pickerPagination.pageSize"
          layout="total, prev, pager, next"
          :total="pickerTotal"
          @current-change="loadPicker()"
        />
      </div>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="充值详情" width="560px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="充值单号">{{ detail.rechargeNum }}</el-descriptions-item>
        <el-descriptions-item label="会员">{{ detail.trueName }}</el-descriptions-item>
        <el-descriptions-item label="手机">{{ detail.mobile }}</el-descriptions-item>
        <el-descriptions-item label="金额">{{ detail.money }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          {{ Number(detail.rechargeType) === 1 ? '赠送' : '充值' }}
        </el-descriptions-item>
        <el-descriptions-item label="操作人">{{ detail.czry }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ detail.mark }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import {
  addOfflineRecharge,
  fetchOfflineRechargeList,
  fetchRechargeUserPicker,
  getOfflineRecharge,
} from '@admin/api/member'
import { deleteExpOrderFile, uploadExpOrderFile } from '@admin/api/experiment'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const filters = reactive({
  recharge_num: '',
  startTime: '',
  endTime: '',
})
const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchOfflineRechargeList({ ...params, ...filters })
)

const createVisible = ref(false)
const pickerVisible = ref(false)
const detailVisible = ref(false)
const saving = ref(false)
const uploading = ref(false)
const payFiles = ref<Record<string, unknown>[]>([])
const createForm = reactive({
  user_id: '',
  money: 100,
  recharge_type: 0,
  mark: '',
  trueName: '',
  mobile: '',
  companyName: '',
  ye: 0 as number | string,
})
const detail = reactive<Record<string, unknown>>({})
const pickerMobile = ref('')
const {
  loading: pickerLoading,
  rows: pickerRows,
  total: pickerTotal,
  pagination: pickerPagination,
  load: loadPickerBase,
} = useDataTable((params) => fetchRechargeUserPicker({ ...params, mobile: pickerMobile.value }))

const balanceText = computed(() => {
  if (!createForm.user_id) return '￥0'
  const n = Number(createForm.ye)
  return Number.isFinite(n) ? `￥${n}` : `￥${createForm.ye || 0}`
})

function reload() {
  return load()
}

function loadPicker() {
  return loadPickerBase()
}

onMounted(() => reload())

function openPicker() {
  pickerVisible.value = true
  loadPicker()
}

function openCreate() {
  createForm.user_id = ''
  createForm.money = 100
  createForm.recharge_type = 0
  createForm.mark = ''
  createForm.trueName = ''
  createForm.mobile = ''
  createForm.companyName = ''
  createForm.ye = 0
  payFiles.value = []
  createVisible.value = true
}

function pickUser(row: Record<string, unknown>) {
  createForm.user_id = String(row.id)
  createForm.trueName = String(row.trueName || '')
  createForm.mobile = String(row.mobile || '')
  createForm.companyName = String(row.companyName || row.company_name || '')
  createForm.ye = (row.ye as number | string) ?? 0
  pickerVisible.value = false
}

async function onUploadPayFile(options: { file: File }) {
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('orderdata', options.file)
    const res = await uploadExpOrderFile(fd)
    if (!isAjaxOk(res) || !res.obj) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    payFiles.value.push(res.obj as Record<string, unknown>)
    ElMessage.success('上传成功')
  } finally {
    uploading.value = false
  }
}

async function removePayFile(idx: number) {
  const file = payFiles.value[idx]
  if (!file) return
  try {
    await ElMessageBox.confirm('确定删除此文件？', '提示', { type: 'warning' })
  } catch {
    return
  }
  const id = file.id
  if (id != null && String(id) !== '') {
    const res = await deleteExpOrderFile(String(id))
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '删除失败'))
      return
    }
  }
  payFiles.value.splice(idx, 1)
  ElMessage.success('删除成功')
}

async function handleCreate() {
  if (!createForm.user_id) {
    ElMessage.warning('请选择会员')
    return
  }
  if (!createForm.money || createForm.money <= 0) {
    ElMessage.warning('充值金额不可为0')
    return
  }
  try {
    await ElMessageBox.confirm(
      `请再次确认充值信息 电话:${createForm.mobile}，姓名：${createForm.trueName}，充值金额：${createForm.money}元?`,
      '确认充值',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  saving.value = true
  try {
    const res = await addOfflineRecharge({
      user_id: createForm.user_id,
      money: createForm.money,
      recharge_type: createForm.recharge_type,
      mark: createForm.mark,
      accessoryId: payFiles.value
        .map((f) => f.id)
        .filter((id) => id != null && String(id) !== ''),
    })
    if (isAjaxOk(res)) {
      ElMessage.success('充值成功')
      createVisible.value = false
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '充值失败'))
  } finally {
    saving.value = false
  }
}

async function openDetail(row: Record<string, unknown>) {
  const res = await getOfflineRecharge(String(row.id))
  if (isAjaxOk(res) && res.obj) {
    Object.assign(detail, res.obj as Record<string, unknown>)
    detailVisible.value = true
  } else {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
  }
}
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
.user-pick {
  display: flex;
  gap: 8px;
  width: 100%;
}
.readonly-text {
  line-height: 32px;
  color: var(--el-text-color-regular);
}
.upload-block {
  width: 100%;
}
.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-bottom: 8px;
}
.file-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.file-name {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
