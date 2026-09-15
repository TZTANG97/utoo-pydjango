<template>
  <admin-page-card :title="pageTitle">
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
          <img
            v-if="goodsImageUrl(row)"
            class="goods-thumb"
            :src="goodsImageUrl(row)"
            alt=""
            referrerpolicy="no-referrer"
            @error="onThumbError"
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

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :width="isLite ? '720px' : '920px'"
      destroy-on-close
      @closed="onDialogClosed"
    >
      <el-form label-width="120px" class="goods-form">
        <!-- 精简版 / 完整版共有：对齐 Java add_goods_second_new -->
        <el-form-item label="商品分类" required>
          <el-select v-model="form.gcId" filterable clearable style="width: 100%">
            <el-option
              v-for="item in classOptions"
              :key="String(item.id)"
              :label="String(item.className)"
              :value="Number(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="商品名称" required>
          <el-input v-model="form.goodsName" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="产品型号">
          <el-input v-model="form.goodsSpec" placeholder="多个型号用英文逗号分隔" />
        </el-form-item>
        <el-form-item label="商品品牌" required>
          <el-select v-model="form.goodsBrandId" filterable clearable style="width: 100%">
            <el-option
              v-for="item in brandOptions"
              :key="String(item.id)"
              :label="String(item.name)"
              :value="Number(item.id)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="商品图片">
          <div class="photo-box">
            <el-tabs v-model="photoTab" type="card" class="photo-tabs">
              <el-tab-pane label="上传图片" name="upload">
                <div class="upload-row">
                  <el-upload
                    :show-file-list="false"
                    accept="image/jpeg,image/png,image/gif,image/webp,.jpg,.jpeg,.png,.gif,.webp"
                    :http-request="onUploadImage"
                  >
                    <el-button type="primary" :loading="uploading">选择上传商品图片</el-button>
                  </el-upload>
                  <el-button v-if="mainPhotoUrl" link type="danger" @click="clearMainPhoto">清除</el-button>
                </div>
              </el-tab-pane>
              <el-tab-pane label="从相册选择" name="album">
                <el-button @click="albumVisible = true">从相册选择</el-button>
              </el-tab-pane>
            </el-tabs>
            <div class="preview-wrap">
              <img
                v-if="mainPhotoUrl"
                class="preview-img"
                :src="mainPhotoUrl"
                alt=""
                referrerpolicy="no-referrer"
              />
              <div v-else class="preview-empty">暂无主图</div>
            </div>
            <div class="field-tip">支持 jpg/png/gif，建议 300x300 以上</div>
          </div>
        </el-form-item>
        <el-form-item label="商品描述">
          <HtmlRichEditor
            v-if="dialogVisible"
            :key="`goods-details-${form.id || 'new'}-${editType}`"
            v-model="form.goodsDetails"
            class="goods-details-editor"
          />
        </el-form-item>
        <el-form-item label="关联配件">
          <div class="relation-box">
            <el-select
              v-model="relationPickId"
              filterable
              remote
              clearable
              placeholder="搜索并添加关联商品"
              :remote-method="searchRelationGoods"
              :loading="relationLoading"
              style="width: 100%"
              @change="addRelationGoods"
            >
              <el-option
                v-for="item in relationOptions"
                :key="String(item.id)"
                :label="`${item.goodsName}${item.brandName ? ' / ' + item.brandName : ''}`"
                :value="Number(item.id)"
              />
            </el-select>
            <div v-if="relationList.length" class="relation-list">
              <div v-for="item in relationList" :key="String(item.id)" class="relation-item">
                <span>{{ item.goodsName }}</span>
                <el-button link type="danger" @click="removeRelationGoods(Number(item.id))">删除</el-button>
              </div>
            </div>
          </div>
        </el-form-item>

        <!-- 完整版专有：对齐 Java add_goods_three -->
        <template v-if="!isLite">
          <el-divider content-position="left">价格与库存</el-divider>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="市场参考价">
                <el-input-number v-model="form.goodsPrice" :min="0" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="本币参考价">
                <div class="inline-pair">
                  <el-input-number v-model="form.localPrice" :min="0" :precision="2" style="flex: 1" />
                  <el-select v-model="form.localType" style="width: 110px">
                    <el-option label="人民币" value="4" />
                    <el-option label="日元" value="1" />
                    <el-option label="美元" value="2" />
                    <el-option label="欧元" value="3" />
                  </el-select>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="商品货期">
                <el-input-number v-model="form.goodsTime" :min="0" :precision="0" style="width: 100%" />
                <span class="field-tip">单位：天</span>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="产品负责人">
                <el-select
                  v-model="form.headUserId"
                  filterable
                  remote
                  clearable
                  reserve-keyword
                  placeholder="搜索用户"
                  :remote-method="searchHeadUsers"
                  :loading="headUserLoading"
                  style="width: 100%"
                >
                  <el-option
                    v-for="item in headUserOptions"
                    :key="String(item.id)"
                    :label="headUserLabel(item)"
                    :value="String(item.id)"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="商品库存">
                <el-input-number v-model="form.goodsInventory" :min="0" :precision="0" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="商品货号">
                <el-input v-model="form.goodsSerial" maxlength="20" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-divider content-position="left">SKU / 库存明细</el-divider>
          <div class="sku-header">
            <span />
            <el-button size="small" @click="addSkuRow">添加行</el-button>
          </div>
          <el-table :data="form.skus" border size="small" class="sku-table">
            <el-table-column label="名称" min-width="110">
              <template #default="{ row }">
                <el-input v-model="row.skuName" />
              </template>
            </el-table-column>
            <el-table-column label="规格ID" width="110">
              <template #default="{ row }">
                <el-input v-model="row.specpids" placeholder="可空" />
              </template>
            </el-table-column>
            <el-table-column label="库存" width="90">
              <template #default="{ row }">
                <el-input-number v-model="row.stocks" :min="0" :controls="false" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="价格" width="100">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.price"
                  :min="0"
                  :precision="2"
                  :controls="false"
                  style="width: 100%"
                />
              </template>
            </el-table-column>
            <el-table-column label="月租基准价" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.yzjzj" :min="0" :precision="2" :controls="false" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="月租市场价" width="100">
              <template #default="{ row }">
                <el-input-number v-model="row.yzscj" :min="0" :precision="2" :controls="false" style="width: 100%" />
              </template>
            </el-table-column>
            <el-table-column label="货号" width="110">
              <template #default="{ row }">
                <el-input v-model="row.skuCode" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="60" align="center">
              <template #default="{ $index }">
                <el-button link type="danger" @click="removeSkuRow($index)">删</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-divider content-position="left">其他信息</el-divider>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="商品发布">
                <el-radio-group v-model="form.goodsStatus">
                  <el-radio :value="0">立即发布</el-radio>
                  <el-radio :value="1">放入仓库</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="商品推荐">
                <el-radio-group v-model="form.goodsRecommend">
                  <el-radio :value="1">是</el-radio>
                  <el-radio :value="0">否</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="校准服务">
                <el-radio-group v-model="form.isCalibration">
                  <el-radio :value="1">是</el-radio>
                  <el-radio :value="2">否</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="维修服务">
                <el-radio-group v-model="form.isMaintenance">
                  <el-radio :value="1">是</el-radio>
                  <el-radio :value="2">否</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="安装服务">
                <el-radio-group v-model="form.isInstall">
                  <el-radio :value="1">是</el-radio>
                  <el-radio :value="2">否</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="是否有二手">
                <el-radio-group v-model="form.isSecondhand">
                  <el-radio :value="1">是</el-radio>
                  <el-radio :value="2">否</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="是否可租赁">
                <el-radio-group v-model="form.isLease">
                  <el-radio :value="1">是</el-radio>
                  <el-radio :value="2">否</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col v-if="form.isLease === 1" :span="12">
              <el-form-item label="最低起租日">
                <el-input-number v-model="form.zdqzr" :min="0" :precision="0" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="产品等级">
                <el-select v-model="form.goodsChoiceType" clearable style="width: 100%">
                  <el-option label="A" :value="1" />
                  <el-option label="B" :value="2" />
                  <el-option label="C" :value="3" />
                  <el-option label="D" :value="4" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <AlbumImagePicker v-model="albumVisible" @select="onAlbumPick" />
  </admin-page-card>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UploadRequestOptions } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'
