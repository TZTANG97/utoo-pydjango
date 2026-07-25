from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("", core_views.root),
    path("health", core_views.health),
    path("health/", core_views.health),
    path("api/", include("apps.core.urls")),
    path("api/experimentOrder/", include("apps.orders.urls")),
    path("api/experimentSubOrder/", include("apps.orders.sub_urls")),
    path("api/experimentChildOrder/", include("apps.orders.child_urls")),
    # 小程序分包子订单别名（与 experimentChildOrder 同源）
    path("api/expSubPurchaseOrder/", include("apps.orders.child_urls")),
    path("api/saleOrder/", include("apps.orders.sale_urls")),
    path("api/bill/", include("apps.orders.bill_urls")),
    path("api/eveluateCompany/", include("apps.orders.eveluate_urls")),
    path("api/wx/", include("apps.orders.wx_scan_urls")),
    path("api/ordersampleinfomation/", include("apps.orders.sample_urls")),
    path("api/sampleAttributeManage/", include("apps.orders.sample_attr_urls")),
    path("api/retestapplication/", include("apps.orders.retest_urls")),
    path("api/pc/", include("apps.pc_order.urls")),
    path("api/", include("apps.admin_experiment.urls")),
    path("api/", include("apps.admin_experiment.mp_catalog_urls")),
]
