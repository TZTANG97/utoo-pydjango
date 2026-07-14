from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("", core_views.root),
    path("health", core_views.health),
    path("health/", core_views.health),
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.admin_system.urls")),
    path("api/", include("apps.admin_member.urls")),
    path("api/", include("apps.admin_ops.urls")),
    path("api/", include("apps.admin_service.urls")),
    path("api/", include("apps.admin_settings.urls")),
    path("api/entry/", include("apps.entry.urls")),
    path("api/invoice/", include("apps.invoices.urls")),
    path("api/pc/", include("apps.pc_invoice.urls")),
]
