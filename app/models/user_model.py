"""
UserModel — User data access layer.
Security: Uses get_db() to avoid premature connection.
"""
from app.database.mongo import get_db
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)


class UserModel:

    @staticmethod
    def get_all_users():
        db = get_db()
        users = []

        for user in db.users.find():
            user["_id"] = str(user["_id"])
            users.append(user)

        return users

    @staticmethod
    def create_user(data):
        db = get_db()
        user = {
            "name": data.get("name"),
        }

        result = db.users.insert_one(user)
        user["_id"] = str(result.inserted_id)
        return user

    @staticmethod
    def update_user(user_id, name):
        db = get_db()

        # Valida ObjectId antes de usar (CWE-20)
        if not ObjectId.is_valid(user_id):
            return None

        result = db.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": {"name": name}},
            return_document=True,
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return result

    @staticmethod
    def delete_user(user_id):
        db = get_db()

        if not ObjectId.is_valid(user_id):
            return False

        result = db.users.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
