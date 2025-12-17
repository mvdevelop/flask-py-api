
from flask import Blueprint
from app.controllers.product_controller import ProductController

product_routes = Blueprint("product_routes", __name__)

# 🔹 Lista produtos
@product_routes.route("/produtos", methods=["GET"])
def get_products():
    return ProductController.get_products()

# 🔹 Cria produto com upload de imagem
@product_routes.route("/produtos", methods=["POST"])
def create_product():
    return ProductController.create_product()

# 🔹 (Opcional – pronto para expansão)
# @product_routes.route("/produtos/<string:product_id>", methods=["GET"])
# def get_product(product_id):
#     return ProductController.get_product(product_id)

# @product_routes.route("/produtos/<string:product_id>", methods=["DELETE"])
# def delete_product(product_id):
#     return ProductController.delete_product(product_id)
