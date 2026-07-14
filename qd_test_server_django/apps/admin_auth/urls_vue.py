from django.urls import path

from apps.admin_auth import views, views_billing

urlpatterns = [
    path("userLogin.ajax", views.user_login, name="admin-user-login"),
    path("getEncryption.ajax", views.get_encryption, name="admin-get-encryption"),
    path("main.ajax", views.main, name="admin-main"),
    path("usercenter.ajax", views.usercenter, name="admin-usercenter"),
    path("welcome.ajax", views.welcome, name="admin-welcome"),
    # 开票收款订单管理
    path("invoice/listPage.ajax", views_billing.invoice_list_page, name="admin-invoice-list"),
    path("invoice/invoiceDetail.ajax", views_billing.invoice_detail, name="admin-invoice-detail"),
    path("invoice/bohuiInvoice.ajax", views_billing.invoice_reject, name="admin-invoice-reject"),
    path("payLog/payList.ajax", views_billing.pay_log_list, name="admin-pay-log-list"),
    path("paymentapply/applylist.ajax", views_billing.payment_apply_list, name="admin-payment-apply-list"),
    path("paymentapply/applyDetail.ajax", views_billing.payment_apply_detail, name="admin-payment-apply-detail"),
    path("bill/agreepayment.ajax", views_billing.payment_apply_agree, name="admin-payment-apply-agree"),
    path("bill/refusepayment.ajax", views_billing.payment_apply_refuse, name="admin-payment-apply-refuse"),
    path("retestapplication/list.ajax", views_billing.retest_list, name="admin-retest-list"),
    path("retestapplication/retestDetail.ajax", views_billing.retest_detail, name="admin-retest-detail"),
    path("retestapplication/agreeretestapplication.ajax", views_billing.retest_agree, name="admin-retest-agree"),
    path("retestapplication/refusetestapplication.ajax", views_billing.retest_refuse, name="admin-retest-refuse"),
]
