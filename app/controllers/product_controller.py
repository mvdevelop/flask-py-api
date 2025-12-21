
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.models.product_model import ProductModel
import os
import uuid
import datetime

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

class ProductController:

    @staticmethod
    def create_product():
        try:
            nome = None
            descricao = None
            image_url = None
            filename = None

            # ==============================
            # JSON
            # ==============================
            if request.is_json:
                data = request.get_json()
                nome = data.get("nome")
                descricao = data.get("descricao")
                image_url = data.get("image_url")

            # ==============================
            # multipart/form-data
            # ==============================
            else:
                nome = request.form.get("nome")
                descricao = request.form.get("descricao")
                file = request.files.get("img")

                if file and file.filename:
                    if not allowed_file(file.filename):
                        return jsonify({"error": "Formato de imagem inválido"}), 400

                    ext = os.path.splitext(file.filename)[1]
                    filename = secure_filename(f"{uuid.uuid4()}{ext}")

                    upload_folder = current_app.config.get(
                        "UPLOAD_FOLDER", "uploads/produtos"
                    )
                    os.makedirs(upload_folder, exist_ok=True)

                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)

                    base_url = os.environ.get(
                        "UPLOAD_BASE_URL",
                        request.host_url.rstrip("/")
                    )
                    image_url = f"{base_url}/uploads/produtos/{filename}"

            if not nome or not descricao:
                return jsonify({"error": "nome e descricao são obrigatórios"}), 400

            product = {
                "nome": nome,
                "descricao": descricao,
                "img": image_url,
                "created_at": datetime.datetime.utcnow()
            }

            created = ProductModel.create(product)
            return jsonify(created), 201

        except Exception as e:
            return jsonify({"error": "Erro ao criar produto"}), 500

    @staticmethod
    def get_products():
        try:
            products = ProductModel.get_all()
            return jsonify({
                "count": len(products),
                "products": products
            }), 200
        except Exception:
            return jsonify({"error": "Erro ao buscar produtos"}), 500

    @staticmethod
    def get_product(product_id):
        product = ProductModel.get_by_id(product_id)
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404
        return jsonify(product), 200

    @staticmethod
    def delete_product(product_id):
        product = ProductModel.get_by_id(product_id)
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404

        if product.get("img"):
            filename = product["img"].split("/")[-1]
            upload_folder = current_app.config.get(
                "UPLOAD_FOLDER", "uploads/produtos"
            )
            filepath = os.path.join(upload_folder, filename)
            if os.path.exists(filepath):
                os.remove(filepath)

        ProductModel.delete(product_id)
        return jsonify({"success": True}), 200
