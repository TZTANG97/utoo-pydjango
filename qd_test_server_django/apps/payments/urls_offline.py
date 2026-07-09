from django.urls import path

from apps.payments import views_compat

urlpatterns = [
    path("rechargeDetail.ajax", views_compat.recharge_detail_view),
]
