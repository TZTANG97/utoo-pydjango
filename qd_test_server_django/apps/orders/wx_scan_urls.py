from django.urls import path

from apps.orders import views_scan

urlpatterns = [
    path("scanCodeOperate.ajax", views_scan.scan_code_operate, name="wx-scanCodeOperate"),
    path("isFlag.ajax", views_scan.is_flag, name="wx-isFlag"),
]
