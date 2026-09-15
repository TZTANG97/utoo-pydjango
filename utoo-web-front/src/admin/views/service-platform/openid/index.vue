<template>
  <admin-page-card title="OpenID管理">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增 OpenID</el-button>
    </template>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="openid" label="OpenID" min-width="280" show-overflow-tooltip />
      <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
      <el-table-column prop="addTime" label="添加时间" min-width="160" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
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
        @current-change="load()"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      title="新增 OpenID"
      width="480px"
      append-to-body
      destroy-on-close
    >
      <el-form label-width="80px">
        <el-form-item label="OpenID" required>
          <el-input v-model="form.openid" placeholder="请输入 OpenID" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" placeholder="备注（可选）" />
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
import { onActivated, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { deleteOpenid, fetchOpenidList, submitOpenid } from '@admin/api/service-platform'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const { loading, rows, total, pagination, load } = useDataTable(fetchOpenidList)
const saving = ref(false)
const dialogVisible = ref(false)
const form = reactive({
  openid: '',
  remark: '',
})

onMounted(() => load())

function openCreate() {
  form.openid = ''
  form.remark = ''
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.openid.trim()) {
    ElMessage.warning('请填写 OpenID')
    return
  }
  saving.value = true
  try {
    const res = await submitOpenid({
      openid: form.openid.trim(),
      remark: form.remark.trim(),
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '添加失败'))
      return
    }
    dialogVisible.value = false
    ElMessage.success('添加成功')
    pagination.page = 1
    await load()
  } catch {
    // 网络异常由 request 拦截器提示
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该 OpenID 吗？', '提示', { type: 'warning' })
  try {
    const res = await deleteOpenid(String(row.id))
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '删除失败'))
      return
    }
    ElMessage.success('删除成功')
    await load()
  } catch {
    // 网络异常由 request 拦截器提示
  }
}

onActivated(() => {
  load()
})
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
