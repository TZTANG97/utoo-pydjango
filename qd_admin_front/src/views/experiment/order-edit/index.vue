<template>
  <div v-loading="loading" class="edit-page">
    <header class="page-head">
      <button type="button" class="back-link" @click="goBack">← 返回详情</button>
      <h2>编辑订单</h2>
      <p v-if="detail && !isExpSub && !isSubcontractSub" class="sub">
        <span class="mono">{{ detail.orderId }}</span>
        · {{ detail.orderStatusLabel }}
      </p>
      <p v-else-if="detail" class="sub">{{ detail.orderStatusLabel }}</p>
    </header>

    <el-form v-if="detail" label-width="130px" class="form-card" @submit.prevent>
      <el-row :gutter="16">
        <el-col v-if="!isExpSub && !isSubcontractSub" :span="12">
          <el-form-item label="订单编号">
            <el-input :model-value="String(detail.orderId || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col v-if="isSubcontractSub || isExpSub" :span="12">
          <el-form-item label="来源单号">
            <el-input :model-value="String(detail.parentOrderId || '')" disabled />
          </el-form-item>
        </el-col>
        <el-col v-if="!isSubcontractSub && !isExpSub" :span="12">
          <el-form-item label="制单人员">
            <el-input :model-value="String(detail.addUser || '')" disabled />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="下单时间" required>
            <el-date-picker
              v-model="form.orderTime"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="yyyy-mm-dd"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col v-if="!isSubcontractSub" :span="12">
          <el-form-item
            :label="isExpSub ? '客户名称' : '客户名称'"
            :required="!isSubcontractSub && !form.customerId && !form.customUserId"
          >
            <div class="inline-ops">
              <el-select
                v-model="form.customerId"
                filterable
                clearable
                placeholder="请选择"
                style="flex: 1"
                @change="onCustomerChange"
              >
                <el-option
                  v-for="o in customerOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button type="primary" link @click="openAddCustomer">添加</el-button>
              <el-button type="primary" link @click="reloadCustomers">刷新</el-button>
            </div>
          </el-form-item>
        </el-col>

        <el-col v-if="isMainOrder" :span="12">
          <el-form-item label="订单类型" required>
            <el-select
              v-model="form.classId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 100%"
            >
              <el-option
                v-for="o in classOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item :label="isExpSub ? '实验室主管' : '销售主管'" required>
            <el-select
              v-model="form.saleManagerId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 100%"
            >
              <el-option
                v-for="o in managerOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col v-if="!isSubcontractSub" :span="12">
          <el-form-item label="销售人员" required>
            <el-select
              v-model="form.saleUserId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 100%"
            >
              <el-option
                v-for="o in saleUserOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col v-if="isSubcontractSub" :span="12">
          <el-form-item label="实验分包公司" required>
            <div class="inline-ops">
              <el-select
                v-model="form.stockCompanyId"
                filterable
                clearable
                placeholder="请选择"
                style="flex: 1"
              >
                <el-option
                  v-for="o in supplierOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button type="primary" link @click="openAddSupplier">添加</el-button>
              <el-button type="primary" link @click="reloadSuppliers">刷新</el-button>
            </div>
          </el-form-item>
        </el-col>
        <el-col v-else :span="12">
          <!-- 主单编辑：type6=供应商；type8=所属公司（对齐 Java） -->
          <el-form-item
            :label="isSubcontractMain ? '所属公司' : isMainOrder ? '供应商' : '所属公司'"
            required
          >
            <div class="inline-ops">
              <el-select
                v-model="form.supplierId"
                filterable
                clearable
                placeholder="请选择"
                style="flex: 1"
              >
                <el-option
                  v-for="o in supplierOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button type="primary" link @click="openAddSupplier">添加</el-button>
              <el-button type="primary" link @click="reloadSuppliers">刷新</el-button>
            </div>
          </el-form-item>
        </el-col>
        <el-col v-if="isMainOrder || isExpSub" :span="12">
          <el-form-item label="客户账号">
            <el-select
              v-model="form.customUserId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 100%"
            >
              <el-option
                v-for="o in accountOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col v-if="isExpSub" :span="12">
          <el-form-item label="仓库管理员" required>
            <el-select
              v-model="form.warehouseUserId"
              filterable
              clearable
              placeholder="请选择"
              style="width: 100%"
            >
              <el-option
                v-for="o in saleUserOpts"
                :key="'w-' + String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col v-if="!isExpSub" :span="12">
          <el-form-item label="订单币种" required>
            <el-select v-model="form.currencyType" style="width: 100%">
              <el-option :value="1" label="人民币" />
              <el-option :value="2" label="美金" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col v-if="isMainOrder" :span="12">
          <el-form-item label="分成比例" required>
            <div class="inline-ops">
              <el-button type="primary" @click="openShareDialog">添加分成比例</el-button>
              <span v-if="shareSummary" class="share-summary">{{ shareSummary }}</span>
              <span v-else class="share-hint">
                {{ isSubcontractMain ? '利润合计须为 100%' : '毛利合计须为 100%' }}
              </span>
            </div>
          </el-form-item>
        </el-col>
        <el-col v-if="isMainOrder" :span="12" />

        <el-col :span="12">
          <el-form-item :label="isSubcontractSub ? '预计发货时间' : '预计收货时间'" required>
            <el-date-picker
              v-model="form.deliveryTime"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="yyyy-mm-dd"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col v-if="!isExpSub" :span="12">
          <el-form-item label="付款方式" required>
            <el-select
              v-model="form.payWay"
              filterable
              :clearable="!payWayLocked"
              placeholder="请选择"
              style="width: 100%"
              :disabled="payWayLocked"
              @change="onPayWayChange"
            >
              <el-option
                v-for="o in payWayOpts"
                :key="String(o.value)"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
          </el-form-item>
        </el-col>

        <template v-if="collectionTimes.length && !isExpSub">
          <el-col v-for="(ct, idx) in collectionTimes" :key="`ct-${idx}`" :span="12">
            <el-form-item
              :label="`${isSubcontractSub ? '预计付款时间' : '预计收款时间'}${collectionTimes.length > 1 ? idx + 1 : ''}`"
              required
            >
              <el-date-picker
                v-model="collectionTimes[idx]"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="yyyy-mm-dd"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </template>

        <el-col v-if="!isExpSub" :span="12">
          <el-form-item :label="isSubcontractSub ? '实验分包总价' : '订单总价'" required>
            <el-input v-model="form.totalPrice" clearable placeholder="订单总价" />
          </el-form-item>
        </el-col>
        <el-col v-if="!isExpSub" :span="12">
          <el-form-item label="是否开票">
            <el-switch v-model="form.invoiceType" inline-prompt active-text="ON" inactive-text="OFF" />
          </el-form-item>
        </el-col>

        <template v-if="form.invoiceType && !isExpSub">
          <el-col :span="12">
            <el-form-item :label="isSubcontractSub ? '进项开票类型' : '出项开票类型'" required>
              <!-- v-model 必须是成员表达式，不能写三元（否则 vite:vue 构建失败） -->
              <el-select
                v-if="isSubcontractSub"
                v-model="form.inBillTypeId"
                filterable
                clearable
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option
                  v-for="o in inBillOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-select
                v-else
                v-model="form.outBillTypeId"
                filterable
                clearable
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option
                  v-for="o in outBillOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="税率" required>
              <el-select
                v-model="form.taxes"
                filterable
                clearable
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option
                  v-for="o in taxOpts"
                  :key="String(o.value)"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </template>

        <template v-if="isMainOrder">
          <el-col :span="12">
            <el-form-item label="样品是否回收">
              <el-switch
                v-model="form.reversoOn"
                inline-prompt
                active-text="ON"
                inactive-text="OFF"
              />
            </el-form-item>
          </el-col>
          <el-col v-if="form.reversoOn" :span="12">
            <el-form-item label="样品回收地址">
              <el-input v-model="form.sendAddress" clearable />
            </el-form-item>
          </el-col>
          <template v-if="form.reversoOn">
            <el-col :span="12">
              <el-form-item label="收件人姓名">
                <el-input v-model="form.addresseeName" clearable />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="收件人电话">
                <el-input v-model="form.addresseeMobile" clearable />
              </el-form-item>
            </el-col>
          </template>
        </template>

        <el-col :span="24">
          <el-form-item label="订单资料">
            <div class="file-row">
              <el-upload :show-file-list="false" :http-request="onUploadOrderFile">
                <el-button type="primary" :loading="uploading">上传文件</el-button>
              </el-upload>
              <div v-if="orderFiles.length" class="file-list">
                <el-tag
                  v-for="(f, idx) in orderFiles"
                  :key="String(f.id || idx)"
                  closable
                  class="file-tag"
                  @close="removeOrderFile(idx)"
                >
                  {{ String(f.info || f.name || f.id || '附件') }}
                </el-tag>
              </div>
            </div>
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="备注">
            <el-input v-model="form.mark" type="textarea" :rows="3" placeholder="请输入内容" />
          </el-form-item>
        </el-col>
      </el-row>

      <section class="lines-block">
        <div class="lines-head">
          <h3>产品明细</h3>
          <el-button v-if="isMainOrder" type="primary" @click="addLine">添加产品</el-button>
        </div>
        <!-- type9 对齐 Java experimentsub/purchase_edit_orders：勾选 + 成本单价 -->
        <el-table
          v-if="isSubcontractSub"
          ref="subLineTableRef"
          :data="lines"
          border
          stripe
          empty-text="暂无产品行"
          @selection-change="onSubLineSelectionChange"
        >
          <el-table-column type="selection" width="48" />
          <el-table-column prop="childOrderId" label="子订单编号" min-width="140" show-overflow-tooltip />
          <el-table-column prop="goodsName" label="产品名称" min-width="140" show-overflow-tooltip />
          <el-table-column prop="goodsBrandName" label="产品品牌" min-width="100" show-overflow-tooltip />
          <el-table-column prop="goodsSpec" label="型号" min-width="120" show-overflow-tooltip />
          <el-table-column prop="goodsNums" label="数量" width="90" />
          <el-table-column label="成本单价" width="130">
            <template #default="{ row }">
              <el-input v-model="row.costPrice" clearable @change="recalcCostTotal" />
            </template>
          </el-table-column>
        </el-table>
        <!-- type10：勾选决定挂接行；可改测试人员 / 实验平台 / 预计完成时间 -->
        <el-table
          v-else-if="isExpSub"
          ref="subLineTableRef"
          :data="lines"
          border
          stripe
          empty-text="暂无产品行"
          @selection-change="onSubLineSelectionChange"
        >
          <el-table-column type="selection" width="48" />
          <el-table-column prop="childOrderId" label="子订单编号" min-width="150" show-overflow-tooltip />
          <el-table-column prop="goodsName" label="产品名称" min-width="140" show-overflow-tooltip />
          <el-table-column label="产品型号" min-width="120">
            <template #default="{ row }">
              <el-input v-model="row.goodsSpec" clearable />
            </template>
          </el-table-column>
          <el-table-column prop="goodsBrandName" label="产品品牌" min-width="100" show-overflow-tooltip />
          <el-table-column label="数量" width="110">
            <template #default="{ row }">
              <el-input-number
                v-model="row.goodsNums"
                :min="1"
                :controls="false"
                style="width: 90px"
              />
            </template>
          </el-table-column>
          <el-table-column prop="projectName" label="实验测试项目" min-width="120" show-overflow-tooltip />
          <el-table-column prop="className" label="实验测试分类" min-width="120" show-overflow-tooltip />
          <el-table-column label="测试人员" width="160">
            <template #default="{ row }">
              <el-select
                v-model="row.testUserId"
                filterable
                clearable
                placeholder="请选择"
                style="width: 140px"
              >
                <el-option
                  v-if="String(row.testUserId || '') === GRAB_POOL_TEST_USER_ID"
                  label="待抢单"
                  :value="GRAB_POOL_TEST_USER_ID"
                />
                <el-option
                  v-for="u in testerOptionsForRow(row)"
                  :key="String(u.id)"
                  :label="testerLabel(u)"
                  :value="String(u.id)"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="实验平台" width="170">
            <template #default="{ row }">
              <el-select
                v-model="row.lineId"
                filterable
                clearable
                placeholder="请选择"
                style="width: 150px"
              >
                <el-option
                  v-for="p in platformOpts"
                  :key="String(p.value)"
                  :label="p.label"
                  :value="String(p.value)"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="预计完成时间" width="190">
            <template #default="{ row }">
              <el-date-picker
                v-model="row.expectFinishTime"
                type="datetime"
                value-format="YYYY-MM-DD HH:mm:ss"
                placeholder="预计完成"
                style="width: 178px"
              />
            </template>
          </el-table-column>
        </el-table>
        <!-- type6/8 主单：对齐 Java 可加减产品、点选商品/项目 -->
        <el-table v-else :data="lines" border stripe empty-text="暂无产品行">
          <el-table-column label="产品名称" min-width="140">
            <template #default="{ row }">
              <el-input
                v-model="row.goodsName"
                readonly
                placeholder="点击选择"
                @click="openGoodsPicker(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="产品型号" min-width="120">
            <template #default="{ row }">
              <el-select
                v-if="row.specOptions.length"
                v-model="row.goodsSpec"
                filterable
                allow-create
                clearable
                style="width: 100%"
              >
                <el-option v-for="s in row.specOptions" :key="s" :label="s" :value="s" />
              </el-select>
              <el-input v-else v-model="row.goodsSpec" clearable />
            </template>
          </el-table-column>
          <el-table-column prop="goodsBrandName" label="产品品牌" min-width="100" show-overflow-tooltip />
          <el-table-column label="数量" width="110">
            <template #default="{ row }">
              <el-input-number
                v-model="row.goodsNums"
                :min="1"
                :controls="false"
                style="width: 90px"
                @change="recalcTotal"
              />
            </template>
          </el-table-column>
          <el-table-column label="实验测试项目" min-width="130">
            <template #default="{ row }">
              <el-input
                v-model="row.projectName"
                readonly
                placeholder="点击选择"
                @click="openProjectPicker(row)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="className" label="实验测试分类" min-width="120" show-overflow-tooltip />
          <el-table-column label="实际测试金额" width="130">
            <template #default="{ row }">
              <el-input v-model="row.goodsPrice" clearable @change="recalcTotal" />
            </template>
          </el-table-column>
          <el-table-column label="标准测试金额" width="120">
            <template #default="{ row }">
              <el-input v-model="row.referencePrice" readonly />
            </template>
          </el-table-column>
          <el-table-column label="总价" width="100">
            <template #default="{ row }">
              <span>{{ lineTotal(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row, $index }">
              <el-button type="primary" link @click="addLine">+</el-button>
              <el-button
                type="danger"
                link
                :disabled="lines.length <= 1 || row.alreadyLinked"
                @click="removeLine($index)"
              >
                -
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="sum-row">
          <span v-if="isSubcontractSub">总成本：{{ totalCostAmount }}</span>
          <template v-else>
            <span>总计数量：{{ totalNums }}</span>
            <span v-if="!isExpSub">总计金额：{{ totalAmount }}</span>
          </template>
        </div>
      </section>

      <div class="save-bar">
        <el-button type="warning" size="large" :loading="saving" @click="onSave">保存</el-button>
        <el-button size="large" @click="goBack">取消</el-button>
      </div>
    </el-form>
    <el-empty v-else-if="!loading" description="订单不存在或不可编辑" />

    <el-dialog v-model="goodsDlg.visible" title="选择商品" width="720px" destroy-on-close>
      <el-form inline class="dlg-filter">
        <el-form-item label="名称">
          <el-input v-model="goodsDlg.keyword" clearable @keyup.enter="loadGoods" />
        </el-form-item>
        <el-button type="primary" @click="loadGoods">查询</el-button>
      </el-form>
      <el-table
        v-loading="goodsDlg.loading"
        :data="goodsDlg.rows"
        border
        stripe
        height="360"
        highlight-current-row
        @row-click="onPickGoods"
      >
        <el-table-column prop="goodsName" label="商品名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="brandName" label="品牌" width="120" show-overflow-tooltip />
        <el-table-column prop="goodsModel" label="型号" min-width="140" show-overflow-tooltip />
      </el-table>
    </el-dialog>

    <el-dialog v-model="projectDlg.visible" title="选择实验测试项目" width="720px" destroy-on-close>
      <el-form inline class="dlg-filter">
        <el-form-item label="名称">
          <el-input v-model="projectDlg.keyword" clearable @keyup.enter="loadProjects" />
        </el-form-item>
        <el-button type="primary" @click="loadProjects">查询</el-button>
      </el-form>
      <el-table
        v-loading="projectDlg.loading"
        :data="projectDlg.rows"
        border
        stripe
        height="360"
        highlight-current-row
        @row-click="onPickProject"
      >
        <el-table-column prop="projectName" label="项目名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="className" label="分类" width="140" show-overflow-tooltip />
        <el-table-column prop="testPrice" label="测试金额" width="120" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="shareDlg.visible" title="添加分成比例" width="720px" destroy-on-close>
      <div class="share-block">
        <div class="share-head">
          <strong>{{ isSubcontractMain ? '利润分成' : '毛利分成' }}</strong>
          <el-button type="primary" link @click="addShareRow(profitRows)">添加</el-button>
        </div>
        <div v-for="(row, idx) in profitRows" :key="`p-${idx}`" class="share-row">
          <el-select
            v-model="row.userId"
            filterable
            clearable
            placeholder="分成人员"
            style="width: 220px"
          >
            <el-option
              v-for="u in shareUsers"
              :key="String(u.id)"
              :label="shareUserLabel(u)"
              :value="String(u.id)"
            />
          </el-select>
          <el-input v-model="row.value" placeholder="比例" style="width: 120px">
            <template #append>%</template>
          </el-input>
          <el-button type="danger" link @click="profitRows.splice(idx, 1)">删除</el-button>
        </div>
      </div>
      <template v-if="!isSubcontractMain">
        <el-divider />
        <div class="share-block">
          <div class="share-head">
            <strong>成本分成</strong>
            <el-button type="primary" link @click="addShareRow(costRows)">添加</el-button>
          </div>
          <div v-for="(row, idx) in costRows" :key="`c-${idx}`" class="share-row">
            <el-select
              v-model="row.userId"
              filterable
              clearable
              placeholder="分成人员"
              style="width: 220px"
            >
              <el-option
                v-for="u in shareUsers"
                :key="String(u.id)"
                :label="shareUserLabel(u)"
                :value="String(u.id)"
              />
            </el-select>
            <el-input v-model="row.value" placeholder="分成金额" style="width: 140px" />
            <el-button type="danger" link @click="costRows.splice(idx, 1)">删除</el-button>
          </div>
        </div>
      </template>
      <template #footer>
        <el-button @click="shareDlg.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmShare">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onDeactivated, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { TableInstance } from 'element-plus'
import {
  deleteExpOrderFile,
  fetchExpGoodsList,
  fetchManageOptions,
  fetchProjectList,
  getExpOrderDetail,
  updateExpOrderBasic,
  uploadExpOrderFile,
} from '@/api/experiment'
import { fetchSelLineList } from '@/api/inventory'
import { fetchCustomerAccounts, fetchCustomerNamesExp } from '@/api/member'
import { fetchBillTypeAll, fetchPaytypeAll, fetchTaxAll } from '@/api/order-settings'
import { fetchSupplierAll, fetchTestUsers, fetchUserList } from '@/api/system'
import { detailFromByOrderType, useTagsViewStore } from '@/stores/tags-view'
import { ajaxErrorMessage, isAjaxOk } from '@/utils/request'

type Opt = { value: string; label: string; nums?: number }
type ShareRow = { userId: string; value: string }
type LineRow = {
  id: string | number
  goodsId: string
  goodsName: string
  goodsSpec: string
  goodsBrandId: string
  goodsBrandName: string
  goodsNums: number
  goodsPrice: string
  referencePrice: string
  costPrice: string
  projectId: string
  projectName: string
  classId: string
  className: string
  childOrderId: string
  specOptions: string[]
  testUserId: string
  lineId: string
  expectFinishTime: string
  /** 子单编辑：是否已挂接到本单（默认勾选） */
  linkedToThis?: boolean
  /** 主单编辑：已挂接有效子订单的产品行不可删除。 */
  alreadyLinked?: boolean
}

const route = useRoute()
const router = useRouter()
const tagsViewStore = useTagsViewStore()
const orderId = String(route.params.id || '')

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const lines = ref<LineRow[]>([])
/** type9/10 勾选列：对齐 Java checkChilds，决定本子单挂接哪些产品行 */
const subLineTableRef = ref<TableInstance>()
const selectedSubLines = ref<LineRow[]>([])
/** 编辑页点「-」移除的已有产品行 id，保存时显式软删 */
const removedLineIds = ref<(string | number)[]>([])
const orderFiles = ref<Record<string, unknown>[]>([])
const collectionTimes = ref<string[]>([])
const payWayLocked = ref(false)

/** 6=实验主单 8=分包主单 9=分包子单 10=实验子单 */
const orderType = computed(() => String(detail.value?.orderType || detail.value?.order_type || '6'))
const isMainOrder = computed(() => orderType.value === '6' || orderType.value === '8')
/** 分包主单：对齐 Java 仅利润分成，无成本分成 */
const isSubcontractMain = computed(() => orderType.value === '8')
const isSubcontractSub = computed(() => orderType.value === '9')
const isExpSub = computed(() => orderType.value === '10')

const form = reactive({
  totalPrice: '',
  mark: '',
  deliveryTime: '',
  orderTime: '',
  currencyType: 1 as number,
  payWay: '',
  invoiceType: false,
  taxes: '',
  outBillTypeId: '',
  inBillTypeId: '',
  saleManagerId: '',
  saleUserId: '',
  supplierId: '',
  stockCompanyId: '',
  customerId: '',
  customUserId: '',
  warehouseUserId: '',
  classId: '',
  sendAddress: '',
  addresseeName: '',
  addresseeMobile: '',
  userScaleInfo: '',
  salecbUserScaleInfo: '',
  reversoOn: false,
})

const supplierOpts = ref<Opt[]>([])
const customerOpts = ref<Opt[]>([])
const accountOpts = ref<Opt[]>([])
const classOpts = ref<Opt[]>([])
const managerOpts = ref<Opt[]>([])
const saleUserOpts = ref<Opt[]>([])
const payWayOpts = ref<Opt[]>([])
const outBillOpts = ref<Opt[]>([])
const inBillOpts = ref<Opt[]>([])
const taxOpts = ref<Opt[]>([])
const shareUsers = ref<Record<string, unknown>[]>([])
const profitRows = ref<ShareRow[]>([{ userId: '', value: '' }])
const costRows = ref<ShareRow[]>([{ userId: '', value: '' }])
const shareDlg = reactive({ visible: false })
const shareSummary = ref('')
const goodsDlg = reactive({
  visible: false,
  loading: false,
  keyword: '',
  rows: [] as Record<string, unknown>[],
  target: null as LineRow | null,
})
const projectDlg = reactive({
  visible: false,
  loading: false,
  keyword: '',
  rows: [] as Record<string, unknown>[],
  target: null as LineRow | null,
})
const platformOpts = ref<Opt[]>([])
const testerDefault = ref<Record<string, unknown>[]>([])
const testerByClass = ref<Record<string, Record<string, unknown>[]>>({})
/** Java 待抢池哨兵：test_user_id=22 */
const GRAB_POOL_TEST_USER_ID = '22'

const totalNums = computed(() =>
  lines.value.reduce((s, r) => s + (Number(r.goodsNums) || 0), 0)
)
const totalAmount = computed(() =>
  lines.value
    .reduce((s, r) => s + (Number(r.goodsNums) || 0) * (parseFloat(String(r.goodsPrice || 0)) || 0), 0)
    .toFixed(2)
)
const totalCostAmount = computed(() => {
  const rows =
    isSubcontractSub.value && selectedSubLines.value.length
      ? selectedSubLines.value
      : lines.value
  return rows.reduce((s, r) => s + (parseFloat(String(r.costPrice || 0)) || 0), 0).toFixed(2)
})

function onSubLineSelectionChange(rows: LineRow[]) {
  selectedSubLines.value = rows
}

function mapChildToLine(ch: Record<string, unknown>): LineRow {
  const spec = String(ch.goodsSpec || '')
  return {
    id: (ch.id ?? '') as string | number,
    goodsId: String(ch.goodsId || ch.goods_id || ''),
    goodsName: String(ch.goodsName || ''),
    goodsSpec: spec,
    goodsBrandId: String(ch.goodsBrandId || ch.goods_brand_id || ''),
    goodsBrandName: String(ch.goodsBrandName || ch.goodsBrand || ''),
    goodsNums: Number(ch.goodsNums || ch.goodsCount || 1) || 1,
    goodsPrice:
      ch.price != null ? String(ch.price) : ch.goodsPrice != null ? String(ch.goodsPrice) : '',
    referencePrice:
      ch.referencePrice != null
        ? String(ch.referencePrice)
        : ch.reference_price != null
          ? String(ch.reference_price)
          : '',
    costPrice: ch.costPrice != null ? String(ch.costPrice) : '',
    projectId: String(ch.projectId || ch.experimentProjectId || ''),
    projectName: String(ch.projectName || ch.experimentProjectName || ''),
    classId: String(ch.classId || ch.experimentClassId || ''),
    className: String(ch.className || ch.experimentClassName || ch.deviceName || ''),
    childOrderId: String(ch.childOrderId || ch.orderId || ''),
    specOptions: spec ? [spec] : [],
    testUserId: ch.testUserId != null ? String(ch.testUserId) : '',
    lineId: ch.lineId != null ? String(ch.lineId) : ch.line_id != null ? String(ch.line_id) : '',
    expectFinishTime: String(
      ch.expectFinishTime || ch.expect_finishtime || ch.finishTime || ''
    ),
    linkedToThis:
      ch.linkedToThis === true ||
      ch.linkedToThis === 1 ||
      ch.linkedToThis === '1' ||
      ch.linkedToThis == null,
    alreadyLinked:
      ch.alreadyLinked === true || ch.alreadyLinked === 1 || ch.alreadyLinked === '1',
  }
}

async function applyDefaultSubSelection() {
  await nextTick()
  await nextTick()
  const table = subLineTableRef.value
  if (!table) return
  table.clearSelection()
  for (const row of lines.value) {
    if (row.linkedToThis !== false) {
      table.toggleRowSelection(row, true)
    }
  }
}

function goBack() {
  router.push({
    name: 'ExperimentOrderDetail',
    params: { id: orderId },
    query: {
      from: detailFromByOrderType(orderType.value),
      ...(detail.value?.orderId
        ? { orderNo: String(detail.value.orderId) }
        : {}),
    },
  })
}

/** 保存成功：关闭编辑标签 → 打开详情并强制刷新 */
async function closeEditAndRefreshDetail() {
  const editPath = route.path
  const orderNo = String(detail.value?.orderId || '').trim()
  const from = detailFromByOrderType(orderType.value)
  await router.push({
    name: 'ExperimentOrderDetail',
    params: { id: orderId },
    query: {
      from,
      ...(orderNo ? { orderNo } : {}),
    },
  })
  tagsViewStore.delView(editPath)
  // 离开后再作废编辑页 keep-alive，避免下次仍用「新增行 id 为空」的脏缓存
  tagsViewStore.refreshView(editPath)
  tagsViewStore.refreshView(router.currentRoute.value.path)
}

function openAddCustomer() {
  window.open(router.resolve({ name: 'MemberEnterprise' }).href, '_blank')
}
function openAddSupplier() {
  window.open(router.resolve({ name: 'SystemCompanies' }).href, '_blank')
}

/** 统一成 string，避免 el-select 因 number/string 不一致只显示裸 id */
function asOptValue(v: unknown): string {
  if (v == null || v === '') return ''
  return String(v)
}

function displayLabel(v: unknown): string {
  const s = String(v ?? '').trim()
  return !s || s === '-' ? '' : s
}

function ensureOpt(opts: { value: Opt[] }, value: string | number | '', label?: string) {
  if (value === '' || value == null) return
  const key = String(value)
  const text = displayLabel(label)
  const idx = opts.value.findIndex((o) => String(o.value) === key)
  if (idx >= 0) {
    const cur = opts.value[idx]
    const weakLabel = !cur.label || cur.label === key || String(cur.label) === String(cur.value)
    if (cur.value !== key || (text && weakLabel)) {
      opts.value[idx] = { ...cur, value: key, label: text && weakLabel ? text : cur.label || text || key }
    }
    return
  }
  opts.value.unshift({ value: key, label: text || key })
}

function mapUserRows(rows: Record<string, unknown>[]): Opt[] {
  return rows
    .map((u) => ({
      value: String(u.id ?? ''),
      label: String(u.trueName || u.true_name || u.userName || u.user_name || u.id || ''),
    }))
    .filter((o) => o.value !== '')
}

function lineTotal(row: LineRow) {
  const n = (Number(row.goodsNums) || 0) * (parseFloat(String(row.goodsPrice || 0)) || 0)
  return n ? n.toFixed(2) : ''
}

function recalcTotal() {
  form.totalPrice = totalAmount.value
}

function recalcCostTotal() {
  form.totalPrice = totalCostAmount.value
}

function emptyLine(): LineRow {
  return {
    id: '',
    goodsId: '',
    goodsName: '',
    goodsSpec: '',
    goodsBrandId: '',
    goodsBrandName: '',
    goodsNums: 1,
    goodsPrice: '',
    referencePrice: '',
    costPrice: '',
    projectId: '',
    projectName: '',
    classId: '',
    className: '',
    childOrderId: '',
    specOptions: [],
    testUserId: '',
    lineId: '',
    expectFinishTime: '',
  }
}

function addLine() {
  lines.value.push(emptyLine())
}

function removeLine(idx: number) {
  if (lines.value.length <= 1) {
    ElMessage.warning('实验订单至少选择一个产品，不可删除最后一个')
    return
  }
  const row = lines.value[idx]
  if (row?.alreadyLinked) {
    ElMessage.warning('该产品已创建子订单，不可删除')
    return
  }
  if (row && row.id !== '' && row.id != null) {
    removedLineIds.value.push(row.id)
  }
  lines.value.splice(idx, 1)
  recalcTotal()
}

function testerLabel(u: Record<string, unknown>) {
  return String(u.trueName || u.true_name || u.userName || u.user_name || u.id || '')
}

function testerOptionsForRow(row: LineRow) {
  const cid = String(row.classId || detail.value?.classId || '')
  const raw =
    cid && testerByClass.value[cid]?.length
      ? testerByClass.value[cid]
      : testerDefault.value
  // 待抢池账号不进普通下拉，避免与「待抢单」选项抢同一 value 导致回显错乱
  return (raw || []).filter((u) => String(u.id) !== GRAB_POOL_TEST_USER_ID)
}

/** 把当前行测试人员塞进下拉，保证抢单后能回显姓名而非「待抢单」 */
function ensureTesterOnRow(row: LineRow, children: Record<string, unknown>[]) {
  const tid = String(row.testUserId || '').trim()
  if (!tid || tid === GRAB_POOL_TEST_USER_ID) return
  const hit = children.find((c) => String(c.id) === String(row.id))
  let name = String(
    hit?.testUserTrueName || hit?.testUserName || hit?.testUser || ''
  ).trim()
  if (!name || name === '-' || name === '待抢单' || name === '抢单') {
    name = ''
  }
  const patch = {
    id: tid,
    trueName: name || tid,
    userName: name || tid,
  }
  const cid = String(row.classId || '').trim()
  if (cid) {
    const bucket = testerByClass.value[cid] || []
    if (!bucket.some((u) => String(u.id) === tid)) {
      testerByClass.value[cid] = [patch, ...bucket]
    } else {
      // 列表里已有但名为空时补姓名
      testerByClass.value[cid] = bucket.map((u) =>
        String(u.id) === tid && name && !testerLabel(u)
          ? { ...u, trueName: name, userName: name }
          : u
      )
    }
  }
  if (!testerDefault.value.some((u) => String(u.id) === tid)) {
    testerDefault.value = [patch, ...testerDefault.value]
  } else if (name) {
    testerDefault.value = testerDefault.value.map((u) =>
      String(u.id) === tid && !testerLabel(u)
        ? { ...u, trueName: name, userName: name }
        : u
    )
  }
}

async function loadTestersForClasses(classIds: string[]) {
  const silent = { silentError: true } as const
  const uniq = Array.from(new Set(classIds.map((x) => String(x || '').trim()).filter(Boolean)))
  if (!uniq.length) {
    try {
      const res = await fetchTestUsers('', silent)
      testerDefault.value = Array.isArray(res.obj) ? (res.obj as Record<string, unknown>[]) : []
    } catch {
      testerDefault.value = []
    }
    return
  }
  await Promise.all(
    uniq.map(async (cid) => {
      if (testerByClass.value[cid]?.length) return
      try {
        const res = await fetchTestUsers(cid, silent)
        testerByClass.value[cid] = Array.isArray(res.obj)
          ? (res.obj as Record<string, unknown>[])
          : []
      } catch {
        testerByClass.value[cid] = []
      }
    })
  )
  const first = uniq[0]
  if (first) testerDefault.value = testerByClass.value[first] || []
}

async function loadPlatforms() {
  try {
    const res = await fetchSelLineList({ start: 0, length: 500, draw: 1 })
    const list = Array.isArray(res.data) ? res.data : Array.isArray(res.obj) ? res.obj : []
    platformOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: String(r.id ?? ''),
        label: String(r.lineNum || r.line_num || r.name || r.id || ''),
      }))
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    platformOpts.value = []
  }
}

