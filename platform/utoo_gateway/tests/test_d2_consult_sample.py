"""D2 预约/样品/复测路由冒烟"""

import pytest


def test_exp_make_list_route(live_client):
    r = live_client.get("/api/pc/expMakeList.ajax")
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0
    assert isinstance(body.get("data"), list)


def test_sample_attribute_state_route(live_client):
    r = live_client.get("/api/ordersampleinfomation/getAttributeStateList.ajax")
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0
