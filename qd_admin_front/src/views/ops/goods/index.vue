<template>
  <admin-page-card title="产品管理">
    <el-tabs v-model="activeTab" class="goods-tabs" @tab-change="onTabChange">
      <el-tab-pane label="所有商品" name="list" />
      <el-tab-pane label="添加新商品" name="add" />
    </el-tabs>

    <el-form :inline="true" class="filter-form" @submit.prevent>
      <el-form-item label="商品名称">
        <el-input v-model="filters.q_goods_name" clearable placeholder="商品名称" />
      </el-form-item>
      <el-form-item label="品牌名称">
        <el-select
          v-model="filters.goods_brand_id"
          clearable
          filterable
          placeholder="所有品牌"
          style="width: 160px"
        >
          <el-option
            v-for="item in brandOptions"
            :key="String(item.id)"
            :label="String(item.name)"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="类别">
        <el-select
          v-model="filters.gc_id"
          clearable
          filterable
          placeholder="所有分类"
          style="width: 180px"
        >
          <el-option
            v-for="item in classOptions"
            :key="String(item.id)"
            :label="String(item.className)"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="人气推荐">
        <el-select
          v-model="filters.q_goods_recommend"
          clearable
          placeholder="是否人气推荐"
          style="width: 140px"
        >
          <el-option label="是" value="true" />
          <el-option label="否" value="false" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload()">搜索</el-button>
      </el-form-item>
    </el-form>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      class="tip-banner"
      title="友情提示"
      description="上架商品，在商城前台所有访客均可查看，管理员可以设置商品上架状态"
    />

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column label="商品图片" width="90" align="center">
        <template #default="{ row }">
          <el-image
            v-if="goodsImageUrl(row)"
            class="goods-thumb"
            :src="goodsImageUrl(row)"
            fit="cover"
            :preview-src-list="[goodsImageUrl(row)]"
            preview-teleported
          />
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="goodsName" label="商品名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="brandName" label="品牌" width="110" show-overflow-tooltip />
      <el-table-column prop="className" label="分类名" width="120" show-overflow-tooltip />
      <el-table-column label="商品状态" width="90" align="center">
        <template #default="{ row }">{{ statusLabel(row.goodsStatus) }}</template>
      </el-table-column>
      <el-table-column label="人气推荐" width="90" align="center">
        <template #default="{ row }">
          <el-button link class="recommend-btn" @click="handleRecommend(row)">
            <el-icon :size="20" :color="Number(row.goodsRecommend) === 1 ? '#409eff' : '#c0c4cc'">
              <StarFilled v-if="Number(row.goodsRecommend) === 1" />
              <Star v-else />
            </el-icon>
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="是否有校准服务" width="120" align="center">
        <template #default="{ row }">
          <span class="svc-flag">{{ Number(row.isCalibration) === 1 ? '是' : '否' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="是否有维修服务" width="120" align="center">
        <template #default="{ row }">
          <span class="svc-flag">{{ Number(row.isMaintenance) === 1 ? '是' : '否' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="是否有安装服务" width="120" align="center">
        <template #default="{ row }">
          <span class="svc-flag">{{ Number(row.isInstall) === 1 ? '是' : '否' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="负责人" width="110" show-overflow-tooltip>
        <template #default="{ row }">{{ row.headUserName || '-' }}</template>
      </el-table-column>
      <el-table-column label="是否现货" width="90" align="center">
        <template #default="{ row }">
          {{ Number(row.goodsInventory) > 0 ? '是' : '否' }}
        </template>
      </el-table-column>
      <el-table-column prop="goodsInventory" label="库存量" width="90" align="center" />
      <el-table-column label="操作" width="180" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="handleSale(row)">
            {{ Number(row.goodsStatus) === 0 ? '下架' : '上架' }}
          </el-button>
          <el-button link type="primary" @click="handleCopy(row)">复制</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="() => load(listParams())"
      />
    </div>
  </admin-page-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'
import AdminPageCard from '@/components/AdminPageCard.vue'
import {
  fetchGoodsBrandOptions,
  fetchGoodsClassOptions,
  fetchGoodsList,
  toggleGoodsRecommend,
  toggleGoodsSale,
} from '@/api/ops'
import { useDataTable } from '@/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

const OSS_BASE = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/'

const activeTab = ref('list')
const filters = reactive({
  q_goods_name: '',
  goods_brand_id: undefined as string | number | undefined,
  gc_id: undefined as string | number | undefined,
  q_goods_recommend: undefined as string | undefined,
})
const brandOptions = ref<Record<string, unknown>[]>([])
const classOptions = ref<Record<string, unknown>[]>([])

function listParams() {
  return {
    q_goods_name: filters.q_goods_name,
    'q_goods.goods_brand.id': filters.goods_brand_id,
    'q_goods.gc.id': filters.gc_id,
    q_goods_recommend: filters.q_goods_recommend,
  }
}

const { loading, rows, total, pagination, load } = useDataTable((params) =>
  fetchGoodsList({ ...params, ...listParams() })
)

function goodsImageUrl(row: Record<string, unknown>) {
  const path = String(row.photoPath || '')
  const name = String(row.photoName || '')
  if (!path && !name) return ''
  if (path.includes('https') || path.startsWith('http://')) {
    return path.includes(name) ? path : `${path.replace(/\/?$/, '/')}${name}`
  }
  return `${OSS_BASE}${path.replace(/^\//, '')}/${name.replace(/^\//, '')}`
}

function statusLabel(status: unknown) {
  const n = Number(status)
  if (n === 0) return '上架'
  if (n === 1) return '仓库中'
  if (n === -1) return '已下架'
  return String(status ?? '-')
}

function reload() {
  pagination.page = 1
  return load(listParams())
}

function onTabChange(name: string | number) {
  if (name === 'add') {
    activeTab.value = 'list'
    ElMessage.info('添加新商品功能迁移中，请稍后')
  }
}

onMounted(async () => {
  await reload()
  const [brandRes, classRes] = await Promise.all([
    fetchGoodsBrandOptions(),
    fetchGoodsClassOptions(),
  ])
  if (isAjaxOk(brandRes) && Array.isArray(brandRes.obj)) {
    brandOptions.value = brandRes.obj as Record<string, unknown>[]
  }
  if (isAjaxOk(classRes) && Array.isArray(classRes.obj)) {
    classOptions.value = classRes.obj as Record<string, unknown>[]
  }
})

async function handleRecommend(row: Record<string, unknown>) {
  const res = await toggleGoodsRecommend(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('操作成功')
    await load(listParams())
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}

async function handleSale(row: Record<string, unknown>) {
  const res = await toggleGoodsSale(String(row.id))
  if (isAjaxOk(res)) {
    ElMessage.success('商品上下架成功')
    await reload()
  } else {
    ElMessage.error(ajaxErrorMessage(res, '操作失败'))
  }
}

function handleEdit(row: Record<string, unknown>) {
  ElMessage.info(`编辑商品功能迁移中（ID: ${row.id}）`)
}

function handleCopy(row: Record<string, unknown>) {
  ElMessage.info(`复制商品功能迁移中（ID: ${row.id}）`)
}
</script>

<style scoped lang="scss">
.goods-tabs {
  margin-bottom: 4px;
}
.filter-form {
  margin-bottom: 12px;
}
.tip-banner {
  margin-bottom: 12px;
}
.goods-thumb {
  width: 30px;
  height: 33px;
}
.svc-flag {
  color: #409eff;
}
.recommend-btn {
  vertical-align: middle;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
