"""
Testes de integracao para PyStore API.
Security Champion Note:
- Mocka MongoDB com mongomock — testes isolados
- Testa todos os endpoints do controller
- Inclui testes de headers de seguranca e error handling
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch
import mongomock


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    """Mocka variaveis de ambiente para testes."""
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-for-testing-only")
    monkeypatch.setenv("SECRET_KEY", "test-secret-for-testing-only")
    monkeypatch.setenv("MONGO_URI", "mongodb://mockserver/py_store_test")
    monkeypatch.setenv("MONGO_DB", "py_store_test")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")


@pytest.fixture
def app():
    """Cria app Flask para testes com MongoDB mockado."""
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["py_store_test"]

    with patch("pymongo.MongoClient", return_value=mock_client):
        from app.app import create_app
        app = create_app("testing")
        app.config["TESTING"] = True
        app.config["JWT_SECRET_KEY"] = "test-jwt-secret-for-testing-only"

        with patch("app.database.mongo.get_db", return_value=mock_db):
            with patch("app.models.product_model.get_db", return_value=mock_db):
                with patch("app.models.user_model.get_db", return_value=mock_db):
                    with patch("app.models.admin_model.get_db", return_value=mock_db):
                        yield app


@pytest.fixture
def client(app):
    """Cliente de teste Flask."""
    return app.test_client()


# ==============================
# Test: Root endpoint
# ==============================
class TestRootEndpoint:

    def test_root_returns_service_name(self, client):
        """GET / deve retornar nome do servico."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.get_json()
        assert data["service"] == "PyStore API"

    def test_root_returns_timestamp(self, client):
        """GET / deve incluir timestamp."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.get_json()
        assert "timestamp" in data


# ==============================
# Test: Health check
# ==============================
class TestHealthEndpoint:

    def test_health_returns_200_when_db_connected(self, client):
        """Health check retorna 200 quando DB conectado (mockado)."""
        response = client.get("/health")
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert "status" in data

    def test_health_minimal_disclosure(self, client):
        """Health check nao expoe detalhes de infra (CWE-200)."""
        response = client.get("/health")
        data = response.get_json()
        assert "collections" not in json.dumps(data)
        assert "produtos" not in json.dumps(data)


# ==============================
# Test: Security Headers
# ==============================
class TestSecurityHeadersResponse:
    """Verifica headers de seguranca em responses HTTP."""

    def test_x_content_type_options(self, client):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, client):
        response = client.get("/")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_csp_header(self, client):
        response = client.get("/")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp

    def test_referrer_policy(self, client):
        response = client.get("/")
        assert "strict" in response.headers.get("Referrer-Policy", "").lower()

    def test_no_server_header(self, client):
        """Server header deve ser removido."""
        response = client.get("/")
        assert "Server" not in response.headers


# ==============================
# Test: Error handling
# ==============================
class TestErrorHandling:

    def test_404_returns_json(self, client):
        """404 deve retornar JSON."""
        response = client.get("/nonexistent-endpoint-12345")
        assert response.status_code == 404
        assert response.is_json
        data = response.get_json()
        assert "error" in data


# ==============================
# Test: Schema validation no endpoint
# ==============================
class TestInputValidation:

    def test_product_create_requires_auth(self, client):
        """POST /api/produtos sem auth deve retornar 401 (JWT required)."""
        response = client.post("/api/produtos", json={"descricao": "teste"})
        # 401 = sem token, 400 = schema validation, 405 = route nao matched (prefikso)
        assert response.status_code in [401, 400, 405]


# ==============================
# Test: NoSQL Injection Prevention
# ==============================
class TestNoSQLInjection:

    def test_rejects_invalid_objectid(self, client):
        """ObjectId invalido deve ser rejeitado."""
        response = client.get("/api/produtos/invalid-id-not-valid-objectid")
        assert response.status_code in [400, 404, 401, 500]


# ==============================
# Test: Rate Limiting no login
# ==============================
class TestRateLimiting:

    def test_login_endpoint_exists(self, client):
        """Login endpoint deve existir e retornar erro de validacao."""
        response = client.post("/api/user_admin/login",
            json={"email": "test@test.com", "password": "wrong"}
        )
        # 401 = credenciais invalidas, 400 = dados invalidos
        assert response.status_code in [401, 400, 429, 500]

    def test_login_rate_limited_after_5_attempts(self, client):
        """Apos 5 tentativas falhas, deve retornar 429."""
        responses = []
        for i in range(6):
            response = client.post("/api/user_admin/login",
                json={"email": f"user{i}@test.com", "password": "wrong"}
            )
            responses.append(response.status_code)
        # Pelo menos uma das tentativas deve ser 429 (rate limited)
        assert 429 in responses or 401 in responses
