from fastapi.testclient import TestClient

from app.main import app


def test_app_startup_and_serves_requests() -> None:
    with TestClient(app) as client:
        response = client.get("/__startup_smoke__")

    assert response.status_code == 404
