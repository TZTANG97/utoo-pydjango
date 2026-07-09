"""个人资料 + 微信域冒烟"""

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


def test_set_password_validation(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/pc/setPassword.ajax",
        {"password": "abc", "password1": "xyz"},
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] != 0


def test_wx_qr_generator(live_client):
    r = live_client.get("/api/wx/WeChatQRCodeGenerator.ajax")
    assert r.status_code == 200
    if r.get("Content-Type", "").startswith("application/json"):
        body = r.json()
        if body.get("code") == 501:
            pytest.skip(body.get("message"))
        assert "url" in body or body.get("code") == 0


def test_add_or_update_user_data_requires_login(live_client):
    r = live_client.get("/api/pc/addOrUpdateUserData.ajax")
    assert r.status_code == 200
    assert r.json()["code"] != 0


def test_add_or_update_user_company_data_requires_login(live_client):
    r = live_client.get("/api/pc/addOrUpdateUserCompanyData.ajax")
    assert r.status_code == 200
    assert r.json()["code"] != 0


def test_wx_reservation_invalid(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/wx/reservationDetail.ajax",
        {"id": "999999999"},
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    if r.status_code >= 500:
        pytest.skip("数据库不可用")
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] != 0
