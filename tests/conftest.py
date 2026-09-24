"""
Fixtures de teste para PyStore API.
"""
import os
import sys

# Adiciona raiz do projeto no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    """Mocka variaveis de ambiente para testes seguros."""
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-for-testing-only")
    monkeypatch.setenv("SECRET_KEY", "test-secret-for-testing-only")
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017/py_store_test")
    monkeypatch.setenv("MONGO_DB", "py_store_test")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    yield
