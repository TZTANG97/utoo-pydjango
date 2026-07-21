import type { AdminMenuItem } from '@/types/admin'

const MENU_ROUTE_MAP: Record<string, string> = {
  'invoice/InvoiceApplyLog.htm': '/invoice/apply',
  'invoice/invoiceApplyLog.htm': '/invoice/apply',
  'payLog/logList.htm': '/payment/records',
  'paymentapply/paymentapply.htm': '/payment/application',
  'retestapplication/retestList.htm': '/orders/retest',
  'taxesConfig/taxes_config.htm': '/order-settings/tax-rate',
  'consumePaytype/payment.htm': '/order-settings/payment-method',
  'edit/set_evaluate_setting.htm': '/order-settings/auto-evaluate',
  'billtype/bill.htm?type=1': '/order-settings/outgoing-invoice',
  'billtype/bill.htm?type=2': '/order-settings/incoming-invoice',
  'orderType/orderTypeList.htm': '/order-settings/order-type',
  'sys/dept/load.do': '/system/depts',
  'sys/user/load.do': '/system/users',
  'sys/role/load.do': '/system/roles',
  'logs/list.htm': '/system/ops-logs',
  'userCompany/usercompany.htm': '/member/enterprise',
  'supplier/supplierList.htm': '/system/companies',
  'member/memberPage.htm': '/member/personal',
  'applyVip/ListPage.htm': '/member/apply',
  'integral/set_integral.htm': '/member/integral',
  'integral/set_integral_convert_ratio.htm': '/member/integral',
  'offlineRecharge/rechargeList.htm': '/member/offline-recharge',
  'sys/menu/load.do': '/system/menus',
  'district/area.htm': '/system/areas',
  'sys/district/load.do': '/system/districts',
  'sys/userType/load.do': '/system/user-types',
  'appUser/ListPage.htm': '/system/app-users',
  'testaddress/addressList.htm': '/system/test-addresses',
  'companyaccount/accountList.htm': '/system/company-accounts',
  'caliOrder/todoJzlist.htm': '/service-platform/service-apply',
  'caliOrder/list.htm': '/service-platform/service-apply',
  'apply/device_back_manage.htm': '/service-platform/buyback',
  'consult/ListPage.htm': '/service-platform/consult',
  'consult/serviceSetting.htm': '/service-platform/consult-message',
  'records/problemlistPage.htm': '/service-platform/faq',
  'experimentSubOrder/suborderList.htm': '/service-platform/evaluated-sub-orders',
  'experimentOrder/evaluatelist.htm': '/service-platform/evaluated-orders',
  'records/recordslistPage.htm': '/service-platform/records',
  'productOrder/proveList.htm': '/service-platform/proposals',
  'consult/isshowCustomer.htm': '/service-platform/customer-service',
  'expOpenid/openidList.htm': '/service-platform/openid',
  // 运营管理
  'admin/advert_list.htm': '/ops/advert',
  'admin/adv_pos_list.htm': '/ops/adv-pos',
  'banner/slideshow.htm': '/ops/banner-pc',
  'banner/bannerList.htm': '/ops/banner-xcx',
  'banner/xcxfmslideshow.htm': '/ops/banner-xcxfm',
  'edit/set_device.htm': '/ops/setting-device',
  'edit/set_product_test.htm': '/ops/setting-product',
  'edit/set_business_support.htm': '/ops/setting-business',
  'edit/set_rent_device.htm': '/ops/setting-rent',
  'edit/set_second_hand.htm': '/ops/setting-secondhand',
  'redeem/redeemGoodsLogList.htm': '/ops/redeem',
  'entry/commentList.htm': '/ops/comment',
  'entry/entryList.htm': '/ops/entry',
  'whitelist/whitelist.htm': '/ops/whitelist',
  'goods/goods_list.htm': '/ops/goods',
  'redeem/redeemGoodsList.htm': '/ops/goods',
  'goodspec/goods_spec_list.htm': '/ops/spec',
  'goodsbrand/goods_brand_list.htm': '/ops/brand',
  'goodsbrand/goods_brand_list': '/ops/brand',
  'goodstype/goods_type_list.htm': '/ops/goods-type',
  'goodsclass/goods_class_list.htm': '/ops/goods-class',
  'album/album.htm': '/ops/album',
  'evaluate/list.htm': '/ops/goods-evaluate',
  '/evaluate/list.htm': '/ops/goods-evaluate',
  'consult/consultEdit.htm': '/ops/consult-config',
  // 数字化中心
  'testUserStats/testUserStatsPage.htm': '/digital/stats',
  'testUserPerformance/load.do': '/digital/test-plan',
  'labPerformance/labPerformancePag.htm': '/digital/lab-test-perf',
  'labPerformance/labPerformancePag.html': '/digital/lab-test-perf',
  'saleUserPerformance/load.do': '/digital/sale-plan',
  'labPerformanceSaleuser/labPerformancePag.htm': '/digital/lab-sale-perf',
  'labPerformanceSaleuser/labPerformancePag.html': '/digital/lab-sale-perf',
  // 库存管理
  'inventory/inventoryList.htm': '/inventory/list',
  'storeHouse/storeHouseList.htm': '/inventory/warehouses',
  'inIncome/incomeDetail.htm': '/inventory/income',
  'lab/labList.htm': '/inventory/labs',
  'expLog/logList.htm': '/inventory/device-booking',
  'inTreasury/inTreasuryList.htm': '/inventory/sample-orders',
  'samplestoreHouse/sampleStoreHouse.htm': '/inventory/sample-warehouses',
  'sampleremainstoreHouse/sampleStoreHouse.htm': '/inventory/sample-retain-warehouses',
  // 实验管理（主数据）
  'experimentManage/labManageList.htm': '/experiment/classes?type=1',
  'experimentManage/labTestSecClassList.htm': '/experiment/classes?type=2',
  'experimentManage/labTestClassList.htm': '/experiment/classes?type=3',
  'experimentProject/projectList.htm': '/experiment/projects',
  'experimentGoods/goodsList.htm': '/experiment/goods',
  'goodsbrand/experiment_goods_brand_list.htm': '/experiment/brands',
  'sampleAttributeManage/getListone.htm': '/experiment/sample-attrs?type=1',
  'sampleAttributeManage/getListtwo.htm': '/experiment/sample-attrs?type=2',
  'sampleAttributeManage/getListthree.htm': '/experiment/sample-attrs?type=3',
  // 实验管理（订单）
  'experimentChildOrder/listPage1.htm': '/experiment/grab-orders',
  'experimentOrder/orderList.htm': '/experiment/orders',
  'experimentChildOrder/listPage.htm': '/experiment/sub-orders',
  'experimentSubOrder/orderList.htm': '/experiment/subcontract-orders',
  'expSubPurchaseOrder/listPage.htm': '/experiment/subcontract-sub-orders',
  // 资金管理
  'funds/assetAccount.htm': '/fund/account',
  'funds/accountLog.htm': '/fund/management',
  'funds/account.htm': '/fund/settings',
  'funds/setUSExchangeRate.htm': '/fund/exchange-rate',
  'funds/accountList.htm': '/fund/account-list',
  'digitalManage/digitalManageCenter.htm': '/fund/digital-center',
  'companyPay/companyPayPag.htm': '/fund/company-pay',
  'userPay/userPayPag.htm': '/fund/personal-pay',
  'companyLoanPay/loanPayPag.htm': '/fund/company-loan',
  'projectPay/projectPayPag.htm': '/fund/project-pay',
}

