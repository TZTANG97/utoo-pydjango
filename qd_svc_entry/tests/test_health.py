def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "qd_svc_entry"


import pytest


def test_entry_comment_tree_route(live_client):
    r = live_client.get("/api/entry/commenttreebulder.ajax")
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0
