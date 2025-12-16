
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from app.routes.user_routes import user_routes

def create_app():
    app = Flask(__name__)

    app.register_blueprint(user_routes, url_prefix="/api")

    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.json"

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "API de Usuários"}
    )

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app
