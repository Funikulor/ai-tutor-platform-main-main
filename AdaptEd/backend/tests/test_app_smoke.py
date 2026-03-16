from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_root_returns_ok():
    response = client.get("/")
    assert response.status_code == 200


def test_debug_endpoint_available():
    response = client.get("/debug")
    # В проде может быть отключен persistent_storage, поэтому проверяем только, что эндпоинт отвечает
    assert response.status_code == 200