import AdminPageCard from '@admin/components/AdminPageCard.vue'
import AlbumImagePicker from '@admin/components/AlbumImagePicker.vue'
import HtmlRichEditor from '@admin/components/HtmlRichEditor.vue'
import {
  fetchGoodsBrandOptions,
  fetchGoodsClassOptions,
  fetchGoodsList,
  fetchGoodsOptions,
  fetchSyUserOptions,
  getGoodsDetail,
  saveGoods,
  toggleGoodsRecommend,
  toggleGoodsSale,
  uploadSellerImage,
} from '@admin/api/ops'
import { useDataTable } from '@admin/composables/useDataTable'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type SkuRow = {
  skuName: string
  specpids: string
  stocks: number
  price: number
  skuCode: string
  yzjzj: number
  yzscj: number
}

type RelationItem = { id: number; goodsName: string; brandName?: string }
type AlbumImagePick = { id: number; url: string }

const OSS_BASE = 'https://qgongye.oss-cn-shanghai.aliyuncs.com/'
const route = useRoute()
const pageTitle = computed(() => String(route.meta.title || '产品管理'))
const isLite = computed(
  () => route.meta.goodsMode === 'lite' || String(route.path).includes('goods-lite')
)

const activeTab = ref('list')
const filters = reactive({
  q_goods_name: '',
  goods_brand_id: undefined as string | number | undefined,
  gc_id: undefined as string | number | undefined,
  q_goods_recommend: undefined as string | undefined,
})
const brandOptions = ref<Record<string, unknown>[]>([])
const classOptions = ref<Record<string, unknown>[]>([])
const headUserOptions = ref<Record<string, unknown>[]>([])
const headUserLoading = ref(false)
const relationOptions = ref<RelationItem[]>([])
const relationList = ref<RelationItem[]>([])
const relationPickId = ref<number | undefined>(undefined)
const relationLoading = ref(false)
const albumVisible = ref(false)
const photoTab = ref('upload')
const uploading = ref(false)
const mainPhotoUrl = ref('')