function openGoodsPicker(row: LineRow) {
  goodsDlg.target = row
  goodsDlg.keyword = ''
  goodsDlg.visible = true
  loadGoods()
}

async function loadGoods() {
  goodsDlg.loading = true
  try {
    const res = await fetchExpGoodsList({
      start: 0,
      length: 50,
      draw: 1,
      name: goodsDlg.keyword || '',
    })
    goodsDlg.rows = Array.isArray(res.data) ? res.data : []
  } catch {
    goodsDlg.rows = []
  } finally {
    goodsDlg.loading = false
  }
}

function onPickGoods(row: Record<string, unknown>) {
  const target = goodsDlg.target
  if (!target) return
  target.goodsId = String(row.id || '')
  target.goodsName = String(row.goodsName || '')
  target.goodsBrandId = String(row.brandId || '')
  target.goodsBrandName = String(row.brandName || '')
  const model = String(row.goodsModel || '')
  target.specOptions = model
    ? model
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
    : []
  target.goodsSpec = target.specOptions[0] || model
  goodsDlg.visible = false
  openProjectPicker(target)
}

function openProjectPicker(row: LineRow) {
  projectDlg.target = row
  projectDlg.keyword = ''
  projectDlg.visible = true
  loadProjects()
}

async function loadProjects() {
  projectDlg.loading = true
  try {
    const res = await fetchProjectList({
      start: 0,
      length: 50,
      draw: 1,
      name: projectDlg.keyword || '',
    })
    projectDlg.rows = Array.isArray(res.data) ? res.data : []
  } catch {
    projectDlg.rows = []
  } finally {
    projectDlg.loading = false
  }
}

