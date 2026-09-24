"""
Conexão com MongoDB — versão segura (sem fallback local em produção).
Security Champion Note:
- Removido fallback local de produção (CWE-215: Insertion of Sensitive Information Into Debug Code)
- Não loga URI (CWE-532)
- Fail-fast se MongoDB inacessível em produção
"""
import os
import logging
from pymongo import MongoClient
from flask import current_app

logger = logging.getLogger(__name__)

# Conexão global (thread-safe — PyMongo gerencia pool internamente)
_db = None
_client = None


def init_db(app=None):
    """
    Inicializa conexão com MongoDB.
    Retorna db se sucesso, levanta exceção se falhar em produção.
    """
    global _client, _db

    mongo_uri = None
    if app and app.config.get("MONGO_URI"):
        mongo_uri = app.config["MONGO_URI"]
    elif os.environ.get("MONGO_URI"):
        mongo_uri = os.environ.get("MONGO_URI")
    else:
        logger.warning("MONGO_URI não configurada")
        return None

    db_name = os.environ.get("MONGO_DB", "py_store")

    try:
        _client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            w="majority",
            appname="PyStore-API",
            # Connection pool (evita exhaustion)
            maxPoolSize=50,
            minPoolSize=5,
        )

        # Ping — falha rápido se DB inacessível
        _client.admin.command("ping")
        _db = _client[db_name]

        # Não expõe URI em logs (CWE-532)
        logger.info(f"MongoDB conectado | DB: {db_name}")

        if app:
            app.db = _db
            app.mongo_client = _client

        return _db

    except Exception as e:
        logger.error(f"Falha ao conectar MongoDB: {type(e).__name__}")
        # NÃO loga str(e) — pode conter URI (CWE-532)

        # Fallback apenas em dev (não em prod)
        env = os.environ.get("FLASK_ENV", "production")
        if env == "development":
            try:
                logger.info("Tentando conexão local de fallback (dev only)")
                _client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
                _client.admin.command("ping")
                _db = _client["py_store_dev"]
                logger.info("MongoDB local conectado (dev fallback)")
                if app:
                    app.db = _db
                return _db
            except Exception:
                logger.error("Fallback local também falhou")

        return None


def get_db():
    """Retorna conexão ativa com MongoDB — fail-fast em prod."""
    global _db

    if _db is not None:
        return _db

    # Tenta pegar do current_app (Vercel / serverless)
    try:
        if current_app and hasattr(current_app, "db"):
            _db = current_app.db
            return _db
    except RuntimeError:
        pass  # outside app context

    # Tenta inicializar do ambiente
    _db = init_db()

    # Em produção, falha explícita se DB não conectado
    env = os.environ.get("FLASK_ENV", "production")
    if env == "production" and _db is None:
        raise RuntimeError("MongoDB não conectado em produção")

    return _db


def close_db():
    """Fecha conexão com MongoDB."""
    global _client
    if _client:
        _client.close()
        logger.info("Conexão MongoDB fechada")


# Não expõe db global no import (evita conexão prematura)
# Modelos devem usar get_db() ou app.db
