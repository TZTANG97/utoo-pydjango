"""D2 边角：地址 / 复测确认 / 附件上传"""

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


def test_user_address(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/pc/useraddress.ajax",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0


def test_sel_test_or_sure(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/pc/selTestOrSure.ajax",
        {"id": "1", "type": "1"},
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0


def test_sel_company_name(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/pc/selCompanyName.ajax",
        {"draw": "1", "start": "0", "length": "10", "keyword": "测试"},
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0
    assert "data" in body["data"]


def test_get_delivery_address(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/pc/getdeliveryaddress.ajax",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0
    assert "expUserDeliveryAddresses" in body["data"]


def test_upload_child_data_no_file(live_client):
    token = _login(live_client)
    r = live_client.post(
        "/api/experimentOrder/uploadChildData.ajax",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] != 0
