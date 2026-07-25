from django.urls import path

from apps.orders import views_child
from apps.orders import views_list_dpt
from apps.orders import views_mp_actions
from apps.orders import views_scan

urlpatterns = [
    path("orderdetail.ajax", views_child.purchase_order_detail, name="child-orderdetail"),
    path(
        "getOrdersBySaleOrderId.ajax",
        views_child.orders_by_sale_order_id,
        name="child-getOrdersBySaleOrderId",
    ),
    path("sureOk.ajax", views_child.sure_ok, name="child-sureOk"),
    path("createOrderPage.ajax", views_child.create_order_page, name="child-createOrderPage"),
    path(
        "createOrderPagexcx.ajax",
        views_child.create_order_page_xcx,
        name="child-createOrderPagexcx",
    ),
    path(
        "list_dpt.ajax",
        views_list_dpt.experiment_child_order_list_dpt,
        name="child-list_dpt",
    ),
    path(
        "list_dpt1.ajax",
        views_list_dpt.experiment_child_order_list_dpt,
        name="child-list_dpt1",
    ),
    path(
        "cancelOperate.ajax",
        views_mp_actions.child_cancel_operate,
        name="child-cancelOperate",
    ),
    path(
        "submitAuditExp.ajax",
        views_mp_actions.child_submit_audit,
        name="child-submitAuditExp",
    ),
    path(
        "updateStatus.ajax",
        views_mp_actions.child_update_status,
        name="child-updateStatus",
    ),
    path(
        "auditOrder.ajax",
        views_mp_actions.child_audit_order,
        name="child-auditOrder",
    ),
    path(
        "selGoodsList.ajax",
        views_mp_actions.child_sel_goods_list,
        name="child-selGoodsList",
    ),
    path(
        "addVideoInfo.ajax",
        views_mp_actions.child_add_video_info,
        name="child-addVideoInfo",
    ),
    path(
        "editPagexcx.ajax",
        views_mp_actions.child_edit_page_xcx,
        name="child-editPagexcx",
    ),
    path(
        "editPage.ajax",
        views_mp_actions.child_edit_page,
        name="child-editPage",
    ),
    path(
        "addOrderData.ajax",
        views_mp_actions.child_add_order_data,
        name="child-addOrderData",
    ),
    path(
        "pay.ajax",
        views_mp_actions.child_pay,
        name="child-pay",
    ),
    path(
        "updateOrderStatus.ajax",
        views_mp_actions.child_update_order_status,
        name="child-updateOrderStatus",
    ),
    path(
        "confirmsave.ajax",
        views_scan.confirm_save,
        name="child-confirmsave",
    ),
]
