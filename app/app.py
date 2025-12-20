
# app/app.py
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import datetime
import logging

# ==============================
# Logging básico
# ==============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_name="production"):
    """Factory function para criar a aplicação Flask"""

    logger.info("=" * 60)
    logger.info(f"🚀 Criando app Flask - Ambiente: {config_name}")
    logger.info("=" * 60)

    app = Flask(__name__)

    # ==============================
    # Configurações
    # ==============================
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

    # ==============================
    # JWT
    # ==============================
    jwt_secret = os.environ.get("JWT_SECRET_KEY")

    if not jwt_secret and config_name == "production":
        raise RuntimeError("JWT_SECRET_KEY não configurada em produção")

    app.config["JWT_SECRET_KEY"] = jwt_secret or "dev-secret-key"
    JWTManager(app)
    logger.info("🔐 JWT configurado")

    # ==============================
    # CORS
    # ==============================
    CORS(app, resources={r"/*": {"origins": "*"}})

    # ==============================
    # MongoDB
    # ==============================
    mongo_uri = os.environ.get("MONGO_URI")
    app.db = None

    if mongo_uri:
        try:
            from pymongo import MongoClient

            logger.info("🔗 Conectando ao MongoDB...")
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")

            db_name = os.environ.get("MONGO_DB", "py_store")
            app.db = client[db_name]

            logger.info(f"✅ MongoDB conectado | DB: {db_name}")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB indisponível: {e}")
            app.db = None
    else:
        logger.warning("⚠️ MONGO_URI não configurada")

    # ==============================
    # Rotas básicas
    # ==============================
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "message": "PyStore API 🚀",
            "status": "online",
            "database": "connected" if app.db is not None else "disconnected",
            "environment": config_name,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy" if app.db is not None else "degraded",
            "service": "pystore-api",
            "database": "connected" if app.db is not None else "disconnected",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    # ==============================
    # Rotas da API
    # ==============================
    try:
        from app.routes.product_routes import product_routes
        app.register_blueprint(product_routes, url_prefix="/api")
        logger.info("✅ product_routes carregado")
    except ImportError as e:
        logger.warning(f"⚠️ product_routes não carregado: {e}")

        @app.route("/api/produtos", methods=["GET"])
        def produtos_fallback():
            return jsonify({
                "products": [],
                "message": "Products module not available"
            })

    logger.info("=" * 60)
    logger.info("✅ Aplicação Flask criada com sucesso!")
    logger.info("=" * 60)

    return app
