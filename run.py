
# run.py
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

# ==============================
# Criação do app (ESSENCIAL PARA GUNICORN)
# ==============================
app = create_app(APP_ENV)

# ==============================
# Logging básico
# ==============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================
# Swagger dinâmico
# ==============================
@app.route("/static/swagger.json")
def swagger_json():
    """
    Serve o arquivo swagger.json apropriado para o ambiente
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))

        filenames = (
            ["swagger_prod.json", "swagger.json"]
            if APP_ENV == "production"
            else ["swagger_local.json", "swagger.json"]
        )

        for filename in filenames:
            possible_paths = [
                os.path.join(base_dir, "static", filename),
                os.path.join(base_dir, filename),
                os.path.join(base_dir, "app", "swagger", filename),
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    return send_from_directory(
                        os.path.dirname(path),
                        os.path.basename(path)
                    )

        raise FileNotFoundError("Swagger file not found")

    except Exception as e:
        logger.warning(f"Swagger não encontrado: {e}")

        return jsonify({
            "openapi": "3.0.0",
            "info": {
                "title": "PyStore API",
                "version": "1.0.0",
                "description": "API Documentation"
            },
            "paths": {
                "/health": {
                    "get": {
                        "summary": "Health Check",
                        "responses": {
                            "200": {
                                "description": "Service is healthy"
                            }
                        }
                    }
                }
            }
        }), 200


# ==============================
# Execução LOCAL apenas
# ==============================
if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 5000))
    debug = APP_ENV == "development"

    print("=" * 60)
    print("🚀 Iniciando PyStore API")
    print(f"📍 Endereço: {host}:{port}")
    print(f"🌱 Ambiente: {APP_ENV}")
    print(f"🐛 Debug: {debug}")
    print(f"🕐 Início: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if APP_ENV == "production":
        print("⚠️  Produção detectada")
        print("   Em produção use Gunicorn (Render)")

    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\n👋 Encerrando aplicação...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)
