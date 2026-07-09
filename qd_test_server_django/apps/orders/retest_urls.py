from django.urls import path

from apps.orders import views_retest

urlpatterns = [
    path("addretestapplication.ajax", views_retest.add_retest_application),
]
