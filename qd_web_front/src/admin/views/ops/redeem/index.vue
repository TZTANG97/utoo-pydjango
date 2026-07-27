<template>
  <admin-page-card title="用户兑换记录">
    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="兑换开始时间">
        <el-date-picker
          v-model="filters.order_startime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="兑换开始时间"
        />
      </el-form-item>
      <el-form-item label="兑换结束时间">
        <el-date-picker
          v-model="filters.order_endtime"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="兑换结束时间"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable style="width: 140px" placeholder="全部状态">
          <el-option label="待发货" :value="1" />
          <el-option label="已发货" :value="2" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload()">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column prop="orderId" label="兑换编号" min-width="140" show-overflow-tooltip />
      <el-table-column prop="redeemTime" label="兑换时间" min-width="160" />
      <el-table-column prop="userName" label="收件人" width="120" />
      <el-table-column prop="mobile" label="电话" width="120" />
      <el-table-column prop="address" label="收件地址" min-width="180" show-overflow-tooltip />
      <el-table-column prop="goodName" label="商品名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="redeemNum" label="数量" width="80" align="center" />
      <el-table-column prop="Integralsum" label="消耗积分" width="100" align="center" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          {{ Number(row.fhstatus) === 2 ? '已发货' : '待发货' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="Number(row.fhstatus) !== 2"
            link
            type="primary"
            @click="openShip(row)"
          >
            确认发货
          </el-button>
          <el-button link type="primary" @click="openDetail(row)">查看</el-button>
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

    <el-dialog v-model="detailVisible" title="兑换记录详情" width="560px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="兑换编号">{{ detail.orderId }}</el-descriptions-item>
        <el-descriptions-item label="兑换时间">{{ detail.redeemTime }}</el-descriptions-item>
        <el-descriptions-item label="收件人">{{ detail.userName }}</el-descriptions-item>
        <el-descriptions-item label="电话">{{ detail.mobile }}</el-descriptions-item>
        <el-descriptions-item label="收件地址">{{ detail.address }}</el-descriptions-item>
        <el-descriptions-item label="商品名称">{{ detail.goodName }}</el-descriptions-item>
        <el-descriptions-item label="数量">{{ detail.redeemNum }}</el-descriptions-item>
        <el-descriptions-item label="消耗积分">{{ detail.Integralsum }}</el-descriptions-item>
        <el-descriptions-item label="快递公司">{{ detail.expressCompany }}</el-descriptions-item>
        <el-descriptions-item label="快递单号">{{ detail.expressNum }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="shipVisible" title="确认发货" width="480px">
      <el-form label-width="90px">
        <el-form-item label="快递商" required>
          <el-select v-model="shipForm.mark" filterable style="width: 100%" placeholder="请选择快递商">
            <el-option v-for="item in EXPRESS_OPTIONS" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="快递单号" required>
          <el-input v-model="shipForm.number" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleShip">确认发货</el-button>
      </template>
    </el-dialog>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import { fetchRedeemLogList, getRedeemLogDetail, shipRedeemLog } from '@admin/api/ops'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

const EXPRESS_OPTIONS = [
  '顺丰速运',
  '中通快递',
  '韵达快递',
  '圆通速递',
  '申通快递',
  '京东物流',
  '邮政EMS',
  '邮政平邮',
  '优速快递',
  '德邦快递',
  '快捷快递',
  '宅急送',
  'TNT快递',
  'DHL',
  '联邦快递',
  'UPS快递',
  '百世快递',
  '国通快递',
  '天天快递',
  '安能物流',
  '跨越速运',
]

const filters = reactive({
  order_startime: '',
  order_endtime: '',
  status: undefined as number | undefined,
})
const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchRedeemLogList({ ...params, ...filters })
)
const detailVisible = ref(false)
const shipVisible = ref(false)
const saving = ref(false)
const detail = reactive<Record<string, unknown>>({})
const shipForm = reactive({ id: '', mark: '', number: '' })

function reload() {
  pagination.page = 1
  return load()
}

onMounted(() => reload())

async function openDetail(row: Record<string, unknown>) {
  const res = await getRedeemLogDetail(String(row.id))
  if (isAjaxOk(res) && res.obj) {
    Object.assign(detail, res.obj as Record<string, unknown>)
    detailVisible.value = true
  } else {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
  }
}

function openShip(row: Record<string, unknown>) {
  shipForm.id = String(row.id)
  shipForm.mark = ''
  shipForm.number = ''
  shipVisible.value = true
}

async function handleShip() {
  if (!shipForm.mark.trim() || !shipForm.number.trim()) {
    ElMessage.warning('请选择快递商并填写单号')
    return
  }
  saving.value = true
  try {
    const res = await shipRedeemLog({ ...shipForm })
    if (isAjaxOk(res)) {
      ElMessage.success('发货成功')
      shipVisible.value = false
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '发货失败'))
  } finally {
    saving.value = false
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
</style>
