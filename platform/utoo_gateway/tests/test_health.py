import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "qd_test_server_django"


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "青岛检测平台" in r.json()["message"]


def test_api_health(client):
    r = client.get("/api/health/")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"
