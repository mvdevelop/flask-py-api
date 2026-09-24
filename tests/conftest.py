"""
Fixtures de teste para PyStore API.
Mocka MongoClient globalmente antes de importar/app.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch
import mongomock


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    """Mocka variaveis de ambiente."""
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-for-testing-only")
    monkeypatch.setenv("SECRET_KEY", "test-secret-for-testing-only")
    monkeypatch.setenv("MONGO_URI", "mongodb://mockserver/py_store_test")
    monkeypatch.setenv("MONGO_DB", "py_store_test")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")


@pytest.fixture
def app():
    """
    Cria app Flask para testes com MongoDB mockado.
    Mocka MongoClient no modulo pymongo para que init_db() pegue o mock.
    """
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["py_store_test"]

    # Patch MongoClient antes de create_app ser chamado
    with patch("pymongo.MongoClient", return_value=mock_client):
        from app.app import create_app
        app = create_app("testing")
        app.config["TESTING"] = True
        app.config["JWT_SECRET_KEY"] = "test-jwt-secret-for-testing-only"

        # Patch get_db para usar mock_db em runtime (models)
        with patch("app.database.mongo.get_db", return_value=mock_db):
            with patch("app.models.product_model.get_db", return_value=mock_db):
                with patch("app.models.user_model.get_db", return_value=mock_db):
                    with patch("app.models.admin_model.get_db", return_value=mock_db):
                        yield app


@pytest.fixture
def client(app):
    """Cliente de teste Flask."""
    return app.test_client()
