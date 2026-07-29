"""/api/wx/* 小程序兼容：登录 + pc 别名(Ajax) + 缺口 stub。"""
from django.urls import path

from apps.pc_compat import (
    views_asset,
    views_auth,
    views_catalog,
    views_consult,
    views_evaluate,
    views_invoice,
    views_order,
    views_pay,
    views_profile,
)
from apps.wx_mp import views_login, views_order_count, views_profile as vp
from apps.wx_mp import views_scan
from apps.wx_mp.ajax_wrap import wrap_as_ajax

# (wx 路径, pc 视图, 转发用的 /api/pc 路径)
_pc_alias = [
    ("addOrUpdateUserData.ajax", views_profile.add_or_update_user_data, "/api/pc/addOrUpdateUserData.ajax"),
    ("addOrUpdateUserCompanyData.ajax", views_profile.add_or_update_user_company_data, "/api/pc/addOrUpdateUserCompanyData.ajax"),
    ("serviceConsultAdd.ajax", views_consult.service_consult_add, "/api/pc/serviceConsultAdd.ajax"),
    ("expMakeList.ajax", views_consult.exp_make_list, "/api/pc/expMakeList.ajax"),
    ("myExperimentOrderList.ajax", views_order.my_experiment_order_list, "/api/pc/myExperimentOrderList.ajax"),
    ("amountPay.ajax", views_pay.amount_pay, "/api/pc/amountPay.ajax"),
    ("prePay.ajax", views_pay.pre_pay, "/api/pc/prePay.ajax"),
    ("preAmountPay.ajax", views_pay.pre_amount_pay, "/api/pc/preAmountPay.ajax"),
    ("rechargePrePay.ajax", views_pay.recharge_pre_pay, "/api/pc/rechargePrePay.ajax"),
    ("addRecharge.ajax", views_pay.add_recharge_view, "/api/pc/addRecharge.ajax"),
    ("addCash.ajax", views_pay.add_cash_view, "/api/pc/addCash.ajax"),
    ("pay.ajax", views_pay.wechat_pay_notify, "/api/pc/pay.ajax"),
    ("center/getAccount.ajax", views_asset.get_account, "/api/pc/center/getAccount.ajax"),
    ("center/getIntegralList.ajax", views_asset.get_integral_list, "/api/pc/center/getIntegralList.ajax"),
    ("center/getInvoiceInfo.ajax", views_invoice.get_invoice_info, "/api/pc/center/getInvoiceInfo.ajax"),
    ("center/applyInvoice.ajax", views_invoice.apply_invoice, "/api/pc/center/applyInvoice.ajax"),
    ("getinvoiceInfo.ajax", views_invoice.get_invoice_info_list, "/api/pc/getinvoiceInfo.ajax"),
    ("insertinvoiceInfo.ajax", views_invoice.insert_invoice_info, "/api/pc/insertinvoiceInfo.ajax"),
    ("updateinvoiceInfo.ajax", views_invoice.update_invoice_info, "/api/pc/updateinvoiceInfo.ajax"),
    ("delinvoiceInfo.ajax", views_invoice.del_invoice_info, "/api/pc/delinvoiceInfo.ajax"),
    ("addInvoiceInfo.ajax", views_invoice.add_invoice_info_legacy, "/api/pc/addInvoiceInfo.ajax"),
    ("setPassword.ajax", views_profile.set_password, "/api/pc/setPassword.ajax"),
    ("telCodeVerify.ajax", views_auth.tel_code_verify, "/api/pc/telCodeVerify.ajax"),
    ("getVerifyCodeFindPw.ajax", views_auth.get_verify_code_find_pw, "/api/pc/getVerifyCodeFindPw.ajax"),
    ("writeevaluate.ajax", views_evaluate.write_evaluate, "/api/pc/writeevaluate.ajax"),
    ("bannerList.ajax", views_catalog.banner_list, "/api/pc/bannerList.ajax"),
    ("selFirAndSecClassList.ajax", views_catalog.sel_fir_and_sec_class_list, "/api/pc/selFirAndSecClassList.ajax"),
]

urlpatterns = [
    path("getVerifyCodeLogin.ajax", views_login.get_verify_code_login),
    path("userLoginToken.ajax", views_login.user_login_token),
    path("phoneCodeLogin.ajax", views_login.phone_code_login),
    path("phoneOneLogin.ajax", views_login.phone_one_login),
    path("phoneOneLoginTZ.ajax", views_login.phone_one_login_tz),
    path("getIdentifyData.ajax", vp.get_identify_data),
    path("clearBindData.ajax", vp.clear_bind_data),
    path("myInfo.ajax", vp.my_info),
    path("getbindstatus.ajax", vp.get_bind_status),
    path("checkLoginName.ajax", vp.check_login_name),
    path("updateNickName.ajax", vp.update_nick_name),
    path("bindaccount.ajax", vp.bind_account_stub),
    path("bindaccountTZ.ajax", vp.bind_account_stub),
    path("securebind.ajax", vp.secure_bind_stub),
    path("getUserInfo.ajax", vp.get_user_info),
    path("userInfoAdd.ajax", vp.user_info_add),
    path("ticketIsExist.ajax", vp.ticket_is_exist),
    path("TuZhebannerList.ajax", vp.tuzhe_banner_list),
    path("selFirAndSecClassListTuZhe.ajax", vp.sel_fir_and_sec_class_list_tuzhe),
    path("getOrderCount.ajax", views_order_count.get_order_count),
    # 扫码（优先于 stub）
    path("scanCodeOperate.ajax", views_scan.scan_code_operate),
    path("isFlag.ajax", views_scan.is_flag),
]

urlpatterns += [
    path(name, wrap_as_ajax(view, pc_path=pc_path)) for name, view, pc_path in _pc_alias
]

_STUBS = [
    "getAuditOrderList.ajax",
    "getAuditOrderList1.ajax",
    "getLog.ajax",
    "selBankList.ajax",
    "selSecondClassList.ajax",
    "signInIntegral.ajax",
]

urlpatterns += [path(name, vp.not_implemented) for name in _STUBS]
