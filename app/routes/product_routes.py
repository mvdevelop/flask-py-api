
from flask import Blueprint, request
from app.controllers.product_controller import ProductController

product_routes = Blueprint(
    "product_routes",
    __name__,
    url_prefix="/produtos"
)

# ==============================
# LIST
# GET /produtos
# ==============================
@product_routes.route("", methods=["GET"])
def list_products():
    return ProductController.get_products()

# ==============================
# CREATE
# POST /produtos
# ==============================
@product_routes.route("", methods=["POST"])
def create_product():
    return ProductController.create_product()

# ==============================
# READ
# GET /produtos/<id>
# ==============================
@product_routes.route("/<string:product_id>", methods=["GET"])
def get_product(product_id):
    return ProductController.get_product(product_id)

# ==============================
# UPDATE
# PUT /produtos/<id>
# ==============================
@product_routes.route("/<string:product_id>", methods=["PUT"])
def update_product(product_id):
    return ProductController.update_product(product_id)

# ==============================
# DELETE
# DELETE /produtos/<id>
# ==============================
@product_routes.route("/<string:product_id>", methods=["DELETE"])
def delete_product(product_id):
    return ProductController.delete_product(product_id)