function onPickProject(row: Record<string, unknown>) {
  const target = projectDlg.target
  if (!target) return
  target.projectId = String(row.id || '')
  target.projectName = String(row.projectName || '')
  target.classId = String(row.classId || '')
  target.className = String(row.className || '')
  const price = row.testPrice ?? row.test_price ?? row.price
  if (price != null && price !== '') {
    const n = Number(price)
    if (!Number.isNaN(n)) {
      target.goodsPrice = String(n)
      target.referencePrice = String(n)
    }
  }
  projectDlg.visible = false
  recalcTotal()
}

function shareUserLabel(u: Record<string, unknown>) {
  return String(u.trueName || u.true_name || u.userName || u.user_name || u.id || '')
}

function addShareRow(list: ShareRow[]) {
  list.push({ userId: '', value: '' })
}

function buildScaleInfo(rows: ShareRow[]) {
  return rows
    .filter((r) => r.userId && String(r.value).trim() !== '')
    .map((r) => `${r.userId}_${String(r.value).trim()}`)
    .join(',')
}

function parseScalePairs(raw: unknown): ShareRow[] {
  const s = String(raw || '').trim()
  if (!s) return [{ userId: '', value: '' }]
  const rows = s
    .split(',')
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => {
      const idx = p.indexOf('_')
      if (idx < 0) return { userId: p, value: '' }
      return { userId: p.slice(0, idx), value: p.slice(idx + 1) }
    })
  return rows.length ? rows : [{ userId: '', value: '' }]
}

