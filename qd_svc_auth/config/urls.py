from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("", core_views.root),
    path("health", core_views.health),
    path("health/", core_views.health),
    path("api/", include("apps.core.urls")),
    path("api/auth/", include("apps.auth_domain.urls")),
]
