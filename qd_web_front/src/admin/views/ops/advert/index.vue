<template>
  <admin-page-card title="广告管理">
    <div class="tab-row">
      <el-button :type="!dialogVisible ? 'primary' : 'default'" @click="stayList">所有广告</el-button>
      <el-button :type="dialogVisible && !isEdit ? 'primary' : 'default'" @click="openCreate">
        新增广告
      </el-button>
    </div>

    <el-form :inline="true" class="filter-form" @submit.prevent="reload">
      <el-form-item label="广告名称">
        <el-input
          v-model="filters.ad_title"
          clearable
          placeholder="广告名称"
          style="width: 200px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload">搜索</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="adTitle" label="广告名称" min-width="160" show-overflow-tooltip />
      <el-table-column label="所属广告位" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ row.apTitle || '-' }}</template>
      </el-table-column>
      <el-table-column label="类别" width="100" align="center">
        <template #default="{ row }">{{ apTypeLabel(row.apType) }}</template>
      </el-table-column>
      <el-table-column label="开始时间" width="120" align="center">
        <template #default="{ row }">{{ formatDate(row.adBeginTime) }}</template>
      </el-table-column>
      <el-table-column label="结束时间" width="120" align="center">
        <template #default="{ row }">{{ formatDate(row.adEndTime) }}</template>
      </el-table-column>
      <el-table-column label="点击率" width="90" align="center">
        <template #default="{ row }">{{ row.adClickNum ?? 0 }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <span class="sep">|</span>
          <el-button link type="primary" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="() => load({ ad_title: filters.ad_title })"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑广告' : '新增广告'" width="640px">
      <el-form label-width="100px">
        <el-form-item label="广告名称" required>
          <el-input v-model="form.ad_title" />
        </el-form-item>
        <el-form-item label="所属广告位" required>
          <el-select v-model="form.ad_ap_id" clearable filterable style="width: 100%">
            <el-option
              v-for="item in posOptions"
              :key="String(item.id)"
              :label="String(item.apTitle || item.id)"
              :value="Number(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间" required>
          <el-date-picker
            v-model="form.ad_begin_time"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" required>
          <el-date-picker
            v-model="form.ad_end_time"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="链接" required>
          <el-input v-model="form.ad_url" />
        </el-form-item>
        <el-form-item label="文本">
          <el-input v-model="form.ad_text" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="终端" required>
          <el-select v-model="form.mark" style="width: 160px">
            <el-option label="PC" :value="1" />
            <el-option label="MOBILE" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.ad_slide_sequence" :min="0" />
        </el-form-item>
        <el-form-item label="图片附件ID">
          <el-input v-model="form.ad_acc_id" />
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
  deleteAdvert,
  fetchAdvertList,
  fetchAdvPosOptions,
  saveAdvert,
} from '@admin/api/ops'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const AP_TYPE_MAP: Record<string, string> = {
  img: '图片',
  scroll: '滚动',
  slide: '幻灯',
  text: '文字',
}

const filters = reactive({ ad_title: '' })
const { loading, rows, total, pagination, load } = useDataTable(fetchAdvertList)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const posOptions = ref<Record<string, unknown>[]>([])
const form = reactive({
  id: '',
  ad_title: '',
  ad_ap_id: undefined as number | undefined,
  ad_begin_time: '',
  ad_end_time: '',
  ad_url: '',
  ad_text: '',
  mark: 1,
  ad_slide_sequence: 0,
  ad_acc_id: '',
})

function stayList() {
  dialogVisible.value = false
  isEdit.value = false
}

function apTypeLabel(type: unknown) {
  return AP_TYPE_MAP[String(type || '')] || String(type || '-')
}

function formatDate(val: unknown) {
  if (!val) return '-'
  const s = String(val)
  return s.length >= 10 ? s.slice(0, 10) : s
}

function reload() {
  pagination.page = 1
  return load({ ad_title: filters.ad_title })
}

onMounted(async () => {
  await reload()
  const res = await fetchAdvPosOptions()
  if (isAjaxOk(res) && Array.isArray(res.obj)) {
    posOptions.value = res.obj as Record<string, unknown>[]
  }
})

function resetForm() {
  form.id = ''
  form.ad_title = ''
  form.ad_ap_id = undefined
  form.ad_begin_time = ''
  form.ad_end_time = ''
  form.ad_url = ''
  form.ad_text = ''
  form.mark = 1
  form.ad_slide_sequence = 0
  form.ad_acc_id = ''
}

function openCreate() {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  form.id = String(row.id)
  form.ad_title = String(row.adTitle || '')
  form.ad_ap_id = row.adApId != null ? Number(row.adApId) : undefined
  form.ad_begin_time = String(row.adBeginTime || '')
  form.ad_end_time = String(row.adEndTime || '')
  form.ad_url = String(row.adUrl || '')
  form.ad_text = String(row.adText || '')
  form.mark = Number(row.mark || 1)
  form.ad_slide_sequence = Number(row.adSlideSequence || 0)
  form.ad_acc_id = String(row.adAccId || '')
  isEdit.value = true
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.ad_title.trim()) {
    ElMessage.warning('请填写广告名称')
    return
  }
  if (!form.ad_ap_id) {
    ElMessage.warning('请选择所属广告位')
    return
  }
  if (!form.ad_begin_time || !form.ad_end_time) {
    ElMessage.warning('请选择开始/结束时间')
    return
  }
  if (!form.ad_url.trim()) {
    ElMessage.warning('请填写链接')
    return
  }
  saving.value = true
  try {
    const res = await saveAdvert({ ...form })
    if (isAjaxOk(res)) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('删除后不可恢复，是否继续?', '提示', { type: 'warning' })
  const res = await deleteAdvert(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '删除失败'))
  }
}
</script>

<style scoped lang="scss">
.tab-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.filter-form {
  margin-bottom: 12px;
}

.sep {
  margin: 0 4px;
  color: var(--el-text-color-secondary);
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
