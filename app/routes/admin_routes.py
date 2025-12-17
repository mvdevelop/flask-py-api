
from flask import Blueprint
from app.controllers.admin_controller import AdminController

admin_routes = Blueprint("admin_routes", __name__)

admin_routes.route("/user_admin/login", methods=["POST"])(
    AdminController.login
)
