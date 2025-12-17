
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
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

        # 🔹 Gera nome único para evitar sobrescrita
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"

        filename = secure_filename(unique_filename)
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # 🔹 MONTA URL PÚBLICA DA IMAGEM
        image_url = f"https://flask-py-api.onrender.com//uploads/produtos/{filename}"
        #image_url = f"http://localhost:3000/uploads/produtos/{filename}"

        product = ProductModel.create({
            "nome": nome,
            "descricao": descricao,
            "img": image_url  # 👈 agora é URL
        })

        return jsonify(product), 201

    @staticmethod
    def get_products():
        return jsonify(ProductModel.get_all()), 200