const dialogVisible = ref(false)
const saving = ref(false)
const editType = ref('') // '' 新建 | '1' 编辑 | '2' 复制
const form = reactive({
  id: undefined as number | undefined,
  goodsName: '',
  enName: '',
  goodsBrandId: undefined as number | undefined,
  gcId: undefined as number | undefined,
  goodsSerial: '',
  goodsSpec: '',
  goodsPrice: 0,
  storePrice: 0,
  localPrice: 0,
  localType: '4',
  goodsTime: 0 as number | undefined,
  goodsInventory: 0,
  goodsStatus: 0,
  goodsRecommend: 0,
  headUserId: '' as string,
  isCalibration: 1,
  isMaintenance: 1,
  isInstall: 1,
  isSecondhand: 1,
  isLease: 1,
  zdqzr: 0,
  goodsChoiceType: undefined as number | undefined,
  goodsMainPhotoId: '' as string,
  goodsDetails: '',
  inventoryType: 'all',
  skus: [] as SkuRow[],
})

const dialogTitle = computed(() => {
  const prefix = isLite.value ? '精简版' : ''
  if (editType.value === '2') return `${prefix}复制商品`
  if (form.id) return `${prefix}编辑商品`
  return `${prefix}添加新商品`
})

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

function mediaUrl(path: unknown, name: unknown) {
  const p = String(path || '')
  const n = String(name || '')
  if (!p && !n) return ''
  if (p.includes('https') || p.startsWith('http://')) {
    return p.includes(n) ? p : `${p.replace(/\/?$/, '/')}${n}`
  }
  return `${OSS_BASE}${p.replace(/^\//, '')}/${n.replace(/^\//, '')}`
}

function goodsImageUrl(row: Record<string, unknown>) {
  return mediaUrl(row.photoPath || row.path, row.photoName || row.name)
}

