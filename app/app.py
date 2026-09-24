# ==============================
# Application Factory — PyStore API
# ==============================
# Security Champion Note:
# Esta factory implementa defesa em profundidade:
# 1. Fail-fast security — segredos do environment (CWE-798)
# 2. CORS restrito (CWE-306)
# 3. Security headers + CSP (CWE-79, CWE-1021)
# 4. Rate limiting global (CWE-307, CWE-770)
# 5. Error handling sem vazamento (CWE-209)
# 6. Health check minimal disclosure (CWE-200)
# 7. Logging estruturado sem PII (CWE-532)
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import logging
import datetime
from config import config

# Logging estruturado (evita print() — CWE-532)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config_name: str = "default") -> Flask:
    """Factory para criar a aplicação Flask com segurança configurada."""

    logger.info("=" * 60)
    logger.info("Inicializando PyStore API")
    logger.info("=" * 60)

    app = Flask(__name__)

    # ==============================
    # Configurações (fail-fast security)
    # ==============================
    app.config.from_object(config[config_name])
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

    # ==============================
    # JWT — inicializado com secret do env
    # ==============================
    jwt_secret = app.config.get("JWT_SECRET_KEY")
    if not jwt_secret or jwt_secret == "dev-only-not-for-production":
        env = os.environ.get("FLASK_ENV", "production")
        if env == "production":
            raise RuntimeError(
                "JWT_SECRET_KEY não configurada. A aplicação não iniciará em produção sem segredo válido."
            )
        logger.warning("JWT_SECRET_KEY usando fallback de desenvolvimento")

    JWTManager(app)
    logger.info("JWT configurado")

    # ==============================
    # CORS — origens restritas (CWE-306 fix)
    # ==============================
    cors_origins = app.config.get("CORS_ORIGINS", [])
    if not cors_origins or cors_origins == [""]:
        if app.config.get("FLASK_ENV") == "development":
            cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
        else:
            cors_origins = []
            logger.warning("CORS_ORIGINS não configurada — API será inacessível via browser até configurado")

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": False,
            }
        },
    )
    logger.info(f"CORS configurado para origens: {cors_origins}")

    # ==============================
    # Security Headers Middleware (CWE-79, CWE-1021, CWE-430)
    # ==============================
    from app.middlewares.security_headers import init_security_headers, init_error_handler

    init_security_headers(app)
    init_error_handler(app)

    # ==============================
    # MongoDB — usa camada database/mongo.py (testável)
    # ==============================
    from app.database.mongo import init_db

    # init_db falha com RuntimeError em produção se DB inacessível
    db = init_db(app)
    if db is None and os.environ.get("FLASK_ENV", "production") == "production":
        raise RuntimeError("MongoDB não conectado em produção")

    app.db = db
    logger.info("MongoDB configurado no app")

    # ==============================
    # Rotas básicas
    # ==============================
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "service": "PyStore API",
            "status": "operational",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        })

    @app.route("/health", methods=["GET"])
    def health():
        # Mínima disclosure (CWE-200 fix)
        status = "healthy" if app.db else "unhealthy"
        return jsonify({
            "status": status,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }), 200 if app.db else 503

    # ==============================
    # Rotas da API
    # ==============================
    from app.routes.product_routes import product_routes
    from app.routes.user_routes import user_routes
    from app.routes.admin_routes import admin_routes

    app.register_blueprint(product_routes, url_prefix="/api")
    app.register_blueprint(user_routes, url_prefix="/api")
    app.register_blueprint(admin_routes, url_prefix="/api")

    logger.info("Aplicação Flask pronta")
    return app
