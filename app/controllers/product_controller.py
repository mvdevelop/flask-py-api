from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.models.product_model import ProductModel
from app.schemas import ProductCreateSchema, ProductUpdateSchema
from app.middlewares.auth import admin_required
from pydantic import ValidationError
import os
import uuid
import datetime

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def allowed_file(filename: str) -> bool:
    """Valida extensão do arquivo — whitelist segura (CWE-434)."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class ProductController:

    @staticmethod
    @admin_required
    def get_products():
        """Lista todos produtos ativos — protegido (admin)."""
        try:
            result = ProductModel.get_all()
            return jsonify(result), 200
        except Exception:
            return jsonify({"error": "Erro ao buscar produtos"}), 500

    @staticmethod
    @admin_required
    def get_product(product_id: str):
        """Busca produto por ID — protegido (admin)."""
        product = ProductModel.get_by_id(product_id)
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404
        return jsonify(product), 200

    @staticmethod
    @admin_required
    def create_product():
        """Cria produto via JSON validado ou multipart form."""
        try:
            nome = None
            descricao = None
            image_url = None

            # ==============================
            # JSON validado por Pydantic (CWE-20 fix)
            # ==============================
            if request.is_json:
                data = request.get_json()
                try:
                    schema = ProductCreateSchema(**data)
                    nome = schema.nome
                    descricao = schema.descricao
                    image_url = schema.image_url
                except ValidationError as e:
                    return jsonify({"error": "Dados inválidos", "details": e.errors()}), 400

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
                        request.host_url.rstrip("/"),
                    )
                    image_url = f"{base_url}/uploads/produtos/{filename}"

            if not nome or not descricao:
                return jsonify({"error": "nome e descricao são obrigatórios"}), 400

            product = {
                "nome": nome,
                "descricao": descricao,
                "img": image_url,
                "created_at": datetime.datetime.utcnow(),
            }

            created = ProductModel.create(product)
            return jsonify(created), 201

        except Exception:
            # Não expõe stack trace (CWE-209)
            return jsonify({"error": "Erro ao criar produto"}), 500

    @staticmethod
    @admin_required
    def update_product(product_id: str):
        """Atualiza produto por ID — protegido (admin) + validado (CWE-20)."""
        product = ProductModel.get_by_id(product_id)
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "Payload JSON obrigatório"}), 400

        # Strip keys perigosos antes de atualizar (prevenir mass assignment)
        data.pop("_id", None)
        data.pop("created_at", None)
        data.pop("active", None)  # active só via soft-delete controller

        try:
            schema = ProductUpdateSchema(**data)
            update_data = {k: v for k, v in schema.model_dump(exclude_unset=True).items() if v is not None}
            if not update_data:
                return jsonify({"error": "Nenhum campo válido para atualizar"}), 400

            success = ProductModel.update(product_id, update_data)
            if not success:
                return jsonify({"error": "Produto não encontrado"}), 404

            updated = ProductModel.get_by_id(product_id)
            return jsonify(updated), 200
        except ValidationError as e:
            return jsonify({"error": "Dados inválidos", "details": e.errors()}), 400

    @staticmethod
    @admin_required
    def delete_product(product_id: str):
        """Deleta produto (soft delete) — protegido (admin)."""
        product = ProductModel.get_by_id(product_id)
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404

        if product.get("img"):
            filename = product["img"].split("/")[-1]
            upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads/produtos")
            filepath = os.path.join(upload_folder, filename)
            if os.path.exists(filepath):
                os.remove(filepath)

        ProductModel.delete(product_id)
        return jsonify({"success": True}), 200
