"""方案 B / V3：forward_*_first 未配 SVC 不得 silent twin。"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from django.http import JsonResponse
from django.test import RequestFactory, override_settings


_CORE = Path(__file__).resolve().parents[1] / "apps" / "core"

_FORWARD_MODULES = (
    "identity_forward.py",
    "order_forward.py",
    "payment_forward.py",
    "invoice_forward.py",
    "entry_forward.py",
    "wx_forward.py",
    "admin_asset_forward.py",
    "admin_platform_forward.py",
)


def _forward_first_fn(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _msg(resp) -> str:
    return str(json.loads(resp.content.decode("utf-8")).get("message") or "")


@pytest.mark.parametrize("mod", _FORWARD_MODULES)
def test_forward_first_source_never_calls_view_func(mod: str):
    """静态：forward_*_first 包装体不得再 return view_func(...)（silent twin）。"""
    src = (_CORE / mod).read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn_name = None
    for line in src.splitlines():
        if line.startswith("def forward_") and line.endswith("_first(view_func):"):
            fn_name = line[len("def ") :].split("(", 1)[0]
            break
    assert fn_name, mod
    fn = _forward_first_fn(tree, fn_name)
    assert fn is not None, fn_name
    text = ast.unparse(fn)
    assert "view_func(" not in text, f"{mod}: still calls view_func in {fn_name}"
    assert "mid_svc_unconfigured_response" in text or "503" in text


@override_settings(SVC_ORDER_URL="")
def test_forward_order_first_503_when_unconfigured():
    from apps.core.order_forward import forward_order_first

    @forward_order_first
    def local_view(request):
        raise AssertionError("must not run local twin")

    resp = local_view(RequestFactory().get("/api/pc/getXcxBanner.ajax"))
    assert isinstance(resp, JsonResponse)
    assert resp.status_code == 503
    msg = _msg(resp)
    assert "SVC_ORDER_URL" in msg
    assert "\u672a\u914d\u7f6e" in msg


@override_settings(SVC_PAYMENT_URL="")
def test_forward_payment_first_503_when_unconfigured():
    from apps.core.payment_forward import forward_payment_first

    @forward_payment_first
    def local_view(request):
        raise AssertionError("must not run local twin")

    resp = local_view(RequestFactory().post("/api/pc/addCash.ajax"))
    assert resp.status_code == 503
    assert "SVC_PAYMENT_URL" in _msg(resp)


@override_settings(SVC_IDENTITY_URL="")
def test_forward_identity_first_503_when_unconfigured():
    from apps.core.identity_forward import forward_identity_first

    @forward_identity_first
    def local_view(request):
        raise AssertionError("must not run local twin")

    resp = local_view(RequestFactory().post("/api/pc/register.ajax"))
    assert resp.status_code == 503
    assert "SVC_IDENTITY_URL" in _msg(resp)


@override_settings(
    SVC_INVOICE_URL="",
    SVC_ADMIN_PLATFORM_URL="",
    UTOO_BIZ_SERVICE_URL="",
    UTOO_GATEWAY_BFF_ONLY=False,
)
def test_forward_invoice_first_503_when_unconfigured():
    from apps.core.invoice_forward import forward_invoice_first

    @forward_invoice_first
    def local_view(request):
        raise AssertionError("must not run local twin")

    resp = local_view(RequestFactory().get("/api/pc/center/getInvoiceInfo.ajax"))
    assert resp.status_code == 503
    assert "\u672a\u914d\u7f6e" in _msg(resp)


@override_settings(SVC_PAYMENT_URL="http://127.0.0.1:19084")
def test_forward_payment_first_no_local_on_upstream_404():
    """配了 SVC 后上游 404 也不得回落本地 twin。"""
    from unittest.mock import patch

    from apps.core.payment_forward import forward_payment_first
    from rest_framework.response import Response

    @forward_payment_first
    def local_view(request):
        raise AssertionError("must not run local twin on upstream 404")

    upstream = Response(
        {"code": 404, "message": "Not Found", "data": None},
        status=404,
    )
    with patch(
        "apps.core.payment_forward.forward_payment",
        return_value=upstream,
    ):
        resp = local_view(RequestFactory().get("/api/pc/addCash.ajax"))
    assert resp.status_code == 404
