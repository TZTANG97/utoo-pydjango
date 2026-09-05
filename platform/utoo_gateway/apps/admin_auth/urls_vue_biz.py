"""DEPRECATED (2026-09-05): welcome twin 本体。

biz 开启时不再挂 `api/_internal/vue/`；正式流量走 utoo_biz（BIZ_LOCAL）/ mid。
勿新写功能；删除计划 P3。见 docs/utoo-route-inventory.md §4 / V4。
未开 biz 时仍作应急 `_internal` welcome。开票等已改网关 BFF 直挂。
"""
from django.urls import path

from apps.admin_auth import views

urlpatterns = [
    path("welcome.ajax", views.welcome, name="internal-admin-welcome"),
]
