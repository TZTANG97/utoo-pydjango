import json


def test_login_requires_channel(client):
    r = client.post(
        "/api/v1/identity/auth/login",
        data=json.dumps({"loginName": "x", "password": "y"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("code") == 400


def test_menus_pc_requires_auth(client):
    r = client.get("/api/v1/identity/menus", HTTP_X_CHANNEL="pc")
    body = r.json()
    assert body.get("code") == 401


def test_factory_channel_rejected_on_login(client):
    r = client.post(
        "/api/v1/identity/auth/login",
        data=json.dumps({"name": "x", "password": "y"}),
        content_type="application/json",
        HTTP_X_CHANNEL="emku",
    )
    body = r.json()
    assert body.get("code") == 400
    assert "工厂" in (body.get("message") or "")
