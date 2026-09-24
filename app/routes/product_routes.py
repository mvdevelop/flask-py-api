from flask import Blueprint
from app.controllers.product_controller import ProductController

product_routes = Blueprint("product_routes", __name__, url_prefix="/produtos")

# ==============================
# Todos os endpoints de produtos são protegidos por admin_required
# (aplicado no controller via decorator)
# ==============================
product_routes.route("", methods=["GET"])(ProductController.get_products)
product_routes.route("", methods=["POST"])(ProductController.create_product)
product_routes.route("/<string:product_id>", methods=["GET"])(ProductController.get_product)
product_routes.route("/<string:product_id>", methods=["PUT"])(ProductController.update_product)
product_routes.route("/<string:product_id>", methods=["DELETE"])(ProductController.delete_product)