function refreshShareSummary() {
  const profitText = parseScalePairs(form.userScaleInfo)
    .filter((r) => r.userId)
    .map((r) => {
      const u = shareUsers.value.find((x) => String(x.id) === r.userId)
      return `${shareUserLabel(u || { id: r.userId })} ${r.value}%`
    })
    .join('，')
  const label = isSubcontractMain.value ? '利润' : '毛利'
  shareSummary.value = profitText
    ? `${label}：${profitText}`
    : form.userScaleInfo
      ? `${label}：${form.userScaleInfo}`
      : ''
}

function openShareDialog() {
  profitRows.value = parseScalePairs(form.userScaleInfo)
  costRows.value = isSubcontractMain.value
    ? [{ userId: '', value: '' }]
    : parseScalePairs(form.salecbUserScaleInfo)
  shareDlg.visible = true
}

function confirmShare() {
  const profitLabel = isSubcontractMain.value ? '利润分成' : '毛利分成'
  for (const r of profitRows.value) {
    if (r.userId && !String(r.value).trim()) {
      ElMessage.warning('请填写正确的分成比例!')
      return
    }
    if (!r.userId && String(r.value).trim()) {
      ElMessage.warning(`请选择${profitLabel}人员!`)
      return
    }
  }
  const sum = profitRows.value
    .filter((r) => r.userId)
    .reduce((s, r) => s + (parseFloat(String(r.value)) || 0), 0)
  if (Math.abs(sum - 100) > 0.01 && profitRows.value.some((r) => r.userId)) {
    ElMessage.warning('总的分成比例不是100，请重新输入')
    return
  }
  form.userScaleInfo = buildScaleInfo(profitRows.value)
  form.salecbUserScaleInfo = isSubcontractMain.value ? '' : buildScaleInfo(costRows.value)
  refreshShareSummary()
  shareDlg.visible = false
}

