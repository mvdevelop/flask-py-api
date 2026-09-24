from flask import request, jsonify
from app.models.user_model import UserModel
from app.schemas import UserCreateSchema, UserUpdateSchema
from pydantic import ValidationError


class UserController:

    @staticmethod
    def get_users():
        """Lista todos usuários."""
        users = UserModel.get_all_users()
        return jsonify(users), 200

    @staticmethod
    def create_user():
        """Cria usuário — validado (CWE-20) e sem exposição de campos internos."""
        data = request.get_json()

        if not data:
            return jsonify({"error": "Dados JSON obrigatórios"}), 400

        try:
            schema = UserCreateSchema(**data)
        except ValidationError as e:
            return jsonify({"error": "Dados inválidos", "details": e.errors()}), 400

        user = UserModel.create_user({"name": schema.name})
        return jsonify(user), 201

    @staticmethod
    def update_user(user_id):
        """Atualiza usuário — validado (CWE-20)."""
        data = request.get_json()

        if not data:
            return jsonify({"error": "Dados JSON obrigatórios"}), 400

        try:
            schema = UserUpdateSchema(**data)
        except ValidationError as e:
            return jsonify({"error": "Dados inválidos", "details": e.errors()}), 400

        user = UserModel.update_user(user_id, schema.name)

        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404

        return jsonify(user), 200

    @staticmethod
    def delete_user(user_id):
        """Deleta usuário."""
        success = UserModel.delete_user(user_id)
        if not success:
            return jsonify({"error": "Usuário não encontrado"}), 404

        return jsonify({"message": "Usuário removido com sucesso"}), 200
