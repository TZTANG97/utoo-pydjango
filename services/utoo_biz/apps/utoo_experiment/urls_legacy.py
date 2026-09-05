"""阶段 A：愉兔管理端/C 端实验域旧路径 → utoo_biz 业务层 → platform/order。"""
from django.urls import path, re_path

from apps.utoo_experiment.views import legacy_ajax
from shared.utoo_experiment_routes import EXPERIMENT_ORDER_PREFIXES

# 与 utoo_gateway/config/urls.py 中实验订单主链前缀对齐
LEGACY_ORDER_PREFIXES = EXPERIMENT_ORDER_PREFIXES

urlpatterns: list = []
for prefix in LEGACY_ORDER_PREFIXES:
    urlpatterns.append(re_path(rf"^{prefix}/(?P<subpath>.+)$", legacy_ajax.proxy_legacy_ajax))
    urlpatterns.append(path(f"{prefix}/", legacy_ajax.proxy_legacy_ajax))
