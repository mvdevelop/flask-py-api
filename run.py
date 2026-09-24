"""
Entry point da PyStore API.
Para produção: gunicorn -w 4 -b 0.0.0.0:$PORT run:app
"""
import os
import sys
import datetime
import logging
from flask import send_from_directory, jsonify
from app.app import create_app

# ==============================
# Ambiente
# ==============================
APP_ENV = os.getenv("APP_ENV", "production")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ==============================
# Criação do app (ESSENCIAL PARA GUNICORN)
# ==============================
try:
    app = create_app(APP_ENV)
except RuntimeError as e:
    logger.error(f"Falha na inicialização: {e}")
    sys.exit(1)


# ==============================
# Swagger JSON — serve arquivo estático
# ==============================
@app.route("/static/swagger.json")
def swagger_json():
    """
    Serve o swagger.json.
    Em dev: app/static/swagger.json (se existir)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "app", "static", "swagger.json"),
        os.path.join(base_dir, "static", "swagger.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            from flask import send_file
            return send_file(path, mimetype="application/json")

    logger.warning("Swagger JSON não encontrado — servindo fallback")
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "PyStore API",
            "version": "1.0.0",
            "description": "API Documentation — configure MONGO_URI e JWT_SECRET_KEY",
        },
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health Check",
                    "responses": {"200": {"description": "Service is healthy"}},
                }
            }
        },
    }), 200


# ==============================
# Execução LOCAL
# ==============================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = APP_ENV == "development"

    print("=" * 60)
    print("PyStore API")
    print(f"  Host: 0.0.0.0:{port}")
    print(f"  Env:  {APP_ENV}")
    print(f"  Debug: {debug}")
    print(f"  Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if APP_ENV == "production":
        print("⚠️  Produção — use gunicorn (Render)")

    try:
        app.run(
            host="0.0.0.0",
            port=port,
            debug=debug,
            use_reloader=debug,
        )
    except KeyboardInterrupt:
        print("\nEncerrando...")
        sys.exit(0)
    except Exception as e:
        print(f"Erro ao iniciar: {e}")
        sys.exit(1)
