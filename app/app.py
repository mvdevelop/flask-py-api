# ==============================
# Application Factory — PyStore API
# ==============================
# Security Champion Note:
# Esta factory sigue princípios de fail-fast e defesa em profundidade:
# 1. Segredos vêm exclusivamente de environment variables (CWE-798)
# 2. CORS restrito a origens específicas (CWE-306)
# 3. Health check expõe apenas informações mínimas (CWE-200)
# 4. Segredos não são logados (CWE-532)
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import logging
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
        # Em desenvolvimento, permite localhost
        if app.config.get("FLASK_ENV") == "development":
            cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
        else:
            # Em produção, NENHUMA origem por padrão — exige configuração
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
    # MongoDB
    # ==============================
    mongo_uri = app.config.get("MONGO_URI")
    app.db = None

    if not mongo_uri or mongo_uri == "mongodb://localhost:27017/py_store":
        env = os.environ.get("FLASK_ENV", "production")
        if env == "production":
            raise RuntimeError("MONGO_URI não configurada para produção")

    try:
        from pymongo import MongoClient

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Ping — falha rápido se DB inacessível
        client.admin.command("ping")

        db_name = app.config.get("MONGO_DB", "py_store")
        app.db = client[db_name]
        app.mongo_client = client

        logger.info(f"MongoDB conectado | DB: {db_name}")

    except Exception as e:
        logger.error(f"Falha ao conectar MongoDB: {type(e).__name__}")
        raise RuntimeError("Database connection failed") from e

    # ==============================
    # Rotas básicas
    # ==============================
    import datetime

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "service": "PyStore API",
            "status": "operational",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        })

    @app.route("/health", methods=["GET"])
    def health():
        # Mínima disclosure (CWE-200 fix) — não expõe detalhes de infra
        db_status = "connected" if app.db else "disconnected"
        return jsonify({
            "status": "healthy" if app.db else "unhealthy",
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