export function mapLegacyMenuUrl(raw: string): string {
  const normalized = raw.replace(/^\/+/, '').split('?')[0]
  const withQuery = raw.replace(/^\/+/, '')
  if (MENU_ROUTE_MAP[withQuery]) return MENU_ROUTE_MAP[withQuery]
  if (MENU_ROUTE_MAP[normalized]) return MENU_ROUTE_MAP[normalized]
  if (normalized.includes('taxes_config')) return '/order-settings/tax-rate'
  if (normalized.includes('consumePaytype/payment') || normalized.endsWith('payment.htm')) {
    return '/order-settings/payment-method'
  }
  if (normalized.includes('set_evaluate_setting')) return '/order-settings/auto-evaluate'
  if (normalized.includes('billtype/bill')) {
    if (raw.includes('type=2')) return '/order-settings/incoming-invoice'
    return '/order-settings/outgoing-invoice'
  }
  if (normalized.includes('orderTypeList') || normalized.includes('orderType/orderType')) {
    return '/order-settings/order-type'
  }
  if (normalized.includes('InvoiceApply') || normalized.includes('invoiceApply')) {
    return '/invoice/apply'
  }
  if (normalized.includes('payLog/logList') || normalized.includes('payLog/')) {
    return '/payment/records'
  }
  if (normalized.includes('paymentapply')) return '/payment/application'
  if (normalized.includes('retestList') || normalized.includes('retestapplication')) {
    return '/orders/retest'
  }
  if (normalized.includes('sys/dept') || normalized.includes('dept/load')) {
    return '/system/depts'
  }
  if (normalized.includes('logs/list') || normalized.includes('/logs/')) {
    return '/system/ops-logs'
  }
  if (normalized.includes('sys/user/load')) {
    return '/system/users'
  }
  if (normalized.includes('sys/role') || normalized.includes('role/load')) {
    return '/system/roles'
  }
  if (normalized.includes('usercompany') || normalized.includes('userCompany')) {
    return '/member/enterprise'
  }
  if (normalized.includes('supplier/supplierList') || normalized.includes('supplierList')) {
    return '/system/companies'
  }
  if (normalized.includes('member/memberPage') || normalized.includes('memberPage.htm')) {
    return '/member/personal'
  }
  if (normalized.includes('applyVip') || (normalized.includes('applyVip/') && normalized.includes('ListPage'))) {
    return '/member/apply'
  }
  if (normalized.includes('set_integral') || normalized.includes('integral_convert_ratio') || normalized.includes('integral/set_')) {
    return '/member/integral'
  }
  if (normalized.includes('offlineRecharge') || normalized.includes('rechargeList.htm')) {
    return '/member/offline-recharge'
  }
  if (normalized.includes('sys/menu') || normalized.includes('menu/load')) {
    return '/system/menus'
  }
  if (normalized.includes('district/area') || normalized.includes('area.htm')) {
    return '/system/areas'
  }
  if (normalized.includes('sys/district') || normalized.includes('district/load')) {
    return '/system/districts'
  }
  if (normalized.includes('userType') || normalized.includes('user_type')) {
    return '/system/user-types'
  }
  if (normalized.includes('appUser') || (normalized.includes('ListPage.htm') && !normalized.includes('consult/') && !normalized.includes('applyVip'))) {
    return '/system/app-users'
  }
  if (normalized.includes('testaddress') || normalized.includes('addressList')) {
    return '/system/test-addresses'
  }
  if (normalized.includes('companyaccount') || normalized.includes('accountList')) {
    return '/system/company-accounts'
  }
  if (normalized.includes('caliOrder/list') || normalized.includes('caliOrder/todoJzlist') || normalized.includes('todoJzlist')) {
    return '/service-platform/service-apply'
  }
  if (normalized.includes('device_back_manage') || normalized.includes('apply/device_back')) {
    return '/service-platform/buyback'
  }
  if (normalized.includes('consult/ListPage') || normalized.includes('consult/list')) {
    return '/service-platform/consult'
  }
  if (normalized.includes('serviceSetting') || normalized.includes('consult/serviceSetting')) {
    return '/service-platform/consult-message'
  }
  if (normalized.includes('problemlistPage') || normalized.includes('problemlist')) {
    return '/service-platform/faq'
  }
  if (normalized.includes('suborderList') || normalized.includes('experimentSubOrder/suborder')) {
    return '/service-platform/evaluated-sub-orders'
  }
  if (normalized.includes('evaluatelist') || normalized.includes('evaluate_list_dpt')) {
    return '/service-platform/evaluated-orders'
  }
  // 实验管理（须先于通用 experimentOrder / goodsbrand / sampleAttribute 模糊匹配）
  if (normalized.includes('experimentManage/labManageList') || normalized.includes('labManageList.htm')) {
    return '/experiment/classes?type=1'
  }
  if (
    normalized.includes('experimentManage/labTestSecClassList') ||
    normalized.includes('labTestSecClassList')
  ) {
    return '/experiment/classes?type=2'
  }
  if (normalized.includes('experimentManage/labTestClassList') || normalized.includes('labTestClassList')) {
    return '/experiment/classes?type=3'
  }
  if (normalized.includes('experimentProject/projectList') || normalized.includes('experimentProject/')) {
    return '/experiment/projects'
  }
  if (normalized.includes('experimentGoods/goodsList') || normalized.includes('experimentGoods/')) {
    return '/experiment/goods'
  }
  if (
    normalized.includes('experiment_goods_brand_list') ||
    normalized.includes('goodsbrand/experiment_')
  ) {
    return '/experiment/brands'
  }
  if (normalized.includes('sampleAttributeManage/getListone') || normalized.includes('getListone.htm')) {
    return '/experiment/sample-attrs?type=1'
  }
  if (normalized.includes('sampleAttributeManage/getListtwo') || normalized.includes('getListtwo.htm')) {
    return '/experiment/sample-attrs?type=2'
  }
  if (
    normalized.includes('sampleAttributeManage/getListthree') ||
    normalized.includes('getListthree.htm')
  ) {
    return '/experiment/sample-attrs?type=3'
  }
  if (normalized.includes('experimentChildOrder/listPage1') || normalized.includes('listPage1.htm')) {
    return '/experiment/grab-orders'
  }
  if (
    normalized.includes('experimentChildOrder/listPage') ||
    (normalized.includes('experimentChildOrder/') && normalized.includes('listPage'))
  ) {
    return '/experiment/sub-orders'
  }
  if (normalized.includes('experimentOrder/orderList') || normalized.includes('experimentOrder/orderList.htm')) {
    return '/experiment/orders'
  }
  if (normalized.includes('experimentSubOrder/orderList')) {
    return '/experiment/subcontract-orders'
  }
  if (normalized.includes('expSubPurchaseOrder/listPage') || normalized.includes('expSubPurchaseOrder/')) {
    return '/experiment/subcontract-sub-orders'
  }
  if (normalized.includes('recordslistPage') || normalized.includes('records/recordslist')) {
    return '/service-platform/records'
  }
  if (normalized.includes('proveList') || normalized.includes('productOrder/prove')) {
    return '/service-platform/proposals'
  }
  if (normalized.includes('isshowCustomer') || normalized.includes('consult/isshow')) {
    return '/service-platform/customer-service'
  }
  if (normalized.includes('expOpenid') || normalized.includes('openidList')) {
    return '/service-platform/openid'
  }
  // 运营管理
  if (normalized.includes('advert_list')) return '/ops/advert'
  if (normalized.includes('adv_pos_list')) return '/ops/adv-pos'
  if (normalized.includes('banner/slideshow') || normalized.endsWith('slideshow.htm')) {
    return '/ops/banner-pc'
  }
  if (normalized.includes('banner/bannerList') || normalized.includes('bannerList.htm')) {
    return '/ops/banner-xcx'
  }
  if (normalized.includes('xcxfmslideshow')) return '/ops/banner-xcxfm'
  if (normalized.includes('set_device.htm') || normalized.includes('set_device_service')) {
    return '/ops/setting-device'
  }
  if (normalized.includes('set_product_test')) return '/ops/setting-product'
  if (normalized.includes('set_business_support')) return '/ops/setting-business'
  if (normalized.includes('set_rent_device')) return '/ops/setting-rent'
  if (normalized.includes('set_second_hand')) return '/ops/setting-secondhand'
  if (normalized.includes('redeemGoodsLogList') || normalized.includes('redeem/redeemGoodsLog')) {
    return '/ops/redeem'
  }
  if (normalized.includes('redeemGoodsList') || normalized.includes('redeem/redeemGoodsList')) {
    return '/ops/goods'
  }
  if (normalized.includes('entry/commentList') || normalized.includes('commentList.htm')) {
    return '/ops/comment'
  }
  if (normalized.includes('entry/entryList') || normalized.includes('entryList.htm')) {
    return '/ops/entry'
  }
  if (normalized.includes('whitelist/whitelist') || normalized.includes('whitelist.htm')) {
    return '/ops/whitelist'
  }
  if (normalized.includes('goods/goods_list') || normalized.includes('goods_list.htm')) {
    return '/ops/goods'
  }
  if (normalized.includes('goodspec/goods_spec_list') || normalized.includes('goods_spec_list')) {
    return '/ops/spec'
  }
  if (
    (normalized.includes('goodsbrand/goods_brand_list') || normalized.includes('goods_brand_list')) &&
    !normalized.includes('experiment_goods_brand')
  ) {
    return '/ops/brand'
  }
  if (normalized.includes('goodstype/goods_type_list') || normalized.includes('goods_type_list')) {
    return '/ops/goods-type'
  }
  if (normalized.includes('goodsclass/goods_class_list') || normalized.includes('goods_class_list')) {
    return '/ops/goods-class'
  }
  if (normalized.includes('album/album')) return '/ops/album'
  if (normalized.includes('evaluate/list')) return '/ops/goods-evaluate'
  if (normalized.includes('consult/consultEdit') || normalized.includes('consultEdit.htm')) {
    return '/ops/consult-config'
  }
  // 数字化中心
  if (normalized.includes('testUserStats') || normalized.includes('testUserStatsPage')) {
    return '/digital/stats'
  }
  if (normalized.includes('testUserPerformance')) {
    return '/digital/test-plan'
  }
  if (normalized.includes('labPerformanceSaleuser') || normalized.includes('labPerformanceSale')) {
    return '/digital/lab-sale-perf'
  }
  if (normalized.includes('labPerformance')) {
    return '/digital/lab-test-perf'
  }
  if (normalized.includes('saleUserPerformance')) {
    return '/digital/sale-plan'
  }
  // 库存管理
  if (normalized.includes('inventory/inventoryList') || normalized.includes('inventoryList.htm')) {
    return '/inventory/list'
  }
  if (normalized.includes('storeHouse/storeHouseList') || normalized.includes('storeHouseList')) {
    return '/inventory/warehouses'
  }
  if (normalized.includes('inIncome/incomeDetail') || normalized.includes('incomeDetail.htm')) {
    return '/inventory/income'
  }
  if (normalized.includes('lab/labList') || normalized.includes('labList.htm')) {
    return '/inventory/labs'
  }
  if (normalized.includes('expLog/logList') || normalized.includes('expLog/')) {
    return '/inventory/device-booking'
  }
  if (normalized.includes('inTreasury/inTreasuryList') || normalized.includes('inTreasuryList')) {
    return '/inventory/sample-orders'
  }
  if (normalized.includes('sampleremainstoreHouse') || normalized.includes('sampleRemain')) {
    return '/inventory/sample-retain-warehouses'
  }
  if (normalized.includes('samplestoreHouse') || normalized.includes('sampleStoreHouse')) {
    return '/inventory/sample-warehouses'
  }
  // 资金管理
  if (normalized.includes('funds/assetAccount') || normalized.includes('assetAccount.htm')) {
    return '/fund/account'
  }
  if (normalized.includes('funds/accountLog') || normalized.includes('accountLog.htm')) {
    return '/fund/management'
  }
  if (normalized.includes('funds/setUSExchangeRate') || normalized.includes('setUSExchangeRate')) {
    return '/fund/exchange-rate'
  }
  if (normalized.includes('funds/accountList') || normalized.includes('accountList.htm')) {
    return '/fund/account-list'
  }
  if (
    (normalized.includes('funds/account.htm') || normalized.endsWith('funds/account')) &&
    !normalized.includes('accountLog') &&
    !normalized.includes('accountList') &&
    !normalized.includes('assetAccount')
  ) {
    return '/fund/settings'
  }
  if (normalized.includes('digitalManageCenter') || normalized.includes('digitalManage/digital')) {
    return '/fund/digital-center'
  }
  if (normalized.includes('companyPay/companyPayPag') || normalized.includes('companyPayPag')) {
    return '/fund/company-pay'
  }
  if (normalized.includes('userPay/userPayPag') || normalized.includes('userPayPag')) {
    return '/fund/personal-pay'
  }
  if (normalized.includes('companyLoanPay') || normalized.includes('loanPayPag')) {
    return '/fund/company-loan'
  }
  if (normalized.includes('projectPay/projectPayPag') || normalized.includes('projectPayPag')) {
    return '/fund/project-pay'
  }
  return ''
}

export function resolveMenuPath(item: AdminMenuItem): string {
  const raw = (item.menu_url || '').trim()
  if (!raw || raw.startsWith('http')) return ''

  if (raw.startsWith('#')) return raw.slice(1) || '/dashboard'

  const legacy = mapLegacyMenuUrl(raw)
  if (legacy) return legacy

  const id = String(item.id || '')
  if (!id) return ''
  return `/legacy/pending/${id}`
}

export function isMenuReady(item: AdminMenuItem): boolean {
  const path = resolveMenuPath(item)
  return !!path && !path.startsWith('/legacy/pending/')
}

export function indexPendingMenus(
  items: AdminMenuItem[],
  out: Record<string, { title: string; url: string }> = {}
) {
  for (const item of items) {
    if (item.id != null) {
      out[String(item.id)] = {
        title: item.menu_name || '未命名菜单',
        url: item.menu_url || '',
      }
    }
    if (item.children?.length) {
      indexPendingMenus(item.children, out)
    }
  }
  return out
}
