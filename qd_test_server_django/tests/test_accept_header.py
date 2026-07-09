"""旧前端 Accept: '*' 不应再 406"""


def test_banner_with_star_accept(client):
    r = client.get(
        "/api/pc/bannerList.ajax",
        HTTP_ACCEPT="*",
    )
    assert r.status_code == 200, r.content
    body = r.json()
    assert body.get("code") is not None


def test_index_class_list_with_star_accept(client):
    r = client.get(
        "/api/pc/indexClassList.ajax",
        HTTP_ACCEPT="*",
    )
    assert r.status_code == 200, r.content


def test_index_exp_list_post_with_star_accept(client):
    r = client.post(
        "/api/pc/indexExpList.ajax",
        HTTP_ACCEPT="*",
    )
    assert r.status_code == 200, r.content
