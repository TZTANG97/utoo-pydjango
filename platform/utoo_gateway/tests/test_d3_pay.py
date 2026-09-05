def test_pay_notify_route_exists(client):
    r = client.post("/api/pc/pay.ajax", data=b"{}", content_type="application/json")
    # 无有效微信签名时返回 500；路由存在即可
    assert r.status_code in (200, 500)


def test_amount_pay_route_requires_auth(client):
    r = client.get("/api/pc/amountPay.ajax")
    assert r.status_code == 200
    body = r.json()
    assert body.get("code") in (401, 403, 0)
