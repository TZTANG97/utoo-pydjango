from django.urls import path

from apps.orders import views_list_dpt
from apps.orders import views_mp_actions

urlpatterns = [
    path("list_dpt.ajax", views_list_dpt.experiment_sub_order_list_dpt, name="experiment-sub-list_dpt"),
    path(
        "getChildFormByIdExp.ajax",
        views_list_dpt.get_child_form_by_id_exp_sub,
        name="experiment-sub-getChildFormByIdExp",
    ),
    path(
        "orderdetail.ajax",
        views_mp_actions.sub_order_detail,
        name="experiment-sub-orderdetail",
    ),
    path(
        "customeOperateCancel.ajax",
        views_mp_actions.custome_operate_cancel,
        name="experiment-sub-customeOperateCancel",
    ),
    path(
        "submitAuditExp.ajax",
        views_mp_actions.submit_audit_exp,
        name="experiment-sub-submitAuditExp",
    ),
    path(
        "updateStatus.ajax",
        views_mp_actions.update_status_withdraw,
        name="experiment-sub-updateStatus",
    ),
    path(
        "auditOrder.ajax",
        views_mp_actions.audit_order_mp,
        name="experiment-sub-auditOrder",
    ),
    path(
        "costSettleSure.ajax",
        views_mp_actions.cost_settle_sure,
        name="experiment-sub-costSettleSure",
    ),
    path(
        "updateShareRatio.ajax",
        views_mp_actions.update_share_ratio_mp,
        name="experiment-sub-updateShareRatio",
    ),
    path(
        "editPage.ajax",
        views_mp_actions.sub_edit_page,
        name="experiment-sub-editPage",
    ),
    path(
        "getOrderStatus.ajax",
        views_mp_actions.sub_get_order_status,
        name="experiment-sub-getOrderStatus",
    ),
]
