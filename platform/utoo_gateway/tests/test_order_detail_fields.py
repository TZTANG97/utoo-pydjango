"""主订单详情字段 — 对齐 FastAPI test_phase2_extended"""

import json
import os

import pytest

TEST_MOBILE = os.getenv("TEST_LOGIN_MOBILE", "18211984686")
TEST_PASSWORD = os.getenv("TEST_LOGIN_PASSWORD", "123456")


def _login(live_client):
    r = live_client.post(
        "/api/auth/login",
        data=json.dumps(
            {"name": TEST_MOBILE, "password": TEST_PASSWORD, "loginType": "1"}
        ),
        content_type="application/json",
    )
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    if body.get("code") != 0:
        pytest.skip(body.get("message", "login failed"))
    return body["data"]["token"]


def test_order_detail_fields(live_client):
    token = _login(live_client)
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_TOKEN": token}
    lst = live_client.get(
        "/api/pc/myExperimentOrderList.ajax",
        {"draw": "1", "start": "0", "length": "5", "type": "0"},
        **headers,
    )
    list_body = lst.json()
    if list_body.get("code") == 503:
        pytest.skip(list_body.get("message"))
    rows = (list_body.get("data") or {}).get("data") or []
    if not rows:
        pytest.skip("无订单")
    oid = rows[0]["id"]
    r = live_client.get(
        "/api/experimentOrder/orderdetail.ajax",
        {"id": oid},
        **headers,
    )
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0, body.get("message")
    data = body["data"]
    of = data.get("of")
    assert of
    assert of.get("order_id")
    assert of.get("order_statusstr")
    assert "testClass" in of
    assert of["testClass"].get("name")
    assert "testFiles" in data
    assert "hzdFiles" in data
    assert "jdshow" in data
    assert "ispjqx" in data
