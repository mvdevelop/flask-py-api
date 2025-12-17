
from flask import Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from app.routes.user_routes import user_routes

def create_app():
    app = Flask(__name__)

    # 🔹 Rota inicial
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "message": "API rodando 🚀"
        })

    # 🔹 Rotas da API
    app.register_blueprint(user_routes, url_prefix="/api")

    # 🔹 Swagger
    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.json"

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "API de Usuários"}
    )

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app
