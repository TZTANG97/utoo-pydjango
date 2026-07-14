<template>
  <admin-page-card title="收付款方式">
    <template #actions>
      <el-button type="primary" @click="dialogVisible = true">添加收付款</el-button>
    </template>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" width="60" label="#" />
      <el-table-column prop="name" label="收付款名称" min-width="160" />
      <el-table-column label="收付款方式" min-width="140">
        <template #default="{ row }">{{ payTypeLabel(row.payType) }}</template>
      </el-table-column>
      <el-table-column label="次数" width="100">
        <template #default="{ row }">
          <span v-if="row.payType === 1 || row.payType === 2">{{ row.nums || '-' }}</span>
          <span v-else-if="row.payType === 3">{{ row.jszq === 1 ? '月' : '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="收付款比例" min-width="180">
        <template #default="{ row }">
          <span v-if="row.payType === 1">{{ row.scaleVal || '-' }}</span>
          <span v-else-if="row.payType === 2">比例平均分配</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            :type="row.delStatus ? 'success' : 'danger'"
            @click="toggleStatus(row)"
          >
            {{ row.delStatus ? '启用' : '禁用' }}
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
        @current-change="load()"
      />
    </div>

    <el-dialog v-model="dialogVisible" title="添加收付款方式" width="520px">
      <el-form label-width="110px">
        <el-form-item label="收付款名称">
          <el-input v-model="form.name" placeholder="请输入收付款名称" />
        </el-form-item>
        <el-form-item label="收付款方式">
          <el-radio-group v-model="form.payType">
            <el-radio :value="1">按次数比例自定义</el-radio>
            <el-radio :value="2">按次数比例平均</el-radio>
            <el-radio :value="3">按周期</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.payType !== 3" label="收付款次数">
          <el-input-number v-model="form.nums" :min="1" :max="72" />
        </el-form-item>
        <el-form-item v-if="form.payType === 1" label="比例设置">
          <el-input
            v-model="form.scaleVal"
            placeholder="如 30,40,30"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item v-if="form.payType === 3" label="结算周期">
          <el-select v-model="form.jszq" style="width: 160px">
            <el-option label="按月结算" :value="1" />
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
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { fetchPaytypeList, submitPaytype, updatePaytypeStatus } from '@/api/order-settings'
import { useDataTable } from '@/composables/useDataTable'
import { isAjaxOk } from '@/utils/request'

const { loading, rows, total, pagination, load } = useDataTable(fetchPaytypeList)
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  name: '',
  payType: 1,
  nums: 1,
  scaleVal: '',
  jszq: 1,
})

onMounted(() => load())

function payTypeLabel(value: unknown) {
  const num = Number(value)
  if (num === 1 || num === 2) return '按次数'
  if (num === 3) return '按周期'
  return '-'
}

async function handleSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入收付款名称')
    return
  }
  saving.value = true
  try {
    const ok = await submitPaytype({ ...form, name: form.name.trim() })
    if (ok) {
      ElMessage.success('添加成功')
      dialogVisible.value = false
      form.name = ''
      await load()
      return
    }
    ElMessage.error('名称已存在或保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: Record<string, unknown>) {
  const status = row.delStatus ? '0' : '1'
  const res = await updatePaytypeStatus(String(row.id), status as '0' | '1')
  if (isAjaxOk(res)) {
    ElMessage.success('操作成功')
    await load()
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
