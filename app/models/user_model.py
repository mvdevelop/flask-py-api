
from app.database.mongo import db
from bson.objectid import ObjectId

class UserModel:

    @staticmethod
    def get_all_users():
        users = []

        for user in db.users.find():
            user["_id"] = str(user["_id"])
            users.append(user)

        return users

    @staticmethod
    def create_user(data):
        user = {
            "name": data.get("name")
        }

        result = db.users.insert_one(user)
        user["_id"] = str(result.inserted_id)

        return user

    @staticmethod
    def update_user(user_id, name):
        result = db.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": {"name": name}},
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return result

    @staticmethod
    def delete_user(user_id):
        result = db.users.delete_one(
            {"_id": ObjectId(user_id)}
        )

        return result.deleted_count > 0
