from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("", core_views.root),
    path("health", core_views.health),
    path("health/", core_views.health),
    path("api/", include("apps.core.urls")),
    path("api/experimentOrder/", include("apps.orders.urls")),
    path("api/experimentChildOrder/", include("apps.orders.child_urls")),
    path("api/ordersampleinfomation/", include("apps.orders.sample_urls")),
    path("api/sampleAttributeManage/", include("apps.orders.sample_attr_urls")),
    path("api/retestapplication/", include("apps.orders.retest_urls")),
    path("api/pc/", include("apps.pc_order.urls")),
]
