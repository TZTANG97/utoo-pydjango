from django.urls import path

from apps.orders import views_child

urlpatterns = [
    path("orderdetail.ajax", views_child.purchase_order_detail, name="child-orderdetail"),
    path(
        "getOrdersBySaleOrderId.ajax",
        views_child.orders_by_sale_order_id,
        name="child-getOrdersBySaleOrderId",
    ),
    path("sureOk.ajax", views_child.sure_ok, name="child-sureOk"),
]
