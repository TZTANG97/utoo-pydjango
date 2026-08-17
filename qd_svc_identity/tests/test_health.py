def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "qd_svc_identity"
    assert body["status"] == "ok"
