import pytest

import app as demo


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "DB_PATH", str(tmp_path / "test.db"))
    demo.init_db()
    demo.app.config["TESTING"] = True
    return demo.app.test_client()


def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_register_and_safe_lookup(client):
    resp = client.post("/register", data={"name": "ana", "password": "123"})
    assert resp.status_code == 201

    resp = client.get("/safe/user?name=ana")
    assert resp.get_json()["users"][0][1] == "ana"


def test_user_lookup(client):
    client.post("/register", data={"name": "bia", "password": "abc"})
    resp = client.get("/user?name=bia")
    assert resp.status_code == 200
    assert resp.get_json()["users"][0][1] == "bia"


def test_hello(client):
    resp = client.get("/hello?name=Murilo")
    assert b"Murilo" in resp.data
