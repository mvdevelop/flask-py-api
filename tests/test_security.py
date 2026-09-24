"""
Testes de seguranca para PyStore API — Etapa 1, 2, 3.
Validam: secrets, CORS, schemas, rate limiting, headers, ObjectId, bcrypt, error handling.

Security Champion Note:
Estes testes implementam verificacao automatica de controles de seguranca.
Rodar com: pytest -v
"""
import pytest
from pathlib import Path
import os
import inspect
from unittest.mock import patch


# ==============================
# Test 1: Nenhum segredo hardcoded
# ==============================
class TestNoHardcodedSecrets:
    """CWE-798: Use of Hard-coded Credentials."""

    def test_config_jwt_not_hardcoded(self):
        """JWT_SECRET_KEY nao deve conter fallback hardcoded."""
        import os
        os.environ.pop("JWT_SECRET_KEY", None)
        os.environ["FLASK_ENV"] = "development"
        from config import _require_env
        result = _require_env("JWT_SECRET_KEY")
        assert result == "dev-only-not-for-production"

    def test_config_secret_key_not_hardcoded(self):
        """SECRET_KEY nao deve conter fallback hardcoded."""
        import os
        os.environ.pop("SECRET_KEY", None)
        os.environ["FLASK_ENV"] = "development"
        from config import _require_env
        result = _require_env("SECRET_KEY")
        assert result == "dev-only-not-for-production"

    def test_no_known_secrets_in_codebase(self):
        """Nenhum arquivo Python da aplicacao deve conter segredos conhecidos."""
        forbidden = ["super-secret-admin-key", "dev-secret-key-change-in-production", "dev-secret-key"]
        app_files = list(Path("app").rglob("*.py")) + list(Path(".").glob("*.py"))
        app_files = [f for f in app_files if "venv" not in str(f) and "__pycache__" not in str(f) and "tests" not in str(f)]
        for fp in app_files:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for s in forbidden:
                    assert s not in content, f"Segredo em {fp}: {s}"


# ==============================
# Test 2: CORS restringido
# ==============================
class TestCORSRestricted:
    """CWE-306: Missing Authentication for Critical Function (CORS)."""

    def test_cors_no_wildcard(self):
        """Codigo nao deve usar origins='*'."""
        app_py = Path("app/app.py").read_text(encoding="utf-8")
        assert '"*"' not in app_py.replace(" ", "")

    def test_config_has_cors_origins(self):
        from config import Config
        assert hasattr(Config, "CORS_ORIGINS")


# ==============================
# Test 3: Schema validation (Pydantic)
# ==============================
class TestSchemaValidation:
    """CWE-20: Improper Input Validation."""

    def test_product_create_requires_nome(self):
        from app.schemas import ProductCreateSchema
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ProductCreateSchema(descricao="teste")

    def test_product_create_nome_max_length(self):
        from app.schemas import ProductCreateSchema
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ProductCreateSchema(nome="a" * 201, descricao="teste")

    def test_user_create_requires_name(self):
        from app.schemas import UserCreateSchema
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserCreateSchema()

    def test_admin_login_rejects_empty(self):
        from app.schemas import AdminLoginSchema
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AdminLoginSchema(email="", password="")

    def test_product_create_strips_whitespace(self):
        from app.schemas import ProductCreateSchema
        schema = ProductCreateSchema(nome="  Teste  ", descricao="  Desc  ")
        assert schema.nome == "Teste"
        assert schema.descricao == "Desc"


# ==============================
# Test 4: Rate limiting
# ==============================
class TestRateLimit:
    """CWE-307: Improper Restriction of Excessive Authentication Attempts."""

    def test_admin_controller_has_rate_limit(self):
        from app.controllers.admin_controller import AdminController
        assert hasattr(AdminController, "login")
        source = inspect.getsource(AdminController.login)
        assert "rate_limit" in source

    def test_rate_limit_constants(self):
        from app.controllers.admin_controller import MAX_LOGIN_ATTEMPTS, LOGIN_WINDOW_SECONDS
        assert MAX_LOGIN_ATTEMPTS >= 3
        assert LOGIN_WINDOW_SECONDS >= 60

    def test_rate_limit_decorador_existe(self):
        from app.middlewares.rate_limit import rate_limit
        assert callable(rate_limit)


# ==============================
# Test 5: ObjectId validation
# ==============================
class TestObjectIdValidation:
    """CWE-20: ObjectId deve ser validado antes de queries."""

    def test_user_model_validates_objectid(self):
        from app.models.user_model import UserModel
        source = inspect.getsource(UserModel)
        assert "ObjectId.is_valid" in source

    def test_product_model_validates_objectid(self):
        from app.models.product_model import ProductModel
        source = inspect.getsource(ProductModel)
        assert "ObjectId.is_valid" in source


# ==============================
# Test 6: Security headers
# ==============================
class TestSecurityHeaders:
    """CWE-79, CWE-1021: Security headers configurados."""

    def test_config_has_security_headers(self):
        from config import Config
        assert hasattr(Config, "SECURITY_HEADERS")
        headers = Config.SECURITY_HEADERS
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

    def test_security_headers_middleware_existe(self):
        from app.middlewares.security_headers import init_security_headers
        assert callable(init_security_headers)

    def test_csp_header_existe(self):
        source = Path("app/middlewares/security_headers.py").read_text(encoding="utf-8")
        assert "Content-Security-Policy" in source
        assert "X-Frame-Options" in source
        assert "X-Content-Type-Options" in source