function onPayWayChange(id: string | number | '') {
  const pt = payWayOpts.value.find((p) => String(p.value) === String(id))
  const nums = Math.max(0, Number(pt?.nums || 0))
  const prev = [...collectionTimes.value]
  collectionTimes.value = Array.from({ length: nums }, (_, i) => prev[i] || '')
}

async function reloadCustomers() {
  try {
    const res = await fetchCustomerNamesExp()
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    customerOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: String(r.id ?? ''),
        label: String(r.name || r.companyName || r.company_name || ''),
      }))
      .filter((o) => o.value !== '' && o.label)
  } catch {
    /* ignore */
  }
}

async function reloadAccounts(parentId?: string | number) {
  try {
    const res = await fetchCustomerAccounts(parentId || '')
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    accountOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: String(r.id ?? ''),
        label: String(r.mobile || r.userName || r.trueName || r.name || r.id || ''),
      }))
      .filter((o) => o.value !== '')
  } catch {
    accountOpts.value = []
  }
}

async function onCustomerChange(id: string | number | '') {
  form.customUserId = ''
  await reloadAccounts(id || '')
}

async function reloadSuppliers() {
  try {
    const res = await fetchSupplierAll({ silentError: true })
    const list = Array.isArray(res.obj) ? res.obj : Array.isArray(res.data) ? res.data : []
    supplierOpts.value = (list as Record<string, unknown>[])
      .map((r) => ({
        value: String(r.id ?? ''),
        label: String(r.companyName || r.company_name || r.name || r.id || ''),
      }))
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
}

async function loadOptions() {
  const silent = { silentError: true } as const
  await reloadCustomers()
  // 先加载全量客户账号，详情回填/未选客户名称时下拉也有数据
  await reloadAccounts('')
  await reloadSuppliers()
  try {
    const cls = await fetchManageOptions(3)
    const list = Array.isArray(cls.obj) ? (cls.obj as Record<string, unknown>[]) : []
    classOpts.value = list
      .map((r) => ({
        value: String(r.id ?? r.value ?? ''),
        label: String(r.name || r.label || r.id || ''),
      }))
      .filter((o) => o.value !== '')
  } catch {
    classOpts.value = []
  }
  try {
    const mgr = await fetchUserList({ start: 0, length: 500, type: 1, draw: 1 }, silent)
    managerOpts.value = mapUserRows(Array.isArray(mgr.data) ? mgr.data : [])
  } catch {
    /* ignore */
  }
  try {
    const sale = await fetchUserList({ start: 0, length: 500, type: -1, draw: 1 }, silent)
    const rows = Array.isArray(sale.data) ? sale.data : []
    saleUserOpts.value = mapUserRows(rows)
    shareUsers.value = rows as Record<string, unknown>[]
  } catch {
    /* ignore */
  }
  try {
    const pay = await fetchPaytypeAll()
    const rows = Array.isArray(pay.data) ? pay.data : []
    payWayOpts.value = rows
      .map((r) => {
        const row = r as Record<string, unknown>
        return {
          value: String(row.id ?? ''),
          label: String(row.name || row.payName || row.id || ''),
          nums: Number(row.nums || row.payNums || row.pay_nums || 0) || 0,
        }
      })
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
  try {
    const bills = await fetchBillTypeAll(1)
    const rows = Array.isArray(bills.data) ? bills.data : []
    outBillOpts.value = rows
      .map((r) => {
        const row = r as Record<string, unknown>
        return {
          value: String(row.id ?? ''),
          label: String(row.name || row.id || ''),
        }
      })
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
  try {
    const billsIn = await fetchBillTypeAll(2)
    const rows = Array.isArray(billsIn.data) ? billsIn.data : []
    inBillOpts.value = rows
      .map((r) => {
        const row = r as Record<string, unknown>
        return {
          value: String(row.id ?? ''),
          label: String(row.name || row.id || ''),
        }
      })
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
  try {
    const tax = await fetchTaxAll()
    const list = Array.isArray(tax.obj)
      ? (tax.obj as Record<string, unknown>[])
      : Array.isArray(tax.data)
        ? (tax.data as Record<string, unknown>[])
        : []
    taxOpts.value = list
      .map((r) => ({
        value: String(r.taxValue ?? r.tax_value ?? r.id ?? ''),
        label: String(
          r.name ||
            (r.taxValue != null || r.tax_value != null
              ? `${Number(r.taxValue ?? r.tax_value) * 100}%`
              : r.id) ||
            ''
        ),
      }))
      .filter((o) => o.value !== '' && o.value != null)
  } catch {
    /* ignore */
  }
}

async function load() {
  if (!orderId) return
  loading.value = true
  try {
    const res = await getExpOrderDetail(orderId)
    if (!isAjaxOk(res) || !res.obj) {
      detail.value = null
      ElMessage.error(ajaxErrorMessage(res, '加载失败'))
      return
    }
    const obj = res.obj as Record<string, unknown>
    detail.value = obj
    const st = Number(obj.orderStatus ?? obj.order_status ?? 0)
    const isOnline = Number(obj.isOnline ?? obj.is_online ?? 0) === 1
    // 对齐 Java experiment_edit_orders / experimentsub_edit_orders：
    // 线上订单 is_online=1 不可改；已审核(30)/已完成(50)不可改
    payWayLocked.value = isOnline || st === 30 || st === 50

    const files = Array.isArray(obj.files) ? (obj.files as Record<string, unknown>[]) : []
    orderFiles.value = files.map((f) => ({ ...f }))
    form.totalPrice = obj.totalPrice != null ? String(obj.totalPrice) : ''
    form.mark = String(obj.mark || obj.msg || '')
    form.deliveryTime = String(obj.deliveryTime || '').slice(0, 10)
    form.orderTime = String(obj.orderTime || '').slice(0, 10)
    form.currencyType = Number(obj.currencyType || 1) === 2 ? 2 : 1
    form.payWay = asOptValue(obj.payWay)
    form.invoiceType = String(obj.invoiceType || '') === '1' || obj.invoiceLabel === '是'
    form.taxes = obj.taxes != null && String(obj.taxes) !== '' ? String(obj.taxes) : ''
    form.outBillTypeId = asOptValue(obj.outBillTypeId)
    form.inBillTypeId = asOptValue(obj.inBillTypeId)
    form.saleManagerId = asOptValue(obj.saleManagerId)
    form.saleUserId = asOptValue(obj.saleUserId)
    form.supplierId = asOptValue(obj.supplierId)
    form.stockCompanyId = asOptValue(
      obj.stockCompanyId || obj.stock_company_name || obj.stockCompanyName
    )
    form.customerId = asOptValue(obj.customerId)
    form.customUserId = asOptValue(obj.customUserId)
    form.warehouseUserId = asOptValue(obj.warehouseUserId || obj.stockUserId)
    form.classId = asOptValue(obj.classId)
    form.userScaleInfo = String(obj.userScaleInfo || obj.scaleInfo || '')
    form.salecbUserScaleInfo = String(obj.salecbUserScaleInfo || '')
    form.reversoOn =
      String(obj.reversoContext || '').toUpperCase() === 'ON' ||
      String(obj.reversoLabel || '') === '是' ||
      Number(obj.reversoContext) === 1
    form.sendAddress = String(obj.shipAddress || obj.sendAddress || '')
    form.addresseeName = String(obj.shipUser || obj.addresseeName || '')
    form.addresseeMobile = String(obj.shipPhone || obj.addresseeMobile || obj.mobile || '')

    ensureOpt(supplierOpts, form.supplierId, displayLabel(obj.supplierName))
    ensureOpt(
      supplierOpts,
      form.stockCompanyId,
      displayLabel(obj.stockCompanyName || obj.supplierName)
    )
    ensureOpt(customerOpts, form.customerId, displayLabel(obj.customerName || obj.companyName))
    ensureOpt(classOpts, form.classId, displayLabel(obj.testClassName || obj.className))
    ensureOpt(managerOpts, form.saleManagerId, displayLabel(obj.saleManager || obj.saleManagerTrueName || obj.saleManagerName))
    ensureOpt(saleUserOpts, form.saleUserId, displayLabel(obj.saleUser || obj.saleUserTrueName || obj.saleUserName))
    ensureOpt(
      saleUserOpts,
      form.warehouseUserId,
      displayLabel(obj.warehouseUser || obj.stockUser || obj.warehouseUserTrueName || obj.warehouseUserName)
    )
    ensureOpt(payWayOpts, form.payWay, displayLabel(obj.payWayName))
    ensureOpt(outBillOpts, form.outBillTypeId, displayLabel(obj.outBillTypeName))
    ensureOpt(inBillOpts, form.inBillTypeId, displayLabel(obj.inBillTypeName))
    if (form.taxes !== '') ensureOpt(taxOpts, form.taxes, String(form.taxes))

    // 无客户名称时也拉取账号列表（parentId 空=全部），避免下拉「无数据」无法选择
    await reloadAccounts(form.customerId || '')
    ensureOpt(
      accountOpts,
      form.customUserId,
      displayLabel(obj.customMobile || obj.customUserMobile || obj.customUserName || obj.mobile)
    )

    const coll = String(obj.collectionTime || '')
    onPayWayChange(form.payWay)
    if (coll && collectionTimes.value.length) {
      const parts = coll.split(',').map((x) => x.trim().slice(0, 10))
      collectionTimes.value = collectionTimes.value.map((_, i) => parts[i] || '')
    } else if (coll && !collectionTimes.value.length) {
      collectionTimes.value = coll
        .split(',')
        .map((x) => x.trim().slice(0, 10))
        .filter(Boolean)
    }

    refreshShareSummary()

    const orderTypeRaw = String(obj.orderType || obj.order_type || '')
    const childrenRaw =
      orderTypeRaw === '9' || orderTypeRaw === '10'
        ? Array.isArray(obj.editSelectableChildren)
          ? (obj.editSelectableChildren as Record<string, unknown>[])
          : Array.isArray(obj.children)
            ? (obj.children as Record<string, unknown>[])
            : []
        : Array.isArray(obj.children)
          ? (obj.children as Record<string, unknown>[])
          : []
    removedLineIds.value = []
    selectedSubLines.value = []
    lines.value = childrenRaw.map((ch) => mapChildToLine(ch))

    if (String(obj.orderType || obj.order_type || '') === '10') {
      await loadPlatforms()
      const classIds = lines.value.map((r) => r.classId).filter(Boolean)
      if (obj.classId) classIds.push(String(obj.classId))
      await loadTestersForClasses(classIds)
      for (const row of lines.value) {
        ensureTesterOnRow(row, childrenRaw)
        if (row.lineId) {
          const hit = childrenRaw.find((c) => String(c.id) === String(row.id))
          ensureOpt(
            platformOpts,
            row.lineId,
            String(hit?.platformName || hit?.lineNum || hit?.line_num || row.lineId)
          )
        }
      }
    }
    if (
      String(obj.orderType || obj.order_type || '') === '9' ||
      String(obj.orderType || obj.order_type || '') === '10'
    ) {
      await applyDefaultSubSelection()
    }
  } finally {
    loading.value = false
  }
}

async function onSave() {
  // 对齐 Java：客户名称 / 客户账号二选一，仅两者都空才拦截
  if (!isSubcontractSub.value && !form.customerId && !form.customUserId) {
    ElMessage.warning('客户名称和客户账号不能同时为空')
    return
  }
  if (!form.saleManagerId) {
    ElMessage.warning(isExpSub.value ? '请选择实验室主管' : '请选择销售主管')
    return
  }
  if (!isSubcontractSub.value && !form.saleUserId) {
    ElMessage.warning('请选择销售人员')
    return
  }
  if (isSubcontractSub.value && !form.stockCompanyId) {
    ElMessage.warning('请选择实验分包公司')
    return
  }
  if (!isSubcontractSub.value && !form.supplierId) {
    ElMessage.warning(isMainOrder.value ? '请选择供应商' : '请选择所属公司')
    return
  }
  if (isExpSub.value && !form.warehouseUserId) {
    ElMessage.warning('请选择仓库管理员')
    return
  }
  if (!form.deliveryTime) {
    ElMessage.warning(isSubcontractSub.value ? '请填写预计发货时间' : '请填写预计收货时间')
    return
  }
  if (!isExpSub.value && !form.payWay) {
    ElMessage.warning('请选择付款方式')
    return
  }
  if (!isExpSub.value && collectionTimes.value.length && collectionTimes.value.some((t) => !t)) {
    ElMessage.warning(isSubcontractSub.value ? '请填写预计付款时间' : '请填写预计收款时间')
    return
  }
  if (isSubcontractSub.value) {
    if (!selectedSubLines.value.length) {
      ElMessage.warning('请至少选择一个子订单!')
      return
    }
    if (selectedSubLines.value.some((r) => !String(r.costPrice || '').trim())) {
      ElMessage.warning('请填写成本单价')
      return
    }
    form.totalPrice = totalCostAmount.value
  }
  if (isMainOrder.value) {
    if (!lines.value.length) {
      ElMessage.warning('实验订单至少选择一个产品才可提交')
      return
    }
    for (const [i, row] of lines.value.entries()) {
      if (!row.goodsId && !row.goodsName) {
        ElMessage.warning(`第 ${i + 1} 行请选择产品`)
        return
      }
      if (!row.projectId && !row.projectName) {
        ElMessage.warning(`第 ${i + 1} 行请选择测试项目`)
        return
      }
    }
    recalcTotal()
  }
  if (isExpSub.value) {
    if (!selectedSubLines.value.length) {
      ElMessage.warning('请至少选择一个子订单!')
      return
    }
    for (const [i, row] of selectedSubLines.value.entries()) {
      if (!row.testUserId) {
        ElMessage.warning(`第 ${i + 1} 行请选择测试人员`)
        return
      }
      if (!row.lineId) {
        ElMessage.warning(`第 ${i + 1} 行请选择实验平台`)
        return
      }
    }
  }
  if (isMainOrder.value && !form.classId) {
    ElMessage.warning('请选择订单类型')
    return
  }
  if (isMainOrder.value && !form.supplierId) {
    ElMessage.warning('请选择供应商')
    return
  }
  if (!isExpSub.value && !form.totalPrice) {
    ElMessage.warning(isSubcontractSub.value ? '请填写实验分包总价' : '请填写订单总价')
    return
  }
  if (isMainOrder.value && !form.userScaleInfo) {
    ElMessage.warning('请填写分成比例')
    return
  }
  if (form.invoiceType && !isExpSub.value) {
    const billId = isSubcontractSub.value ? form.inBillTypeId : form.outBillTypeId
    if (!billId || form.taxes === '') {
      ElMessage.warning(
        isSubcontractSub.value ? '请填写进项开票类型和税率' : '请填写出项开票类型和税率'
      )
      return
    }
  }
  saving.value = true
  try {
    const saveLines =
      isExpSub.value || isSubcontractSub.value ? selectedSubLines.value : lines.value
    const payload: Record<string, unknown> = {
      id: orderId,
      totalPrice: form.totalPrice,
      mark: form.mark,
      deliveryTime: form.deliveryTime,
      orderTime: form.orderTime,
      collectionTime: collectionTimes.value.filter(Boolean).join(','),
      currencyType: form.currencyType,
      payWay: form.payWay,
      invoiceType: form.invoiceType ? 1 : 0,
      taxes: form.invoiceType ? form.taxes : '',
      saleManagerId: form.saleManagerId,
      saleUserId: form.saleUserId,
      // 清空时显式传空串，避免后端把 null 当成「不改字段」
      customerId: form.customerId || '',
      customUserId: form.customUserId || '',
      children: saveLines.map((row) => ({
        // 新行显式传 null，避免后端把空串当成已有 id
        id: row.id !== '' && row.id != null ? row.id : null,
        goodsId: row.goodsId,
        goodsName: row.goodsName,
        goodsBrandId: row.goodsBrandId,
        goodsBrandName: row.goodsBrandName,
        goodsNums: row.goodsNums,
        goodsPrice: row.goodsPrice,
        goodsSpec: row.goodsSpec,
        referencePrice: row.referencePrice,
        costPrice: row.costPrice,
        projectId: row.projectId,
        projectName: row.projectName,
        classId: row.classId,
        className: row.className,
        testUserId: row.testUserId,
        lineId: row.lineId,
        expectFinishTime: row.expectFinishTime,
      })),
      deletedChildIds: [...removedLineIds.value],
    }
    if (isMainOrder.value) {
      payload.classId = form.classId
      payload.supplierId = form.supplierId
      payload.outBillTypeId = form.invoiceType ? form.outBillTypeId : ''
      payload.userScaleInfo = form.userScaleInfo
      payload.salecbUserScaleInfo = isSubcontractMain.value ? '' : form.salecbUserScaleInfo
      payload.reversoContext = form.reversoOn ? 1 : 2
      payload.shipAddress = form.reversoOn ? form.sendAddress : ''
      payload.shipUser = form.reversoOn ? form.addresseeName : ''
      payload.shipPhone = form.reversoOn ? form.addresseeMobile : ''
    } else if (isSubcontractSub.value) {
      payload.stockCompanyId = form.stockCompanyId
      payload.inBillTypeId = form.invoiceType ? form.inBillTypeId : ''
    } else if (isExpSub.value) {
      payload.supplierId = form.supplierId
      payload.warehouseUser = form.warehouseUserId
      payload.stockUser = form.warehouseUserId
    }
    const res = await updateExpOrderBasic(payload)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success('保存成功')
    removedLineIds.value = []
    await closeEditAndRefreshDetail()
  } finally {
    saving.value = false
  }
}

async function onUploadOrderFile(options: { file: File }) {
  if (!orderId) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('orderdata', options.file)
    fd.append('id', orderId)
    fd.append('type', '3')
    const res = await uploadExpOrderFile(fd)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '上传成功'))
    await load()
  } finally {
    uploading.value = false
  }
}

async function removeOrderFile(idx: number) {
  const f = orderFiles.value[idx]
  if (!f) return
  const aid = f.id
  if (aid != null && String(aid) !== '') {
    const res = await deleteExpOrderFile(aid as string | number)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '删除失败'))
      return
    }
  }
  orderFiles.value.splice(idx, 1)
  ElMessage.success('已删除')
}

