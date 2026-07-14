<template>
  <admin-page-card title="评价管理">
    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column prop="goodsName" label="产品名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="goodsBrandName" label="产品品牌" width="120" show-overflow-tooltip />
      <el-table-column prop="customerName" label="客户企业" min-width="160" show-overflow-tooltip />
      <el-table-column label="买家评价" width="100" align="center">
        <template #default="{ row }">{{ evalTypeLabel(row.evaluateType) }}</template>
      </el-table-column>
      <el-table-column prop="evaluateInfo" label="评论内容" min-width="180" show-overflow-tooltip />
      <el-table-column label="评论状态" width="100" align="center">
        <template #default="{ row }">
          {{ Number(row.evaluateStatus) === 0 ? '显示' : '不显示' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
          <el-button link type="primary" @click="handleToggle(row)">
            {{ Number(row.evaluateStatus) === 0 ? '不显示' : '显示' }}
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

    <el-dialog v-model="detailVisible" title="评价详情" width="640px">
      <el-descriptions v-if="detail" :column="1" border>
        <el-descriptions-item label="产品名称">{{ detail.goodsName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="产品品牌">{{ detail.goodsBrandName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="客户企业">{{ detail.customerName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="买家评价">{{ evalTypeLabel(detail.evaluateType) }}</el-descriptions-item>
        <el-descriptions-item label="评论内容">{{ detail.evaluateInfo || '-' }}</el-descriptions-item>
        <el-descriptions-item label="评论状态">
          {{ Number(detail.evaluateStatus) === 0 ? '显示' : '不显示' }}
        </el-descriptions-item>
        <el-descriptions-item label="评价时间">{{ detail.addTime || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@/components/AdminPageCard.vue'
import { checkGoodsEvaluate, fetchGoodsEvaluateList, getGoodsEvaluateDetail } from '@/api/ops'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const detailVisible = ref(false)
const detail = ref<Record<string, unknown> | null>(null)

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchGoodsEvaluateList(params)
)

function evalTypeLabel(value: unknown) {
  const n = Number(value)
  if (n === 0) return '差评'
  if (n === 1) return '中评'
  if (n === 2) return '好评'
  return String(value ?? '-')
}

async function openDetail(row: Record<string, unknown>) {
  const res = await getGoodsEvaluateDetail(String(row.id))
  if (isAjaxOk(res) && res.obj) {
    detail.value = res.obj as Record<string, unknown>
    detailVisible.value = true
  } else {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
  }
}

async function handleToggle(row: Record<string, unknown>) {
  const next = Number(row.evaluateStatus) === 0 ? 1 : 0
  const res = await checkGoodsEvaluate(String(row.id), next)
  if (isAjaxOk(res)) {
    ElMessage.success('操作成功')
    await load()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}

onMounted(() => load())
</script>

<style scoped lang="scss">
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
