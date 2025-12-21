
from flask import Flask, jsonify
from flask_cors import CORS
import os
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    logger.info("=" * 60)
    logger.info("🚀 Criando app Flask - Produção (Render)")
    logger.info("=" * 60)

    app = Flask(__name__)

    # ==============================
    # Configurações básicas
    # ==============================
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

    # ==============================
    # CORS
    # ==============================
    CORS(app, resources={
        r"/api/*": {
            "origins": os.environ.get("CORS_ORIGINS", "*")
        }
    })

    # ==============================
    # MongoDB
    # ==============================
    mongo_uri = os.environ.get("MONGO_URI")
    app.db = None

    if not mongo_uri:
        raise RuntimeError("MONGO_URI não configurada")

    try:
        from pymongo import MongoClient

        logger.info("🔗 Conectando ao MongoDB...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")

        db_name = os.environ.get("MONGO_DB", "py_store")
        app.db = client[db_name]

        logger.info(f"✅ MongoDB conectado | DB: {db_name}")

    except Exception as e:
        logger.error(f"❌ Falha ao conectar MongoDB: {e}")
        raise RuntimeError("Database connection failed")

    # ==============================
    # Rotas básicas
    # ==============================
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "service": "PyStore API",
            "status": "online",
            "environment": "production",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    # ==============================
    # Rotas da API
    # ==============================
    from app.routes.product_routes import product_routes
    app.register_blueprint(product_routes, url_prefix="/api")

    logger.info("=" * 60)
    logger.info("✅ Aplicação Flask pronta para produção")
    logger.info("=" * 60)

    return app
