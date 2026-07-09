from django.urls import path

from apps.payments import views_compat

urlpatterns = [
    path("userredeemloglist.ajax", views_compat.user_redeem_log_list_view),
    path("redeemGoodsLogDetail.ajax", views_compat.redeem_goods_log_detail_view),
]