function onThumbError(ev: Event) {
  const el = ev.target as HTMLImageElement | null
  if (el) el.style.opacity = '0.3'
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

function emptyForm() {
  Object.assign(form, {
    id: undefined,
    goodsName: '',
    enName: '',
    goodsBrandId: undefined,
    gcId: undefined,
    goodsSerial: '',
    goodsSpec: '',
    goodsPrice: 0,
    storePrice: 0,
    localPrice: 0,
    localType: '4',
    goodsTime: 0,
    goodsInventory: 0,
    goodsStatus: 0,
    goodsRecommend: 0,
    headUserId: '',
    isCalibration: 1,
    isMaintenance: 1,
    isInstall: 1,
    isSecondhand: 1,
    isLease: 1,
    zdqzr: 0,
    goodsChoiceType: undefined,
    goodsMainPhotoId: '',
    goodsDetails: '',
    inventoryType: 'all',
    skus: [{ skuName: '标准商品', specpids: '', stocks: 0, price: 0, skuCode: '', yzjzj: 0, yzscj: 0 }],
  })
  relationList.value = []
  relationPickId.value = undefined
  mainPhotoUrl.value = ''
  photoTab.value = 'upload'
}

function fillFormFromDetail(obj: Record<string, unknown>, asCopy: boolean) {
  const skusRaw = Array.isArray(obj.skus) ? (obj.skus as Record<string, unknown>[]) : []
  const skus: SkuRow[] = skusRaw.map((s) => ({
    skuName: String(s.skuName || s.sku_name || '标准商品'),
    specpids: String(s.specpids || ''),
    stocks: Number(s.stocks ?? 0),
    price: Number(s.price ?? 0),
    skuCode: String(s.skuCode || s.sku_code || ''),
    yzjzj: Number(s.yzjzj ?? 0),
    yzscj: Number(s.yzscj ?? 0),
  }))
  if (!skus.length) {
    skus.push({
      skuName: '标准商品',
      specpids: '',
      stocks: Number(obj.goodsInventory ?? 0),
      price: Number(obj.goodsPrice ?? 0),
      skuCode: String(obj.goodsSerial || ''),
      yzjzj: 0,
      yzscj: 0,
    })
  }
  const headId = obj.headUserId != null && obj.headUserId !== '' ? String(obj.headUserId) : ''
  if (headId && obj.headUserName) {
    headUserOptions.value = [
      { id: headId, userName: obj.headUserName, trueName: '' },
      ...headUserOptions.value.filter((u) => String(u.id) !== headId),
    ]
  }
  const rel =
    Array.isArray(obj.relationGoodsList) && obj.relationGoodsList.length
      ? (obj.relationGoodsList as RelationItem[])
      : []
  relationList.value = rel.map((r) => ({
    id: Number(r.id),
    goodsName: String(r.goodsName || ''),
  }))

  const photoId =
    obj.goodsMainPhotoId != null && obj.goodsMainPhotoId !== ''
      ? String(obj.goodsMainPhotoId)
      : ''
  mainPhotoUrl.value = mediaUrl(obj.photoPath || obj.path, obj.photoName || obj.name)

  Object.assign(form, {
    id: asCopy ? undefined : Number(obj.id),
    goodsName: asCopy
      ? `${String(obj.goodsName || obj.goods_name || '')} (复制)`
      : String(obj.goodsName || obj.goods_name || ''),
    enName: String(obj.enName || obj.en_name || ''),
    goodsBrandId: obj.goodsBrandId != null ? Number(obj.goodsBrandId) : undefined,
    gcId: obj.gcId != null ? Number(obj.gcId) : undefined,
    goodsSerial: asCopy ? '' : String(obj.goodsSerial || obj.goods_serial || ''),
    goodsSpec: String(obj.goodsSpec || obj.goods_spec || ''),
    goodsPrice: Number(obj.goodsPrice ?? 0),
    storePrice: Number(obj.storePrice ?? obj.goodsPrice ?? 0),
    localPrice: Number(obj.localPrice ?? obj.goodsPrice ?? 0),
    localType: String(obj.localType || '4'),
    goodsTime: obj.goodsTime != null && obj.goodsTime !== '' ? Number(obj.goodsTime) : 0,
    goodsInventory: Number(obj.goodsInventory ?? 0),
    goodsStatus: Number(obj.goodsStatus ?? 0) === -1 ? 1 : Number(obj.goodsStatus ?? 0),
    goodsRecommend: Number(obj.goodsRecommend ?? 0) ? 1 : 0,
    headUserId: headId,
    isCalibration: Number(obj.isCalibration) === 1 ? 1 : 2,
    isMaintenance: Number(obj.isMaintenance) === 1 ? 1 : 2,
    isInstall: Number(obj.isInstall) === 1 ? 1 : 2,
    isSecondhand: Number(obj.isSecondhand) === 1 ? 1 : 2,
    isLease: Number(obj.isLease) === 1 ? 1 : 2,
    zdqzr: Number(obj.zdqzr ?? 0),
    goodsChoiceType: obj.goodsChoiceType != null ? Number(obj.goodsChoiceType) : undefined,
    goodsMainPhotoId: photoId,
    goodsDetails: String(obj.goodsDetails || obj.goods_details || ''),
    inventoryType: String(obj.inventoryType || obj.inventory_type || 'all'),
    skus,
  })
}

function onTabChange(name: string | number) {
  if (name === 'add') {
    activeTab.value = 'list'
    openCreate()
  }
}

function openCreate() {
  editType.value = ''
  emptyForm()
  dialogVisible.value = true
}

async function openById(id: string | number, asCopy: boolean) {
  const res = await getGoodsDetail(id)
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载商品失败'))
    return
  }
  editType.value = asCopy ? '2' : '1'
  fillFormFromDetail(res.obj as Record<string, unknown>, asCopy)
  dialogVisible.value = true
}

