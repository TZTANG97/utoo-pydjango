"""阶段 B：C 端 / 登录 / 小程序（经 utoo_biz 路由至各中台）。"""
from django.urls import path, re_path

from apps.utoo_consumer.views import proxy, user_roles

_CONSUMER_PREFIXES = (
    "pc",
    "auth",
    "wx",
    "consult",
)

urlpatterns: list = [
    # 产品枚举本地实现（禁止回落 gateway _internal）
    path("index/userRoles.ajax", user_roles.user_roles),
]
for prefix in _CONSUMER_PREFIXES:
    urlpatterns.append(re_path(rf"^{prefix}/(?P<subpath>.+)$", proxy.proxy_consumer))
    urlpatterns.append(path(f"{prefix}/", proxy.proxy_consumer))
