from django.urls import path

from apps.admin_service.views import apply as apply_views
from apps.admin_service.views import cali_order as cali_views
from apps.admin_service.views import consult as consult_views
from apps.admin_service.views import evaluate_order as evaluate_views
from apps.admin_service.views import faq as faq_views
from apps.admin_service.views import openid as openid_views
from apps.admin_service.views import proposal as proposal_views
from apps.admin_service.views import records as records_views

urlpatterns = [
    # Buyback
    path("apply/list.ajax", apply_views.buyback_list),
    path("apply/update.ajax", apply_views.buyback_update),
    # Consult
    path("consult/list.ajax", consult_views.consult_list),
    path("consult/consultDetail.ajax", consult_views.consult_detail),
    path("consult/cancelConsult.ajax", consult_views.cancel_consult),
    path("consult/settingGet.ajax", consult_views.setting_get),
    path("consult/settingSave.ajax", consult_views.setting_save),
    path("consult/isshowGet.ajax", consult_views.isshow_get),
    path("consult/isshowSave.ajax", consult_views.isshow_save),
    # FAQ & communication records
    path("records/problemlistPage.ajax", faq_views.problem_list),
    path("records/submitproblem.ajax", faq_views.submit_problem),
    path("records/editproblem.ajax", faq_views.edit_problem),
    path("records/deleteproblem.ajax", faq_views.delete_problem),
    path("records/recordslistPage.ajax", records_views.records_list),
    path("records/recordsDetail.ajax", records_views.records_detail),
    path("records/deleterecords.ajax", records_views.records_delete),
    # Evaluated orders
    path("experimentOrder/evaluate_list_dpt.ajax", evaluate_views.evaluate_list_dpt),
    path("experimentSubOrder/sublist_dpt.ajax", evaluate_views.sublist_dpt),
    # Proposals
    path("productOrder/prove_list.ajax", proposal_views.prove_list),
    path("productOrder/proveDetail.ajax", proposal_views.prove_detail),
    path("productOrder/updateProposalImprove.ajax", proposal_views.update_proposal_improve),
    # OpenID
    path("expOpenid/openidList.ajax", openid_views.openid_list),
    path("expOpenid/submitOpenid.ajax", openid_views.submit_openid),
    path("expOpenid/del.ajax", openid_views.openid_delete),
    path("expOpenid/updateStatus.ajax", openid_views.update_status),
    # Service apply (caliOrder)
    path("caliOrder/list.ajax", cali_views.service_apply_list),
    path("caliOrder/todoList.ajax", cali_views.todo_list),
    path("caliOrder/update.ajax", cali_views.service_apply_update),
]
