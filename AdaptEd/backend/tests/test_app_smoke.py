from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_root_returns_ok():
    response = client.get("/")
    assert response.status_code == 200


def test_debug_hidden_without_debug_flag(monkeypatch):
    monkeypatch.delenv("DEBUG", raising=False)
    response = client.get("/debug")
    assert response.status_code == 404


def test_debug_ok_when_debug_enabled(monkeypatch):
    monkeypatch.setenv("DEBUG", "1")
    response = client.get("/debug")
    assert response.status_code == 200
    body = response.json()
    assert "users_count" in body
    assert "data_file_exists" in body
    assert "users" not in body


def test_homeworks_requires_auth():
    r = client.get("/homeworks")
    assert r.status_code == 401


def test_library_materials_public():
    r = client.get("/materials")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_tests_list_requires_auth():
    r = client.get("/tests")
    assert r.status_code == 401
