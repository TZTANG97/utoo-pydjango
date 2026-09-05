"""网关发票转发：WSGIRequest 不得因缺 query_params 而 500。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.http import JsonResponse
from django.test import RequestFactory, override_settings


@override_settings(SVC_INVOICE_URL="http://127.0.0.1:19091")
def test_forward_invoice_first_accepts_wsgi_request():
    from apps.core.invoice_forward import forward_invoice_first

    @forward_invoice_first
    def local_view(request):
        raise AssertionError("should forward, not call local view")

    factory = RequestFactory()
    wsgi_req = factory.get(
        "/api/pc/center/getInvoiceInfo.ajax",
        data={"_": "1"},
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"code": 0, "message": "ok", "data": {}}
    mock_resp.content = b'{"code":0}'

    with patch("apps.core.svc_proxy.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.get.return_value = mock_resp
        resp = local_view(wsgi_req)

    assert isinstance(resp, JsonResponse)
    assert resp.status_code == 200
    payload = resp.content.decode("utf-8")
    assert '"code": 0' in payload or '"code":0' in payload
    client.get.assert_called_once()
    _, kwargs = client.get.call_args
    assert kwargs.get("params") is not None


@override_settings(SVC_INVOICE_URL="http://127.0.0.1:19091")
def test_forward_request_wsgi_query_params_no_attribute_error():
    from apps.core.svc_proxy import forward_request
    from rest_framework.response import Response

    factory = RequestFactory()
    wsgi_req = factory.get("/api/pc/center/getInvoiceList.ajax", {"start": "0"})

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"code": 0, "data": {"stayApplyMoney": 0}}
    mock_resp.content = b"{}"

    with patch("apps.core.svc_proxy.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.get.return_value = mock_resp
        out = forward_request(
            wsgi_req,
            base_url="http://127.0.0.1:19091",
            path="/api/pc/center/getInvoiceList.ajax",
            service_name="发票服务",
        )

    assert isinstance(out, Response)
    assert out.status_code == 200
    assert out.data["code"] == 0


def test_invoice_info_bit_normalize():
    from apps.invoices.services.tax_info_crud import _normalize_row

    assert _normalize_row({"is_default": b"\x01", "id": 1})["is_default"] is True
    assert _normalize_row({"is_default": b"\x00", "id": 2})["is_default"] is False
    assert _normalize_row({"is_default": 1, "id": 3})["is_default"] is True
    assert _normalize_row({"is_default": "\x01", "id": 4})["is_default"] is True