/** keep-alive 停用标记：再次进入时必须重新拉详情，否则新增行 id 为空会导致删除不落库 */
const editActive = ref(true)
onActivated(async () => {
  const fromCache = !editActive.value
  editActive.value = true
  if (fromCache && orderId) {
    await loadOptions()
    await load()
  }
})
onDeactivated(() => {
  editActive.value = false
})

onMounted(async () => {
  await loadOptions()
  await load()
})
</script>

<style scoped>
.edit-page {
  padding: 8px 4px 24px;
}
.page-head {
  margin-bottom: 16px;
}
.back-link {
  border: 0;
  background: transparent;
  color: #409eff;
  cursor: pointer;
  padding: 0;
  margin-bottom: 8px;
}
.page-head h2 {
  margin: 0 0 4px;
  font-size: 20px;
}
.sub {
  margin: 0;
  color: #909399;
  font-size: 13px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.form-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px 20px 8px;
  max-width: 1200px;
}
.inline-ops {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.share-summary {
  color: #606266;
  font-size: 13px;
}
.share-hint {
  color: #c0c4cc;
  font-size: 12px;
}
.file-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.file-tag {
  max-width: 220px;
}
.lines-block {
  margin: 8px 0 20px;
}
.lines-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.lines-head h3 {
  margin: 0;
  font-size: 16px;
}
.dlg-filter {
  margin-bottom: 12px;
}
.sum-row {
  display: flex;
  gap: 24px;
  margin-top: 10px;
  color: #606266;
  font-size: 13px;
}
.save-bar {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 8px 0 16px;
}
.share-block {
  margin-bottom: 8px;
}
.share-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.share-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
</style>