function onDialogClosed() {
  editType.value = ''
}

function clearMainPhoto() {
  form.goodsMainPhotoId = ''
  mainPhotoUrl.value = ''
}

function onAlbumPick(pick: AlbumImagePick) {
  form.goodsMainPhotoId = String(pick.id)
  mainPhotoUrl.value = pick.url
  photoTab.value = 'upload'
}

async function onUploadImage(options: UploadRequestOptions) {
  uploading.value = true
  try {
    const res = await uploadSellerImage(options.file as File)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    const obj = (res.obj || res) as Record<string, unknown>
    const id = Number(obj.id || obj.accessoryId || 0)
    const url = String(obj.url || obj.path || '')
    if (!id) {
      ElMessage.error('上传成功但未返回图片ID')
      return
    }
    form.goodsMainPhotoId = String(id)
    mainPhotoUrl.value = url || mainPhotoUrl.value
    ElMessage.success('上传成功')
  } finally {
    uploading.value = false
  }
}

function addSkuRow() {
  form.skus.push({
    skuName: '',
    specpids: '',
    stocks: 0,
    price: form.goodsPrice || 0,
    skuCode: '',
    yzjzj: 0,
    yzscj: 0,
  })
}

function removeSkuRow(index: number) {
  form.skus.splice(index, 1)
}

function headUserLabel(item: Record<string, unknown>) {
  const name = String(item.userName || item.trueName || item.id || '')
  const trueName = String(item.trueName || '')
  return trueName && trueName !== name ? `${name}（${trueName}）` : name
}

async function searchHeadUsers(keyword: string) {
  headUserLoading.value = true
  try {
    const res = await fetchSyUserOptions(keyword || '')
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      headUserOptions.value = res.obj as Record<string, unknown>[]
    }
  } finally {
    headUserLoading.value = false
  }
}

async function searchRelationGoods(keyword: string) {
  relationLoading.value = true
  try {
    const res = await fetchGoodsOptions(keyword || '')
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      relationOptions.value = (res.obj as RelationItem[]).map((r) => ({
        id: Number(r.id),
        goodsName: String(r.goodsName || ''),
        brandName: r.brandName ? String(r.brandName) : '',
      }))
    }
  } finally {
    relationLoading.value = false
  }
}

function addRelationGoods(id: number | undefined) {
  if (!id) return
  if (relationList.value.some((r) => Number(r.id) === Number(id))) {
    ElMessage.warning('商品已存在关联配件中')
    relationPickId.value = undefined
    return
  }
  const found = relationOptions.value.find((r) => Number(r.id) === Number(id))
  relationList.value.push({
    id: Number(id),
    goodsName: found?.goodsName || String(id),
  })
  relationPickId.value = undefined
}

function removeRelationGoods(id: number) {
  relationList.value = relationList.value.filter((r) => Number(r.id) !== Number(id))
}

