from django.urls import path

from apps.admin_settings import views

urlpatterns = [
    path("taxesConfig/getTaxesList.ajax", views.taxes_list),
    path("taxesConfig/submitTases.ajax", views.taxes_submit),
    path("taxesConfig/getTasesById.ajax", views.taxes_get_by_id),
    path("taxesConfig/updateTases.ajax", views.taxes_update),
    path("taxesConfig/updateStatus.ajax", views.taxes_update_status),
    path("taxesConfig/deleteById.ajax", views.taxes_delete),
    path("taxesConfig/getAllConfigs.ajax", views.taxes_get_all),
    path("consumePaytype/getPaymentList.ajax", views.paytype_list),
    path("consumePaytype/getallptype.ajax", views.paytype_get_all),
    path("consumePaytype/submitPayment.ajax", views.paytype_submit),
    path("consumePaytype/updateDelStatus.ajax", views.paytype_update_status),
    path("consumePaytype/del.ajax", views.paytype_delete),
    path("billtype/getBillByType.ajax", views.billtype_list),
    path("billtype/allBill.ajax", views.billtype_all_bill),
    path("billtype/submitBillType.ajax", views.billtype_submit),
    path("billtype/getBillTypeById.ajax", views.billtype_get_by_id),
    path("billtype/updateBillType.ajax", views.billtype_update),
    path("billtype/updateStatus.ajax", views.billtype_update_status),
    path("billtype/del.ajax", views.billtype_delete),
    path("orderType/list.ajax", views.order_type_list),
    path("orderType/submitOrderType.ajax", views.order_type_submit),
    path("orderType/updateOrderType.ajax", views.order_type_update),
    path("orderType/del.ajax", views.order_type_delete),
    path("orderType/queryOrderType.ajax", views.order_type_query_all),
    path("orderType/queryAllOrderType.ajax", views.order_type_query_tables),
    path("edit/evaluateSetting.ajax", views.evaluate_setting_get),
    path("edit/evaluateSave.ajax", views.evaluate_setting_save),
]
