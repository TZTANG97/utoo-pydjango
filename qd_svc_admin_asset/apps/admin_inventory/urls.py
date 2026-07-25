from django.urls import path

from apps.admin_inventory.views import inventory as inv
from apps.admin_inventory.views import storehouse as sh

urlpatterns = [
    # 仓库管理
    path("storeHouse/list.ajax", sh.storehouse_list),
    path("storeHouse/get.ajax", sh.storehouse_get),
    path("storeHouse/submitStoreHouse.ajax", sh.storehouse_save),
    path("storeHouse/updateStoreHouse.ajax", sh.storehouse_save),
    path("storeHouse/updateStatus.ajax", sh.storehouse_status),
    path("storeHouse/del.ajax", sh.storehouse_del),
    # 样品仓库 type=1
    path("samplestoreHouse/list.ajax", sh.sample_storehouse_list),
    path("samplestoreHouse/get.ajax", sh.sample_storehouse_get),
    path("samplestoreHouse/submitStoreHouse.ajax", sh.sample_storehouse_save),
    path("samplestoreHouse/updateStoreHouse.ajax", sh.sample_storehouse_save),
    path("samplestoreHouse/updateStatus.ajax", sh.sample_storehouse_status),
    path("samplestoreHouse/del.ajax", sh.sample_storehouse_del),
    # 样品留存仓库 type=2
    path("sampleremainstoreHouse/list.ajax", sh.sample_remain_storehouse_list),
    path("sampleremainstoreHouse/get.ajax", sh.sample_storehouse_get),
    path("sampleremainstoreHouse/submitStoreHouse.ajax", sh.sample_remain_storehouse_save),
    path("sampleremainstoreHouse/updateStoreHouse.ajax", sh.sample_remain_storehouse_save),
    path("sampleremainstoreHouse/updateStatus.ajax", sh.sample_storehouse_status),
    path("sampleremainstoreHouse/del.ajax", sh.sample_storehouse_del),
    # 库存管理
    path("inventory/list.ajax", inv.inventory_list),
    path("inventory/inventoryList.ajax", inv.inventory_list),
    path("inventory/children.ajax", inv.inventory_children),
    path("inventory/summary.ajax", inv.inventory_summary),
    path("inventory/get.ajax", inv.inventory_get),
    path("inventory/update.ajax", inv.inventory_update),
    path("inventory/updateInventory.ajax", inv.inventory_update),
    # 实验室
    path("lab/list.ajax", inv.lab_list),
    path("lab/options.ajax", inv.lab_options),
    path("lab/selLineList.ajax", inv.sel_line_list),
    path("lab/get.ajax", inv.lab_get),
    path("lab/save.ajax", inv.lab_save),
    path("lab/updateStatus.ajax", inv.lab_status),
    path("lab/del.ajax", inv.lab_del),
    # 样品管理单
    path("inTreasury/list.ajax", inv.sample_order_list),
    path("inTreasury/options.ajax", inv.sample_order_options),
    path("samplestoreHouse/queryStore.ajax", inv.sample_order_options),
    path("samplestoreHouse/queryListByStoreId.ajax", inv.sample_store_positions),
    path("inTreasury/detail.ajax", inv.sample_order_detail),
    path("inTreasury/export.ajax", inv.sample_order_export),
    # 设备预约
    path("expLog/list.ajax", inv.device_booking_list),
    path("expLog/logDetail.ajax", inv.device_booking_detail),
    path("expLog/options.ajax", inv.device_booking_options),
    # 内部收益明细
    path("inIncome/overview.ajax", inv.income_overview),
    path("inIncome/costList.ajax", inv.income_list),
    path("inIncome/queryTzblmx.ajax", inv.income_ratio),
    path("inIncome/queryCzUsers.ajax", inv.income_invest_users),
    path("inIncome/queryUsers.ajax", inv.income_user_options),
    path("inIncome/submitInvestFreez.ajax", inv.income_submit_invest),
    path("inIncome/submitDisInvest.ajax", inv.income_submit_disinvest),
    path("inIncome/submitOtherPay.ajax", inv.income_submit_tax),
]
