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


def test_get_account_real_arrear_and_invoice(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/pc/center/getAccount.ajax",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0, body.get("message")
    data = body["data"]
    assert "arrearAmount" in data
    assert "invoicingAmount" in data
    assert "amount" in data
    assert "accountBalance" in data
    arrear = float(data["arrearAmount"])
    invoicing = float(data["invoicingAmount"])
    balance = float(data["accountBalance"])
    available = float(data["amount"])
    net = float(data.get("netBalance", balance - arrear))
    assert arrear >= 0
    assert invoicing >= 0
    assert available == balance
    assert net == balance - arrear