onMounted(async () => {
  await reload()
  const [brandRes, classRes] = await Promise.all([
    fetchGoodsBrandOptions(),
    fetchGoodsClassOptions(),
    searchHeadUsers(''),
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
  void openById(String(row.id), false)
}

function handleCopy(row: Record<string, unknown>) {
  void openById(String(row.id), true)
}

async function handleSubmit() {
  if (!form.goodsName.trim()) {
    ElMessage.warning('请填写商品名称')
    return
  }
  if (!form.goodsBrandId) {
    ElMessage.warning('请选择品牌')
    return
  }
  if (!form.gcId) {
    ElMessage.warning('请选择分类')
    return
  }
  if (!isLite.value && !form.goodsChoiceType) {
    ElMessage.warning('请选择产品等级')
    return
  }
  const inventory =
    !isLite.value && form.skus.length > 0
      ? form.skus.reduce((sum, s) => sum + (Number(s.stocks) || 0), 0)
      : form.goodsInventory
  saving.value = true
  try {
    const payload: Record<string, unknown> = {
      id: editType.value === '2' ? undefined : form.id,
      editType: editType.value || (form.id ? '1' : ''),
      formMode: isLite.value ? 'lite' : 'full',
      goodsName: form.goodsName.trim(),
      goodsBrandId: form.goodsBrandId,
      gcId: form.gcId,
      goodsSpec: form.goodsSpec.trim(),
      goodsMainPhotoId: form.goodsMainPhotoId ? Number(form.goodsMainPhotoId) : undefined,
      goodsDetails: form.goodsDetails,
      relationGoods: relationList.value.map((r) => r.id).join(','),
    }
    if (!isLite.value || editType.value === '2') {
      // skus 以 JSON 字符串提交，避免部分网关对嵌套数组解析挂起/丢参
      const skusPayload = form.skus.map((s) => ({
        skuName: s.skuName,
        specpids: s.specpids,
        stocks: Number(s.stocks) || 0,
        price: Number(s.price) || 0,
        skuCode: s.skuCode,
        yzjzj: Number(s.yzjzj) || 0,
        yzscj: Number(s.yzscj) || 0,
      }))
      Object.assign(payload, {
        enName: form.enName.trim(),
        goodsSerial: form.goodsSerial.trim(),
        goodsPrice: form.goodsPrice,
        storePrice: form.storePrice || form.goodsPrice,
        localPrice: form.localPrice || form.goodsPrice,
        localType: form.localType,
        goodsTime: form.goodsTime,
        goodsInventory: inventory,
        goodsStatus: form.goodsStatus,
        goodsRecommend: form.goodsRecommend,
        headUserId: form.headUserId,
        isCalibration: form.isCalibration,
        isMaintenance: form.isMaintenance,
        isInstall: form.isInstall,
        isSecondhand: form.isSecondhand,
        isLease: form.isLease,
        zdqzr: form.zdqzr,
        goodsChoiceType: form.goodsChoiceType,
        inventoryType: form.skus.length > 1 ? 'spec' : form.inventoryType || 'all',
        skus: JSON.stringify(skusPayload),
      })
    }
    const res = await saveGoods(payload)
    if (isAjaxOk(res)) {
      ElMessage.success(editType.value === '2' ? '复制成功' : '保存成功')
      dialogVisible.value = false
      saving.value = false
      // 列表刷新与按钮 loading 解耦，避免 reload 慢/挂起时按钮一直转圈
      await reload()
      return
    }
    ElMessage.error(ajaxErrorMessage(res, '保存失败'))
  } catch (err: unknown) {
    const msg =
      err && typeof err === 'object' && 'message' in err
        ? String((err as { message?: string }).message || '')
        : ''
    ElMessage.error(msg || '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
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
  object-fit: cover;
  vertical-align: middle;
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
.sku-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 10px;
}
.sku-table {
  margin-bottom: 8px;
}
.inline-pair {
  display: flex;
  gap: 8px;
  width: 100%;
}
.field-tip {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
}
.relation-box {
  width: 100%;
}
.relation-list {
  margin-top: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.relation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  border-bottom: 1px solid #ebeef5;
}
.relation-item:last-child {
  border-bottom: none;
}
.photo-box {
  width: 100%;
}
.photo-tabs {
  margin-bottom: 8px;
}
.upload-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.preview-wrap {
  width: 200px;
  height: 200px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #fafafa;
}
.preview-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.preview-empty {
  color: #c0c4cc;
  font-size: 13px;
}
.goods-details-editor {
  width: 100%;
}
.goods-details-editor :deep(.editor-host) {
  height: 360px;
}
</style>
