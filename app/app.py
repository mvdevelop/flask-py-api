
from flask import Flask, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.routes.user_routes import user_routes
from app.routes.product_routes import product_routes
from app.routes.admin_routes import admin_routes
import os

def create_app():
    app = Flask(__name__)

    # 🔐 JWT (Admin Auth)
    app.config["JWT_SECRET_KEY"] = "super-secret-admin-key"
    JWTManager(app)

    # 🔓 CORS TOTALMENTE ABERTO
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        allow_headers="*",
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

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

    # 🔹 Rota pública para servir imagens
    @app.route("/uploads/produtos/<filename>")
    def serve_product_image(filename):
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename
        )

    # 🔹 Rotas da API
    app.register_blueprint(user_routes, url_prefix="/api")
    app.register_blueprint(product_routes, url_prefix="/api")
    app.register_blueprint(admin_routes, url_prefix="/api")

    # 🔹 Swagger
    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.json"

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "API de Usuários, Produtos e Admin"}
    )

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app
