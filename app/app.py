
from flask import Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from app.routes.user_routes import user_routes
from app.routes.product_routes import product_routes
import os

def create_app():
    app = Flask(__name__)

    # 🔹 Configuração de upload
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads", "produtos")

    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # 🔹 Rota inicial
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({"message": "API rodando 🚀"})

    # 🔹 Rotas da API
    app.register_blueprint(user_routes, url_prefix="/api")
    app.register_blueprint(product_routes, url_prefix="/api")

    # 🔹 Swagger
    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.json"

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "API de Usuários e Produtos"}
    )

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app
