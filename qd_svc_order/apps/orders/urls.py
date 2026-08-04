from django.urls import path

from apps.admin_experiment import views as admin_exp_views
from apps.orders import views
from apps.orders import views_list_dpt
from apps.orders import views_mp_actions

urlpatterns = [
    path("list_dpt.ajax", views_list_dpt.experiment_order_list_dpt, name="experiment-list_dpt"),
    path("uploadChildData.ajax", views.upload_child_data, name="experiment-uploadChildData"),
    path("loadaccessory.ajax", views.load_accessory, name="experiment-loadaccessory"),
    path("printpdf.ajax", views.print_pdf, name="experiment-printpdf"),
    path("orderdetail.ajax", views.order_detail, name="experiment-orderdetail"),
    path(
        "orderdetaildptxcx.ajax",
        views_list_dpt.experiment_order_detail_dpt_xcx,
        name="experiment-orderdetaildptxcx",
    ),
    path(
        "getChildFormByIdExp.ajax",
        views.get_child_form_by_id_exp,
        name="experiment-getChildFormByIdExp",
    ),
    path(
        "getChildFormByIdExp_dpt.ajax",
        views_list_dpt.get_child_form_by_id_exp_dpt,
        name="experiment-getChildFormByIdExp_dpt",
    ),
    path(
        "addRelevanceOrder_dpt.ajax",
        views_list_dpt.add_relevance_order_dpt,
        name="experiment-addRelevanceOrder_dpt",
    ),
    path(
        "geranateYydForm.ajax",
        views_list_dpt.geranate_yyd_form,
        name="experiment-geranateYydForm",
    ),
    path(
        "submitExpOrder.ajax",
        admin_exp_views.order_submit_exp,
        name="experiment-submitExpOrder",
    ),
    path(
        "customeOperateCancel.ajax",
        views_mp_actions.custome_operate_cancel,
        name="experiment-customeOperateCancel",
    ),
    path(
        "submitAuditExp.ajax",
        views_mp_actions.submit_audit_exp,
        name="experiment-submitAuditExp",
    ),
    path(
        "updateStatus.ajax",
        views_mp_actions.update_status_withdraw,
        name="experiment-updateStatus",
    ),
    path(
        "auditOrder.ajax",
        views_mp_actions.audit_order_mp,
        name="experiment-auditOrder",
    ),
    path(
        "costSettleSure.ajax",
        views_mp_actions.cost_settle_sure,
        name="experiment-costSettleSure",
    ),
    path(
        "updateShareRatio.ajax",
        views_mp_actions.update_share_ratio_mp,
        name="experiment-updateShareRatio",
    ),
]
