
from flask import Blueprint
from app.controllers.product_controller import ProductController

product_routes = Blueprint("product_routes", __name__)

product_routes.route("/produtos", methods=["POST"])(
    ProductController.create_product
)

product_routes.route("/produtos", methods=["GET"])(
    ProductController.get_products
)
