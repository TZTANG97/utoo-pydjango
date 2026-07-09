from django.urls import path

from apps.orders import views_consult_check

urlpatterns = [
    path("isServiceConsult.ajax", views_consult_check.is_service_consult_view),
]
