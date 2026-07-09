import json
import os

import pytest

TEST_MOBILE = os.getenv("TEST_LOGIN_MOBILE", "18211984686")
TEST_PASSWORD = os.getenv("TEST_LOGIN_PASSWORD", "123456")


def _login(client):
    r = client.post(
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


def test_index_class_list(live_client):
    client = live_client
    r = client.get("/api/pc/indexClassList.ajax")
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0
    assert isinstance(body["data"], list)


def test_sel_third_class_list(live_client):
    client = live_client
    r = client.get("/api/pc/selThirdClassList.ajax?start=0&length=5&draw=1")
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0
    assert "data" in body["data"]


def test_child_order_routes(live_client):
    token = _login(live_client)
    for path in (
        "/api/experimentOrder/getChildFormByIdExp.ajax?ofId=1&start=0&length=10&draw=1",
        "/api/experimentChildOrder/getOrdersBySaleOrderId.ajax?ofId=1&start=0&length=10&draw=1",
        "/api/experimentChildOrder/orderdetail.ajax?id=1",
    ):
        r = live_client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_TOKEN=token)
        assert r.status_code == 200
        body = r.json()
        if body.get("code") == 503:
            pytest.skip(body.get("message"))
        assert body["code"] == 0


def test_integral_list_route(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/pc/center/getIntegralList.ajax?start=0&length=10&draw=1",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0


def test_query_pro_city_co1(live_client):
    r = live_client.get("/api/pc/queryProCityCo1.ajax")
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0


def test_invoice_list_route(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/pc/center/getInvoiceList.ajax?start=0&length=10&draw=1&type=2",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0


def test_my_order_list(live_client):
    client = live_client
    token = _login(client)
    r = client.get(
        "/api/pc/myExperimentOrderList.ajax?start=0&length=10&draw=1&type=0",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0
    assert "data" in body["data"]
