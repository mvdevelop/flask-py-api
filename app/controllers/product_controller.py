
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from app.models.product_model import ProductModel

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class ProductController:

    @staticmethod
    def create_product():
        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        file = request.files.get("img")

        if not nome or not descricao or not file:
            return jsonify({"error": "nome, descricao e img são obrigatórios"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Formato de imagem inválido"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        product = ProductModel.create({
            "nome": nome,
            "descricao": descricao,
            "img": filename
        })

        return jsonify(product), 201

    @staticmethod
    def get_products():
        return jsonify(ProductModel.get_all()), 200
