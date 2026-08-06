from django.urls import path

from apps.admin_member.views import apply_vip as apply_views
from apps.admin_member.views import company_detail as company_detail_views
from apps.admin_member.views import integral as integral_views
from apps.admin_member.views import member as member_views
from apps.admin_member.views import offline_recharge as recharge_views

urlpatterns = [
    # 个人会员
    path("member/memberList.ajax", member_views.member_list),
    path("member/getUserByUserId.ajax", member_views.member_detail),
    path("member/addMember.ajax", member_views.member_add),
    path("member/editMember.ajax", member_views.member_edit),
    path("member/addLinkUser.ajax", member_views.member_add),
    path("member/editLinkUser.ajax", member_views.member_edit),
    path("member/updateStatus.ajax", member_views.member_update_status),
    path("member/bindUser.ajax", member_views.member_bind),
    path("member/validUserMobileUtoo.ajax", member_views.valid_mobile),
    path("member/loadCustomerNames.ajax", member_views.load_customer_names),
    path("member/loadCustomerNamesExp.ajax", member_views.load_customer_names_exp),
    path("member/queryAllCompanykh.ajax", member_views.query_all_company_kh),
    path("member/getUserListByComId.ajax", company_detail_views.contact_list_by_company),
    path("member/queryProCityCo.ajax", company_detail_views.query_pro_city_co),
    # 企业会员明细 Tab
    path("companyinvoicelog/invoiceList.ajax", company_detail_views.invoice_list),
    path("payLog/list0909.ajax", company_detail_views.pay_list_0909),
    path("payLog/list910.ajax", company_detail_views.pay_list_910),
    path("payLog/qklist0909.ajax", company_detail_views.arrears_list_0909),
    # 个人会员明细 Tab
    path("userinvoicelog/invoiceList.ajax", company_detail_views.user_invoice_list),
    path("payLog/list828.ajax", company_detail_views.pay_list_828),
    path("payLog/list.ajax", company_detail_views.pay_list),
    path("payLog/qklist.ajax", company_detail_views.arrears_list),
    # 会员申请
    path("applyVip/list.ajax", apply_views.apply_list),
    path("applyVip/detail.ajax", apply_views.apply_detail),
    path("applyVip/update.ajax", apply_views.apply_update),
    # 积分设置
    path("integral/setting_get.ajax", integral_views.integral_get),
    path("integral/setting_save.ajax", integral_views.expire_save),
    path("integral/integral_convert_ratio_save.ajax", integral_views.ratio_save),
    # 线下充值
    path("offlineRecharge/offRechargeList.ajax", recharge_views.recharge_list),
    path("offlineRecharge/rechargeDetail.ajax", recharge_views.recharge_detail),
    path("offlineRecharge/userList.ajax", recharge_views.user_picker),
    path("offlineRecharge/recharge_add.ajax", recharge_views.recharge_add),
]
