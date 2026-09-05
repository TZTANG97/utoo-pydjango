"""讨论区 /api/entry/* 路由冒烟（空库时 skip）"""

import pytest


def test_entry_comment_tree_route(live_client):
    r = live_client.get("/api/entry/commenttreebulder.ajax")
    assert r.status_code == 200
    body = r.json()
    if body.get("code") == 503:
        pytest.skip(body.get("message"))
    assert body["code"] == 0
    data = body.get("data") or {}
    assert "data" in data
    assert "recordsTotal" in data
