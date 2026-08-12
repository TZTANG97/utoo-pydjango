from django.urls import path

from apps.orders import views_mp_actions

urlpatterns = [
    path("addBillData.ajax", views_mp_actions.add_bill_data, name="bill-addBillData"),
    path("amountPay.ajax", views_mp_actions.amount_pay, name="bill-amountPay"),
]
