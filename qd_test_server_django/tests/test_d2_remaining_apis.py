"""C 端剩余接口：路由存在性（服务层已移植）"""

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


@pytest.mark.parametrize(
    "path,needs_auth",
    [
        ("/api/pc/register.ajax", False),
        ("/api/pc/getVerifyCode.ajax?telephone=13800000000", False),
        ("/api/pc/getVerifyCodeFindPw.ajax?telephone=13800000000", False),
        ("/api/pc/selRechargeStatus.ajax", True),
        ("/api/pc/selRechargeList.ajax", True),
        ("/api/pc/selDefaultAccount.ajax", True),
        ("/api/paymentapply/applyDetail.ajax?id=0", True),
        ("/api/offlineRecharge/rechargeDetail.ajax?id=0", True),
        ("/api/redeem/userredeemloglist.ajax", True),
        ("/api/consult/isServiceConsult.ajax?id=0", False),
        ("/api/pc/downloadFile.ajax?id=0", False),
    ],
)
def test_remaining_routes_exist(live_client, path, needs_auth):
    headers = {}
    if needs_auth:
        token = _login(live_client)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_TOKEN": token}
    r = live_client.get(path, **headers)
    assert r.status_code == 200
    if "downloadFile" in path:
        ct = r.get("Content-Type", "")
        if ct.startswith("application/json"):
            body = r.json()
            if body.get("code") == 503:
                pytest.skip(body.get("message"))
            assert body.get("code") in (0, 400, 401, 404)
        return
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body.get("code") is not None or "res" in body


def test_sel_recharge_status_shape(live_client):
    token = _login(live_client)
    r = live_client.get(
        "/api/pc/selRechargeStatus.ajax",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_TOKEN=token,
    )
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert "res" in body
    assert isinstance(body["res"], bool)
