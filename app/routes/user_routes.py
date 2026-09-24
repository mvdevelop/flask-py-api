from flask import Blueprint
from app.controllers.user_controller import UserController

user_routes = Blueprint("user_routes", __name__)

# GET e POST de users são públicos (cria conta, lista)
# PUT e DELETE requerem autenticação (aplicada no controller ou próxima etapa)
user_routes.route("/users", methods=["GET"])(UserController.get_users)
user_routes.route("/users", methods=["POST"])(UserController.create_user)
user_routes.route("/users/<string:user_id>", methods=["PUT"])(UserController.update_user)
user_routes.route("/users/<string:user_id>", methods=["DELETE"])(UserController.delete_user)
