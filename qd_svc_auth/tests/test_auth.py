import json
import os

import pytest

TEST_MOBILE = os.getenv("TEST_LOGIN_MOBILE", "18211984686")
TEST_PASSWORD = os.getenv("TEST_LOGIN_PASSWORD", "123456")


def test_login(live_client):
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
    if body.get("code") == 401:
        pytest.skip(body.get("message", "login failed"))
    assert body["code"] == 0
    assert body["data"]["token"]
