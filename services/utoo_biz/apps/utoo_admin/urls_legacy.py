"""阶段 C：管理端 welcome / billing / asset 前缀。"""
from django.urls import path, re_path

from apps.utoo_admin.views import proxy, welcome
from shared.utoo_admin_routes import ASSET_PREFIXES, VUE_BIZ_EXACT

urlpatterns: list = [
    # welcome 真实现（禁止再回落 gateway _internal）
    path("vue/welcome.ajax", welcome.welcome),
]

for exact in VUE_BIZ_EXACT:
    if exact == "welcome.ajax":
        continue
    urlpatterns.append(path(f"vue/{exact}", proxy.proxy_admin))

for prefix in ASSET_PREFIXES:
    if "/" in prefix or prefix.endswith(".ajax"):
        urlpatterns.append(path(prefix, proxy.proxy_admin))
    else:
        urlpatterns.append(re_path(rf"^{prefix}/(?P<subpath>.+)$", proxy.proxy_admin))
        urlpatterns.append(path(f"{prefix}/", proxy.proxy_admin))
