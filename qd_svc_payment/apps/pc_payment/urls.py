from django.urls import path

from apps.pc_payment import views_asset, views_pay

urlpatterns = [
    path("getIntegral.ajax", views_asset.get_integral),
    path("getIntegralConvertRatio.ajax", views_asset.get_integral_convert_ratio),
    path("center/getAccount.ajax", views_asset.get_account),
    path("center/getIntegralList.ajax", views_asset.get_integral_list),
    path("amountPay.ajax", views_pay.amount_pay),
    path("prePay.ajax", views_pay.pre_pay),
    path("preAmountPay.ajax", views_pay.pre_amount_pay),
    path("rechargePrePay.ajax", views_pay.recharge_pre_pay),
    path("rechargeContinuePay.ajax", views_pay.recharge_continue_pay),
    path("addRecharge.ajax", views_pay.add_recharge_view),
    path("queryPayStatus.ajax", views_pay.query_pay_status),
    path("queryPayStatusByOrder.ajax", views_pay.query_pay_status_by_order),
    path("pay.ajax", views_pay.wechat_pay_notify),
    path("rechargePay.ajax", views_pay.wechat_recharge_notify),
    path("amountPayBack.ajax", views_pay.wechat_amount_pay_back),
]
