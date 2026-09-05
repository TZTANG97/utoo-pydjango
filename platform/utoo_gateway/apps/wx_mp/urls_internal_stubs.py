"""biz 开启时 `_internal/wx/` 仅挂 `_WX_STUBS`（501 / 未实现 stub）。

不含已 MID 路径（登录/资料/QR 补资料/仓扫等），也不含 wechatconfig（GW-LOCAL）。
未开 biz 时仍用整包 `apps.wx_mp.urls`。
"""
from django.urls import path

from apps.wx_mp import views_profile as vp
from shared.utoo_consumer_routes import _WX_STUBS

# 明确 stub 视图（非通用 not_implemented）
_NAMED_STUBS = {
    "bindaccount.ajax": vp.bind_account_stub,
    "bindaccountTZ.ajax": vp.bind_account_stub,
    "securebind.ajax": vp.secure_bind_stub,
}

_NOT_IMPLEMENTED = (
    "getAuditOrderList.ajax",
    "getAuditOrderList1.ajax",
    "getLog.ajax",
    "selBankList.ajax",
    "selSecondClassList.ajax",
    "signInIntegral.ajax",
)

# 与 _WX_STUBS 对齐：漏挂 / 多挂都会在导入时失败
assert set(_NAMED_STUBS) | set(_NOT_IMPLEMENTED) == set(_WX_STUBS), (
    "urls_internal_stubs must match shared.utoo_consumer_routes._WX_STUBS exactly"
)

urlpatterns = [
    path(name, view) for name, view in _NAMED_STUBS.items()
] + [path(name, vp.not_implemented) for name in _NOT_IMPLEMENTED]
