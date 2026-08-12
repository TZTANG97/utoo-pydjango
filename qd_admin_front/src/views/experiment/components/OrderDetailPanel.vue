<template>
  <div v-loading="loading" class="detail-panel">
    <template v-if="detail">
      <header class="hero">
        <div class="hero-main">
          <button type="button" class="back-link" @click="emit('back')">← 返回列表</button>
          <div class="hero-title-row">
            <h2 class="hero-title">{{ titleText }}</h2>
            <el-tag :type="statusTagType" effect="dark" round>{{ detail.orderStatusLabel }}</el-tag>
            <el-tag v-if="isChildKind && !isGrabMode" type="info" effect="plain" round>{{
              detail.confirmLabel
            }}</el-tag>
          </div>
          <p class="hero-sub">
            <span class="mono">{{ detail.orderId }}</span>
            <span class="dot">·</span>
            {{ orderTypeLabel }}
            <template v-if="detail.parentOrderId">
              <span class="dot">·</span>
              来源
              <el-button
                v-if="detail.parentPkId"
                link
                type="primary"
                @click="
                  goDetail(
                    Number(detail.parentPkId),
                    orderType === '9' ? '8' : '6',
                    detail.parentOrderId
                  )
                "
              >
                {{ detail.parentOrderId }}
              </el-button>
              <span v-else>{{ detail.parentOrderId }}</span>
            </template>
          </p>
        </div>
        <div class="hero-meta">
          <div v-if="!isGrabMode && canViewFinance" class="meta-item">
            <span class="meta-label">总价</span>
            <strong>{{ detail.totalPrice ?? '-' }}</strong>
            <small>{{ detail.currencyLabel }}</small>
          </div>
          <div v-if="!isGrabMode && !isChildKind" class="meta-item">
            <span class="meta-label">已开票 / 已收款</span>
            <strong>{{ detail.invoiceAmount ?? 0 }} / {{ detail.receiveAmount ?? 0 }}</strong>
          </div>
        </div>
      </header>

      <!-- 抢单详情：仅查看 + 子单抢单，不展示顶部操作按钮 -->
      <section v-if="!isGrabMode" class="action-bar">
        <el-button
          v-if="detail.canCancel"
          class="btn-warn"
          :loading="acting"
          @click="onCancel"
        >
          取消订单
        </el-button>
        <el-button v-if="detail.canEdit" plain @click="onEditOrder">编辑订单</el-button>
        <el-button
          v-if="detail.canWithdrawAudit"
          plain
          :loading="acting"
          @click="onWithdrawAudit"
        >
          取消审核申请
        </el-button>
        <el-button
          v-if="detail.canSubmitAudit"
          type="warning"
          :loading="acting"
          @click="onSubmitAudit"
        >
          提交审核
        </el-button>
        <!-- Java 主单：创建子单在审核通过/驳回之前 -->
        <el-button
          v-if="detail.canCreateChild"
          class="btn-accent"
          @click="onCreateChild"
        >
          {{ orderType === '8' ? '创建实验分包子订单' : '创建实验子订单' }}
        </el-button>
        <el-button
          v-if="detail.canAudit"
          type="success"
          :loading="acting"
          @click="doAudit(true)"
        >
          审核通过
        </el-button>
        <el-button
          v-if="detail.canAudit"
          type="danger"
          :loading="acting"
          @click="doAudit(false)"
        >
          驳回
        </el-button>
        <!-- Java 子订单：保存在样品流转按钮之前 -->
        <el-button v-if="detail.canSaveFinish" type="primary" :loading="acting" @click="onSaveFinish">
          保存
        </el-button>
        <el-button
          v-if="detail.canConfirmOrdered"
          type="warning"
          :loading="acting"
          @click="onConfirmOrdered"
        >
          确认已下单
        </el-button>
        <el-button
          v-if="detail.canAskPay"
          type="warning"
          :loading="acting"
          @click="onSubPay('1')"
        >
          申请付款
        </el-button>
        <el-button
          v-if="detail.canAuditPay"
          type="success"
          :loading="acting"
          @click="onSubPay('2')"
        >
          付款审核通过
        </el-button>
        <el-button
          v-if="detail.canAuditPay"
          type="danger"
          :loading="acting"
          @click="onSubPay('3')"
        >
          付款申请驳回
        </el-button>
        <el-button
          v-if="detail.canReAskPay"
          type="warning"
          :loading="acting"
          @click="onSubPay('1')"
        >
          重新发起付款申请
        </el-button>
        <el-button
          v-if="detail.canUploadPay"
          type="warning"
          :loading="acting"
          @click="subPayBillVisible = true"
        >
          上传付款信息
        </el-button>
        <el-button
          v-if="detail.canUploadInvoice"
          type="warning"
          :loading="acting"
          @click="subInvoiceVisible = true"
        >
          上传发票信息
        </el-button>
        <!-- Java 主单：开票 → 收款 → 确认付款 → 沟通确认 → 分成 → 结清 → 关联 -->
        <el-button
          v-if="detail.canInvoice"
          type="warning"
          :loading="acting"
          @click="invoiceVisible = true"
        >
          开票
        </el-button>
        <el-button
          v-if="detail.canReceiveBill"
          type="warning"
          :loading="acting"
          @click="receiveVisible = true"
        >
          收款
        </el-button>
        <el-button
          v-if="detail.canConfirmPay"
          type="success"
          :loading="acting"
          @click="onConfirmPay"
        >
          确认付款
        </el-button>
        <el-button
          v-if="detail.canConfirmCustomer"
          type="primary"
          :loading="acting"
          @click="onConfirmCustomer"
        >
          已和客户沟通确认
        </el-button>
        <el-button
          v-if="detail.canShareRatio"
          class="btn-accent"
          @click="openShareDialog"
        >
          调整分成比例
        </el-button>
        <el-button
          v-if="detail.canCostSettle"
          class="btn-accent"
          :loading="acting"
          @click="onCostSettle"
        >
          所有成本已结清
        </el-button>
        <el-button
          v-if="detail.canAddRelated"
          class="btn-accent"
          @click="relatedVisible = true"
        >
          增加关联订单
        </el-button>
        <el-button v-if="detail.canMoreInfo" @click="onMoreInfo">更多信息</el-button>
        <el-button
          v-if="detail.canGenerateAppointment"
          class="btn-accent"
          :loading="acting"
          @click="onGenerateAppointment"
        >
          生成预约单
        </el-button>
        <!-- type=9/10 样品流转 -->
        <el-button
          v-if="detail.ypdhShow"
          type="primary"
          :loading="acting"
          @click="openSampleAction('arrive')"
        >
          样品到货
        </el-button>
        <el-button
          v-if="detail.videoShow"
          plain
          :loading="acting"
          @click="openSampleAction('video')"
        >
          预约云视频
        </el-button>
        <el-button
          v-if="detail.yplyShow"
          type="primary"
          :loading="acting"
          @click="openSampleAction('pick')"
        >
          样品领用
        </el-button>
        <el-button
          v-if="detail.kscsShow"
          type="success"
          :loading="acting"
          @click="openSampleAction('testStart')"
        >
          开始测试
        </el-button>
        <el-button
          v-if="detail.cswcShow"
          type="success"
          :loading="acting"
          @click="openSampleAction('testEnd')"
        >
          测试完成
        </el-button>
        <el-button
          v-if="detail.ypghShow"
          type="primary"
          :loading="acting"
          @click="openSampleAction('return')"
        >
          样品归还
        </el-button>
        <el-button
          v-if="detail.ypjhShow"
          type="warning"
          :loading="acting"
          @click="openSampleAction('ship')"
        >
          样品寄回
        </el-button>
        <el-button
          v-if="detail.yplcShow"
          plain
          :loading="acting"
          @click="openSampleAction('retain')"
        >
          样品留存
        </el-button>
        <el-button
          v-if="detail.ypfcShow"
          plain
          :loading="acting"
          @click="openSampleAction('retest')"
        >
          样品复测
        </el-button>
        <el-button
          v-if="detail.qrwcShow || detail.canConfirmDone"
          type="success"
          :loading="acting"
          @click="openSampleAction('confirmDone')"
        >
          确认完成
        </el-button>
      </section>

      <section class="card">
        <h3 class="card-title">基本信息</h3>
        <!-- 实验分包子订单：对齐 Java experimentsub/purchaseorder/purchase_order_detail -->
        <el-descriptions
          v-if="orderType === '9'"
          :column="3"
          border
          class="soft-desc"
        >
          <el-descriptions-item label="订单状态">
            {{ detail.orderStatusLabel || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="订单编号">
            <span class="mono">{{ detail.orderId || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="来源单号">
            <el-button
              v-if="detail.parentPkId"
              link
              type="primary"
              @click="
                goDetail(Number(detail.parentPkId), '8', detail.parentOrderId)
              "
            >
              {{ detail.parentOrderId || '-' }}
            </el-button>
            <span v-else>{{ detail.parentOrderId || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="销售主管">{{ detail.saleManager || '-' }}</el-descriptions-item>
          <el-descriptions-item label="制单人员">{{ detail.addUser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="实验室测试主管">
            {{ detail.testManager || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="实验分包公司名称">
            {{ detail.stockCompanyName || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="canViewFinance" label="实验分包总价">
            {{ detail.totalPrice ?? '-' }}
            <template v-if="detail.currencyLabel === '人民币'"> 元</template>
          </el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ detail.orderTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预计完成时间">
            {{ detail.deliveryTime || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="canViewFinance" label="订单币种">
            {{ detail.currencyLabel || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="canViewFinance" label="付款方式">
            {{ detail.payWayName || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="canViewFinance" label="付款状态">
            {{ detail.payStatusLabel || '-' }}
          </el-descriptions-item>
          <template v-if="canViewFinance && expectPayRows.length">
            <template v-for="(ep, idx) in expectPayRows" :key="'ep-' + idx">
              <el-descriptions-item label="预计付款时间">{{ ep.time || '-' }}</el-descriptions-item>
              <el-descriptions-item label="预计付款金额" :span="2">
                {{ ep.price || '-' }}
              </el-descriptions-item>
              <el-descriptions-item v-if="ep.actualReceiveTime" label="实际付款时间">
                {{ ep.actualReceiveTime }}
              </el-descriptions-item>
              <el-descriptions-item
                v-if="ep.actualReceiveAmount != null && ep.actualReceiveAmount !== ''"
                label="实际付款金额"
                :span="2"
              >
                {{ ep.actualReceiveAmount }}
              </el-descriptions-item>
            </template>
          </template>
          <template v-if="canViewFinance && receiveBillRows.length && !expectPayRows.length">
            <template v-for="(b, idx) in receiveBillRows" :key="'rb9-' + idx">
              <el-descriptions-item label="实际付款时间">{{ b.billDate || '-' }}</el-descriptions-item>
              <el-descriptions-item label="实际付款金额" :span="2">
                {{ b.money ?? '-' }}
              </el-descriptions-item>
            </template>
          </template>
          <el-descriptions-item v-if="canViewFinance" label="是否开票">
            {{ detail.invoiceLabel || '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="canViewFinance && Number(detail.invoiceType) === 1"
            label="进项开票类型"
          >
            {{ inBillTypeLabel }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="canViewFinance && Number(detail.invoiceType) === 1"
            label="税率"
          >
            {{ detail.taxes || '-' }}
          </el-descriptions-item>
          <template v-if="canViewFinance && invoiceBillRows.length">
            <template v-for="(b, idx) in invoiceBillRows" :key="'ib9-' + idx">
              <el-descriptions-item :label="'开票时间' + (invoiceBillRows.length > 1 ? idx + 1 : '')">
                {{ b.billDate || '-' }}
              </el-descriptions-item>
              <el-descriptions-item
                :label="'开票金额' + (invoiceBillRows.length > 1 ? idx + 1 : '')"
                :span="2"
              >
                {{ b.money ?? '-' }}
              </el-descriptions-item>
            </template>
          </template>
          <el-descriptions-item label="联系电话">{{ detail.contactPhone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="样品是否回收">
            {{ detail.reversoLabel || '-' }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="detail.showShipAddress"
            label="样品寄回地址"
            :span="2"
          >
            {{ detail.shipAddress || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="是否云视频">{{ detail.isVideoLabel || '-' }}</el-descriptions-item>
        </el-descriptions>
        <!-- 抢单详情：对齐 Java qdorderdetail，仅保留必要字段 -->
        <el-descriptions
          v-else-if="orderType === '10' && isGrabMode"
          :column="3"
          border
          class="soft-desc"
        >
          <el-descriptions-item label="订单状态">{{ detail.orderStatusLabel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="订单编号">
            <span class="mono">{{ detail.orderId || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="来源单号">
            <el-button
              v-if="detail.parentPkId"
              link
              type="primary"
              @click="goDetail(Number(detail.parentPkId), '6', detail.parentOrderId)"
            >
              {{ detail.parentOrderId || '-' }}
            </el-button>
            <span v-else>{{ detail.parentOrderId || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="订单类型">
            {{ detail.testClassName || orderTypeLabel }}
          </el-descriptions-item>
          <el-descriptions-item label="客户名称">
            {{ detail.customerName || detail.companyName || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="所属公司">{{ detail.supplierName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="实验室主管">{{ detail.saleManager || '-' }}</el-descriptions-item>
          <el-descriptions-item label="销售人员">{{ detail.saleUser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="制单人">{{ detail.addUser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ detail.orderTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预计收货时间">{{ detail.deliveryTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="客户账号">
            {{ detail.customMobile || detail.mobile || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="联系电话">
            {{ detail.contactPhone || detail.mobile || detail.shipPhone || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="样品是否回收">{{ detail.reversoLabel || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-descriptions v-else-if="orderType === '10'" :column="3" border class="soft-desc">
          <el-descriptions-item label="订单状态">{{ detail.orderStatusLabel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="订单编号">
            <span class="mono">{{ detail.orderId || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="来源单号">
            <el-button
              v-if="detail.parentPkId"
              link
              type="primary"
              @click="goDetail(Number(detail.parentPkId), '6', detail.parentOrderId)"
            >
              {{ detail.parentOrderId || '-' }}
            </el-button>
            <span v-else>{{ detail.parentOrderId || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="订单类型">
            {{ detail.testClassName || orderTypeLabel }}
          </el-descriptions-item>
          <el-descriptions-item label="客户名称">
            {{ detail.customerName || detail.companyName || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="所属公司">{{ detail.supplierName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="实验室主管">{{ detail.saleManager || '-' }}</el-descriptions-item>
          <el-descriptions-item label="销售人员">{{ detail.saleUser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="制单员">{{ detail.addUser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ detail.orderTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预计收货时间">{{ detail.deliveryTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="客户账号">{{ detail.customMobile || '-' }}</el-descriptions-item>
          <el-descriptions-item label="仓库管理员">{{ detail.warehouseUser || detail.stockUser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">
            {{ detail.contactPhone || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="样品是否回收">{{ detail.reversoLabel || '-' }}</el-descriptions-item>
          <el-descriptions-item
            v-if="detail.showShipAddress"
            label="样品寄回地址"
            :span="2"
          >
            {{ detail.shipAddress || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="是否云视频">{{ detail.isVideoLabel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="是否确认">{{ detail.confirmLabel || '-' }}</el-descriptions-item>
        </el-descriptions>
        <el-descriptions v-else :column="3" border class="soft-desc">
          <el-descriptions-item label="订单编号">
            <span class="mono">{{ detail.orderId || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="订单状态">{{ detail.orderStatusLabel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="订单类型">
            {{ detail.testClassName || orderTypeLabel }}
          </el-descriptions-item>
          <el-descriptions-item label="制单人员">{{ detail.addUser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="所属公司">{{ detail.supplierName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="录入订单时间">{{ detail.addTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ detail.orderTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="总价">
            {{ detail.totalPrice ?? '-' }}
            <template v-if="detail.currencyLabel"> {{ detail.currencyLabel }}</template>
          </el-descriptions-item>
          <el-descriptions-item label="销售主管">{{ detail.saleManager || '-' }}</el-descriptions-item>
          <el-descriptions-item label="销售人员">{{ detail.saleUser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="客户名称">
            {{ detail.customerName || detail.companyName || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="客户账号">{{ detail.customMobile || detail.mobile || '-' }}</el-descriptions-item>
          <el-descriptions-item label="订单币种">{{ detail.currencyLabel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="预计收货时间">{{ detail.deliveryTime || '-' }}</el-descriptions-item>
          <el-descriptions-item label="付款方式">{{ detail.payWayName || '-' }}</el-descriptions-item>
          <template v-if="expectPayRows.length">
            <template v-for="(ep, idx) in expectPayRows" :key="'ep6-' + idx">
              <el-descriptions-item label="预计收款时间">{{ ep.time || '-' }}</el-descriptions-item>
              <el-descriptions-item label="预计收款金额" :span="2">{{ ep.price || '-' }}</el-descriptions-item>
              <el-descriptions-item v-if="ep.actualOnlineReceiveTime" label="实际线上收款时间">
                {{ ep.actualOnlineReceiveTime }}
              </el-descriptions-item>
              <el-descriptions-item
                v-if="ep.actualOnlineReceiveAmount != null && ep.actualOnlineReceiveAmount !== ''"
                label="实际线上收款金额"
                :span="2"
              >
                {{ ep.actualOnlineReceiveAmount }}
              </el-descriptions-item>
              <el-descriptions-item v-if="ep.actualReceiveTime" label="实际收款时间">
                {{ ep.actualReceiveTime }}
              </el-descriptions-item>
              <el-descriptions-item v-if="ep.actualReceiveAmount != null" label="实际收款金额" :span="2">
                {{ ep.actualReceiveAmount }}
              </el-descriptions-item>
              <el-descriptions-item v-if="ep.actualInvoiceTime" label="开票时间">
                {{ ep.actualInvoiceTime }}
              </el-descriptions-item>
              <el-descriptions-item v-if="ep.actualInvoiceAmount != null" label="开票金额" :span="2">
                {{ ep.actualInvoiceAmount }}
              </el-descriptions-item>
            </template>
          </template>
          <template v-if="onlineReceiveBillRows.length && !expectPayRows.length">
            <template v-for="(b, idx) in onlineReceiveBillRows" :key="'orb-' + idx">
              <el-descriptions-item
                :label="'实际线上收款时间' + (onlineReceiveBillRows.length > 1 ? idx + 1 : '')"
              >
                {{ b.billDate || '-' }}
              </el-descriptions-item>
              <el-descriptions-item
                :label="'实际线上收款金额' + (onlineReceiveBillRows.length > 1 ? idx + 1 : '')"
                :span="2"
              >
                {{ b.money ?? '-' }}
              </el-descriptions-item>
            </template>
          </template>
          <template v-if="receiveBillRows.length && !expectPayRows.length">
            <template v-for="(b, idx) in receiveBillRows" :key="'rb-' + idx">
              <el-descriptions-item :label="'实际收款时间' + (receiveBillRows.length > 1 ? idx + 1 : '')">
                {{ b.billDate || '-' }}
              </el-descriptions-item>
              <el-descriptions-item :label="'实际收款金额' + (receiveBillRows.length > 1 ? idx + 1 : '')" :span="2">
                {{ b.money ?? '-' }}
              </el-descriptions-item>
            </template>
          </template>
          <template v-if="invoiceBillRows.length && !expectPayRows.some((e) => e.actualInvoiceTime)">
            <template v-for="(b, idx) in invoiceBillRows" :key="'ib-' + idx">
              <el-descriptions-item :label="'开票时间' + (invoiceBillRows.length > 1 ? idx + 1 : '')">
                {{ b.billDate || '-' }}
              </el-descriptions-item>
              <el-descriptions-item :label="'开票金额' + (invoiceBillRows.length > 1 ? idx + 1 : '')" :span="2">
                {{ b.money ?? '-' }}
              </el-descriptions-item>
            </template>
          </template>
          <el-descriptions-item v-if="!isChildKind" label="实际收款合计">
            {{ detail.receiveAmount ?? 0 }}
          </el-descriptions-item>
          <el-descriptions-item v-if="!isChildKind" label="是否开票">
            {{ detail.invoiceLabel || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="!isChildKind && Number(detail.invoiceType) === 1" label="出项开票类型">
            {{ outBillTypeLabel }}
          </el-descriptions-item>
          <el-descriptions-item v-if="!isChildKind && Number(detail.invoiceType) === 1" label="税率">
            {{ detail.taxes || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="!isChildKind" label="已开票金额">
            {{ detail.invoiceAmount ?? 0 }}
          </el-descriptions-item>
          <el-descriptions-item v-if="!isChildKind" label="成本结清">
            {{ detail.costSettleLabel || '-' }}
          </el-descriptions-item>
          <el-descriptions-item v-if="!isChildKind && detail.canViewShareInfo !== false" label="分成信息" :span="3">
            <div>毛利：{{ detail.userScaleLabel || detail.userScaleInfo || '-' }}</div>
            <div v-if="detail.costScaleLabel || detail.salecbUserScaleInfo">
              成本：{{ detail.costScaleLabel || detail.salecbUserScaleInfo }}
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="样品是否回收">{{ detail.reversoLabel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="收件人">{{ detail.shipUser || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detail.shipPhone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="寄回地址" :span="3">
            {{ detail.shipAddress || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="是否云视频">{{ detail.isVideoLabel || '-' }}</el-descriptions-item>
        </el-descriptions>
        <!-- 订单资料 / 发票资料 / 订单备注；抢单详情仅保留订单备注（对齐 Java） -->
        <div v-if="showOrderDocsBlock" class="order-files-block">
          <template v-if="!isGrabMode">
            <div class="files-row">
              <span class="files-label">订单资料</span>
              <div class="files-list">
                <div v-for="f in orderFiles" :key="'of-' + String(f.id)" class="file-item">
                  <a
                    class="file-name"
                    href="#"
                    @click.prevent="onPreviewFile(f)"
                  >{{ fileLabel(f) }}</a>
                  <el-button type="success" size="small" @click="onDownloadFile(f)">下载</el-button>
                  <el-button type="danger" size="small" :loading="acting" @click="onDeleteFile(f)">
                    删除
                  </el-button>
                </div>
                <span v-if="!orderFiles.length" class="files-empty">暂无</span>
                <el-upload
                  :show-file-list="false"
                  :http-request="onUploadOrderFile"
                  accept="*/*"
                >
                  <el-button type="primary">上传文件</el-button>
                </el-upload>
              </div>
            </div>
            <div v-if="canViewFinance" class="files-row">
              <span class="files-label">发票资料</span>
              <div class="files-list">
                <div v-for="f in invoiceFiles" :key="'inv-' + String(f.id)" class="file-item">
                  <a
                    class="file-name"
                    href="#"
                    @click.prevent="onPreviewFile(f)"
                  >{{ fileLabel(f) }}</a>
                  <el-button type="success" size="small" @click="onDownloadFile(f)">下载</el-button>
                  <el-button type="danger" size="small" :loading="acting" @click="onDeleteFile(f)">
                    删除
                  </el-button>
                </div>
                <span v-if="!invoiceFiles.length" class="files-empty">暂无</span>
                <el-upload
                  :show-file-list="false"
                  :http-request="onUploadInvoiceFile"
                  accept="*/*"
                >
                  <el-button type="primary">上传文件</el-button>
                </el-upload>
              </div>
            </div>
          </template>
          <div class="remark-row">
            <span class="files-label">订单备注</span>
            <el-input
              v-model="orderMsg"
              type="textarea"
              :rows="3"
              placeholder="请输入备注"
              @blur="onSaveOrderMsg"
            />
          </div>
        </div>
      </section>

      <section class="card">
        <div class="card-head">
          <h3 class="card-title">产品 / 测试明细</h3>
          <span class="card-hint">共 {{ editChildren.length }} 行</span>
        </div>
        <!-- 抢单：对齐 Java 产品列（不含子单号/单价/设备/确认等） -->
        <el-table
          v-if="isGrabMode"
          :data="editChildren"
          border
          stripe
          class="detail-table"
        >
          <el-table-column prop="goodsName" label="产品名称" min-width="140" show-overflow-tooltip />
          <el-table-column prop="goodsSpec" label="产品型号" min-width="100" show-overflow-tooltip />
          <el-table-column prop="goodsBrand" label="产品品牌" min-width="100" show-overflow-tooltip />
          <el-table-column prop="goodsCount" label="数量" width="70" align="center" />
          <el-table-column
            prop="projectName"
            label="实验测试项目"
            min-width="120"
            show-overflow-tooltip
          />
          <el-table-column
            prop="className"
            label="实验测试分类"
            min-width="110"
            show-overflow-tooltip
          />
          <el-table-column prop="testUserName" label="测试人员" width="100" />
          <el-table-column prop="platformName" label="实验平台" min-width="100" show-overflow-tooltip />
          <el-table-column prop="orderStatusLabel" label="状态" width="100" />
          <el-table-column label="抢单" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.canGrab"
                link
                type="success"
                :loading="acting"
                @click="onGrabChild(row)"
              >
                抢单
              </el-button>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
        <el-table v-else :data="editChildren" border stripe class="detail-table">
          <el-table-column type="index" width="50" label="#" align="center" />
          <el-table-column prop="childOrderId" label="子单号" min-width="130" show-overflow-tooltip />
          <el-table-column prop="goodsName" label="产品名称" min-width="120" show-overflow-tooltip />
          <el-table-column prop="goodsSpec" label="型号" min-width="100" show-overflow-tooltip />
          <el-table-column prop="goodsBrand" label="品牌" min-width="90" show-overflow-tooltip />
          <el-table-column prop="goodsCount" label="数量" width="70" align="center" />
          <el-table-column prop="projectName" label="测试项目" min-width="120" show-overflow-tooltip />
          <el-table-column prop="className" label="实验测试分类" min-width="110" show-overflow-tooltip />
          <el-table-column
            v-if="!isChildKind"
            prop="price"
            label="实验测试金额"
            width="110"
            align="right"
          />
          <el-table-column
            v-if="!isChildKind"
            prop="referencePrice"
            label="标准测试金额"
            width="110"
            align="right"
          />
          <el-table-column
            v-if="!isChildKind"
            label="总价"
            width="90"
            align="right"
          >
            <template #default="{ row }">
              {{
                (
                  Number(row.price ?? 0) * Number(row.goodsCount ?? 1)
                ).toFixed(2)
              }}
            </template>
          </el-table-column>
          <!-- type=10 实验子订单产品列 -->
          <el-table-column v-if="orderType === '10'" prop="price" label="单价" width="90" align="right" />
          <el-table-column
            v-if="orderType === '10'"
            prop="referencePrice"
            label="测试金额"
            width="100"
            align="right"
          >
            <template #default="{ row }">
              <el-input
                v-if="detail.canEditReferencePrice"
                v-model="row.referencePrice"
                size="small"
                @blur="onSaveReferencePrice(row)"
              />
              <span v-else>{{ row.referencePrice ?? '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="isChildKind"
            prop="testUserName"
            :label="orderType === '9' ? '测试人员' : '测试员'"
            width="100"
          />
          <el-table-column v-if="orderType === '10'" prop="deviceName" label="设备名称" min-width="100" show-overflow-tooltip />
          <el-table-column v-if="orderType === '10'" label="实验平台" min-width="100" show-overflow-tooltip>
            <template #default="{ row }">
              {{
                row.platformName && String(row.platformName) !== '-1'
                  ? row.platformName
                  : '-'
              }}
            </template>
          </el-table-column>
          <el-table-column v-if="orderType === '10'" prop="confirmLabel" label="是否确认" width="90" align="center" />
          <el-table-column
            v-if="orderType === '10'"
            prop="confirmMark"
            label="确认描述"
            min-width="100"
            show-overflow-tooltip
          />
          <el-table-column v-if="orderType === '10'" label="确认文件" min-width="140">
            <template #default="{ row }">
              <template v-if="Array.isArray(row.accessoryList) && row.accessoryList.length">
                <div v-for="f in row.accessoryList" :key="'cf-' + String(f.id)" class="inline-file">
                  <a href="#" @click.prevent="onPreviewFile(f)">{{ fileLabel(f) }}</a>
                </div>
              </template>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <!-- type=9 分包子订单：对齐 Java purchase_order_detail 子表 -->
          <el-table-column
            v-if="orderType === '9' && canViewFinance"
            prop="costPrice"
            label="分包单价"
            width="90"
            align="right"
          />
          <el-table-column
            v-if="isChildKind"
            prop="orderStatusLabel"
            label="状态"
            width="100"
          />
          <el-table-column
            v-if="orderType === '9' || orderType === '10'"
            prop="jtTime"
            label="具体完成时间"
            width="160"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="orderType === '9'"
            label="预估完成时间"
            width="120"
          >
            <template #default="{ row }">
              {{ row.estimateFinish ?? '0' }}{{ row.timeTypeLabel ? ` ${row.timeTypeLabel}` : '' }}
            </template>
          </el-table-column>
          <el-table-column v-if="orderType === '10'" prop="expectFinishTime" label="预计完成时间" width="160" show-overflow-tooltip />
          <el-table-column v-if="orderType === '10'" label="预估完成时间" width="120">
            <template #default="{ row }">
              {{ row.estimateFinish ?? '0' }}{{ row.timeTypeLabel ? ` ${row.timeTypeLabel}` : '' }}
            </template>
          </el-table-column>
          <el-table-column
            v-if="orderType === '9' || orderType === '10'"
            label="实际完成时间"
            width="140"
          >
            <template #default="{ row }">
              <span>{{ row.sjsj ?? row.actualFinish ?? '-' }}</span>
              <el-select
                v-if="detail.canSaveFinish"
                :model-value="String(row.timeType || '')"
                size="small"
                style="width: 72px; margin-left: 4px"
                @change="(v) => onSaveTimeType(row, String(v))"
              >
                <el-option label="分钟" value="3" />
                <el-option label="小时" value="1" />
                <el-option label="天" value="2" />
              </el-select>
              <span v-else-if="row.timeTypeLabel"> {{ row.timeTypeLabel }}</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="orderType === '9' || orderType === '10'"
            prop="storePosition"
            label="仓库位置"
            min-width="120"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="orderType === '9' || orderType === '10'"
            label="样品管理单"
            min-width="130"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <el-button
                v-if="row.outNum"
                link
                type="primary"
                @click="onOpenSampleOrder(row)"
              >
                {{ row.outNum }}
              </el-button>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="orderType === '9' || orderType === '10'"
            prop="retestOrderNo"
            label="关联复测编号"
            min-width="120"
            show-overflow-tooltip
          />
          <el-table-column v-if="orderType === '10'" prop="settingTime" label="预约云视频时间" width="160" show-overflow-tooltip />
          <el-table-column v-if="orderType === '10'" prop="meetingNum" label="腾讯会议号" width="110" show-overflow-tooltip />
          <el-table-column
            v-if="orderType === '9' || orderType === '10'"
            label="测试数据"
            min-width="160"
          >
            <template #default="{ row }">
              <template v-if="Array.isArray(row.testFiles) && row.testFiles.length">
                <div v-for="f in row.testFiles" :key="'tf-' + String(f.id)" class="inline-file">
                  <a href="#" @click.prevent="onPreviewFile(f)">{{ fileLabel(f) }}</a>
                </div>
              </template>
              <el-upload
                :show-file-list="false"
                :http-request="(opt) => onUploadChildTestFile(opt, row)"
                accept="*/*"
              >
                <el-button link type="primary" size="small">上传</el-button>
              </el-upload>
            </template>
          </el-table-column>
          <el-table-column
            v-if="orderType === '9' || orderType === '10'"
            label="样品信息"
            width="90"
            align="center"
          >
            <template #default="{ row }">
              <el-button
                v-if="row.sampleShow"
                link
                type="warning"
                @click="onViewSampleInfo(row)"
              >
                查看
              </el-button>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column v-if="orderType === '10'" label="保存预计完成" width="170">
            <template #default="{ row }">
              <el-date-picker
                v-if="detail.canSaveFinish"
                v-model="row.finishTime"
                type="datetime"
                value-format="YYYY-MM-DD HH:mm:ss"
                placeholder="预计完成时间"
                style="width: 158px"
              />
              <span v-else>{{ row.finishTime || row.expectFinishTime || '-' }}</span>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section v-if="!isGrabMode && relatedOrders.length" class="card">
        <h3 class="card-title">关联订单</h3>
        <el-table :data="relatedOrders" border stripe class="detail-table">
          <el-table-column type="index" width="50" label="#" align="center" />
          <el-table-column prop="orderId" label="订单编号" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="goDetail(row.id, row.orderType, row.orderId)"
              >
                {{ row.orderId }}
              </el-button>
            </template>
          </el-table-column>
          <el-table-column prop="companyName" label="客户" min-width="120" show-overflow-tooltip />
          <el-table-column prop="supplierName" label="供应商" min-width="120" show-overflow-tooltip />
          <el-table-column prop="saleManager" label="销售主管" width="100" />
          <el-table-column prop="saleUser" label="销售人员" width="100" />
          <el-table-column prop="totalPrice" label="金额" width="90" align="right" />
          <el-table-column prop="addTime" label="录入订单时间" width="170" />
          <el-table-column prop="invoiceLabel" label="是否开票" width="90" align="center" />
          <el-table-column prop="orderStatusLabel" label="状态" width="100" />
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="danger" :loading="acting" @click="onDelRelated(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section v-if="!isGrabMode && linkedOrders.length" class="card">
        <h3 class="card-title">{{ linkedTitle }}</h3>
        <el-table :data="linkedOrders" border stripe class="detail-table">
          <el-table-column
            prop="orderId"
            :label="orderType === '8' ? '分包子订单编号' : '实验子订单编号'"
            min-width="180"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="goDetail(row.id, row.orderType, row.orderId)"
              >
                {{ row.orderId }}
              </el-button>
            </template>
          </el-table-column>
          <el-table-column prop="addTime" label="创建时间" width="170" />
          <el-table-column prop="supplierName" label="所属公司" min-width="140" show-overflow-tooltip />
          <el-table-column prop="orderStatusLabel" label="状态" width="120" />
        </el-table>
      </section>

      <section v-if="!isGrabMode && consultList.length" class="card">
        <h3 class="card-title">业务咨询</h3>
        <el-table :data="consultList" border stripe class="detail-table">
          <el-table-column
            prop="appointmentNo"
            label="预约单号"
            min-width="200"
            show-overflow-tooltip
          />
          <el-table-column prop="consultTime" label="咨询时间" width="170" />
          <el-table-column prop="className" label="测试分类" min-width="140" show-overflow-tooltip />
          <el-table-column prop="userName" label="姓名" width="120" show-overflow-tooltip />
          <el-table-column prop="mobile" label="手机号" width="130" />
          <el-table-column prop="companyName" label="公司名" min-width="140" show-overflow-tooltip />
          <el-table-column prop="statusLabel" label="状态" width="110" />
        </el-table>
      </section>

      <section v-if="!isGrabMode && detail.canViewLogs !== false" class="card">
        <h3 class="card-title">操作日志</h3>
        <el-table :data="logs" border stripe class="detail-table" max-height="360">
          <el-table-column prop="addTime" label="时间" width="170" />
          <el-table-column label="操作人" width="120" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.logUser || row.logUserName || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="logInfo" label="内容" min-width="240" show-overflow-tooltip />
        </el-table>
      </section>
    </template>
    <el-empty v-else-if="!loading" description="订单不存在或加载失败" />

    <el-dialog v-model="shareVisible" title="调整分成比例" width="720px" destroy-on-close>
      <div class="share-block">
        <div class="share-block-head">
          <strong>毛利分成</strong>
          <span class="share-hint">比例合计须为 100%</span>
          <el-button link type="primary" @click="addShareRow(profitRows)">添加一行</el-button>
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
          <el-button link type="danger" @click="profitRows.splice(idx, 1)">删除</el-button>
        </div>
      </div>
      <div v-if="orderType === '6'" class="share-block" style="margin-top: 16px">
        <div class="share-block-head">
          <strong>成本分成</strong>
          <span class="share-hint">按固定金额</span>
          <el-button link type="primary" @click="addShareRow(costRows)">添加一行</el-button>
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
          <el-input v-model="row.value" placeholder="金额" style="width: 140px" />
          <el-button link type="danger" @click="costRows.splice(idx, 1)">删除</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="shareVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="onShareSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="relatedVisible" title="增加关联订单" width="460px">
      <el-form label-width="110px">
        <el-form-item label="选择订单类型" required>
          <el-select v-model="relatedType" placeholder="请选择" style="width: 100%">
            <el-option label="实验订单" value="5" />
            <el-option label="实验分包订单" value="6" />
          </el-select>
        </el-form-item>
        <el-form-item label="订单号" required>
          <el-input v-model="relatedOrderNo" placeholder="请输入订单号" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="relatedVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="onAddRelated">添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="receiveVisible" title="收款" width="420px">
      <el-form label-width="100px">
        <el-form-item label="收款金额" required>
          <el-input v-model="receiveMoney" placeholder="请输入收款金额" clearable />
        </el-form-item>
        <el-form-item label="收款日期">
          <el-date-picker
            v-model="receiveDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="默认今天"
            clearable
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="receiveRemark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
        <p class="receive-hint">
          成本已结清时，保存后将按订单分成配置自动分钱到相关账户。
        </p>
      </el-form>
      <template #footer>
        <el-button @click="receiveVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="onSaveReceive">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="invoiceVisible" title="开票" width="420px">
      <el-form label-width="100px">
        <el-form-item label="开票金额" required>
          <el-input v-model="invoiceMoney" placeholder="请输入开票金额" clearable />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="invoiceRemark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="invoiceVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="onSaveInvoice">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="subPayBillVisible" title="上传付款信息" width="420px">
      <el-form label-width="100px">
        <el-form-item label="付款金额" required>
          <el-input v-model="subPayMoney" placeholder="请输入付款金额" clearable />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="subPayRemark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="subPayBillVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="onUploadSubPay">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="subInvoiceVisible" title="上传发票信息" width="420px">
      <el-form label-width="100px">
        <el-form-item label="发票金额" required>
          <el-input v-model="subInvoiceMoney" placeholder="请输入发票金额" clearable />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="subInvoiceRemark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="subInvoiceVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="onUploadSubInvoice">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="sampleVisible" :title="sampleDialogTitle" width="720px">
      <el-alert
        v-if="sampleExtraHint"
        type="info"
        :closable="false"
        show-icon
        class="sample-alert"
        :title="sampleExtraHint"
      />
      <el-form v-if="sampleNeedExtra" label-width="90px" class="sample-extra">
        <el-form-item
          v-if="
            sampleAction === 'arrive' ||
            sampleAction === 'return' ||
            sampleAction === 'pick' ||
            sampleAction === 'ship' ||
            (sampleAction === 'retain' && sampleRetainMode === 'scrap')
          "
          label="仓库名称"
          :required="
            sampleAction === 'pick' ||
            (sampleAction === 'ship' && !!sampleConfirmLocation) ||
            (sampleAction === 'retain' && sampleRetainMode === 'scrap' && !!sampleConfirmLocation)
          "
        >
          <el-select
            v-model="sampleStoreId"
            filterable
            clearable
            :placeholder="
              sampleAction === 'arrive' || sampleAction === 'return'
                ? '请选择（可不填）'
                : sampleConfirmLocation
                  ? `请确认：${sampleConfirmLocation}`
                  : '请选择'
            "
            style="width: 100%"
            @change="onSampleStoreChange"
          >
            <el-option
              v-for="s in sampleStoreOptions"
              :key="String(s.value)"
              :label="String(s.label || s.sample_store_name || s.name || '')"
              :value="String(s.value || s.id || '')"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          v-if="
            sampleAction === 'arrive' ||
            sampleAction === 'return' ||
            sampleAction === 'pick' ||
            sampleAction === 'ship' ||
            (sampleAction === 'retain' && sampleRetainMode === 'scrap')
          "
          label="仓库位置"
          :required="
            sampleAction === 'pick' ||
            (sampleAction === 'ship' && !!sampleConfirmLocation) ||
            (sampleAction === 'retain' && sampleRetainMode === 'scrap' && !!sampleConfirmLocation)
          "
        >
          <el-select
            v-model="sampleStorePosId"
            filterable
            clearable
            :placeholder="
              sampleAction === 'pick' && sampleExpectedPosLabel
                ? `请确认：${sampleExpectedPosLabel}`
                : sampleAction === 'arrive' || sampleAction === 'return'
                  ? '请选择（可不填）'
                  : sampleConfirmLocation
                    ? `请确认：${sampleConfirmLocation}`
                    : '请选择'
            "
            style="width: 100%"
            :disabled="!sampleStoreId"
          >
            <el-option
              v-for="p in samplePosOptions"
              :key="String(p.value || p.id)"
              :label="String(p.label || p.blockName || p.number || p.id || '')"
              :value="String(p.value || p.id || '')"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          v-if="sampleAction === 'testStart' && orderType === '10'"
          label="实验平台"
          required
        >
          <el-input
            :model-value="sampleConfirmPlatform"
            disabled
            placeholder="请勾选一行以确认实验平台"
          />
        </el-form-item>
        <el-form-item
          v-if="
            (sampleAction === 'ship' ||
              (sampleAction === 'retain' && sampleRetainMode === 'scrap')) &&
            sampleSelected.length === 1
          "
          label="确认位置"
        >
          <el-input
            :model-value="sampleConfirmLocation || '该子行暂无仓库位置记录，请上方选择后确认'"
            disabled
          />
        </el-form-item>
        <el-form-item v-if="sampleAction === 'ship'" label="快递公司" required>
          <el-input v-model="sampleExpressName" placeholder="必填" clearable />
        </el-form-item>
        <el-form-item v-if="sampleAction === 'ship'" label="快递单号" required>
          <el-input v-model="sampleExpress" placeholder="必填" clearable />
        </el-form-item>
        <el-form-item v-if="sampleAction === 'video'" label="预约时间" required>
          <el-date-picker
            v-model="sampleVideoTime"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="请选择预约云视频时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item v-if="sampleAction === 'video'" label="会议号" required>
          <el-input v-model="sampleMeeting" placeholder="请输入云视频会议号" clearable />
        </el-form-item>
        <el-form-item v-if="sampleAction === 'retain'" label="处理方式" required>
          <el-radio-group v-model="sampleRetainMode">
            <el-radio value="retain">样品留存</el-radio>
            <el-radio value="scrap">样品报废</el-radio>
          </el-radio-group>
        </el-form-item>
        <template v-if="sampleAction === 'retain' && sampleRetainMode === 'retain'">
          <el-form-item v-if="sampleConfirmLocation" label="确认位置">
            <el-input :model-value="sampleConfirmLocation" disabled />
          </el-form-item>
          <el-form-item label="是否入库" required>
            <el-radio-group v-model="sampleIsPosition">
              <el-radio value="1">入库到留存仓库</el-radio>
              <el-radio value="0">不入库（仓库位置无）</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="sampleIsPosition === '1'" label="留存仓库" required>
            <el-select
              v-model="sampleRetainStoreId"
              filterable
              clearable
              placeholder="请选择留存仓库"
              style="width: 100%"
              @change="onRetainStoreChange"
            >
              <el-option
                v-for="s in remainStoreOptions"
                :key="String(s.value)"
                :label="String(s.label || '')"
                :value="String(s.value)"
              />
            </el-select>
          </el-form-item>
          <el-form-item v-if="sampleIsPosition === '1'" label="留存仓位" required>
            <el-select
              v-model="sampleRetainStorePosId"
              filterable
              clearable
              placeholder="请选择留存仓位"
              style="width: 100%"
              :disabled="!sampleRetainStoreId"
            >
              <el-option
                v-for="p in remainPosOptions"
                :key="String(p.value)"
                :label="String(p.label || '')"
                :value="String(p.value)"
              />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item v-if="sampleAction === 'confirmDone'" label="备注" required>
          <el-input
            v-model="sampleConfirmMark"
            type="textarea"
            :rows="2"
            placeholder="必填，请填写确认备注"
            clearable
          />
        </el-form-item>
      </el-form>
      <el-table
        ref="sampleTableRef"
        :data="sampleSelectableRows"
        border
        stripe
        max-height="360"
        @selection-change="onSampleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="childOrderId" label="子单号" min-width="120" show-overflow-tooltip />
        <el-table-column prop="goodsName" label="产品" min-width="120" show-overflow-tooltip />
        <el-table-column
          v-if="sampleAction === 'testStart' && orderType === '10'"
          prop="platformName"
          label="实验平台"
          min-width="120"
          show-overflow-tooltip
        />
        <el-table-column prop="orderStatusLabel" label="状态" width="100" />
        <el-table-column prop="confirmLabel" label="确认" width="80" />
      </el-table>
      <template #footer>
        <el-button @click="sampleVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="onSubmitSampleAction">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="moreVisible" title="更多信息" width="560px">
      <el-descriptions v-if="moreInfo" :column="1" border>
        <el-descriptions-item label="样品寄回地址">
          {{ moreInfo.shipAddress || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="收件人姓名">
          {{ moreInfo.shipUser || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="收件人电话">
          {{ moreInfo.shipPhone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="公司汇款账户">
          {{ moreInfo.companyAccount || moreInfo.bankCardNum || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="实验测试地址">
          {{ moreInfo.testAddress || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog
      v-model="appointmentVisible"
      title="生成预约单 · 选择寄送地址"
      width="560px"
      destroy-on-close
    >
      <el-radio-group v-model="appointmentAddressId" class="addr-radio-group">
        <el-radio
          v-for="a in appointmentAddressOpts"
          :key="String(a.value)"
          :value="a.value"
          class="addr-radio"
        >
          {{ a.label }}
        </el-radio>
      </el-radio-group>
      <el-empty v-if="!appointmentAddressOpts.length && !appointmentLoading" description="暂无寄送地址，请先在系统中维护" />
      <template #footer>
        <el-button @click="appointmentVisible = false">取消</el-button>
        <el-button type="primary" :loading="acting || appointmentLoading" @click="submitAppointment">
          确定生成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onDeactivated, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  detailFromByOrderType,
  detailTitleByOrderType,
  useTagsViewStore,
} from '@admin/stores/tags-view'
import type { ElTable } from 'element-plus'
import {
  addExpOrderRelated,
  delExpOrderRelated,
  addVideoExpOrder,
  auditExpOrder,
  cancelExpOrder,
  confirmDoneExpOrder,
  confirmExpOrdered,
  confirmExpOrderCustomer,
  confirmExpOrderPay,
  costSettleExpOrder,
  fetchExpOrderMoreInfo,
  generateExpOrderAppointment,
  getExpOrderDetail,
  grabExpOrder,
  retestExpOrder,
  sampleArriveExpOrder,
  samplePickExpOrder,
  sampleRetainExpOrder,
  sampleReturnExpOrder,
  sampleShipExpOrder,
  saveExpChildReferencePrice,
  saveExpOrderFinish,
  saveExpOrderInvoiceBill,
  saveExpOrderReceiveBill,
  submitExpOrderAudit,
  subPayExpOrder,
  testEndExpOrder,
  testStartExpOrder,
  updateExpChildTimeType,
  updateExpOrderShareRatio,
  uploadSubInvoiceExpOrder,
  uploadSubPayExpOrder,
  uploadExpOrderFile,
  deleteExpOrderFile,
  downloadExpOrderFile,
  previewExpOrderFile,
  updateExpOrderMsg,
  withdrawExpOrderAudit,
} from '@admin/api/experiment'
import { fetchIncomeUsers, fetchSampleOrderOptions, fetchSampleStorePositions, fetchRemainSampleStoreOptions, fetchRemainSampleStorePositions } from '@admin/api/inventory'
import { fetchTestAddressList } from '@admin/api/system'
import { ajaxErrorMessage, isAjaxOk } from '@admin/utils/request'

type SampleAction =
  | 'arrive'
  | 'video'
  | 'pick'
  | 'testStart'
  | 'testEnd'
  | 'return'
  | 'ship'
  | 'retain'
  | 'scrap'
  | 'retest'
  | 'confirmDone'

const props = defineProps<{ orderId: string | number }>()
const emit = defineEmits<{ back: []; refreshed: [] }>()

const route = useRoute()
const router = useRouter()
const tagsViewStore = useTagsViewStore()

/** keep-alive 停用期间忽略 orderId 变化，避免其它带 :id 路由误触发「订单不存在」 */
const panelActive = ref(true)
onActivated(() => {
  const fromCache = !panelActive.value
  panelActive.value = true
  if (fromCache && props.orderId) load()
})
onDeactivated(() => {
  panelActive.value = false
})

function syncDetailTagTitle(ot: string, orderNo?: string) {
  if (route.name !== 'ExperimentOrderDetail') return
  // 仅更新「当前路由」对应标签；缓存实例在错误时机 load 时不得改写其它详情的标题
  if (String(route.params.id || '') !== String(props.orderId || '')) return
  const queryFrom = String(route.query.from || '')
  const from = queryFrom || detailFromByOrderType(ot)
  // 仅当显式带列表 from 时补列表标签；勿按 orderType 推断，否则会从资金/支付等页硬插列表标签
  if (queryFrom) tagsViewStore.ensureSourceListTag(queryFrom)
  const no = String(orderNo || '').trim()
  const title =
    from === 'grab-orders'
      ? no
        ? `${no} 抢单实验详情`
        : '抢单实验详情'
      : detailTitleByOrderType(ot, orderNo)
  tagsViewStore.updateViewTitle(route.path, title)
  // 同步 query.orderNo，便于标签/刷新后仍带单号
  if (no && String(route.query.orderNo || '') !== no) {
    router.replace({
      path: route.path,
      query: { ...route.query, from, orderNo: no },
    })
  }
}
const loading = ref(false)
const acting = ref(false)
const detail = ref<Record<string, unknown> | null>(null)
const editChildren = ref<Record<string, unknown>[]>([])
const orderFiles = ref<Record<string, unknown>[]>([])
const invoiceFiles = ref<Record<string, unknown>[]>([])
const orderMsg = ref('')
const shareVisible = ref(false)
const shareUsers = ref<Record<string, unknown>[]>([])
type ShareRow = { userId: string; value: string }
const profitRows = ref<ShareRow[]>([{ userId: '', value: '' }])
const costRows = ref<ShareRow[]>([{ userId: '', value: '' }])
const relatedVisible = ref(false)
const relatedType = ref('')
const relatedOrderNo = ref('')
const receiveVisible = ref(false)
const receiveMoney = ref('')
const receiveDate = ref('')
const receiveRemark = ref('')
const invoiceVisible = ref(false)
const invoiceMoney = ref('')
const invoiceRemark = ref('')
const subPayBillVisible = ref(false)
const subPayMoney = ref('')
const subPayRemark = ref('')
const subInvoiceVisible = ref(false)
const subInvoiceMoney = ref('')
const subInvoiceRemark = ref('')
const moreVisible = ref(false)
const moreInfo = ref<Record<string, unknown> | null>(null)
const appointmentVisible = ref(false)
const appointmentLoading = ref(false)
const appointmentAddressId = ref<string | number>('')
const appointmentAddressOpts = ref<{ value: string | number; label: string }[]>([])

const sampleVisible = ref(false)
const sampleAction = ref<SampleAction>('arrive')
const sampleTableRef = ref<InstanceType<typeof ElTable>>()
const sampleSelected = ref<Record<string, unknown>[]>([])
/** 强制单选时清表/重勾会再触发 selection-change，用锁避免递归 */
let sampleSelectionLock = false
const sampleStoreId = ref('')
const sampleStorePosId = ref('')
const sampleStoreOptions = ref<Record<string, unknown>[]>([])
const samplePosOptions = ref<Record<string, unknown>[]>([])
const sampleExpress = ref('')
const sampleExpressName = ref('')
const sampleMeeting = ref('')
const sampleVideoTime = ref('')
const sampleConfirmMark = ref('')
const sampleRetainMode = ref<'retain' | 'scrap'>('retain')
const sampleIsPosition = ref('1')
const sampleRetainStoreId = ref('')
const sampleRetainStorePosId = ref('')
const remainStoreOptions = ref<Record<string, unknown>[]>([])
const remainPosOptions = ref<Record<string, unknown>[]>([])

const logs = computed(() => (detail.value?.logs as Record<string, unknown>[]) || [])
const consultList = computed(
  () => (detail.value?.consultList as Record<string, unknown>[]) || []
)
const linkedOrders = computed(
  () => (detail.value?.linkedOrders as Record<string, unknown>[]) || []
)
const relatedOrders = computed(
  () => (detail.value?.relatedOrders as Record<string, unknown>[]) || []
)
const orderType = computed(() => String(detail.value?.orderType || ''))
const isChildKind = computed(() => ['9', '10'].includes(orderType.value))
/** 对齐 Java isFlag：测试主管/测试人员不可看付款·开票相关数据 */
const canViewFinance = computed(() => detail.value?.canViewFinance !== false)
const showOrderDocsBlock = computed(() => ['6', '8', '9', '10'].includes(orderType.value))
const outBillTypeLabel = computed(() => {
  const d = detail.value
  if (!d) return '-'
  const nested = d.outBillType as Record<string, unknown> | undefined
  return String(d.outBillTypeName || nested?.name || '-').trim() || '-'
})
const inBillTypeLabel = computed(() => {
  const d = detail.value
  if (!d) return '-'
  const nested = d.inBillType as Record<string, unknown> | undefined
  return String(d.inBillTypeName || nested?.name || '-').trim() || '-'
})
/** 抢单列表进入：对齐 Java qdorderdetail，精简财务操作，子单可单独抢单 */
const isGrabMode = computed(() => String(route.query.from || '') === 'grab-orders')

const expectPayRows = computed(() => {
  const list = detail.value?.expectPayList
  return Array.isArray(list)
    ? (list as {
        time?: string
        price?: string
        actualOnlineReceiveTime?: string
        actualOnlineReceiveAmount?: string | number
        actualReceiveTime?: string
        actualReceiveAmount?: string | number
        actualReceiveOnline?: boolean
        actualInvoiceTime?: string
        actualInvoiceAmount?: string | number
      }[])
    : []
})

const onlineReceiveBillRows = computed(() => {
  const list = detail.value?.onlineReceiveBills
  if (Array.isArray(list) && list.length) {
    return list as { billDate?: string; money?: string | number }[]
  }
  return []
})

const receiveBillRows = computed(() => {
  const list = detail.value?.receiveBills
  if (Array.isArray(list) && list.length) return list as { billDate?: string; money?: string | number }[]
  const bills = detail.value?.bills
  if (!Array.isArray(bills)) return []
  return (bills as { type?: number; billDate?: string; money?: string | number }[]).filter(
    (b) => Number(b.type) === 2
  )
})

const invoiceBillRows = computed(() => {
  const list = detail.value?.invoiceBills
  if (Array.isArray(list) && list.length) return list as { billDate?: string; money?: string | number }[]
  const bills = detail.value?.bills
  if (!Array.isArray(bills)) return []
  return (bills as { type?: number; billDate?: string; money?: string | number }[]).filter(
    (b) => Number(b.type) === 1
  )
})

const orderTypeLabel = computed(() => {
  const map: Record<string, string> = {
    '6': '实验订单',
    '10': '实验子订单',
    '8': '实验分包订单',
    '9': '实验分包子订单',
  }
  return map[orderType.value] || orderType.value || '-'
})
const titleText = computed(() =>
  isGrabMode.value ? `抢单实验详情` : `${orderTypeLabel.value}详情`
)
const linkedTitle = computed(() =>
  orderType.value === '8' ? '关联分包子订单' : '关联实验子订单'
)

const statusTagType = computed(() => {
  const st = Number(detail.value?.orderStatus)
  if (st === 0) return 'info'
  if (st === 10) return 'danger'
  if (st === 20) return 'warning'
  if (st === 30 || st === 50) return 'success'
  return 'primary'
})

const SAMPLE_TITLES: Record<SampleAction, string> = {
  arrive: '样品到货',
  video: '预约云视频',
  pick: '样品领用',
  testStart: '开始测试',
  testEnd: '测试完成',
  return: '样品归还',
  ship: '样品寄回',
  retain: '样品留存',
  scrap: '样品报废',
  retest: '样品复测',
  confirmDone: '确认完成',
}

const sampleDialogTitle = computed(() => SAMPLE_TITLES[sampleAction.value] || '选择子单行')
const sampleNeedExtra = computed(() =>
  ['arrive', 'return', 'pick', 'ship', 'video', 'confirmDone', 'retain', 'testStart'].includes(
    sampleAction.value,
  ),
)
const sampleExpectedPosLabel = computed(() => {
  if (sampleAction.value !== 'pick' || sampleSelected.value.length !== 1) return ''
  const row = sampleSelected.value[0]
  const store = String(row.sampleStoreName || '')
  const block = String(row.storeBlock || '')
  const num = String(row.storeNumber || '')
  const slot = [block, num].filter(Boolean).join('-')
  if (!store && !slot) return ''
  return [store, slot].filter(Boolean).join(' ')
})
const sampleConfirmPlatform = computed(() => {
  if (sampleSelected.value.length !== 1) return ''
  const row = sampleSelected.value[0]
  return String(row.platformName || row.lineId || '')
})
/** 留存/寄回：展示当前样品仓库位置供确认（对齐 Java storeInfo） */
const sampleConfirmLocation = computed(() => {
  if (sampleSelected.value.length !== 1) return ''
  const row = sampleSelected.value[0]
  const parts = [
    row.sampleStoreName || row.storeName,
    row.storeBlock || row.blockName,
    row.storeNumber || row.storePosNumber || row.number,
    row.storePosition,
  ]
    .map((x) => String(x || '').trim())
    .filter(Boolean)
  return parts.length ? parts.join(' / ') : String(row.storePosId || '')
})
const sampleExtraHint = computed(() => {
  if (sampleAction.value === 'arrive')
    return '请勾选一条已处理(状态2)的子行；仓库名称/位置可不填，填了则入库到对应仓位'
  if (sampleAction.value === 'return')
    return '请勾选一条测试完成(状态39)的子行；仓库名称/位置可不填'
  if (sampleAction.value === 'pick')
    return sampleExpectedPosLabel.value
      ? `请勾选一条样品到货(状态36)的子行，并确认出库仓库位置（${sampleExpectedPosLabel.value}）`
      : '请勾选一条样品到货(状态36)的子行；若已入库则须确认仓库位置出库'
  if (sampleAction.value === 'ship')
    return '请勾选一条已归还(状态41)的子行；须确认仓库位置，并填写快递公司与单号'
  if (sampleAction.value === 'video')
    return '请勾选一条尚未预约会议的子行，并填写预约时间与会议号'
  if (sampleAction.value === 'testStart')
    return orderType.value === '10'
      ? '请勾选一条已领用(状态37)的子行，并确认实验平台与创建子单时一致'
      : '请勾选一条已领用(状态37)的子行'
  if (sampleAction.value === 'testEnd')
    return '请勾选一条已开始测试(状态38)的子行'
  if (sampleAction.value === 'retain')
    return '请勾选一条已归还(状态41)的子行；留存可入库到留存仓；报废须确认原仓库位置'
  if (sampleAction.value === 'retest') return '请勾选一条测试完成或已归还的子行'
  if (sampleAction.value === 'confirmDone')
    return '请勾选一条测试完成且未确认的子行，备注必填（确认完成≠订单已完成）'
  return ''
})

function childStatusNum(row: Record<string, unknown>) {
  return Number(row.orderStatus ?? -1)
}

function childConfirmNum(row: Record<string, unknown>) {
  return Number(row.isConfirm ?? 0)
}

const sampleSelectableRows = computed(() => {
  const rows = editChildren.value
  const act = sampleAction.value
  return rows.filter((r) => {
    const st = childStatusNum(r)
    if (act === 'arrive') return st === 2
    if (act === 'pick') return st === 36
    if (act === 'testStart') return st === 37
    if (act === 'testEnd') return st === 38
    if (act === 'return') return st === 39
    if (act === 'ship' || act === 'retain' || act === 'scrap') return st === 41
    if (act === 'retest') return st === 39 || st === 41
    if (act === 'confirmDone') return st >= 39 && childConfirmNum(r) === 0
    if (act === 'video') return st >= 36 && Number(r.isMeeting ?? 0) === 0
    return true
  })
})

async function load() {
  if (!props.orderId) return
  loading.value = true
  try {
    const res = await getExpOrderDetail(props.orderId)
    if (!isAjaxOk(res) || !res.obj) {
      detail.value = null
      editChildren.value = []
      orderFiles.value = []
      invoiceFiles.value = []
      orderMsg.value = ''
      ElMessage.error(ajaxErrorMessage(res, '加载详情失败'))
      return
    }
    detail.value = res.obj as Record<string, unknown>
    const kids = (detail.value.children as Record<string, unknown>[]) || []
    editChildren.value = kids.map((c) => ({ ...c }))
    orderFiles.value = Array.isArray(detail.value.files)
      ? (detail.value.files as Record<string, unknown>[])
      : []
    invoiceFiles.value = Array.isArray(detail.value.invoiceFiles)
      ? (detail.value.invoiceFiles as Record<string, unknown>[])
      : []
    orderMsg.value = String(detail.value.msg || '')
    const ot = String(detail.value.orderType || '')
    const orderNo = String(detail.value.orderId || '')
    syncDetailTagTitle(ot, orderNo)
  } finally {
    loading.value = false
  }
}

function fileLabel(f: Record<string, unknown>) {
  return String(f.info || f.name || '附件')
}

function fileUrl(f: Record<string, unknown>) {
  const u = String(f.url || '')
  if (u) return u
  const path = String(f.path || '').replace(/\/$/, '')
  const name = String(f.name || '')
  if (path && name) return `${path}/${name}`
  return path || name || '#'
}

async function onPreviewFile(f: Record<string, unknown>) {
  const id = Number(f.id)
  if (!id) {
    ElMessage.warning('文件无效')
    return
  }
  const name = fileLabel(f)
  const result = await previewExpOrderFile(id, name)
  if (!result.ok) {
    ElMessage.error(result.message || '预览失败')
  }
}

async function onDownloadFile(f: Record<string, unknown>) {
  const id = Number(f.id)
  if (!id) {
    ElMessage.warning('文件无效')
    return
  }
  const name = fileLabel(f)
  const result = await downloadExpOrderFile(id, name)
  if (!result.ok) {
    ElMessage.error(result.message || '下载失败')
  }
}

async function onDeleteFile(f: Record<string, unknown>) {
  const id = Number(f.id)
  if (!id) return
  await ElMessageBox.confirm('确定删除此文件？', '删除附件', { type: 'warning' })
  await runAction(async () => {
    const res = await deleteExpOrderFile(id)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '删除失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '已删除'))
    await load()
  })
}

async function onUploadOrderFile(options: { file: File }) {
  if (!props.orderId) return
  const fd = new FormData()
  fd.append('orderdata', options.file)
  fd.append('id', String(props.orderId))
  fd.append('type', '3')
  await runAction(async () => {
    const res = await uploadExpOrderFile(fd)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '上传成功'))
    await load()
  })
}

async function onUploadInvoiceFile(options: { file: File }) {
  if (!props.orderId) return
  const fd = new FormData()
  fd.append('orderdata', options.file)
  fd.append('id', String(props.orderId))
  fd.append('type', '5')
  await runAction(async () => {
    const res = await uploadExpOrderFile(fd)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '上传成功'))
    await load()
  })
}

async function onSaveOrderMsg() {
  if (!props.orderId || !detail.value) return
  const prev = String(detail.value.msg || '')
  if (orderMsg.value === prev) return
  const res = await updateExpOrderMsg(props.orderId, orderMsg.value)
  if (!isAjaxOk(res)) {
    ElMessage.error(ajaxErrorMessage(res, '备注保存失败'))
    return
  }
  detail.value.msg = orderMsg.value
}

async function onSaveReferencePrice(row: Record<string, unknown>) {
  const childId = Number(row.id)
  if (!childId) return
  await runAction(async () => {
    const res = await saveExpChildReferencePrice({
      id: childId,
      referencePrice: row.referencePrice,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存测试金额失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '已保存'))
    await load()
  })
}

async function onSaveTimeType(row: Record<string, unknown>, timeType: string) {
  const childId = Number(row.id)
  if (!childId) return
  await runAction(async () => {
    const res = await updateExpChildTimeType({ id: childId, timeType })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存时间单位失败'))
      return
    }
    row.timeType = timeType
    ElMessage.success(String(res.resMsg || '已保存'))
    await load()
  })
}

function onOpenSampleOrder(row: Record<string, unknown>) {
  const gotId = row.gotId
  const outNum = String(row.outNum || '').trim()
  if (!gotId && !outNum) {
    ElMessage.warning('无样品单号')
    return
  }
  // 对齐 Java inTreasury/indetail：跳转库存样品出库/管理单列表并带单号
  router.push({
    name: 'InventorySampleOrders',
    query: {
      ...(gotId ? { id: String(gotId) } : {}),
      ...(outNum ? { outNum } : {}),
    },
  })
}

function onViewSampleInfo(row: Record<string, unknown>) {
  const info = (row.sampleInfo || {}) as Record<string, unknown>
  const name = String(info.sampleName || row.sampleName || '-')
  const num = String(info.sampleNum || row.sampleNum || '-')
  ElMessageBox.alert(
    `<div>样品名称：${name}</div><div>样品数量：${num}</div>`,
    '样品信息',
    { dangerouslyUseHTMLString: true, confirmButtonText: '关闭' }
  )
}

async function onUploadChildTestFile(
  options: { file: File },
  row: Record<string, unknown>
) {
  const childId = Number(row.id)
  if (!childId) return
  const fd = new FormData()
  fd.append('orderdata', options.file)
  fd.append('id', String(props.orderId))
  fd.append('childId', String(childId))
  fd.append('type', '4')
  await runAction(async () => {
    const res = await uploadExpOrderFile(fd)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '上传成功'))
    await load()
  })
}

function resolveDetailPk(
  id: string | number | undefined | null,
  orderNo?: string | number
): number {
  const n = Number(id)
  if (Number.isFinite(n) && n > 0) return n
  const no = String(orderNo || id || '').trim()
  if (!no) return 0
  const hit =
    relatedOrders.value.find((r) => String(r.orderId) === no) ||
    linkedOrders.value.find((r) => String(r.orderId) === no)
  const pk = Number(hit?.id)
  return Number.isFinite(pk) && pk > 0 ? pk : 0
}

async function goDetail(
  id: string | number,
  linkedOrderType?: string | number,
  orderNo?: string | number
) {
  const pk = resolveDetailPk(id, orderNo)
  if (!pk) {
    ElMessage.warning('无法打开该订单')
    return
  }
  // 优先用目标单 orderType；未传时默认按「主单 → 关联子单」
  let ot = linkedOrderType != null && String(linkedOrderType) !== '' ? String(linkedOrderType) : ''
  if (!ot) {
    ot = orderType.value === '8' ? '9' : '10'
  }
  const no = String(orderNo || '').trim()
  const targetId = String(pk)
  // 已在目标详情：强制刷新（避免同路由误判为无跳转）
  if (route.name === 'ExperimentOrderDetail' && String(route.params.id) === targetId) {
    await load()
    return
  }
  await router.push({
    name: 'ExperimentOrderDetail',
    params: { id: targetId },
    query: {
      from: detailFromByOrderType(ot),
      ...(no ? { orderNo: no } : {}),
    },
  })
}

async function runAction(fn: () => Promise<void>) {
  acting.value = true
  try {
    await fn()
  } finally {
    acting.value = false
  }
}

async function doAudit(pass: boolean) {
  await ElMessageBox.confirm(pass ? '确认审核通过？' : '确认驳回该订单？', '提示', {
    type: pass ? 'warning' : 'error',
  })
  await runAction(async () => {
    const res = await auditExpOrder({ id: props.orderId, pass })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '操作失败'))
      return
    }
    ElMessage.success(pass ? '审核通过' : '已驳回')
    await load()
    emit('refreshed')
  })
}

async function onCancel() {
  await ElMessageBox.confirm('是否取消此订单?', '取消订单', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
  await runAction(async () => {
    const res = await cancelExpOrder({ id: props.orderId })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '取消失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '订单已取消'))
    await load()
    emit('refreshed')
  })
}

async function onGrabChild(row: Record<string, unknown>) {
  const label = String(row.childOrderId || row.id || '')
  await ElMessageBox.confirm(`确认抢单子单 ${label}？`, '抢单', { type: 'warning' })
  await runAction(async () => {
    const res = await grabExpOrder(String(row.id))
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '抢单失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '抢单成功！请前往实验子订单列表进行测试！'))
    await load()
    emit('refreshed')
  })
}

function parseScalePairs(raw: unknown): ShareRow[] {
  const text = String(raw || '').trim()
  if (!text) return [{ userId: '', value: '' }]
  const rows = text
    .split(',')
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => {
      const [userId = '', value = ''] = p.split('_')
      return { userId: userId.trim(), value: value.trim().replace('%', '') }
    })
    .filter((r) => r.userId || r.value)
  return rows.length ? rows : [{ userId: '', value: '' }]
}

function shareUserLabel(u: Record<string, unknown>) {
  const name = String(u.trueName || u.userName || '')
  const uname = String(u.userName || '')
  return name && uname && name !== uname ? `${name}（${uname}）` : name || uname || String(u.id)
}

function addShareRow(rows: ShareRow[]) {
  rows.push({ userId: '', value: '' })
}

async function openShareDialog() {
  profitRows.value = parseScalePairs(detail.value?.userScaleInfo || detail.value?.scaleInfo)
  costRows.value = parseScalePairs(detail.value?.salecbUserScaleInfo)
  shareVisible.value = true
  try {
    const res = await fetchIncomeUsers('')
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      shareUsers.value = res.obj as Record<string, unknown>[]
    }
  } catch {
    shareUsers.value = []
  }
}

function buildScaleInfo(rows: ShareRow[]): string {
  return rows
    .filter((r) => r.userId && String(r.value).trim() !== '')
    .map((r) => `${r.userId}_${String(r.value).trim()}`)
    .join(',')
}

async function onShareSave() {
  const profitInfo = buildScaleInfo(profitRows.value)
  if (!profitInfo) {
    ElMessage.warning('请填写分成比例!')
    return
  }
  let total = 0
  for (const r of profitRows.value) {
    if (!r.userId && !String(r.value).trim()) continue
    if (!r.userId) {
      ElMessage.warning('请选择毛利分成人员!')
      return
    }
    const n = Number(r.value)
    if (!Number.isFinite(n) || n < 0) {
      ElMessage.warning('请填写正确的分成比例!')
      return
    }
    total += n
  }
  if (Math.abs(total - 100) > 0.01) {
    ElMessage.warning('总的分成比例不是100，请重新输入')
    return
  }
  const costInfo = orderType.value === '6' ? buildScaleInfo(costRows.value) : ''
  await runAction(async () => {
    const res = await updateExpOrderShareRatio({
      id: props.orderId,
      user_scale_info: profitInfo,
      salecb_user_scale_info: costInfo,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '操作成功'))
    shareVisible.value = false
    await load()
    emit('refreshed')
  })
}

async function onAddRelated() {
  if (!relatedType.value) {
    ElMessage.warning('请选择订单类型')
    return
  }
  if (!relatedOrderNo.value.trim()) {
    ElMessage.warning('请输入订单号')
    return
  }
  await runAction(async () => {
    const res = await addExpOrderRelated({
      id: props.orderId,
      rSelect: relatedType.value,
      rOrderId: relatedOrderNo.value.trim(),
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '关联失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '关联成功'))
    relatedVisible.value = false
    relatedType.value = ''
    relatedOrderNo.value = ''
    await load()
    emit('refreshed')
  })
}

async function onDelRelated(row: Record<string, unknown>) {
  const relatedNo = String(row.orderId || '').trim()
  const ofId = String(detail.value?.orderId || '').trim()
  if (!relatedNo || !ofId) return
  await ElMessageBox.confirm(
    `确定要删除订单号为：${relatedNo}的关联订单吗？`,
    '删除关联订单',
    { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
  )
  await runAction(async () => {
    const res = await delExpOrderRelated({ ofId, order_id: relatedNo })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '删除失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '删除成功'))
    await load()
    emit('refreshed')
  })
}

async function onSubmitAudit() {
  await ElMessageBox.confirm('确认提交审核？', '提交审核', { type: 'warning' })
  await runAction(async () => {
    const res = await submitExpOrderAudit(props.orderId)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '提交失败'))
      return
    }
    ElMessage.success('已提交审核')
    await load()
    emit('refreshed')
  })
}

async function onWithdrawAudit() {
  await ElMessageBox.confirm('确认取消审核申请？', '取消审核', { type: 'warning' })
  await runAction(async () => {
    const res = await withdrawExpOrderAudit(props.orderId)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '操作失败'))
      return
    }
    ElMessage.success('已取消审核申请')
    await load()
    emit('refreshed')
  })
}

async function onCostSettle() {
  await ElMessageBox.confirm(
    '确认标记「所有成本已结清」？若已有收款将按分成配置补分钱。',
    '成本结清',
    { type: 'warning' }
  )
  await runAction(async () => {
    const res = await costSettleExpOrder(props.orderId)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '操作失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '已结清'))
    await load()
    emit('refreshed')
  })
}

async function onSaveReceive() {
  const money = Number(receiveMoney.value)
  if (!Number.isFinite(money) || money <= 0) {
    ElMessage.warning('请输入有效收款金额')
    return
  }
  await runAction(async () => {
    const res = await saveExpOrderReceiveBill({
      id: props.orderId,
      money,
      billDate: receiveDate.value || undefined,
      logInfo: receiveRemark.value.trim() || '录入收款',
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '收款失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '收款成功'))
    receiveVisible.value = false
    receiveMoney.value = ''
    receiveDate.value = ''
    receiveRemark.value = ''
    await load()
    emit('refreshed')
  })
}

async function onSaveFinish() {
  await runAction(async () => {
    const items = editChildren.value.map((c) => ({
      id: c.id,
      finishTime: c.finishTime || c.expectFinishTime || '',
    }))
    const res = await saveExpOrderFinish({
      id: props.orderId,
      // 网关/表单序列化场景下对象数组易丢结构，同时传 JSON 字符串兜底
      items: JSON.stringify(items),
      childIds: items.map((x) => x.id).join(','),
      finishTimes: items.map((x) => String(x.finishTime || '')).join(','),
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '保存失败'))
      return
    }
    ElMessage.success('保存成功')
    await load()
    emit('refreshed')
  })
}

async function onMoreInfo() {
  const res = await fetchExpOrderMoreInfo(props.orderId)
  if (!isAjaxOk(res) || !res.obj) {
    ElMessage.error(ajaxErrorMessage(res, '加载失败'))
    return
  }
  moreInfo.value = res.obj as Record<string, unknown>
  moreVisible.value = true
}

function onEditOrder() {
  router.push({
    name: 'ExperimentOrderEdit',
    params: { id: String(props.orderId) },
  })
}

function onCreateChild() {
  router.push({
    name: 'ExperimentSubOrderCreate',
    query: { saleOrderId: String(props.orderId) },
  })
}

async function onSaveInvoice() {
  const money = Number(invoiceMoney.value)
  if (!Number.isFinite(money) || money <= 0) {
    ElMessage.warning('请输入有效开票金额')
    return
  }
  await runAction(async () => {
    const res = await saveExpOrderInvoiceBill({
      id: props.orderId,
      money,
      logInfo: invoiceRemark.value.trim() || '录入开票',
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '开票失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '开票成功'))
    invoiceVisible.value = false
    invoiceMoney.value = ''
    invoiceRemark.value = ''
    await load()
    emit('refreshed')
  })
}

async function onConfirmPay() {
  await ElMessageBox.confirm('确认将线上未结清差额记为已收款？', '确认付款', { type: 'warning' })
  await runAction(async () => {
    const res = await confirmExpOrderPay(props.orderId)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '确认失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '已确认付款'))
    await load()
    emit('refreshed')
  })
}

async function onConfirmOrdered() {
  await ElMessageBox.confirm('确认已向厂家/分包方下单？（附件可后续补充）', '确认已下单', {
    type: 'warning',
  })
  await runAction(async () => {
    const res = await confirmExpOrdered(props.orderId)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '确认失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '已确认下单'))
    await load()
    emit('refreshed')
  })
}

async function onSubPay(type: '1' | '2' | '3') {
  const titles: Record<string, string> = {
    '1': '确认提交付款申请？',
    '2': '确认付款审核通过？',
    '3': '确认驳回付款申请？',
  }
  await ElMessageBox.confirm(titles[type] || '确认操作？', '付款申请', {
    type: type === '3' ? 'error' : 'warning',
  })
  await runAction(async () => {
    const res = await subPayExpOrder({ id: props.orderId, type })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '操作失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '操作成功'))
    await load()
    emit('refreshed')
  })
}

async function onUploadSubPay() {
  const money = Number(subPayMoney.value)
  if (!Number.isFinite(money) || money <= 0) {
    ElMessage.warning('请输入有效付款金额')
    return
  }
  await runAction(async () => {
    const res = await uploadSubPayExpOrder({
      id: props.orderId,
      money,
      logInfo: subPayRemark.value.trim() || '上传付款信息',
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '上传成功'))
    subPayBillVisible.value = false
    subPayMoney.value = ''
    subPayRemark.value = ''
    await load()
    emit('refreshed')
  })
}

async function onUploadSubInvoice() {
  const money = Number(subInvoiceMoney.value)
  if (!Number.isFinite(money) || money <= 0) {
    ElMessage.warning('请输入有效发票金额')
    return
  }
  await runAction(async () => {
    const res = await uploadSubInvoiceExpOrder({
      id: props.orderId,
      money,
      logInfo: subInvoiceRemark.value.trim() || '上传发票信息',
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '上传失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '上传成功'))
    subInvoiceVisible.value = false
    subInvoiceMoney.value = ''
    subInvoiceRemark.value = ''
    await load()
    emit('refreshed')
  })
}

async function onConfirmCustomer() {
  await ElMessageBox.confirm('确认已和客户沟通？订单将进入已审核状态。', '客户确认', {
    type: 'warning',
  })
  await runAction(async () => {
    const res = await confirmExpOrderCustomer(props.orderId)
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '确认失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '已确认'))
    await load()
    emit('refreshed')
  })
}

async function onGenerateAppointment() {
  appointmentAddressId.value = ''
  appointmentVisible.value = true
  appointmentLoading.value = true
  try {
    const res = await fetchTestAddressList({ start: 0, length: 500, draw: 1 })
    const rows = Array.isArray(res.data) ? res.data : []
    appointmentAddressOpts.value = rows
      .map((a) => {
        const row = a as Record<string, unknown>
        const label = String(
          row.name ||
            [row.trueName || row.true_name, row.mobile, row.address].filter(Boolean).join(' · ') ||
            row.id ||
            ''
        )
        return { value: (row.id ?? '') as string | number, label }
      })
      .filter((o) => o.value !== '' && o.value != null)
    const preset = detail.value?.testAddressId
    if (preset != null && preset !== '' && appointmentAddressOpts.value.some((o) => String(o.value) === String(preset))) {
      appointmentAddressId.value = preset as string | number
    }
  } catch {
    appointmentAddressOpts.value = []
  } finally {
    appointmentLoading.value = false
  }
}

async function submitAppointment() {
  if (!appointmentAddressId.value && appointmentAddressId.value !== 0) {
    ElMessage.warning('请选择寄送地址')
    return
  }
  await runAction(async () => {
    const res = await generateExpOrderAppointment({
      id: props.orderId,
      testAddressId: appointmentAddressId.value,
      test_address_id: appointmentAddressId.value,
    })
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '生成失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '已生成预约单'))
    appointmentVisible.value = false
    await load()
    emit('refreshed')
  })
}

async function onSampleSelectionChange(rows: Record<string, unknown>[]) {
  if (sampleSelectionLock) return
  let selected = rows
  // 对齐 Java 样品流程：一次只能选一条
  if (rows.length > 1) {
    ElMessage.warning('只能选择一条数据!')
    const last = rows[rows.length - 1]
    sampleSelectionLock = true
    sampleTableRef.value?.clearSelection()
    await nextTick()
    sampleTableRef.value?.toggleRowSelection(last, true)
    sampleSelectionLock = false
    selected = [last]
  }
  sampleSelected.value = selected
  // 领用/寄回/报废：勾选一行时预填原仓库/仓位便于确认
  const needConfirmPos =
    sampleAction.value === 'pick' ||
    sampleAction.value === 'ship' ||
    (sampleAction.value === 'retain' && sampleRetainMode.value === 'scrap')
  if (needConfirmPos && selected.length === 1) {
    const row = selected[0]
    const sid = row.storeId != null ? String(row.storeId) : ''
    const pid = row.storePosId != null ? String(row.storePosId) : ''
    if (sid) {
      sampleStoreId.value = sid
      await onSampleStoreChange(sid)
      if (pid) sampleStorePosId.value = pid
    }
  }
}

async function loadSampleStoreOptions() {
  try {
    const res = await fetchSampleOrderOptions()
    if (isAjaxOk(res) && res.obj) {
      const obj = res.obj as Record<string, unknown>
      const stores = (obj.stores || res.obj) as Record<string, unknown>[]
      const rows = Array.isArray(stores) ? stores : []
      sampleStoreOptions.value = rows.map((s) => ({
        ...s,
        value: s.value ?? s.id,
        label: s.label || s.sample_store_name || s.sampleStoreName || s.name || s.id,
      }))
    }
  } catch {
    sampleStoreOptions.value = []
  }
}

async function onSampleStoreChange(storeId: string) {
  sampleStorePosId.value = ''
  samplePosOptions.value = []
  if (!storeId) return
  try {
    // 领用/寄回/报废确认：含已占用仓位；到货/归还：空闲仓位
    const confirmOccupied =
      sampleAction.value === 'pick' ||
      sampleAction.value === 'ship' ||
      (sampleAction.value === 'retain' && sampleRetainMode.value === 'scrap')
    const posType = confirmOccupied ? 1 : 0
    const res = await fetchSampleStorePositions(storeId, posType as 0 | 1)
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      samplePosOptions.value = (res.obj as Record<string, unknown>[]).map((p) => ({
        ...p,
        value: p.value ?? p.id,
        label:
          p.label ||
          [p.block || p.blockName, p.number || p.posNumber].filter(Boolean).join('-') ||
          p.id,
      }))
    }
  } catch {
    samplePosOptions.value = []
  }
}

async function loadRemainStoreOptions() {
  try {
    const res = await fetchRemainSampleStoreOptions()
    if (isAjaxOk(res) && res.obj) {
      const obj = res.obj as Record<string, unknown>
      const stores = (obj.stores || res.obj) as Record<string, unknown>[]
      const rows = Array.isArray(stores) ? stores : []
      remainStoreOptions.value = rows.map((s) => ({
        ...s,
        value: s.value ?? s.id,
        label: s.label || s.sample_store_name || s.sampleStoreName || s.name || s.id,
      }))
    }
  } catch {
    remainStoreOptions.value = []
  }
}

async function onRetainStoreChange(storeId: string) {
  sampleRetainStorePosId.value = ''
  remainPosOptions.value = []
  if (!storeId) return
  try {
    const res = await fetchRemainSampleStorePositions(storeId, 0)
    if (isAjaxOk(res) && Array.isArray(res.obj)) {
      remainPosOptions.value = (res.obj as Record<string, unknown>[]).map((p) => ({
        ...p,
        value: p.value ?? p.id,
        label:
          p.label ||
          [p.block || p.blockName, p.number || p.posNumber].filter(Boolean).join('-') ||
          p.id,
      }))
    }
  } catch {
    remainPosOptions.value = []
  }
}

async function openSampleAction(act: SampleAction) {
  sampleAction.value = act
  sampleSelected.value = []
  sampleStoreId.value = ''
  sampleStorePosId.value = ''
  samplePosOptions.value = []
  sampleExpress.value = ''
  sampleExpressName.value = ''
  sampleMeeting.value = ''
  sampleVideoTime.value = ''
  sampleConfirmMark.value = ''
  sampleRetainMode.value = 'retain'
  sampleIsPosition.value = '1'
  sampleRetainStoreId.value = ''
  sampleRetainStorePosId.value = ''
  remainPosOptions.value = []
  sampleVisible.value = true
  if (act === 'arrive' || act === 'return' || act === 'pick' || act === 'ship') {
    await loadSampleStoreOptions()
  }
  if (act === 'retain') {
    await loadSampleStoreOptions()
    await loadRemainStoreOptions()
  }
  await nextTick()
  sampleTableRef.value?.clearSelection()
}

async function onSubmitSampleAction() {
  const ids = sampleSelected.value.map((r) => r.id).filter((id) => id != null)
  if (!ids.length) {
    ElMessage.warning('请至少选择一行')
    return
  }
  // 对齐 Java 样品流程：一次只能一条
  if (ids.length !== 1) {
    ElMessage.warning('只能选择一条数据!')
    return
  }
  if (sampleAction.value === 'video' && !sampleMeeting.value.trim()) {
    ElMessage.warning('请填写会议号')
    return
  }
  if (sampleAction.value === 'video' && !sampleVideoTime.value) {
    ElMessage.warning('请选择预约云视频时间')
    return
  }
  if (sampleAction.value === 'ship') {
    if (!sampleExpressName.value.trim()) {
      ElMessage.warning('请填写快递公司')
      return
    }
    if (!sampleExpress.value.trim()) {
      ElMessage.warning('请填写快递单号')
      return
    }
    const needPos = sampleSelected.value.some(
      (r) => r.storePosId != null && String(r.storePosId) !== ''
    )
    if (needPos && !sampleStorePosId.value) {
      ElMessage.warning('请确认样本仓库位置!')
      return
    }
  }
  if (sampleAction.value === 'confirmDone' && !sampleConfirmMark.value.trim()) {
    ElMessage.warning('请填写确认备注')
    return
  }
  if (sampleAction.value === 'arrive') {
    const hasStore = !!sampleStoreId.value
    const hasPos = !!sampleStorePosId.value
    if (hasStore !== hasPos) {
      ElMessage.warning(hasStore ? '请选择仓库位置!' : '请选择仓库!')
      return
    }
  }
  if (sampleAction.value === 'return') {
    const hasStore = !!sampleStoreId.value
    const hasPos = !!sampleStorePosId.value
    if (hasStore !== hasPos) {
      ElMessage.warning(hasStore ? '请选择仓库位置!' : '请选择仓库!')
      return
    }
  }
  if (sampleAction.value === 'pick') {
    const needPos = sampleSelected.value.some(
      (r) => r.storePosId != null && String(r.storePosId) !== ''
    )
    if (needPos && !sampleStorePosId.value) {
      ElMessage.warning('请输入样本仓库位置!')
      return
    }
  }
  if (sampleAction.value === 'testStart') {
    // type=9/8 分包无实验平台，不校验（对齐 Java ceshistart：仅 type=10 校验）
    if (orderType.value === '10') {
      const row = sampleSelected.value[0]
      if (!row.lineId && !row.platformName) {
        ElMessage.warning('该子行缺少实验平台，无法开始测试')
        return
      }
    }
  }
  if (sampleAction.value === 'retain' && sampleRetainMode.value === 'retain') {
    if (sampleIsPosition.value === '1') {
      if (!sampleRetainStoreId.value || !sampleRetainStorePosId.value) {
        ElMessage.warning('请选择留存仓库位置')
        return
      }
    }
  }
  if (sampleAction.value === 'retain' && sampleRetainMode.value === 'scrap') {
    const needPos = sampleSelected.value.some(
      (r) => r.storePosId != null && String(r.storePosId) !== ''
    )
    if (needPos && !sampleStorePosId.value) {
      ElMessage.warning('请确认样本仓库位置!')
      return
    }
  }
  const act = sampleAction.value
  await runAction(async () => {
    let res
    const base = { id: props.orderId, childIds: ids }
    if (act === 'arrive') {
      res = await sampleArriveExpOrder({
        ...base,
        storeId: sampleStoreId.value || '',
        storePosId: sampleStorePosId.value || '',
      })
    } else if (act === 'pick') {
      res = await samplePickExpOrder({
        ...base,
        storeId: sampleStoreId.value || '',
        storePosId: sampleStorePosId.value || '',
      })
    } else if (act === 'testStart') {
      const row = sampleSelected.value[0] || {}
      res = await testStartExpOrder({
        ...base,
        lineId: String(row.lineId || ''),
      })
    } else if (act === 'testEnd') {
      res = await testEndExpOrder(base)
    } else if (act === 'return') {
      res = await sampleReturnExpOrder({
        ...base,
        storeId: sampleStoreId.value || '',
        storePosId: sampleStorePosId.value || '',
      })
    } else if (act === 'ship') {
      res = await sampleShipExpOrder({
        ...base,
        expressNo: sampleExpress.value,
        expressName: sampleExpressName.value,
        storePosId: sampleStorePosId.value || '',
      })
    } else if (act === 'retain' || act === 'scrap') {
      res = await sampleRetainExpOrder({
        ...base,
        scrap: act === 'scrap' || sampleRetainMode.value === 'scrap',
        isPosition: sampleRetainMode.value === 'scrap' ? '0' : sampleIsPosition.value,
        newStorePosId: sampleRetainStorePosId.value || '',
        storePosId: String(sampleStorePosId.value || sampleSelected.value[0]?.storePosId || ''),
      })
    } else if (act === 'retest') {
      res = await retestExpOrder(base)
    } else if (act === 'video') {
      res = await addVideoExpOrder({
        ...base,
        meetingNum: sampleMeeting.value.trim(),
        settingTime: sampleVideoTime.value,
      })
    } else {
      res = await confirmDoneExpOrder({ ...base, mark: sampleConfirmMark.value.trim() })
    }
    if (!isAjaxOk(res)) {
      ElMessage.error(ajaxErrorMessage(res, '操作失败'))
      return
    }
    ElMessage.success(String(res.resMsg || '操作成功'))
    sampleVisible.value = false
    await load()
    emit('refreshed')
  })
}

watch(
  () => props.orderId,
  () => {
    if (!panelActive.value) return
    load()
  },
  { immediate: true }
)

defineExpose({ reload: load })
</script>

<style scoped lang="scss">
.detail-panel {
  --ink: #1f2a24;
  --muted: #5f7068;
  --line: #d7e0db;
  --cream: #f4f7f5;
  --accent: #c45c26;
  --accent-soft: #f3e0d4;
  --sea: #1f6f5b;
  min-height: 240px;
  color: var(--ink);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 20px;
  margin-bottom: 14px;
  border-radius: 14px;
  background:
    radial-gradient(1200px 180px at 0% 0%, rgba(31, 111, 91, 0.12), transparent 55%),
    linear-gradient(135deg, #f7faf8 0%, #eef4f1 100%);
  border: 1px solid var(--line);
}

.back-link {
  border: 0;
  background: transparent;
  color: var(--sea);
  padding: 0;
  margin-bottom: 8px;
  cursor: pointer;
  font-size: 13px;
}
.back-link:hover {
  text-decoration: underline;
}

.hero-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.hero-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.hero-sub {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: var(--ink);
}
.dot {
  margin: 0 6px;
  opacity: 0.45;
}

.hero-meta {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  min-width: 200px;
}
.meta-item {
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(215, 224, 219, 0.9);
}
.meta-label {
  display: block;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 4px;
}
.meta-item strong {
  font-size: 18px;
  margin-right: 6px;
}
.meta-item small {
  color: var(--muted);
}

.action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--accent-soft);
  border: 1px solid #e8c9b4;
}

.btn-accent {
  --el-button-bg-color: var(--accent);
  --el-button-border-color: var(--accent);
  --el-button-text-color: #fff;
  --el-button-hover-bg-color: #a84c1d;
  --el-button-hover-border-color: #a84c1d;
  --el-button-hover-text-color: #fff;
}
.btn-warn {
  --el-button-bg-color: #b45309;
  --el-button-border-color: #b45309;
  --el-button-text-color: #fff;
  --el-button-hover-bg-color: #92400e;
  --el-button-hover-border-color: #92400e;
  --el-button-hover-text-color: #fff;
}

.card {
  margin-bottom: 16px;
  padding: 16px 18px 18px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: 0 1px 0 rgba(31, 42, 36, 0.03);
}
.card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.card-title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 700;
  color: var(--sea);
}
.card-hint {
  font-size: 12px;
  color: var(--muted);
}
.mark-text {
  white-space: pre-wrap;
  line-height: 1.5;
}
.order-files-block {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.files-row,
.remark-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.files-label {
  flex: 0 0 88px;
  padding-top: 6px;
  font-size: 13px;
  color: var(--muted);
  text-align: right;
}
.files-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}
.files-empty {
  font-size: 13px;
  color: var(--muted);
  padding-top: 6px;
}
.file-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  padding: 2px 0;
}
.inline-file {
  line-height: 1.5;
  a {
    color: var(--sea);
  }
}
.file-name {
  max-width: 420px;
  flex: 0 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--sea);
  text-decoration: none;
}
.file-name:hover {
  text-decoration: underline;
}
.remark-row :deep(.el-textarea) {
  flex: 1;
}
.receive-hint {
  margin: 0;
  padding-left: 100px;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}
.sample-alert {
  margin-bottom: 12px;
}
.sample-extra {
  margin-bottom: 8px;
}

.soft-desc :deep(.el-descriptions__label) {
  width: 110px;
  background: var(--cream) !important;
  color: var(--muted);
}
.detail-table :deep(th.el-table__cell) {
  background: var(--cream);
  color: var(--muted);
  font-weight: 600;
}

@media (max-width: 900px) {
  .hero {
    flex-direction: column;
  }
  .hero-meta {
    min-width: 0;
  }
}

.share-block {
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fafcfb;
}
.share-block-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.share-hint {
  color: var(--muted);
  font-size: 12px;
  flex: 1;
}
.share-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.addr-radio-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  max-height: 360px;
  overflow: auto;
}
.addr-radio {
  margin-right: 0;
  height: auto;
  white-space: normal;
  align-items: flex-start;
  line-height: 1.4;
}
</style>
