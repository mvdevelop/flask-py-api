
from flask import request, jsonify
from flask_jwt_extended import create_access_token
import bcrypt
from app.models.admin_model import AdminModel

class AdminController:

    @staticmethod
    def login():
        data = request.get_json()

        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email e senha são obrigatórios"}), 400

        admin = AdminModel.find_by_email(data["email"])

        if not admin:
            return jsonify({"error": "Credenciais inválidas"}), 401

        if not bcrypt.checkpw(
            data["password"].encode("utf-8"),
            admin["password"]
        ):
            return jsonify({"error": "Credenciais inválidas"}), 401

        token = create_access_token(
            identity=str(admin["_id"]),
            additional_claims={"role": "admin"}
        )

        return jsonify({
            "token": token,
            "admin": {
                "id": str(admin["_id"]),
                "email": admin["email"]
            }
        }), 200
