"""销售绩效订单明细：Asset 404 时网关本地 / 代理层兜底。"""
from __future__ import annotations

from unittest.mock import patch

from django.test import RequestFactory, override_settings
from rest_framework.response import Response


@override_settings(SVC_ADMIN_ASSET_URL="http://127.0.0.1:19090")
def test_proxy_falls_back_to_local_exp_order_list():
    from apps.core.admin_asset_forward import proxy_admin_asset_request

    factory = RequestFactory()
    req = factory.post(
        "/api/labPerformanceSaleuser/expOrderList.ajax",
        data={
            "sale_user_id": "1",
            "month": "2025-06",
            "type": "1",
            "start": "0",
            "length": "10",
            "draw": "1",
        },
    )
    upstream = Response(
        {"code": 502, "message": "后台Asset服务返回非 JSON（HTTP 404）", "data": None},
        status=502,
    )
    local_resp = Response(
        {"draw": 1, "recordsTotal": 2, "recordsFiltered": 2, "data": [{"id": 1}]},
        status=200,
    )

    with (
        patch(
            "apps.core.admin_asset_forward.forward_admin_asset",
            return_value=upstream,
        ),
        patch(
            "apps.admin_digital.views.digital.lab_sale_order_list",
            return_value=local_resp,
        ) as local_mock,
    ):
        out = proxy_admin_asset_request(req)

    assert local_mock.called
    assert out.status_code == 200
    assert out.data["recordsTotal"] == 2


@override_settings(SVC_ADMIN_ASSET_URL="http://127.0.0.1:19090")
def test_exp_order_list_url_binds_local_view():
    from django.urls import resolve

    match = resolve("/api/labPerformanceSaleuser/expOrderList.ajax")
    assert "lab_sale_order_list" in repr(match)
