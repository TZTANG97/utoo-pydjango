from django.urls import path

from apps.payments import views_compat

urlpatterns = [
    path("applyDetail.ajax", views_compat.apply_detail_view),
]