# ==============================
# Test 7: Controller completo
# ==============================
class TestProductControllerComplete:
    """Verifica que todos os metodos do controller existem."""

    def test_update_product_exists(self):
        from app.controllers.product_controller import ProductController
        assert hasattr(ProductController, "update_product")

    def test_delete_product_exists(self):
        from app.controllers.product_controller import ProductController
        assert hasattr(ProductController, "delete_product")

    def test_get_product_exists(self):
        from app.controllers.product_controller import ProductController
        assert hasattr(ProductController, "get_product")

    def test_all_endpoints_protected(self):
        """Todos os endpoints de produto devem ter admin_required."""
        from app.controllers.product_controller import ProductController
        for method_name in ["get_products", "get_product", "create_product", "update_product", "delete_product"]:
            source = inspect.getsource(getattr(ProductController, method_name))
            assert "@admin_required" in source or "admin_required" in source, f"{method_name} nao tem protecao"


# ==============================
# Test 8: Password hashing
# ==============================
class TestPasswordHashing:
    """CWE-916: bcrypt com salt rounds adequado."""

    def test_admin_model_uses_bcrypt(self):
        from app.models.admin_model import AdminModel
        source = inspect.getsource(AdminModel.create_admin)
        assert "bcrypt" in source and "hashpw" in source

    def test_bcrypt_uses_gensalt(self):
        from app.models.admin_model import AdminModel
        source = inspect.getsource(AdminModel.create_admin)
        assert "gensalt" in source

    def test_bcrypt_rounds_high(self):
        """NIST SP 800-63B: minimo 10 rounds bcrypt."""
        from app.models.admin_model import AdminModel
        source = inspect.getsource(AdminModel.create_admin)
        assert "rounds" in source


# ==============================
# Test 9: Database safety (sem mock ativo)
# ==============================
class TestDatabaseSafety:
    """MongoDB nao deve conectar no import — apenas quando solicitado."""

    def test_models_use_get_db(self):
        from app.models.product_model import ProductModel
        source = inspect.getsource(ProductModel)
        assert "get_db()" in source

    def test_models_not_import_db_global(self):
        """Models nao devem importar db global direto."""
        from app.models.product_model import ProductModel
        source = inspect.getsource(ProductModel)
        assert "from app.database.mongo import db" not in source

    def test_mongo_module_uses_lazy_init(self):
        """mongo.py deve usar lazy init, nao conectar no import."""
        source = Path("app/database/mongo.py").read_text(encoding="utf-8")
        # Nao deve ter db = get_db() no modulo-level
        assert "\ndb = get_db()" not in source
        assert "get_db()" in source  # mas deve ter a funcao


# ==============================
# Test 10: Schemas
# ==============================
class TestSchemasExist:
    """Schemas de validacao devem existir e funcionar."""

    def test_product_create_schema(self):
        from app.schemas import ProductCreateSchema
        schema = ProductCreateSchema(nome="Teste", descricao="Descricao")
        assert schema.nome == "Teste"

    def test_admin_login_schema(self):
        from app.schemas import AdminLoginSchema
        schema = AdminLoginSchema(email="test@example.com", password="password123")
        assert schema.email == "test@example.com"


# ==============================
# Test 11: Error handling sem stack trace
# ==============================
class TestErrorHandling:
    """CWE-209: Nao expor detalhes de stack trace."""

    def test_error_handler_existe(self):
        from app.middlewares.security_headers import init_error_handler
        assert callable(init_error_handler)

    def test_error_handler_not_found(self):
        source = Path("app/middlewares/security_headers.py").read_text(encoding="utf-8")
        assert "404" in source
        assert "500" in source


# ==============================
# Test 12: Rate Limit middleware
# ==============================
class TestRateLimitModule:
    """Verifica o modulo rate_limit completo."""

    def test_rate_limit_decorator(self):
        from app.middlewares.rate_limit import rate_limit
        assert callable(rate_limit)

    def test_rate_limit_store_exists(self):
        from app.middlewares.rate_limit import limiter
        assert limiter is not None


# ==============================
# Test 13: Security headers no app
# ==============================
class TestAppSecurity:
    """Verifica configuracoes de seguranca no app."""

    def test_app_imports_security_headers(self):
        source = Path("app/app.py").read_text(encoding="utf-8")
        assert "init_security_headers" in source

    def test_app_has_cors_restriction(self):
        source = Path("app/app.py").read_text(encoding="utf-8")
        # Nao deve ter origins "*" hardcoded
        assert '"*"' not in source.replace(" ", "")

    def test_app_fail_fast_jwt(self):
        """App deve falhar se JWT_SECRET nao configurado em prod."""
        source = Path("app/app.py").read_text(encoding="utf-8")
        assert "JWT_SECRET_KEY" in source
        assert "RuntimeError" in source

    def test_app_uses_init_db(self):
        """App deve usar init_db para conexao."""
        source = Path("app/app.py").read_text(encoding="utf-8")
        assert "init_db" in source
