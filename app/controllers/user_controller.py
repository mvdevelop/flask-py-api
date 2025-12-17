
from flask import jsonify, request
from app.models.user_model import UserModel

class UserController:

    @staticmethod
    def get_users():
        users = UserModel.get_all_users()
        return jsonify(users), 200

    @staticmethod
    def create_user():
        data = request.get_json()

        if not data or "name" not in data:
            return jsonify({"error": "Nome é obrigatório"}), 400

        user = UserModel.create_user(data)
        return jsonify(user), 201

    @staticmethod
    def update_user(user_id):
        data = request.get_json()

        if not data or "name" not in data:
            return jsonify({"error": "Nome é obrigatório"}), 400

        user = UserModel.update_user(user_id, data["name"])

        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404

        return jsonify(user), 200

    @staticmethod
    def delete_user(user_id):
        success = UserModel.delete_user(user_id)

        if not success:
            return jsonify({"error": "Usuário não encontrado"}), 404

        return jsonify({"message": "Usuário removido com sucesso"}), 200
