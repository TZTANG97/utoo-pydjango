import os

import pytest

TEST_MOBILE = os.getenv("TEST_LOGIN_MOBILE", "18211984686")
TEST_PASSWORD = os.getenv("TEST_LOGIN_PASSWORD", "123456")


def _skip_db(body: dict):
    if body.get("code") == 503:
        pytest.skip(body.get("message", "database unavailable"))


def test_login(live_client):
    client = live_client
    r = client.post(
        "/api/auth/login",
        data={"name": TEST_MOBILE, "password": TEST_PASSWORD, "loginType": "1"},
        content_type="application/json",
    )
    assert r.status_code == 200
    body = r.json()
    _skip_db(body)
    assert body["code"] == 0, body.get("message")
    assert body["data"]["token"]


def test_me_after_login(live_client):
    client = live_client
    login = client.post(
        "/api/auth/login",
        data={"name": TEST_MOBILE, "password": TEST_PASSWORD, "loginType": "1"},
        content_type="application/json",
    )
    body = login.json()
    _skip_db(body)
    if body["code"] != 0:
        pytest.skip(body.get("message", "login failed"))
    token = body["data"]["token"]
    r = client.get(
        "/api/auth/me",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    me = r.json()
    assert me["code"] == 0
    assert me["data"]["mobile"]


def test_get_user_basic_info(live_client):
    client = live_client
    login = client.post(
        "/api/auth/login",
        data={"name": TEST_MOBILE, "password": TEST_PASSWORD, "loginType": "1"},
        content_type="application/json",
    )
    body = login.json()
    _skip_db(body)
    if body["code"] != 0:
        pytest.skip(body.get("message", "login failed"))
    token = body["data"]["token"]
    r = client.get(
        "/api/pc/getUserBasicInfo.ajax",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    info = r.json()
    assert info["code"] == 0
    assert "mobile" in info["data"]
