from django.urls import include, path
from django.http import JsonResponse

urlpatterns = [
    path("health", lambda _request: JsonResponse({"status": "ok", "service": "utoo_biz"})),
    path("api/v1/", include("apps.utoo_experiment.urls_v1")),
    path("api/", include("apps.utoo_experiment.urls_legacy")),
    path("api/", include("apps.utoo_consumer.urls_legacy")),
    path("api/", include("apps.utoo_admin.urls_legacy")),
]
