"""DEPRECATED (2026-09-05): consult `_internal` twin。

biz 开启时不再挂 `api/_internal/consult/`；正式流量走 order/platform（经 utoo_biz）。
勿新写功能；删除计划 P3。见 DEPRECATED-consult.md / docs/utoo-route-inventory.md。
"""
from django.urls import path

from apps.orders import views_consult_check

urlpatterns = [
    path("isServiceConsult.ajax", views_consult_check.is_service_consult_view),
]
