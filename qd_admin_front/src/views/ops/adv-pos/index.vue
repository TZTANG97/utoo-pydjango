<template>
  <admin-page-card title="广告位管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增广告位</el-button>
    </template>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="apTitle" label="广告位名称" min-width="200" show-overflow-tooltip />
      <el-table-column label="类别" width="100" align="center">
        <template #default="{ row }">{{ apTypeLabel(row.apType) }}</template>
      </el-table-column>
      <el-table-column prop="apWidth" label="宽度" width="90" align="center" />
      <el-table-column prop="apHeight" label="高度" width="90" align="center" />
      <el-table-column label="广告类型" width="120" align="center">
        <template #default="{ row }">
          {{ Number(row.apShowType) === 1 ? '随机广告' : '固定广告' }}
        </template>
      </el-table-column>
      <el-table-column label="广告状态" width="100" align="center">
        <template #default="{ row }">
          {{ Number(row.apStatus) === 1 ? '启用' : '禁用' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            link
            type="danger"
            :disabled="Number(row.apSysType) === 0"
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
        @current-change="() => load()"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑广告位' : '新增广告位'" width="640px">
      <el-form label-width="100px">
        <el-form-item label="广告位名称" required>
          <el-input v-model="form.ap_title" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.ap_type" style="width: 180px">
            <el-option label="图片" value="img" />
            <el-option label="滚动" value="scroll" />
            <el-option label="幻灯" value="slide" />
            <el-option label="文本" value="text" />
          </el-select>
        </el-form-item>
        <el-form-item label="宽度">
          <el-input-number v-model="form.ap_width" :min="0" />
        </el-form-item>
        <el-form-item label="高度">
          <el-input-number v-model="form.ap_height" :min="0" />
        </el-form-item>
        <el-form-item label="广告类型">
          <el-select v-model="form.ap_show_type" style="width: 180px">
            <el-option label="固定广告" :value="0" />
            <el-option label="随机广告" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.ap_content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="广告状态">
          <el-switch
            v-model="form.ap_status"
            :active-value="1"
            :inactive-value="0"
            active-text="启用"
            inactive-text="禁用"
          />
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
import AdminPageCard from '@/components/AdminPageCard.vue'
import { deleteAdvPos, fetchAdvPosList, saveAdvPos } from '@/api/ops'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const AP_TYPE_MAP: Record<string, string> = {
  img: '图片',
  scroll: '滚动',
  slide: '幻灯',
  text: '文字',
}

const { loading, rows, total, pagination, load } = useDataTable(fetchAdvPosList)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = reactive({
  id: '',
  ap_title: '',
  ap_type: 'img',
  ap_width: 0,
  ap_height: 0,
  ap_content: '',
  ap_status: 1,
  ap_use_status: 0,
  ap_price: 0,
  ap_sys_type: 1,
  ap_show_type: 0,
  mark: 1,
})

function apTypeLabel(type: unknown) {
  return AP_TYPE_MAP[String(type || '')] || String(type || '-')
}

function reload() {
  pagination.page = 1
  return load()
}

onMounted(() => reload())

function resetForm() {
  form.id = ''
  form.ap_title = ''
  form.ap_type = 'img'
  form.ap_width = 0
  form.ap_height = 0
  form.ap_content = ''
  form.ap_status = 1
  form.ap_sys_type = 1
  form.ap_show_type = 0
}

function openCreate() {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  form.id = String(row.id)
  form.ap_title = String(row.apTitle || '')
  form.ap_type = String(row.apType || 'img')
  form.ap_width = Number(row.apWidth || 0)
  form.ap_height = Number(row.apHeight || 0)
  form.ap_content = String(row.apContent || '')
  form.ap_status = Number(row.apStatus ?? 1)
  form.ap_sys_type = Number(row.apSysType ?? 1)
  form.ap_show_type = Number(row.apShowType ?? 0)
  isEdit.value = true
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.ap_title.trim()) {
    ElMessage.warning('请填写广告位名称')
    return
  }
  saving.value = true
  try {
    const res = await saveAdvPos({ ...form })
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
  await ElMessageBox.confirm('确定删除该广告位吗？', '提示', { type: 'warning' })
  const res = await deleteAdvPos(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('删除成功')
    await reload()
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
