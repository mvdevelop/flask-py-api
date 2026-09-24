# ==============================
# Configurações da aplicação
# ==============================
# Security Champion Note:
# Nenhum segredo deve ter fallback hardcoded.
# Em produção, a falta de segredos deve causar falha rápida (fail-fast).
# Referência: CWE-798 (Use of Hard-coded Credentials)
# OWASP A05:2021 (Security Misconfiguration)
import os
from dotenv import load_dotenv

load_dotenv()

def _require_env(var_name: str, default: str | None = None) -> str:
    """
    Carrega variável do ambiente. Levanta exceção se não definida
    em modo produção (fail-fast security).
    """
    value = os.environ.get(var_name, default)
    if value is None:
        env = os.environ.get("FLASK_ENV", "production")
        if env == "production":
            raise RuntimeError(
                f"[SECURITY] {var_name} must be configured via environment variable in production. "
                f"See .env.example or deployment documentation."
            )
        return "dev-only-not-for-production"
    return value


class Config:
    # Flask
    SECRET_KEY = _require_env("SECRET_KEY")

    # JWT — sem fallback hardcoded (CWE-798)
    JWT_SECRET_KEY = _require_env("JWT_SECRET_KEY")
    # Expired tokens should be invalidated — shorter window in prod
    JWT_ACCESS_TOKEN_EXPIRES = os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", "3600")
    # CSRF protection for cookie-based auth (se aplicado futuramente)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_COOKIE_CSRF_PROTECT = False  # Usamos Bearer tokens, não cookies

    # MongoDB Atlas
    MONGO_URI = _require_env("MONGO_URI", "mongodb://localhost:27017/py_store")
    MONGO_DB = _require_env("MONGO_DB", "py_store")

    # Uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads", "produtos")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "").split(",") if os.environ.get("CORS_ORIGINS") else []

    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    @staticmethod
    def init_app(app):
        """Inicializa configurações de segurança na aplicação."""
        # Aplica security headers
        @app.after_request
        def set_security_headers(response):
            for header, value in Config.SECURITY_HEADERS.items():
                response.headers[header] = value
            return response


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = "production"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": ProductionConfig,
}

# .env.example content (for documentation):
# =============================================
# # Flask
# SECRET_KEY=your-secure-random-flask-secret-key-here
# FLASK_ENV=production
#
# # JWT
# JWT_SECRET_KEY=your-secure-random-jwt-secret-key-here
# JWT_ACCESS_TOKEN_EXPIRES=3600
#
# # MongoDB
# MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/dbname
# MONGO_DB=py_store
#
# # CORS
# CORS_ORIGINS=https://seusite.com.br,https://admin.seusite.com.br
#
# # Upload
# UPLOAD_BASE_URL=https://api.seusite.com.br
# PORT=5000
