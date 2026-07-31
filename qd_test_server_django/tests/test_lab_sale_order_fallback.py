"""销售绩效订单明细：Asset 404 时网关本地兜底。"""
from __future__ import annotations

from unittest.mock import patch

from django.test import RequestFactory, override_settings
from rest_framework.response import Response


@override_settings(SVC_ADMIN_ASSET_URL="http://127.0.0.1:19090")
def test_forward_admin_asset_first_fallback_on_non_json_404():
    from apps.core.admin_asset_forward import forward_admin_asset_first

    called = {"local": False}

    @forward_admin_asset_first
    def local_view(request):
        called["local"] = True
        return Response({"res": True, "obj": []})

    factory = RequestFactory()
    req = factory.get("/api/labPerformanceSaleuser/expOrderList.ajax")
    upstream = Response(
        {"code": 502, "message": "后台Asset服务返回非 JSON（HTTP 404）", "data": None},
        status=502,
    )
    with patch(
        "apps.core.admin_asset_forward.forward_admin_asset",
        return_value=upstream,
    ):
        out = local_view(req)

    assert called["local"] is True
    assert isinstance(out, Response)
    assert out.data["res"] is True


@override_settings(SVC_ADMIN_ASSET_URL="http://127.0.0.1:19090")
def test_exp_order_list_url_prefers_local_view():
    from django.urls import resolve

    match = resolve("/api/labPerformanceSaleuser/expOrderList.ajax")
    assert "lab_sale_order_list" in repr(match)
