"""公网 /api/v1/identity 转发：青岛切流打同一 VIP。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import Client, override_settings


@override_settings(SVC_IDENTITY_URL="")
def test_identity_public_proxy_503_when_unconfigured():
    resp = Client().post(
        "/api/v1/identity/auth/login",
        data='{"user_name":"a","password":"b"}',
        content_type="application/json",
        HTTP_X_CHANNEL="mall_qd",
    )
    assert resp.status_code == 503
    assert resp.json()["code"] == 503


@override_settings(SVC_IDENTITY_URL="http://127.0.0.1:19081")
def test_identity_companies_not_exposed_on_public_vip():
    resp = Client().get("/api/v1/identity/companies")
    assert resp.status_code == 404


@override_settings(SVC_IDENTITY_URL="http://127.0.0.1:19081")
def test_identity_login_forwards_to_mid_and_keeps_channel():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"access_token": "t"}
    mock_resp.content = b'{"access_token":"t"}'
    mock_resp.headers = {"content-type": "application/json"}

    with patch("apps.core.svc_proxy.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.post.return_value = mock_resp
        resp = Client().post(
            "/api/v1/identity/auth/login",
            data='{"user_name":"a","password":"b"}',
            content_type="application/json",
            HTTP_X_CHANNEL="mall_qd",
        )

    assert resp.status_code == 200
    assert resp.json()["access_token"] == "t"
    client.post.assert_called_once()
    args, kwargs = client.post.call_args
    assert args[0] == "http://127.0.0.1:19081/api/v1/identity/auth/login"
    assert kwargs["headers"]["X-Channel"] == "mall_qd"


@override_settings(SVC_IDENTITY_URL="http://127.0.0.1:19081")
def test_identity_users_forwards_to_mid():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": []}
    mock_resp.content = b'{"data":[]}'
    mock_resp.headers = {"content-type": "application/json"}

    with patch("apps.core.svc_proxy.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.get.return_value = mock_resp
        resp = Client().get("/api/v1/identity/users", HTTP_X_CHANNEL="mall_qd")

    assert resp.status_code == 200
    args, _kwargs = client.get.call_args
    assert args[0] == "http://127.0.0.1:19081/api/v1/identity/users"


@override_settings(SVC_IDENTITY_URL="http://127.0.0.1:19081")
def test_identity_menus_all_forwards_to_mid():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": []}
    mock_resp.content = b'{"data":[]}'
    mock_resp.headers = {"content-type": "application/json"}

    with patch("apps.core.svc_proxy.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.get.return_value = mock_resp
        resp = Client().get("/api/v1/identity/menus/all", HTTP_X_CHANNEL="mall_qd")

    assert resp.status_code == 200
    args, _kwargs = client.get.call_args
    assert args[0] == "http://127.0.0.1:19081/api/v1/identity/menus/all"


@override_settings(SVC_IDENTITY_URL="http://127.0.0.1:19081")
def test_identity_password_forwards_to_mid():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": {"id": "u1"}}
    mock_resp.content = b'{"data":{"id":"u1"}}'
    mock_resp.headers = {"content-type": "application/json"}

    with patch("apps.core.svc_proxy.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.post.return_value = mock_resp
        resp = Client().post(
            "/api/v1/identity/auth/password",
            data='{"old_password":"a","new_password":"b"}',
            content_type="application/json",
            HTTP_X_CHANNEL="mall_qd",
        )

    assert resp.status_code == 200
    args, _kwargs = client.post.call_args
    assert args[0] == "http://127.0.0.1:19081/api/v1/identity/auth/password"
