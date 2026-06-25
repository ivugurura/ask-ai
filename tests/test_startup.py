import importlib
import os
import sys
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def test_app_startup_and_serves_requests() -> None:
    os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
    os.environ.setdefault("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    os.environ.setdefault("TOP_K", "6")

    fake_model = MagicMock()
    fake_model.encode.return_value = [[0.0, 0.0, 0.0]]

    with patch("sentence_transformers.SentenceTransformer", return_value=fake_model):
        for module_name in [
            "app.main",
            "app.routers.ask",
            "app.routers.ingest",
            "app.services.ask",
            "app.services.ingest",
        ]:
            sys.modules.pop(module_name, None)

        app_module = importlib.import_module("app.main")

        with TestClient(app_module.app) as client:
            response = client.get("/__startup_smoke__")

    assert response.status_code == 404


def test_health_check_endpoint() -> None:
    os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
    os.environ.setdefault("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    os.environ.setdefault("TOP_K", "6")

    fake_model = MagicMock()
    fake_model.encode.return_value = [[0.0, 0.0, 0.0]]

    with patch("sentence_transformers.SentenceTransformer", return_value=fake_model):
        for module_name in [
            "app.main",
            "app.routers.ask",
            "app.routers.ingest",
            "app.services.ask",
            "app.services.ingest",
        ]:
            sys.modules.pop(module_name, None)

        app_module = importlib.import_module("app.main")

        with TestClient(app_module.app) as client:
            response = client.get("/ai/health")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Healthy",
        'data': None
    }
